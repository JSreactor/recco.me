import twill
from twill import commands as tc
import unittest
from StringIO import StringIO
from functools import wraps
import pickle
import base64
import settings
import settings_test
import db


settings.SETTINGS.update(settings_test.SETTINGS)
settings.SETTINGS['environment'] = 'test'


class BasicTest(unittest.TestCase):

    tc = None
    debug = False
    settings = settings.SETTINGS
    db = None

    def __init__(self, *args, **kwargs):

        self.db_connection = db.Connection(
            host=settings.SETTINGS['db_host'],
            port=settings.SETTINGS['db_port']
        )
        self.db = self.db_connection[settings.SETTINGS['db_name']]
        self.tc = tc
        self.tc.browser.set_agent_string(
            'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8) '
            'Gecko/20051111 Firefox/1.5 BAVM/1.0.0'
        )
        if not self.debug:
            twill.set_output(StringIO())
        return super(BasicTest, self).__init__(*args, **kwargs)

    def get_context(self):
        '''Return serializable tempalte context after twill'''

        return pickle.loads(
            base64.decodestring(self.tc.show().split('==DEBUGINFO==')[1])
        )


def twilltest(func):
    '''Change twill test behavior. Test fails instead of returning error'''

    def _twill_error_to_fail(instance, *args, **kwargs):
        try:
            return func(instance, *args, **kwargs)
        except twill.errors.TwillAssertionError, ex:
            instance.fail('Twill error: %s' % ex)

    return wraps(func)(_twill_error_to_fail)
