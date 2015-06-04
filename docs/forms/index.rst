Forms
=====

We use WTForms_ for making forms. Use ``apps.base.forms.BaseHarmaForm`` as base class for your forms.

.. _WTForms: http://wtforms.simplecodes.com/

Examples
********

**forms.py**::

   from base.forms import BaseHarmaForm
   from wtforms import TextField, PasswordField, validators, ValidationError

   class LoginForm(BaseHarmaForm):

       username = TextField('Username or E-mail', [validators.Required()])
       password = PasswordField('Password', [
                       validators.Length(min=6, max=35), 
                       validators.Required(),
                  ])

       def validate_username(self, field):
           u = field.data
           p = hash_password(self.password.data)
           self._user = self._collection.find_one({'username':u, 'password':p})
           if not self._user:
               self._user = self._collection.find_one({'email':u, 'password':p})
           if not self._user:
               raise ValidationError('Username or password are incorrect')

       def get_user(self):
           return self._user


Fragmet from handler::

    login_form = LoginForm(self.request.arguments, collection=self.db.users)
    if login_form.validate():
        self.finish_login(login_form.get_user()['_id'])
    else:
        self.jinja_render('auth/login.html', 
            login_form=login_form,
            next=self.get_argument("next", self.settings['login_redirect_url'])
        )
    