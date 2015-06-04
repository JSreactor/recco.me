import pymongo
import logging

from utils import hash_password


def init(db, settings):
    db.drop_collection('users')

    db.users.ensure_index('id', pymongo.ASCENDING, unique=True)

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
        res = db.users.insert({
                'username': 'simple_user_with_unstrusted_email',
                'email': 'simple.untrusted.email@harma.dev',
                'password': hash_password('simple_password'),
                'trusted_email': False,
              })
        if res:
            logging.info('Added user "simple_user_with_unstrusted_email"')
