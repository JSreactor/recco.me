import sys
import os
from datetime import timedelta
import difflib
from tornado.options import define, options

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "apps"))

define("port", default=8888, help="run on the given port", type=int)

# settings for tornado.web.Application
SETTINGS = dict(
    static_path=os.path.join(os.path.dirname(__file__), "static"),
    cookie_secret="32oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
    login_url="/auth/login/facebook/",
    login_redirect_url="/movies/",
    logout_redirect_url="/",
    facebook_app_id='',
    facebook_api_key='',
    facebook_secret='',
    twitter_consumer_key='',
    twitter_consumer_secret='',

    # pathes to templates, like in django
    template_dirs=[os.path.join(os.path.dirname(__file__), "templates")],

    # database connection config
    db_host="localhost",
    db_port=27017,
    db_name="smlr",

    # email sending configuration
    mail_server="localhost",
    mail_port=1025,
    mail_use_tls=False,
    mail_use_ssl=False,
    mail_debug=True,
    mail_username=None,
    mail_password=None,
    mail_default_from='mailer@harma.dev',

    admin_users=['838827975'],
    parsed_version=61,

    # socket.io settings
    flash_policy_port=10843,
    flash_policy_file=os.path.join(
        os.path.dirname(__file__), "static/flash/flashpolicy.xml"
    ),
    socket_io_port=options.port,
    frontend_socket_io_port=8888,

    #logger settings
    logger_names=['recommend_me', 'smlr'],
    debug=False,

    smlr_url='http://127.0.0.1:9999/',
    smlr_public_key='test',
    smlr_secret_key='test',
    smlr_username='recco_me',
    smlr_db_name='smlr2',

    lastfm_api_key='5f3d222b3f999727b0ca1e7f13882102',
    lastfm_api_secret='b25fbfcc522105d5e2ab859827390853',

    tmdb_api_key='d118ae636cc26601c01ff0cabf962e8b',

    aws_access_key='AKIAJV7Y2S2LTBQJ54SQ',
    aws_secret_key='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',
    amazon_associate_tag='reccome-20',

    error_report_emails=['anton.agafonov@gmail.com'],
    new_user_notify_emails=['anton.agafonov@gmail.com', 'you@recco.me'],
    beta_mode=False,
    full_profile_update_timedelta=timedelta(days=7),
    admin_ids=['838827975'],
)

# application list, like django's INSTALLED_APPS
APPS = (
    'website',
    'auth',
    'recommendations',
    'collection',
    'activity',
    'admin',
)
