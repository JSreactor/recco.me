import tornado.web

import handlers


urls = (
    tornado.web.url(
        r"/user-activity-feed/(?P<user_id>[\w\d-]+)/(?P<item_id>[\w\d-]+)/",
        handlers.UserActivityFeedHandler,
        name='user-activity-feed'
    ),
    tornado.web.url(
        r"/friends-activity-feed/(?P<user_id>[\w\d-]+)/(?P<item_id>[\w\d-]+)/",
        handlers.FriendsActivityFeedHandler,
        name='user-activity-feed'
    ),
 )
