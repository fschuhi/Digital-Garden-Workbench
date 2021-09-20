#!/usr/bin/env python3

import unittest
from testing import MyTestClass
from consts import HAF_YAML_TESTING

import os

from TalkData import TalkData
from HAFEnvironment import HAFEnvironment


# *********************************************
# TalkData
# *********************************************

class Test_TalkData(MyTestClass):

    @classmethod
    def setUpClass(cls) -> None:
        cls.haf = HAFEnvironment(HAF_YAML_TESTING)        
        return super().setUpClass()


    def test_TalkData(self):
        td = TalkData.fromTalkName("Preliminaries Regarding Voice, Movement, and Gesture - Part 1", self.haf)
        self.assertEqual(os.path.basename(td.sfnPdf), "2020_0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1.pdf")
        self.assertEqual(os.path.basename(td.sfnTranscript), "0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1.md")
        self.assertEqual(os.path.basename(td.sfnSummary), "Preliminaries Regarding Voice, Movement, and Gesture - Part 1.md")

        td.loadTranscriptPage()
        self.assertEqual(td.transcriptPage.transcriptName, td.transcriptName)


if __name__ == "__main__":
    unittest.main()
