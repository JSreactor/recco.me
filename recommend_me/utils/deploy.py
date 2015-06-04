import sys
import logging

def check_dependencies():
    '''
    Check all needed modules to before project running
    '''

    modules = (
        'tornado',
        'wtforms',
        'jinja2',
        'pymongo',
    )
    err = False
    for module in modules:
        try:
            __import__(module)
        except ImportError, s:
            logging.error(s)
            err = True
    if err:
        logging.error('Please, see README.txt for instructions')
        sys.exit(1)
