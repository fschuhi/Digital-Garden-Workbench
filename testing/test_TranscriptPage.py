#!/usr/bin/env python3

from HAFEnvironment import HAFEnvironment
from TranscriptIndex import TranscriptIndex
from TranscriptModel import TranscriptModel
from TranscriptPage import TranscriptPage
from TranscriptParagraph import applySpacyToParagraphs
from testing import MyTestClass
from consts import HAF_YAML_TESTING, RB_YAML_TESTING
import unittest
import os
import re

# *********************************************
# TranscriptPage
# *********************************************

class Test_TranscriptPage(MyTestClass):

    @classmethod
    def setUpClass(cls) -> None:
        cls.haf = HAFEnvironment(HAF_YAML_TESTING)
        cls.transcriptIndex = TranscriptIndex(RB_YAML_TESTING)
        cls.transcriptModel = TranscriptModel(cls.transcriptIndex)        
        return super().setUpClass()

    def test_hasCorrectNumberOfParagraphs(self):
        sfnTranscriptMd = self.haf.getTranscriptFilename("Preliminaries Regarding Voice, Movement, and Gesture - Part 1")
        page = TranscriptPage.fromTranscriptFilename(sfnTranscriptMd)
        self.assertEqual(len(page.paragraphs), 85)


    def test_applySpacyToParagraphs(self):
        sfnTranscriptMd = self.haf.getTranscriptFilename("Preliminaries Regarding Voice, Movement, and Gesture - Part 1")
        page = TranscriptPage.fromTranscriptFilename(sfnTranscriptMd)
        applySpacyToParagraphs(self.transcriptModel, page.paragraphs)
        page.saveToObsidian("tmp/tmp.md")
        import filecmp
        self.assertTrue(filecmp.cmp("tmp/tmp.md", sfnTranscriptMd))
        self.assertTrue(filecmp.cmp("tmp/tmp.md", "testing/data/Test_TranscriptPage.test_transcript_1.md"))


if __name__ == "__main__":
    unittest.main()
