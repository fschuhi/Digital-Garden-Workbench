#!/usr/bin/env python3

import unittest
from util import askRUN, askYesNoCancel, canonicalizeText, deitalicizeTermsWithDiacritics, deitalicizeWithReplace, deitalicizeTerm
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
        self.assertEqual(canonicalizeText('true for me--my tendencies, my'), 'true for me - my tendencies, my')
        self.assertEqual(canonicalizeText('**(2)** The realm of **universal insights**--so, what these are are'), '**(2)** The realm of **universal insights** - so, what these are are')


    def test_deitalizise(self):
        self.assertEqual(deitalicizeWithReplace('some _jhāna_ factor', 'jhāna'), 'some jhāna factor')
        self.assertEqual(deitalicizeTerm('some _jhāna_ factor', 'jhāna'), 'some jhāna factor')

        self.assertEqual(deitalicizeWithReplace('some _Jhāna_ factor', 'jhāna'), 'some Jhāna factor')
        self.assertEqual(deitalicizeTerm('some _Jhāna_ factor', 'jhāna'), 'some Jhāna factor')

        self.assertEqual(deitalicizeWithReplace('some _Jhāna,_ factor', 'jhāna'), 'some Jhāna, factor')
        self.assertEqual(deitalicizeTerm('some _Jhāna,_ factor', 'jhāna'), 'some Jhāna, factor')

        self.assertEqual(deitalicizeTerm('some _J__hāna,_ factor', 'jhāna'), 'some Jhāna, factor')

        self.assertEqual(deitalicizeTermsWithDiacritics('come from _mettā_ practice to develop _samādhi_.'), 'come from mettā practice to develop samādhi.')


if __name__ == "__main__":
    unittest.main()
