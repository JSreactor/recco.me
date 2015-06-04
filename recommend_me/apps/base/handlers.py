import logging
import traceback
import asyncmongo

import tornado.web
import tornado.escape
from tornado import gen
from jinja2 import Environment, ChoiceLoader, PackageLoader, FileSystemLoader
from pymongo.cursor import Cursor
from tornadomail.message import EmailMessage

logger = logging.getLogger('recommend_me')

import settings
#from utils import mail as _mail


class BaseHandler(tornado.web.RequestHandler):
    '''base handler for all handlers. Store general methods'''

    _jinja_env = None

    def __init__(self, *args, **kwargs):
        super(BaseHandler, self).__init__(*args, **kwargs)
        self.username = self.settings['smlr_username']
        if not hasattr(self.application, 'client_async_db_%s' % self.username):
            db_name = '%s_for_client_%s' % (self.settings['smlr_db_name'], self.username)
            setattr(
                self.application,
                'client_async_db_%s' % self.username,
                asyncmongo.Client(
                    pool_id=db_name, host='127.0.0.1', port=27017,
                    mincached=10, maxcached=20, maxconnections=20,
                    autoreconnect=True, dbname=db_name
                )
            )
            setattr(
                self.application,
                'client_db_%s' % self.username,
                self.application.db_connection[db_name]
            )

    @property
    def db(self):
        return self.application.db

    @property
    def async_db(self):
        return self.application.async_db

    @property
    def redis(self):
        return self.application.redis

    @property
    def mail(self):
        return self.application.mail

    def get_current_user(self):
        if hasattr(self, '_current_user'):
            return self._current_user
        user_id = self.get_secure_cookie("user")

        if not user_id:
            return None
        user_id = tornado.escape.json_decode(user_id)
        self._current_user = self.db.users.find_one({'id': user_id})
        return self._current_user

    @gen.engine
    def get_current_user_async(self, callback, fields=None):
        user_id = self.get_secure_cookie("user")

        if hasattr(self, '_current_user'):
            callback(self._current_user)
            return
        if not user_id:
            callback(None)
            return
        user_id = tornado.escape.json_decode(user_id)
        result = yield gen.Task(
            self.async_db.users.find_one,
            {'id': user_id},
            fields=fields
        )
        self._current_user = result.args[0]
        callback(self._current_user)

    @gen.engine
    def get_current_user_id_async(self, callback):
        user = yield gen.Task(self.get_current_user_async)
        if user:
            callback(user['id'])
        else:
            callback(None)

    def flash(self, message, category='info', **kwargs):
        '''flash mesage to next request.
           To display in template and remove from session use
           "get_flashed_messages".
           The following values are recomended for category:
            - "info" for informational messages,
            - "success" for successed completed operations,
            - "error" for errors,
            - "warning" for warning messages,
           '''

        # TODO add possibility to add custom attributes to message using kwargs
        messages = self.get_flashed_messages(clear=False)
        messages.append({'message': message, 'category': category})
        self.set_secure_cookie(
            "messages", tornado.escape.json_encode(messages)
        )

    def get_flashed_messages(self, clear=True):
        '''get flashed messages and
           delete them from future requests if clear=True
        '''

        messages = self.get_secure_cookie("messages")
        if messages:
            messages = tornado.escape.json_decode(messages)
            if clear:
                self.clear_cookie("messages")
        else:
            messages = []
        return messages

    def extra_template_args(self):
        '''
        return extra args to be send to template.
        Rewrite this function to include extra args to every template
        '''

        return dict(
            get_flashed_messages=self.get_flashed_messages
        )

    def jinja_render_to_string(self, template_name, **kwargs):
        '''renders template using jinja2 engine'''

        if not self._jinja_env:
            # settings jinja environment
            template_loaders = [
                FileSystemLoader(self.settings['template_dirs'])
            ]
            for app in settings.APPS:
                template_loaders.append(PackageLoader(app))
            self._jinja_env = Environment(
                                  loader=ChoiceLoader(template_loaders)
                              )

        template = self._jinja_env.get_template(template_name)

        # taken from tornado src
        args = dict(
            handler=self,
            request=self.request,
            current_user=self.current_user,
            locale=self.locale,
            _=self.locale.translate,
            static_url=self.static_url,
            xsrf_form_html=self.xsrf_form_html,
            reverse_url=self.application.reverse_url,
            environment=self.settings['environment']
        )
        args.update(kwargs)
        args.update(self.extra_template_args())

        # TODO move to separate funciton
        if self.settings.get('add_debug_info', False):
            # adding all template context as debug.context
            import pickle
            import base64
            serializable_args = {}
            for key, value in args.items():
                try:
                    # trying to use standart serialization
                    pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
                    serializable_args[key] = value
                except Exception:
                    # serialize mongodb cursor
                    # TODO Add support for more internal formats
                    if isinstance(value, Cursor):
                        serializable_args[key] = [entry for entry in value]
                        args[key] = serializable_args[key]
                    else:
                        try:
                            #If object has debug_data, serialize only this
                            pickle.dumps(
                                value.debug_data,
                                protocol=pickle.HIGHEST_PROTOCOL
                            )
                            serializable_args[key] = value.debug_data
                        except Exception:
                            pass

            debug = {}
            pickled = pickle.dumps(
                          serializable_args,
                          protocol=pickle.HIGHEST_PROTOCOL
                      )
            debug['context'] = args
            debug['context_pickled'] = base64.encodestring(pickled)
            args['debug'] = debug

        return template.render(**args)

    def jinja_render(self, template_name, **kwargs):
        self.finish(self.jinja_render_to_string(template_name, **kwargs))

    @property
    def mail_connection(self):
        return self.application.mail_connection

    def write_error(self, status_code, **kwargs):
        logger.info('Error during request!')
        super(BaseHandler, self).write_error(status_code, **kwargs)
        logger.info('Sending error report to admins...')
        if not self.settings['debug']:
            traceback_data = '\n'.join(
                [l for l in traceback.format_exception(*kwargs["exc_info"])]
            )
            request_data = '\n'.join(
                ["%s: %s" % (k, v) for k, v in self.request.__dict__.items()]
            )
            message = EmailMessage(
                '[Tornado] ERROR %s: %s' % (
                    kwargs["exc_info"][0], self.request.path
                ),
                'Status code: %s\n \n%s\nRequest data:\n %s' % (
                    status_code, traceback_data, request_data
                ),
                self.settings['mail_default_from'],
                self.settings['error_report_emails'],
                connection=self.mail_connection
            )
            message.send()

    def head(self, *args, **kwargs):

        # use get for head request by default
        self.get(*args, **kwargs)
