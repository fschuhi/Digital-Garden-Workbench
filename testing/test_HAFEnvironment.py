#!/usr/bin/env python3

import unittest
import os
from HAFEnvironment import HAFEnvironment, determineTalkname
from consts import HAF_YAML_TESTING, VAJRA_MUSIC_TESTING


# *********************************************
# HAF
# *********************************************

class Test_HAFEnvironment(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.haf = HAFEnvironment(HAF_YAML_TESTING)
        return super().setUpClass()
        

    def test_Parameters(self):
        self.assertEqual(self.haf.yaml['Root'], "testing/data/_Markdown")
        self.assertListEqual(self.haf.yaml['Retreats'], ['2007 Lovingkindness and Compassion As a Path to Awakening', '2020 Vajra Music'])


    def test_createTranscriptFilename(self):
        talkName = "Preliminaries Regarding Voice, Movement, and Gesture - Part 1"
        sfn = self.haf.createTranscriptFilename(talkName)
        self.assertTrue(os.path.exists(sfn))


    def test_getTranscriptFilename(self):
        transcriptName = "0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1"
        sfn = self.haf.getTranscriptFilename(transcriptName)
        self.assertTrue(os.path.exists(sfn))


    def test_getTranscriptFilename2(self):
        talkName = "Preliminaries Regarding Voice, Movement, and Gesture - Part 1"        
        sfn = self.haf.getTranscriptFilename(talkName)
        self.assertTrue(os.path.exists(sfn))


    def test_createSummaryFilename(self):
        talkName = "Preliminaries Regarding Voice, Movement, and Gesture - Part 1"
        sfn = self.haf.createSummaryFilename(talkName)
        self.assertTrue(os.path.exists(sfn))


    def test_collectTranscriptFilenames(self):
        retreatName = os.path.basename(VAJRA_MUSIC_TESTING)
        filenames = self.haf.collectTranscriptFilenames(retreatName)
        self.assertEqual(len(filenames), 2)


    def test_indexFile(self):
        #print(self.haf.vault.pathnames(r"**\Index.md"))
        self.assertTrue(len(self.haf.vault.pathnames(r"**\Index.md")) == 1)


if __name__ == "__main__":
    unittest.main()
