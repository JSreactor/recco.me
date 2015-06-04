URL mapping configuration
=========================

URL mapping is configured in ``urls.py`` file of application

File Structure
**************

``urls`` dictionary contains list of ``tornado.web.url`` instances. For help with ``tornado.web.url`` see `Tornado documentation`_

.. _`Tornado documentation`: http://www.tornadoweb.org/documentation

Examples
********

**urls.py**::

    import tornado.web

    import handlers


    urls = (
        tornado.web.url(r"/auth/login/", handlers.LoginHandler, name='auth_login'),
        tornado.web.url(r"/auth/login/google/", handlers.GoogleLoginHandler, name='auth_google'),
        tornado.web.url(r"/auth/login/facebook/", handlers.FacebookLoginHandler, name='auth_facebook'),
        tornado.web.url(r"/auth/login/twitter/", handlers.TwitterLoginHandler, name='auth_twitter'),
        tornado.web.url(r"/auth/logout/", handlers.LogoutHandler, name='auth_logout'),
        tornado.web.url(r"/auth/register/", handlers.RegistrationHandler, name='auth_register'),
        tornado.web.url(r"/auth/register/complete/", handlers.CompleteRegistrationHandler, name='auth_register_complete'),
        tornado.web.url(r"/auth/profile/linked-services/", handlers.LinkedServicesHandler, name='auth_profile_linked_services'),
        tornado.web.url(r"/auth/confirm-email/(?P<key>[\w]+)/", handlers.ConfirmEmailHandler, name='auth_confirm_email'),
        tornado.web.url(r"/auth/reset-password/", handlers.PasswordResetHandler, name='auth_reset_password'),
        tornado.web.url(r"/auth/reset-password-complete/(?P<key>[\w]+)/", handlers.PasswordResetCompleteHandler, name='auth_reset_password_complete'),

    )
