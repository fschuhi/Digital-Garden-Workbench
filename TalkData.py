#!/usr/bin/env python3

from TranscriptModel import TranscriptModel
import os
from util import baseNameWithoutExt

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
        cls.pdfName = baseNameWithoutExt(cls.sfnPdf)

        cls.sfnTranscript = haf.getTranscriptFilename(talkName)
        cls.sfnSummary = haf.getSummaryFilename(talkName)

        # "names" are the filenames, without the path and extentions
        cls.talkName = talkName
        cls.transcriptName = baseNameWithoutExt(cls.sfnTranscript)
        cls.summaryName = baseNameWithoutExt(cls.sfnSummary)

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


    def createNewSummaryPage(self, model: TranscriptModel):
        assert self.pdfName is not None
        assert self.transcriptName is not None
        assert self.transcriptPage is not None
        self.transcriptPage.applySpacy(model)

        sfnSummary = self.haf.getSummaryFilename(self.talkName)
        self.summaryPage = TranscriptSummaryPage.fromSummaryFilename(sfnSummary)
        self.summaryPage.createNew(self.talkName, self.pdfName, self.transcriptName, self.transcriptPage.paragraphs)


