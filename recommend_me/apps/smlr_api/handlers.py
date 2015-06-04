import logging
import urllib
import tornado.httpclient


logger = logging.getLogger('recommend_me')


class SmlrMixin(object):

    def smlr_request(self, url, data, callback):
        http_client = tornado.httpclient.AsyncHTTPClient()
        initial_data = {
            'public_key': self.settings['smlr_public_key'],
            'secret_key': self.settings['smlr_secret_key']
        }
        if type(data) == list:
            initial_data = initial_data.items()
            initial_data += data
        else:
            initial_data.update(data)
        data = initial_data
        url = "%s%s?%s" % (self.settings['smlr_url'], url, urllib.urlencode(data))
        logger.debug('Making request to smlr: "%s"' % url)
        request = tornado.httpclient.HTTPRequest(url)
        http_client.fetch(request, callback)

    def smlr_dummy_callback(self, response):
        logger.debug('Smlr response was: "%s"' % response)

    def smlr_friendship(self, account_id, friends_ids, category=None, callback=None):
        if not callback:
            callback = self.smlr_dummy_callback
        data = [('account_id', account_id), ('category', category)]
        for f_id in friends_ids:
            data.append(('friends_ids', f_id))
        self.smlr_request("api/friendship/", data, callback)

    def smlr_track(self, account_id, marks, category=None, callback=None):
        if not callback:
            callback = self.smlr_dummy_callback
        data = {
            'account_id': account_id,
            'category': category,
        }
        for item_id, mark in marks.items():
            data["marks.%s" % item_id] = mark
        self.smlr_request("api/track/", data, callback)

    def smlr_account_recommendations(self, account_id, category=None, limit=100, callback=None):
        if not callback:
            callback = self.smlr_dummy_callback
        self.smlr_request(
            "api/recommended/items/for/account/",
            {'account_id': account_id, 'category': category, 'limit': limit},
            callback
        )
