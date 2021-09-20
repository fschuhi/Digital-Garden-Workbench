#!/usr/bin/env python3

import unittest
import logging
import sys

# *********************************************
# codec
# *********************************************

# https://stackoverflow.com/questions/31805474/python-encode-error-cp850-py
# => in console: chcp 65001
# import codecs
# codecs.register(lambda name: codecs.lookup('utf8') if name == 'cp65001' else None)


# *********************************************
# logging
# *********************************************

if False:
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    #formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)


# *********************************************
# testcase base class
# *********************************************

class MyTestClass(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        # create logger with 'spam_application'
        if False:
            logger = logging.getLogger('testcases')
            logger.setLevel(logging.DEBUG)

            # create file handler which logs debug messages
            fh = logging.FileHandler('testcases.log')
            fh.setLevel(logging.DEBUG)
            
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)
            logger.addHandler(fh)
            cls.logger = logger
        return super().setUpClass()

