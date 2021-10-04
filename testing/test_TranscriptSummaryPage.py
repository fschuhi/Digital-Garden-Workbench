#!/usr/bin/env python3

from TranscriptPage import TranscriptPage
from HAFEnvironment import HAFEnvironment, determineTalkname
from TranscriptIndex import TranscriptIndex
from TranscriptModel import TranscriptModel
from TranscriptSummaryPage import TranscriptSummaryPage, createNewSummaryPage
from consts import HAF_YAML_TESTING, RB_YAML_TESTING
import unittest
import filecmp


# *********************************************
# TranscriptSummaryPage
# *********************************************

class Test_TranscriptSummaryPage(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.haf = HAFEnvironment(HAF_YAML_TESTING)
        cls.transcriptIndex = TranscriptIndex(RB_YAML_TESTING)
        cls.transcriptModel = TranscriptModel(cls.transcriptIndex)        
        return super().setUpClass()

    transcriptName = "0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1"

    def test_updateWithOldTargetType(self):
        sfnTranscriptMd = self.haf.getTranscriptFilename(self.transcriptName)
        transcriptPage = TranscriptPage(sfnTranscriptMd)
        transcriptPage.applySpacy(self.transcriptModel)
    
        sfnSummaryMd = self.haf.getSummaryFilename(self.transcriptName)
        summaryPage = TranscriptSummaryPage(sfnSummaryMd)
    
        summaryPage.update(transcriptPage, targetType='#^')
        summaryPage.save("tmp/tmp.md")
        self.assertTrue(filecmp.cmp("tmp/tmp.md", sfnSummaryMd))
        self.assertTrue(filecmp.cmp("tmp/tmp.md", "testing/data/Test_TranscriptSummaryPage.test_updateWithOldTargetType.md"))


    def test_updateWithNewTargetType(self):
        sfnTranscriptMd = self.haf.getTranscriptFilename(self.transcriptName)
        transcriptPage = TranscriptPage(sfnTranscriptMd)
        transcriptPage.applySpacy(self.transcriptModel)
    
        sfnSummaryMd = self.haf.getSummaryFilename(self.transcriptName)
        summaryPage = TranscriptSummaryPage(sfnSummaryMd)
    
        summaryPage.update(transcriptPage, targetType='#')
        summaryPage.save("tmp/tmp.md")
        #self.assertTrue(filecmp.cmp("tmp/tmp.md", sfnSummaryMd))
        self.assertTrue(filecmp.cmp("tmp/tmp.md", "testing/data/Test_TranscriptSummaryPage.test_updateWithNewTargetType.md"))


    def test_createNew(self):
        talkName = determineTalkname(self.transcriptName)
        createNewSummaryPage(talkName, self.haf, self.transcriptModel, "tmp/tmp.md")
        self.assertTrue(filecmp.cmp("tmp/tmp.md", "testing/data/Test_TranscriptSummaryPage.test_createNew.md"))


    def test_collectMissingParagraphHeaderTexts(self):
        talkName = "From Insight to Love"
        sfnSummaryMd = self.haf.getSummaryFilename(talkName)
        summaryPage = TranscriptSummaryPage(sfnSummaryMd)
        self.assertEqual(summaryPage.collectMissingParagraphHeaderTexts(), 2)


if __name__ == "__main__":
    unittest.main()
