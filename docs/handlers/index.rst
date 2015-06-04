Handlers
========

All handlers should be extended from ``apps.base.handlers.BaseHandler``. In this document we assuming that ``self`` is current handler instance. ``apps.base.handlers.BaseHandler`` extends ``tornado.web.RequestHandler``. For more methods see `Tornado documentation`_

.. _`Tornado documentation`: http://www.tornadoweb.org/documentation


Interaction with db
*******************

For interaction with database use ``self.db`` propery. By default it's link to the PyMongo_'s db connection.

.. _PyMongo: http://api.mongodb.org/python/


Working with current user
*************************

To get current user, call ``self.get_current_user``


Working with templates
**********************

We use Jinja2_ template engine for template rendering. To render template, call ``self.jinja_render``. It accept one required parameter ``template_name``. Other parameters will be passed to template. You can use variables and functions as parameters.

.. _Jinja2: http://jinja.pocoo.org/2/

**Examples**::

    self.jinja_render('auth/linked-services.html')
    self.jinja_render('auth/login.html', 
        login_form=LoginForm(),
        next=self.get_argument("next", self.settings['login_redirect_url'])
    )

If you need some template variables to be passed to all templates accross handler, you can overwrite function ``extra_template_args``

**Example**::

    def extra_template_args(self):
        extra_args = super(EventBaseHandler, self).extra_template_args()
        extra_args.update({
            'event_time_filters': TIME_FILTERS.keys()
        })
        return extra_args


If you need to render template to string, use ``self.jinja_render_to_string``. It has same parameters as ``jinja_render``

Flash messages
**************

Flash messages - tools to display short notification messages to user only once. To display flash message, call ``self.flash`` function. Parameters are:

* ``message`` - message to display
* ``category`` - category of message. Default is ``"info"``. Recommended values are:
    * "info" for informational messages,
    * "success" for successed completed operations,
    * "error" for errors,

To get flash messages, call ``self.get_flashed_messages``. You can pass optional parameter ``clear=False`` if you don't want to clear messages.

**Examples**:

    self.flash('Changes saved', category='success')
    self.flash('Sorry, this service doesn\'t exist', category='error')


Working with mail
*****************

For sending e-mail, use ``self.mail``

**Examples**::

    self.mail.sender.send_plain('Your New Harma Password', 
        self.jinja_render_to_string('auth/email/new_password.txt', 
            user=user, password=password
        ),
        user['email'],
    )
    
