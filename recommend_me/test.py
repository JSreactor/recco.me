#!/usr/bin/env python

import imp
import logging
import os
import sys
import fcntl
from subprocess import Popen
import signal
import time
import unittest
import warnings

import settings
import settings_test
from utils.importlib import import_module
from utils.deploy import check_dependencies

warnings.filterwarnings(
    "ignore",
    message="the sha module is deprecated; use the hashlib module instead"
)
warnings.filterwarnings(
    "ignore",
    message="the md5 module is deprecated; use hashlib instead"
)


PID_FNAME = '/tmp/' + '_'.join((os.path.abspath('main.py'
    ).strip('/').split('/'))) + '.pid'
PORT = 9999
HOST = 'harma.dev'


def get_test_server_pid():
    '''
    Return pid, if server is running, 0 otherwise
    '''
    if not os.path.exists(PID_FNAME):
        f = open(PID_FNAME, "w")
        f.write('0')
        f.flush()
        f.close()

    f = open(PID_FNAME, 'r+')
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        started = int(f.read())
    else:
        started = 0
    f.close()
    return started


def stop_test_server():
    started = get_test_server_pid()
    if started:
        os.kill(started, signal.SIGKILL)


def start_test_server():
    started = get_test_server_pid()
    if started:
        os.kill(started, signal.SIGKILL)

    pid = Popen([
                  HOST,
                  os.path.abspath('main.py'),
                  "--env=test",
                  "--reset_db=True",
                  "--port=9999",
                  "--logging=error"
              ],
              executable='python'
          ).pid


def build_test_suite(test_label):
    '''Find test modules, testSuites and test methods that match test_label
       in applications and add them to test suite.
       Format is "app.TestCase.test_method"
    '''

    if test_label:
        test_path = test_label.split(".")
        if len(test_path) > 3:
            raise ValueError(
                "Test path '%s' should be of the form app or "
                "app.TestCase or app.TestCase.test_method" % test_label
            )
    else:
        test_path = None

    suite = unittest.TestSuite()
    for app in settings.APPS:
        #Skipping if app is not in test_path
        if test_path != None and app != test_path[0]:
            continue

        #Taken from django code
        mod = import_module(app)
        try:
            app_path = mod.__path__
        except AttributeError:
            continue
        try:
            imp.find_module('tests', app_path)
        except ImportError:
            continue
        #Getting test moduel
        test_module = import_module("%s.tests" % app)

        if test_path and len(test_path) > 1:
            TestClass = getattr(test_module, test_path[1], None)
            if not TestClass:
                raise ValueError(
                    'class %s is not found int module %s' \
                     % (test_path[1], test_path[0])
                )

            # Loading test case from the tests.py.
            test_method = None
            if len(test_path) > 2:
                test_method = test_path[2]
            if test_method:
                # Loading test method from the tests.py.
                suite.addTest(TestClass(test_method))
            else:
                suite.addTest(
                    unittest.defaultTestLoader.loadTestsFromTestCase(TestClass)
                )
        else:
            # Loading unittests from tests.py.
            suite.addTest(
                unittest.defaultTestLoader.loadTestsFromModule(test_module)
            )
    return suite


def main():

    #Updating settigns with settings for test environment
    settings.SETTINGS.update(settings_test.SETTINGS)

    #Starting test server
    start_test_server()

    #Waiting for server
    time.sleep(2)

    #Building test suite
    suite = unittest.TestSuite()
    try:
        test_path = sys.argv[1]
    except IndexError:
        test_path = None
    suite.addTest(build_test_suite(test_path))

    #Run tests
    unittest.TextTestRunner(verbosity=1).run(suite)
    stop_test_server()


if __name__ == "__main__":
    check_dependencies()
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Stoped.")
