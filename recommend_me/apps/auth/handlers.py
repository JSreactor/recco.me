import tornado.web
import tornado.auth
import tornado.escape
import logging

from base.handlers import BaseHandler
from tornadomail.message import EmailMessage
from activity.mixins import ActivityMixin


logger = logging.getLogger('recommend_me')


class FacebookLoginHandler(ActivityMixin, tornado.auth.FacebookGraphMixin, BaseHandler):

    @tornado.web.asynchronous
    def get(self):
        '''authenticate using Facebook Connect'''

        if self.get_argument("code", False):
            self.get_authenticated_user(

                redirect_uri="%s%s" % (
                    self.settings['host_name'], self.reverse_url('auth-facebook')
                ),
                client_id=self.settings["facebook_api_key"],
                client_secret=self.settings["facebook_secret"],
                code=self.get_argument("code"),
                callback=self.async_callback(self._on_login)
            )
            return

        self.authorize_redirect(
            redirect_uri="%s%s" % (
                self.settings['host_name'], self.reverse_url('auth-facebook')
            ),
            client_id=self.settings["facebook_api_key"],
            extra_params={
                "scope": "user_interests, user_likes, friends_interests, friends_likes, read_friendlists, publish_stream, publish_actions, offline_access, email, read_stream"
            }
        )

    def _on_login(self, facebook_data):
        '''handle answer from Facebook'''

        if not facebook_data:
            raise tornado.web.HTTPError(500, "Facebook auth failed")

        def _find_user_callback(result, error):
            if not result or 'access_token' not in result:
                self.track_activity(
                    facebook_data['id'], facebook_data['name'], 'joined', 'joined',
                    'recco.me', 'recco.me',
                    user_image=facebook_data['picture'],
                )
                self.finish_registration(data=facebook_data)
            else:
                if result.get('inactive'):
                    self.finish(
                        "Sorry, we are in beta mode and your account is not yet activated by admins"
                    )
                    return
                self.finish_login(result, facebook_data=facebook_data)

        self.async_db.users.find_one(
            {'id': facebook_data['id']},
            callback=_find_user_callback
        )

    def finish_login(self, user_data, facebook_data):
        '''Post-login behavior'''

        def _update_user_info_callback(result, error):
            logger.debug('Finishing login process for user with id=%s...' % user_id)
            logger.debug('Access token is "%s"' % user_data['access_token'])
            self.set_secure_cookie(
                "user",
                tornado.escape.json_encode(str(facebook_data['id']))
            )
            self.flash('You have been logged in', category='success')
            self.redirect(self.get_argument(
                "next", self.settings['login_redirect_url']
            ))

        user_id = user_data['id']
        logger.debug('Updating profile data for user id=%s...' % user_id)
        self.async_db.users.update(
            {'id': user_id}, {'$set': facebook_data},
            callback=_update_user_info_callback
        )

    def finish_registration(self, data):
        '''Post-registration behavior'''

        def _user_insert_callback(result, error):
            if result:
                logger.debug(
                    'User data has been inserted to db for user with '
                    'facebook id=%s' % data['id']
                )
                # sending mail to admin
                message = EmailMessage(
                    'New user has registered ',
                    '%s: http://facebook.com/%s' % (data['id'], data['id']),
                    self.settings['mail_default_from'],
                    self.settings['new_user_notify_emails'],
                    connection=self.mail_connection
                )
                message.send()

                if self.settings.get('beta_mode'):
                    self.finish(
                        "Thank your for registration. We will notify you when your account become active."
                    )
                    return
                self.set_secure_cookie(
                    "user",
                    tornado.escape.json_encode(str(data['id']))
                )
                self.redirect(self.reverse_url('recommendations', 'movies'))
            else:
                raise tornado.web.HTTPError(500, "Facebook auth failed")

        logger.debug('Registering new user with facebook id=%s' % data['id'])
        if self.settings.get('beta_mode'):
            data['inactive'] = True
        self.async_db.users.update(
            {'id': data['id']}, data, True,
            callback=_user_insert_callback
        )


class LogoutHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        '''logs out and redirect to next or logout_redirect_url'''

        self.clear_cookie("user")
        self.redirect(
            self.get_argument("next", self.settings['logout_redirect_url'])
        )
