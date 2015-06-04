import tornado.web

import handlers


urls = (
    tornado.web.url(
        r"/auth/login/facebook/",
        handlers.FacebookLoginHandler,
        name='auth-facebook'
    ),
    tornado.web.url(
        r"/auth/logout/", handlers.LogoutHandler, name='auth-logout'
    ),
)
