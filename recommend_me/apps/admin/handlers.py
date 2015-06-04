from functools import wraps
import logging
import json

import tornado.web
import tornado
from tornado import gen

from base.handlers import BaseHandler
from smlr.apps.api.mixins import BaseApiMixin as SmlrBaseApiMixin


logger = logging.getLogger('recommend_me')


def admin_permissions(fn):
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        user = self.get_current_user()
        if user['id'] not in self.settings['admin_ids']:
            raise tornado.web.HTTPError(401)
        return fn(self, *args, **kwargs)
    return wrapper


class AllItemsHandler(SmlrBaseApiMixin, BaseHandler):

    @admin_permissions
    @tornado.web.asynchronous
    @gen.engine
    def get(self, category='movies'):
        q = self.get_argument('q', None)
        limit = int(self.get_argument('limit', 50))
        skip = int(self.get_argument('skip', 0))
        if q:
            result = yield gen.Task(
                self.async_db.items.find,
                {
                    'category': category,
                    'name': {'$regex': "%s" % q, '$options': 'i'}
                },
                fields=['id', 'name', 'details.image', 'details.link', 'details.likes'],
                sort=[('name', 1)],
                skip=skip, limit=limit
            )
        else:
            result = yield gen.Task(
                self.async_db.items.find,
                {'category': category},
                fields=['id', 'name', 'details.image', 'details.link', 'details.likes'],
                sort=[('name', 1)],
                skip=skip, limit=limit
            )

        items = result.args[0]
        # fetching data about merges from redis
        for item in items:
            item['merges'] = list(self.redis.smembers('merges:%s' % item['id']))
            del item['_id']
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            self.add_header('Content-Type', 'application/json')
            self.finish(json.dumps({
                'status': 'ok',
                'items': items
            }))
        else:
            self.jinja_render(
                'admin/all_items.html',
                items=items, category=category,
                prev_skip=max(skip - limit, 0), next_skip=skip + limit
            )


class ItemDeleteHandler(SmlrBaseApiMixin, BaseHandler):

    @admin_permissions
    @tornado.web.asynchronous
    @gen.engine
    def get(self, id, category='movies'):
        yield gen.Task(self.replace, {id: 0}, category)
        res = yield gen.Task(self.async_db.items.remove, {'id': id, 'category': category})
        try:
            deleted_count = res.args[0][0]['n']
        except (IndexError, KeyError):
            deleted_count = 0
        if deleted_count:
            logger.debug('Adding id %s to redis removed list' % id)
            self.redis.set('removed:%s' % id, 1)
        self.flash('Changes saved', category='success')
        self.redirect(self.reverse_url('admin-all-items', category))


class ItemsMergeHandler(SmlrBaseApiMixin, BaseHandler):

    @admin_permissions
    @tornado.web.asynchronous
    @gen.engine
    def post(self, category='movies'):
        target_id = self.get_argument('target')
        source_ids = set(self.get_arguments('source'))
        yield gen.Task(
            self.replace,
            dict([(id, target_id) for id in source_ids]),
            category
        )
        # extend source_ids with ids that point to ids in source id
        result_source_ids = source_ids.copy()
        for source_id in source_ids:
            from_id = self.redis.spop('merges:%s' % source_id)
            while from_id:
                result_source_ids.add(from_id)
                self.redis.delete('duplicates:%s' % from_id)
                from_id = self.redis.spop('merges:%s' % source_id)
        source_ids = result_source_ids

        if target_id in source_ids:
            source_ids.remove(target_id)
        for source_id in source_ids:
            self.redis.set('duplicates:%s' % source_id, target_id)
            self.redis.sadd('merges:%s' % target_id, source_id)
        yield gen.Task(self.async_db.items.remove, {'id': {'$in': list(source_ids)}})
        self.flash('Changes saved', category='success')
        self.redirect(self.reverse_url('admin-all-items', category))
