#!/usr/bin/env python3

import unittest
from util import askRUN, askYesNoCancel, canonicalizeText, deitalizeTermsWithDiacritics, deitaliziseWithReplace, deitaliziseTerm
from testing import MyTestClass


# *********************************************
# TalkData
# *********************************************

class Test_util(MyTestClass):

    def test_askYesNoCancel(self):
        # this is just a test to show how to use askYesNoCancel() and askRUN()
        return

        res = askYesNoCancel("yes, no, cancel")
        print(res)
        
        if askRUN():
            print("run1")
        if askRUN():
            print("run2")


    def test_canonicalizeText(self):
        self.assertEqual(canonicalizeText('“Well, is it going to be helpful to people?”'), '"Well, is it going to be helpful to people?"')
        self.assertEqual(canonicalizeText('Because there’s a sense – as John – you know'), 'Because there\'s a sense - as John - you know')


    def test_deitalizise(self):
        self.assertEqual(deitaliziseWithReplace('some _jhāna_ factor', 'jhāna'), 'some jhāna factor')
        self.assertEqual(deitaliziseTerm('some _jhāna_ factor', 'jhāna'), 'some jhāna factor')

        self.assertEqual(deitaliziseWithReplace('some _Jhāna_ factor', 'jhāna'), 'some Jhāna factor')
        self.assertEqual(deitaliziseTerm('some _Jhāna_ factor', 'jhāna'), 'some Jhāna factor')

        self.assertEqual(deitaliziseWithReplace('some _Jhāna,_ factor', 'jhāna'), 'some Jhāna, factor')
        self.assertEqual(deitaliziseTerm('some _Jhāna,_ factor', 'jhāna'), 'some Jhāna, factor')

        self.assertEqual(deitaliziseTerm('some _J__hāna,_ factor', 'jhāna'), 'some Jhāna, factor')

        self.assertEqual(deitalizeTermsWithDiacritics('come from _mettā_ practice to develop _samādhi_.'), 'come from mettā practice to develop samādhi.')


if __name__ == "__main__":
    unittest.main()
