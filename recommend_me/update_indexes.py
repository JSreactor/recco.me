#!/usr/bin/env python
import imp
import settings
import logging

import db
from utils.importlib import import_module


logging.basicConfig(level=logging.INFO)
db_connection = db.Connection(
    host=settings.SETTINGS['db_host'],
    port=settings.SETTINGS['db_port']
)
db = db_connection[settings.SETTINGS['db_name']]


def update_indexes():
    for app in settings.APPS:
        mod = import_module(app)
        try:
            app_path = mod.__path__
        except AttributeError:
            continue
        try:
            imp.find_module('update_indexes', app_path)
        except ImportError:
            continue
        update_indexes_module = import_module("%s.update_indexes" % app)
        logging.info('Updating indexes for app "%s"' % app)
        update_indexes_module.update_indexes(db, settings.SETTINGS)


if __name__ == '__main__':
    update_indexes()
