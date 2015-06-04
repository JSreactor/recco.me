Testing
=======

Running
*******

To run tests use ``harma/tests.py`` command. You can pass one argument to it - test string. Format is ``{{app_name}}.{{test_class_name}}.{{test_method_name}}``. ``{{test_class_name}}`` and ``{{test_method_name}}`` can be null.


Writing test case
*****************

1. Tests run at test environment, so you can add some extra test settings into ``settings_test.py``.

2. In ``init_db.py`` file of your application write code to init test fixtures. Example::

    def init(connection, db, settings):

        db.drop_collection('users')

        db.users.create_index('username', pymongo.ASCENDING, unique=True)
        if settings['environment'] == 'test':
            logging.info('Adding test users to database...')
            res = db.users.insert({
                    'username': 'simple_user',
                    'email': 'simple.email@harma.dev',
                    'password': hash_password('simple_password'),
                    'trusted_email': True,
                  })
            if res:
                logging.info('Added user "simple_user"')

3. Create ``tests.py`` file in your applicaton. In ``tests.py`` create your test classes. Each test class should extend ``apps.base.tests.BasicTest`` class. Structure of test class is the same as standart python's unittest structure. Additionally you can use attributes:

    * ``self.tc`` - instance of ``twill.commands``
    * ``self.get_context()`` - method to get serializable variables dictionary, passed to template, such as ``self.get_context()['current_user]``, ``self.get_context()['{{your_form_name}}']``. Can be used only after twill's go request.
    * ``self.debug`` - to enable extra debug info printing
    
Examples
********

**Homepage test**::

    from base import tests


    class HomepageTest(tests.BasicTest):

        @tests.twilltest
        def test_homepage(self):
            self.tc.go('http://harma.dev:9999/')
            self.tc.find('Welcome')
            self.tc.find('Harma')

**Login test**::

    from base import tests

    class SimpleAuthTest(tests.BasicTest):

        @tests.twilltest
        def test_login(self):
            self.tc.go('http://harma.dev:9999/auth/login/')
            self.tc.fv('1', 'username', username)
            self.tc.fv('1', 'password', password)
            self.tc.submit()
            ct = self.get_context()
            self.assertTrue(ct['current_user'])
            self.assertEquals(ct['current_user']['username'], 'simple_user')
