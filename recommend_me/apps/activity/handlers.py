import json
import time

import tornado
import tornado.web
from tornado import gen

from base.handlers import BaseHandler
from smlr.apps.api.mixins import BaseApiMixin as SmlrBaseApiMixin


class UserActivityFeedHandler(BaseHandler):

    @tornado.web.asynchronous
    @gen.engine
    def get(self, user_id=None, item_id=None, limit=30):
        '''return activity for given user id'''

        if not user_id:
            user_id = yield gen.Task(self.get_current_user_id_async)
        category = self.get_argument('category', None)
        filters = {'user_id': user_id}
        if category:
            filters['$or'] = [{'category': category}, {'category': None}]
        result = yield gen.Task(
            self.async_db.activity.find,
            filters,
            limit=limit,
            sort=[('created', -1)],
        )
        feed = result.args[0]
        for item in feed:
            item['created'] = item['created'].strftime(
                "%s%s" % ("%Y-%m-%dT%H:%M:%SZ", "%+03d00" % (-time.altzone / 3600))
            )
            del item['_id']

        self.add_header('Content-Type', 'application/json')
        self.finish(json.dumps({
            'status': 'ok',
            'feed': feed
        }))


class FriendsActivityFeedHandler(SmlrBaseApiMixin, BaseHandler):

    @tornado.web.asynchronous
    @gen.engine
    def get(self, user_id=None, item_id=None, include_current_user=True, limit=20):
        '''return activity for friends of given user id'''

        if not user_id or user_id == '0':
            user_id = yield gen.Task(self.get_current_user_id_async)
        friends_ids = yield gen.Task(self.account_friends, user_id)
        filters = {'user_id': {'$in': friends_ids + [user_id]}}
        if item_id and item_id != '0':
            filters['item_id'] = item_id
        category = self.get_argument('category', None)
        if category:
            filters['$or'] = [{'category': category}, {'category': None}]

        result = yield gen.Task(
            self.async_db.activity.find,
            filters, limit=limit, sort=[('created', -1)],
        )
        feed = result.args[0]
        for item in feed:
            item['created'] = item['created'].strftime(
                "%s%s" % ("%Y-%m-%dT%H:%M:%SZ", "%+03d00" % (-time.altzone / 3600))
            )
            del item['_id']

        self.add_header('Content-Type', 'application/json')
        self.finish(json.dumps({
            'status': 'ok',
            'feed': feed
        }))
