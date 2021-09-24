#!/usr/bin/env python3

import os
import logging
import re
import unittest

from consts import VAJRA_MUSIC_TESTING
from createVajraMusicPages import RetreatDirs, TalkFiles

# *********************************************
# TalkFiles
# *********************************************

class Test_TalkFiles(unittest.TestCase):

    def test_TalkFiles(self):
        pdfName = "2020_0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1"
        retreatDirs = RetreatDirs(VAJRA_MUSIC_TESTING)
        talkFiles = TalkFiles.fromTranscriptPdfName(pdfName, retreatDirs)
        self.assertEqual(talkFiles.pdfName, pdfName)
        self.assertEqual(talkFiles.talkName, "Preliminaries Regarding Voice, Movement, and Gesture - Part 1")
        self.assertEqual(talkFiles.talkDate, "0301")
        self.assertEqual(talkFiles.talkYear, "2020")

        path = VAJRA_MUSIC_TESTING
        self.assertEqual(talkFiles.sfnPdf, os.path.join(path, f"PDF\\{pdfName}.pdf"))
        self.assertEqual(talkFiles.sfnSummaryMd, os.path.join(path, f"Summaries\\{talkFiles.talkName}.md"))
        self.assertEqual(talkFiles.sfnTranscriptMd, os.path.join(path, f"Transcripts\\{talkFiles.talkDate} {talkFiles.talkName}.md"))
        #page = TranscriptPage.fromTranscriptMd(talkFiles.sfnTranscriptMd)


# *********************************************
# RetreatDirs
# *********************************************

class Test_RetreatDirs(unittest.TestCase):

    def test_RetreatDirs(self):
        baseDir = VAJRA_MUSIC_TESTING
        retreatDirs = RetreatDirs(baseDir)
        self.assertEqual( retreatDirs.dirPdfs, os.path.join(baseDir, "PDF"))
        self.assertEqual( retreatDirs.dirTranscripts, os.path.join(baseDir, "Transcripts"))
        self.assertEqual( retreatDirs.dirSummaries, os.path.join(baseDir, "Summaries"))
        

if __name__ == "__main__":
    unittest.main()
