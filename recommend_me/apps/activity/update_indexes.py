import pymongo
import logging


def update_indexes(db, settings):
    logging.info('updating indexes for activity...')
    db.activity.ensure_index('user_id', pymongo.ASCENDING)
    db.activity.ensure_index('item_id', pymongo.ASCENDING)
    db.activity.ensure_index('action_id', pymongo.ASCENDING)
    db.activity.ensure_index('category', pymongo.ASCENDING)
