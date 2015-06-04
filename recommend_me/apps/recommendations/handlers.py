import urllib
import urlparse
import logging
from functools import partial
from datetime import datetime
import json
import tornadio2
from tornadio2 import gen as tornadio2_gen

import tornado.web
import tornado
from tornado.httputil import url_concat
from tornado.httpclient import AsyncHTTPClient
from tornado import gen

from base.handlers import BaseHandler
from smlr.apps.api.mixins import BaseApiMixin as SmlrBaseApiMixin
from activity.mixins import ActivityMixin


CATEGORIES = ['movies', 'television', 'music', 'games', 'books']
DISALLOWED_CATEGORIES = [
    'Movie genre', 'Actor/director',
    'Musical genre', 'Album', 'Interest', 'Book genre',
    'Tv channel', 'Tv network'
]
logger = logging.getLogger('recommend_me')


class UpdateProfileMixin(SmlrBaseApiMixin):

    def update_profile(
        self, user_data, access_token=None, category='movies', callback=None
    ):
        '''update info about given user profile'''

        logger.debug('Updating user "%s" profile...' % user_data['id'])
        logger.debug('Fetching list of %s for user "%s"...' % (category, user_data['id']))
        self.facebook_request(
            '/%s/%s' % (user_data['id'], category),
            callback=partial(
                self.update_profile_callback,
                user_data=user_data, access_token=access_token,
                category=category,
                update_user_stats=True,
                callback=callback
            ),
            access_token=access_token or user_data["access_token"]
        )

    @gen.engine
    def update_profile_callback(
        self, data, category='movies', user_data={}, access_token=None,
        log_function=None, update_user_stats=False, callback=None
    ):
        # TODO add old data deletion

        logger.debug('Received data from Facebook: %s' % data)
        if log_function:
            log_function('Updating data for user "%s"' % (
                user_data['id']
            ))

        tasks = []
        data_to_track = {}
        for item in data['data']:
            # checking if item category is allowed
            if item['category'] in DISALLOWED_CATEGORIES:
                continue
            # getting target_id, it will be different from item id
            # if current item is duplicate of it
            target_id = self.redis.get('duplicates:%s' % item['id']) \
                or item['id']
            is_removed = self.redis.get('removed:%s' % target_id)
            if is_removed:
                logger.debug(
                    'Item %s is removed by admin, skipping...' % item['id']
                )
                continue
            update_data = {
                'id': target_id,
                'category': category,
            }
            if target_id == item['id']:
                update_data['name'] = item['name']
                logger.debug('Updating data for user "%s" and item "%s: %s"...' % (
                    user_data['id'], target_id, item['name']
                ))
                tasks.append(gen.Task(
                    self.async_db.items.update,
                    {'id': target_id},
                    {'$set': update_data},
                    upsert=True
                ))
            else:
                logger.debug(
                    'Item %s id is duplicate of item %s' % (item['id'], target_id)
                )
            data_to_track[target_id] = 1
        yield tasks

        if data['data']:
            items_count = yield gen.Task(
                self.track, user_data['id'], data_to_track, category
            )

            if update_user_stats:
                # updating current user stats
                yield gen.Task(
                    self.async_db.users.update,
                    {'id': user_data['id']},
                    {'$set': {'items_count.%s' % category: items_count}},
                    upsert=True
                )

        if callback:
            callback()

    @gen.engine
    def full_profile_update(
        self, user_data, category='movies',
        friends_count_log_function=None, friend_log_function=None,
        callback=None
    ):
        '''updates profile of user's friends'''

        logger.debug('Fetching friends list for user "%s"...' % user_data['id'])
        data = yield gen.Task(
            self.facebook_request,
            '/me/friends',
            access_token=user_data["access_token"]
        )

        logger.debug('Received data from Facebook: %s' % data)
        friends_ids = [f['id'] for f in data['data']]
        logger.debug('Updating friendship info between users %s and %s' % (
            user_data['id'], friends_ids
        ))
        if friends_count_log_function:
            friends_count_log_function(len(friends_ids))
        yield gen.Task(
            self.friendship, user_data['id'], friends_ids, category
        )
        yield gen.Task(
            self.update_profile,
            user_data, category=category
        )
        friends = data['data']
        tasks = []
        for i in xrange(0, len(friends), 20):
            batch_queries = []
            for friend_data in friends[i:i + 20]:
                batch_queries.append({
                    'method': 'GET',
                    'relative_url': '/%s/%s' % (friend_data['id'], category)
                })
            tasks.append(gen.Task(
                self.facebook_request, '/',
                post_args={'batch': json.dumps(batch_queries)},
                access_token=user_data["access_token"]
            ))
        results = yield tasks
        friends_likes = []
        for r in results:
            friends_likes += r

        for i in xrange(len(friends_likes)):
            friend_data = friends[i]
            if friend_data:
                friend_likes = json.loads(friends_likes[i]['body'])

                logger.debug('Updating profile for friend "%s" of user "%s"' % (
                    friend_data['id'], user_data['id']
                ))
                result = yield gen.Task(
                    self.async_db.users.update,
                    {'id': friend_data['id']}, {'$set': friend_data}, upsert=True
                )
                logger.debug('Updated user info for user %s with result %s' % (
                    friend_data['id'], result.args[0]
                ))
                # TODO add error handling
                result = yield gen.Task(
                    self.update_profile_callback,
                    friend_likes, user_data=friend_data,
                    access_token=user_data['access_token'],
                    log_function=friend_log_function,
                    category=category
                )

        yield gen.Task(
            self.async_db.users.update,
            {'id': user_data['id']},
            {'$set': {'imported_categories.%s' % category: datetime.now()}},
            upsert=True
        )

        if callback:
            callback()


class UpdateProfileHandler(
    UpdateProfileMixin, tornado.auth.FacebookGraphMixin, BaseHandler
):

    @tornado.web.authenticated
    @tornado.web.asynchronous
    @gen.engine
    def get(self, category='movies'):

        data = yield gen.Task(self.get_current_user_async)
        yield gen.Task(
            self.full_profile_update,
            user_data=data, category=category
        )
        self.redirect(
            self.reverse_url('recommendations', category)
        )


class UpdateProfileConnection(
    UpdateProfileMixin, tornado.auth.FacebookGraphMixin,
    tornadio2.SocketConnection
):
    def __init__(self, *args, **kwargs):
        super(UpdateProfileConnection, self).__init__(*args, **kwargs)
        self.application = self.session.handler.application
        self.db = self.application.db
        self.async_db = self.application.async_db
        self.redis = self.application.redis
        self.settings = self.application.settings
        self.username = self.settings['smlr_username']
        self.get_secure_cookie = self.session.handler.get_secure_cookie
        self.async_callback = self.session.handler.async_callback

    @tornadio2.event('do_update')
    def do_update(self, category):
        user_id = self.get_secure_cookie("user")
        user_id = tornado.escape.json_decode(user_id)
        result = yield gen.Task(
            self.async_db.users.find_one,
            {'id': user_id},
        )
        data = result.args[0]
        yield gen.Task(
            self.full_profile_update,
            friends_count_log_function=lambda c: \
                self.emit('update-profile-friends-count', c),
            friend_log_function=lambda m: \
                self.emit('update-profile-new-data', m),
            user_data=data, category=category
        )
        self.emit('update-profile-finish', True)

    @tornadio2_gen.sync_engine
    def on_event(self, name, *args, **kwargs):
        """Taken from tornadio2 examples"""
        return super(UpdateProfileConnection, self).on_event(name, *args, **kwargs)


class RecommendationsHandler(
    UpdateProfileMixin, tornado.auth.FacebookGraphMixin, BaseHandler
):

    def render_results(
        self, items, status, items_count, category, tags=[], tag=None
    ):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            self.add_header('Content-Type', 'application/json')
            self.finish(json.dumps({
                'status': status,
                'items': items,
                'items_count': items_count,
            }))
        else:
            self.jinja_render(
                'recommendations/list.html', items=items,
                category=category, items_count=items_count,
                friends_only=self.friends_only,
                PARSED_VERSION=self.settings['parsed_version'],
                socket_io_port=self.settings['frontend_socket_io_port'],
                tags=tags, tag=tag
            )

    @gen.engine
    def _items_find_callback(
        self, result, error, relevance, skip, limit, category,
        save_to_cache=True, tag=None
    ):
        mapping = {}
        for item in result:
            if '_id' in item:
                del item['_id']
            mapping[item['id']] = item
        items = []
        for info in relevance:
            if info['item_id'] in mapping:
                items.append({
                    'info': mapping[info['item_id']],
                    'relevance': info['value'],
                })
            else:
                logger.error(
                    "Can't find item info for item %s" % info['item_id']
                )

        # extracting tags
        tags = set()
        for item in items:
            current_tags = item['info'].get('details', {}).get('tags', [])
            for current_tag in current_tags:
                tags.add(current_tag)
        tags = sorted(tags)

        # applying tags
        if tag:
            items = [
                i for i in items \
                    if not i['info'].get('details', {}) \
                    or tag in i['info'].get('details', {}).get('tags', [])
            ]
        if save_to_cache:
            data = json.dumps({
                'status': 'ok',
                'items': items,
                'items_count': len(items),
            })
            self.redis.set(
                'recommendations:%s:%s:%s' % (self.user_id, category, tag), data
            )
        items_count = len(items)
        # trimming results
        items = items[skip:skip + limit]
        self.render_results(items, 'ok', items_count, category, tags=tags, tag=tag)

    @gen.engine
    def _render_random_items(self, skip, limit, category, tag, save_to_cache=True):
        result = yield gen.Task(
            self.account_items, self.user_id,
            category
        )
        items_ids = result.args[0]
        result = yield gen.Task(
            self.async_db.items.find,
            {
                'category': category,
                'id': {'$nin': items_ids}
            },
            fields=[
                'id', 'name', 'details.image', 'details.image_large',
                'details.link', 'details.tags', 'details.parsed_version',
                'details.likes', 'details.video'
            ],
            sort=[('details.likes', -1)],
            skip=0,
            limit=2000,
        )
        items = [{'info': i} for i in result.args[0]]
        for item in items:
            del item['info']['_id']

        if save_to_cache:
            data = json.dumps({
                'status': 'no-recommendations',
                'items': items,
                'items_count': False,
            })
            self.redis.set(
                'recommendations:%s:%s:%s' % (self.user_id, category, tag), data
            )
        # trimming results
        items = items[skip:skip + limit]

        self.render_results(items, 'no-recommendations', False, category)

    @gen.engine
    def _smlr_recommendations_callback(
        self, results, code, items_count=0, friends_count=0,
        likes_count=0, skip=0, limit=15, category='movies', tag=None
    ):
        is_render_random_items = False
        if results is False:
            if code == 'account-not-exist':
                is_render_random_items = True
        elif not results \
        or (likes_count < 7 or (likes_count < 15 and items_count < 7)):
            is_render_random_items = True

        if is_render_random_items:
            self._render_random_items(skip, limit, category, tag)
            return

        # updating current user stats
        if self.is_current_user and (
            self.current_user.get('friends_count') != friends_count \
            or self.current_user.get('items_count.%s' % category) != likes_count
        ):
            yield gen.Task(
                self.async_db.users.update,
                {'id': self.user_id},
                {'$set': {
                    'friends_count': friends_count,
                    'items_count.%s' % category: likes_count,
                }},
                upsert=True
            )
            self.current_user['friends_count'] = friends_count

        # doing items mapping
        ids = [i['item_id'] for i in results]
        self.async_db.items.find(
            {'id': {'$in': ids}},
            limit=len(ids),
            fields=[
                'id', 'name', 'details.image', 'details.image_large',
                'details.link', 'details.tags', 'details.parsed_version',
                'details.video'
                #'details.category', 'details.amazon_links', 'details.itunes_links'
            ],
            callback=partial(
                self._items_find_callback, relevance=results,
                skip=skip, limit=limit, category=category, tag=tag
            )
        )

    @tornado.web.asynchronous
    @gen.engine
    def get(self, uid=None, category='movies'):
        '''render recommendations'''

        self.friends_only = bool(self.get_argument('friends_only', False))
        skip = self.get_argument('skip', 0)
        limit = self.get_argument('limit', 15)
        tag = self.get_argument('tag', None)
        try:
            skip = int(skip)
        except ValueError:
            skip = 0
        try:
            limit = int(limit)
        except ValueError:
            limit = 15

        if uid:
            self.is_current_user = False
            self.user_id = uid
        else:
            self.is_current_user = True
            self.user_id = yield gen.Task(self.get_current_user_id_async)
            if not self.user_id:
                url = self.get_login_url()
                next_url = self.request.uri
                url += "?" + urllib.urlencode(dict(next=next_url))
                self.redirect(url)
                return
            result = yield gen.Task(
                self.async_db.users.find_one,
                {'id': self.user_id},
                fields=['imported_categories']
            )
            user_data = result.args[0]
            imported_categories = user_data.get('imported_categories', {})
            if category not in imported_categories \
            or datetime.now() - imported_categories[category] > \
                self.settings['full_profile_update_timedelta']:

                self.jinja_render(
                    'recommendations/list.html', items=[],
                    category=category, need_update=True,
                    friends_only=self.friends_only,
                    PARSED_VERSION=self.settings['parsed_version'],
                    socket_io_port=self.settings['frontend_socket_io_port'],
                    items_count=False
                )
                return

        if 'get_from_cache' in self.request.arguments \
        and self.get_argument('get_from_cache'):
            cache_data = self.redis.get('recommendations:%s:%s:%s' % (
                self.user_id, category, tag
            ))
        else:
            cache_data = None
        if cache_data:
            data = json.loads(cache_data)
            self.render_results(
                data['items'][skip:skip + limit], data['status'],
                data['items_count'], category
            )
        else:
            self.items_for_account(
                self.user_id, category, limit=2000, skip=0,
                friends_only=self.friends_only,
                callback=partial(
                    self._smlr_recommendations_callback, skip=skip,
                    limit=limit, category=category,
                    tag=tag
                )
            )


class FacebookSubscribeHandler(tornado.auth.FacebookGraphMixin, BaseHandler):

    @tornado.web.authenticated
    @tornado.web.asynchronous
    def get(self):

        def _subscribe_callback(response):
            self.finish('Done')

        def _subscribe(response):
            if response.error:
                logger.warning("Could not fetch access token")
            access_token = urlparse.parse_qs(response.body).get('access_token')
            if not access_token:
                logger.warning("Could not parse access token")
            else:
                access_token = access_token[0]
            logger.debug('Access token: %s' % access_token)
            self.facebook_request(
                '/%s/subscriptions' % self.settings['facebook_app_id'],
                post_args={
                    'object': 'user',
                    'fields': 'interests, likes, music, books, movies',
                    'callback_url': "%s%s" % (
                        self.settings['host_name'],
                        self.reverse_url('facebook-callback')
                    ),
                    'access_token': access_token,
                    'verify_token': "recommend_me"
                },
                callback=_subscribe_callback,
            )

        http = AsyncHTTPClient()
        url = self._OAUTH_ACCESS_TOKEN_URL
        args = {
            'client_id': self.settings['facebook_app_id'],
            'client_secret': self.settings['facebook_secret'],
            'grant_type': 'client_credentials'
        }
        http.fetch(url_concat(url, args), callback=_subscribe)


class FacebookCallbackHandler(
    UpdateProfileMixin, tornado.auth.FacebookGraphMixin, BaseHandler
):

    def get(self):
        mode = self.get_argument('hub.mode')
        if mode == 'subscribe':
            logger.debug('Received subscribe callback from Facebook')
            if self.get_argument('hub.verify_token') == 'recommend_me':
                logger.debug('Successfull verification')
                self.write(self.get_argument('hub.challenge'))
            else:
                logger.warning('wrong verify_token received from Facebook')
        else:
            logger.debug('Received callback from Facebook')

    @tornado.web.asynchronous
    def post(self):
        def _finish_callback():
            self.finish('Done')

        @gen.engine
        def _update_profile(result, error, next_uids):
            if result:
                for cat in CATEGORIES:
                    yield gen.Task(
                        self.update_profile, result, category=cat
                    )
                _find_and_update_user(next_uids)
            else:
                logger.debug('Error: %s' % error)
                self.finish('Error')

        def _find_and_update_user(uids):
            if not uids:
                _finish_callback()
            else:
                uid = uids.pop()
                self.async_db.users.find_one(
                    {'id': uid}, callback=partial(
                        _update_profile, next_uids=uids
                    )
                )

        logger.debug('Received callback from Facebook')
        logger.debug('Callback body: %s' % self.request.body)
        callback_data = json.loads(self.request.body)
        need_profile_update_uids = []
        if callback_data['object'] == 'user':
            for entry in callback_data['entry']:
                #if 'interests' in entry['changed_fields']:
                need_profile_update_uids.append(entry['uid'])

        _find_and_update_user(need_profile_update_uids)


class LikeHandler(
    SmlrBaseApiMixin, ActivityMixin, tornado.auth.FacebookGraphMixin, BaseHandler
):

    def initialize(
        self, mark=1, action_id='liked', action_name='liked', must_publish=False
    ):
        self.mark = mark
        self.action_name = action_name
        self.action_id = action_id
        self.must_publish = must_publish

    @tornado.web.asynchronous
    @gen.engine
    def post(self):
        user = yield gen.Task(self.get_current_user_async)
        if not user:
            # redirect not authenticatd user
            url = self.get_login_url()
            next_url = self.application.reverse_url(
                'item-info',
                self.get_argument('category', 'item'),
                self.get_argument('item_id', '-1'),
            )
            url += "?" + urllib.urlencode(dict(next=next_url))
            self.redirect(url)
            return
        user_id = user['id']
        items_ids = self.get_arguments('item_id')
        item_url = self.get_argument('item_url', None)
        items_ids = dict([(i, self.mark) for i in items_ids])
        category = self.get_argument('category', 'movies')
        items_count = yield gen.Task(
            self.track, user_id, items_ids, category=category
        )
        for item_id in items_ids:
            item_name = self.get_argument('item_%s_name' % item_id, item_id)
            yield gen.Task(
                self.async_db.items.update,
                {'id': item_id},
                {
                    '$set': {
                        'id': item_id,
                        'name': item_name,
                        'category': category,
                        'users.%s.name' % user_id: user['name'],
                    }
                },
                upsert=True
            )
            if self.must_publish:
                self.track_activity(
                    user_id, user['name'], self.action_id, self.action_name,
                    item_id, item_name,
                    user_image=user['picture'],
                    item_link=self.application.reverse_url('item-info', category, item_id),
                    category=category
                )
                binding = {
                    'movies': 'movie',
                    'music': 'artist',
                    'books': 'book',
                    'television': 'tv_show',
                    'games': 'game'
                }
                our_url = "http://recco.me%s" % self.reverse_url(
                    'item-info', category, items_ids.keys()[0]
                )
                self.facebook_request(
                    '/me/%s:like' % (
                        self.settings['facebook_app_namespace'],
                    ),
                    post_args={
                        binding[category]: our_url
                    },
                    callback=lambda s: logger.debug('finished publishing'),
                    access_token=user["access_token"]
                )
        self.flash('You choice was saved', category='success')

        # updating current user stats
        yield gen.Task(
            self.async_db.users.update,
            {'id': user_id},
            {'$set': {'items_count.%s' % category: items_count}},
            upsert=True
        )
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            self.finish(json.dumps({
                'status': 'ok', 'message': self.get_flashed_messages()
            }))
        else:
            self.redirect(
                self.get_arguments('next') or \
                    self.reverse_url('item-info', category, items_ids.keys()[0])
            )


class UserItemsHandler(SmlrBaseApiMixin, BaseHandler):

    @tornado.web.asynchronous
    @gen.engine
    def get(self, category='movies', user_id=None):
        current_user_id = yield gen.Task(self.get_current_user_id_async)
        user = self.db.users.find_one({'id': user_id})
        is_my_profile = False
        if current_user_id == user_id:
            is_my_profile = True
        result = yield gen.Task(
            self.account_items, user_id, category
        )
        item_ids = result.args[0]
        marks = result.args[1]
        result = yield gen.Task(
            self.async_db.items.find,
            {
                'category': category,
                'id': {'$in': item_ids}
            },
            fields=[
                'id', 'name', 'details.image', 'details.image_large',
                'details.link', 'details.parsed_version'
            ],
            limit=len(item_ids),
            sort=[('name', 1)],
        )
        items = [{'info': i, 'mark': marks[i['id']]['mark']} for i in result.args[0]]
        item_groups = (
            ('Bookmarks', 'bookmark', [i for i in items if i['mark'] == 0.1]),
            ('Likes', 'like', [i for i in items if i['mark'] == 1]),
            ('Dislikes', 'dislike', [i for i in items if i['mark'] == -1]),
            ('Hidden', 'hide', [i for i in items if i['mark'] == 0])
        )
        self.jinja_render(
            'recommendations/account_items.html',
            item_groups=item_groups, category=category, user=user,
            is_my_profile=is_my_profile,
            PARSED_VERSION=self.settings['parsed_version']
        )
