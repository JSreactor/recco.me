import pymongo
import logging


def update_indexes(db, settings):
    logging.info('Updating indexes for recommendation app...')
    db.users.ensure_index('id', pymongo.ASCENDING, unique=True)
    db.items.ensure_index('id', pymongo.ASCENDING, unique=True)
