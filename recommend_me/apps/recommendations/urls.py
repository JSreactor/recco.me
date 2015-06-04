import tornado.web

import handlers


urls = (
    # debug only feature
    tornado.web.url(
        r"/for-user/(?P<uid>[\w\d-]+)/(?P<category>[\w\d-]+)/", handlers.RecommendationsHandler,
        name='user-recommendations'
    ),
    tornado.web.url(
        r"/update-profile/(?P<category>[\w\d-]+)/", handlers.UpdateProfileHandler,
        name='update-profile'
    ),
    tornado.web.url(
        r"/facebook-subscribe/", handlers.FacebookSubscribeHandler,
        name='facebook-subscribe'
    ),
    tornado.web.url(
        r"/facebook-callback/", handlers.FacebookCallbackHandler,
        name='facebook-callback'
    ),
    tornado.web.url(
        r"/like/", handlers.LikeHandler,
        {'mark': 1, 'action_id': 'liked', 'action_name': 'liked', 'must_publish': True},
        name='item-like'
    ),
    tornado.web.url(
        r"/bookmark/", handlers.LikeHandler,
        {'mark': 0.1, 'action_id': 'liked', 'action_name': 'bookmark', 'must_publish': False},
        name='item-bookmark'
    ),
    tornado.web.url(
        r"/dislike/", handlers.LikeHandler,
        {'mark': -1, 'action_id': 'disliked', 'action_name': 'disliked', 'must_publish': False},
        name='item-dislike'
    ),
    tornado.web.url(
        r"/hide/", handlers.LikeHandler,
        {'mark': 0, 'action_id': 'hided', 'action_name': 'hided', 'must_publish': False},
        name='item-hide'
    ),
    tornado.web.url(
        r"/users/(?P<user_id>[\w\d]+)/(?P<category>[\w\d-]+)/", handlers.UserItemsHandler,
        name='user-items'
    ),
    tornado.web.url(
        r"/(?P<category>[movies|music|books|television|games]+)/", handlers.RecommendationsHandler,
        name='recommendations'
    ),
)

socket_io_endpoints = {
    '/update-profile/': handlers.UpdateProfileConnection
}
