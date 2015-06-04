.. _configuration:

Configuration
=============

Configuration is done throw ``settings.py`` file and environment settings files named ``settings\_{your_environment_name}.py``.


settings.py
***********

Almost all settings are stored in ``settings.py`` file in ``harma`` directory. Structure of file:

* **SETTINGS** dictionary contain project parameters. Also contain standart Tornado_ settings parameters. Here is the list of most used parameters:
    * *login_url* - URL to Sign In page
    * *login_redirect_url* - URL where user will be redirected after log in
    * *logout_redirect_url* - URL where user will be redirected after log out
    * *template_dirs* - directory containing templates
    * *db_host*, *db_port*, *db_name* - Database parameters
    * *mail_\** - Settings for sending mail
* **APPS** dictonary containing enabled applications

.. _Tornado: http://tornadoweb.org/

Environment setttings
*********************

You can use to use different settings in environments. To do this, create file ``settings_{your_environment_name}.py``, where ``{your_environment_name}`` is the name of your environment. Format of file are the same as settings.py, except you now it's not possible to change ``APPS``. Default installation contain settings for test environment: ``settings_test.py``.


Examples
********************

**settings.py**::

   import sys, os
   from tornado.options import define, options
   from utils.importlib import import_module

   sys.path.insert(0, os.path.join(os.path.dirname(__file__), "apps"))

   #Settings for tornado.web.Application 
   SETTINGS = dict(
       static_path = os.path.join(os.path.dirname(__file__), "static"),
       cookie_secret = "32oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
       login_url = "/auth/login/",
       login_redirect_url = "/auth/profile/linked-services/",
       logout_redirect_url = "/",
       facebook_app_id = '',
       facebook_api_key = '',
       facebook_secret = '',
       twitter_consumer_key = '',
       twitter_consumer_secret = '',

       #Pathes to templates, like in django
       template_dirs = [os.path.join(os.path.dirname(__file__), "templates")],

       #Database connection config
       db_host = "localhost",
       db_port = 27017,
       db_name = "harma",

       #Email sending configuration
       mail_server = "localhost",
       mail_port = 1025,
       mail_use_tls = False,
       mail_use_ssl = False,
       mail_debug = True,
       mail_username = None,
       mail_password = None,
       mail_default_from = 'mailer@harma.dev'
   )

   #Application list, like django's INSTALLED_APPS
   APPS = (
       'auth',
       'homepage',
   )


**settings_test.py**::

    SETTINGS = {
        'facebook_app_id': '143057305716866',
        'facebook_api_key': 'dc9a23ea873df042d93676ecc52e1e49',
        'facebook_secret': '07cbc271dd13d2025e1083b3259b7302',
        'twitter_consumer_key': 'xivrWYMuLVaJMu9rXTHDcg',
        'twitter_consumer_secret': 'lcVKUXHWsgyeHwKHwUw0Txs2dJqPcLt4qkadq6cslE',

        'db_name' : 'harma_test',
        #Add debug info to the end of each response
        'add_debug_info': True,
        'google_test_username': 'harma.test.user',
        'google_test_password': 'harma.test',
        'facebook_test_email': 'harma.test.user@gmail.com',
        'facebook_test_password': 'harma.test',
        'twitter_test_username': 'harmatestuser',
        'twitter_test_password': 'harmatest',
    }
