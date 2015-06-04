#!/usr/bin/env python
#Start the server, for now we don't need to change it

import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.autoreload
from tornado.options import define, options

from utils.importlib import import_module
from utils.deploy import check_dependencies
import settings
import db
import logging
import fcntl
import os
import sys
import asyncmongo
import tornadio2
import redis
from tornadomail.backends.smtp import EmailBackend


PID_FNAME = '/tmp/' \
    + '_'.join((os.path.abspath(__file__).strip('/').split('/'))) \
    + '.pid'

#define("port", default=8888, help="run on the given port", type=int)
define("env", default='local', help="load extra settings from settings_{env}")
define("reset_db", default=False,
    help="Clear db and load default data", type=bool
)

PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(PROJECT_PATH, '../../smlr2'),)


class Application(tornado.web.Application):

    @property
    def mail_connection(self):
        return EmailBackend(
            settings.SETTINGS['mail_server'],
            settings.SETTINGS['mail_port'],
            settings.SETTINGS['mail_username'],
            settings.SETTINGS['mail_password'],
            settings.SETTINGS['mail_use_tls']
        )

    def __init__(self):
        import imp
        handlers = []
        socket_io_endpoints = {}
        #Updating setting with current environment settings
        try:
            env_settings = import_module("settings_%s" % options.env)
            settings.SETTINGS.update(env_settings.SETTINGS)
            settings.SETTINGS['environment'] = options.env
            logging.info("Using environment: '%s'" % options.env)
        except ImportError:
            logging.warning(
                "Environment settings not found for environment '%s'" \
                 % options.env
            )

        if settings.SETTINGS.get('debug', False):
            logging.basicConfig(level=logging.DEBUG)
            logger = logging.getLogger('recommend_me')
            logger.setLevel(level=logging.DEBUG)

        #Joining applications' handlers schemas
        #Now only absolute patches are supported
        for app in settings.APPS:
            #Taken from django code
            mod = import_module(app)
            try:
                app_path = mod.__path__
            except AttributeError:
                continue
            try:
                imp.find_module('urls', app_path)
            except ImportError:
                continue
            app_settings = import_module("%s.urls" % app)
            handlers += app_settings.urls
            if hasattr(app_settings, 'socket_io_endpoints'):
                socket_io_endpoints.update(app_settings.socket_io_endpoints)

        # initializing socket io features

        class RouterConnection(tornadio2.SocketConnection):
            __endpoints__ = socket_io_endpoints

        router = tornadio2.TornadioRouter(RouterConnection, dict(
            enabled_protocols=[
                'websocket', 'flashsocket', 'htmlfile', 'xhr-polling'
            ]
        ))

        tornado.web.Application.__init__(
            self,  router.apply_routes(handlers), **settings.SETTINGS
        )

        # Have one global connection to the blog DB across all handlers
        self.db_connection = db.Connection(
            host=settings.SETTINGS['db_host'],
            port=settings.SETTINGS['db_port'],
            max_pool_size=5
        )
        self.db = self.db_connection[settings.SETTINGS['db_name']]
        self.async_db = asyncmongo.Client(
            pool_id='smlr', host='127.0.0.1', port=27017,
            mincached=10, maxcached=20, maxconnections=20,
            autoreconnect=True, dbname=settings.SETTINGS['db_name']
        )
        redis_pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
        self.redis = redis.StrictRedis(connection_pool=redis_pool)

        logging.basicConfig(level=settings.SETTINGS.get('logging_level', logging.DEBUG))
        for logger_name in settings.SETTINGS.get('logger_names', ['logger']):
            logger = logging.getLogger(logger_name)
            logger.setLevel(level=settings.SETTINGS.get('logging_level', logging.DEBUG))

        if options.reset_db:
            for app in settings.APPS:
                mod = import_module(app)
                try:
                    app_path = mod.__path__
                except AttributeError:
                    continue
                try:
                    imp.find_module('init_db', app_path)
                except ImportError:
                    continue
                init_db_module = import_module("%s.init_db" % app)
                init_db_module.init(
                    self.db,
                    settings.SETTINGS
                )


def main():
    tornado.options.parse_command_line()
    http_server = tornadio2.SocketServer(Application(), auto_start=False)
    #http_server.listen(options.port)
    logging.info("Server is started.")
    f = open(PID_FNAME, 'w')
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        f.write('%-12i' % os.getpid())
        f.flush()
    except:
        pass
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    check_dependencies()
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Server is stoped.")
