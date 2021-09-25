#!/usr/bin/env python3

from TranscriptModel import TranscriptModel
import os
from util import basenameWithoutExt

from HAFEnvironment import HAFEnvironment
from TranscriptPage import TranscriptPage
from TranscriptSummaryPage import TranscriptSummaryPage


class TalkData():

    @classmethod    
    def fromTalkName(cls, talkName, haf: HAFEnvironment):
        cls.haf = haf

        # determine filenames
        cls.sfnPdf = haf.getPDFFilename(talkName)
        assert cls.sfnPdf is not None
        cls.pdfName = basenameWithoutExt(cls.sfnPdf)

        cls.sfnTranscript = haf.getTranscriptFilename(talkName)
        cls.sfnSummary = haf.getSummaryFilename(talkName)

        # "names" are the filenames, without the path and extentions
        cls.talkName = talkName
        cls.transcriptName = basenameWithoutExt(cls.sfnTranscript)
        cls.summaryName = basenameWithoutExt(cls.sfnSummary)

        # NOTE that any of the files might be None
        cls.transcriptPage = cls.summaryPage = None
        return cls()


    def loadTranscriptPage(self):
        assert os.path.exists(self.sfnTranscript)
        self.transcriptPage = TranscriptPage.fromTranscriptFilename(self.sfnTranscript)

    def loadSummaryPage(self):
        assert os.path.exists(self.sfnSummary)
        self.summaryPage = TranscriptSummaryPage.fromSummaryFilename(self.sfnSummary)
        self.summaryPage.loadSummaryMd()


