#!/usr/bin/env python3

from TranscriptModel import TranscriptModel
import os
from util import *

from HAFEnvironment import HAFEnvironment
from TranscriptPage import TranscriptPage
from TalkPage import TalkPage


class TalkData():

    @classmethod    
    def fromTalkName(cls, talkName, haf: HAFEnvironment):
        cls.haf = haf

        # determine filenames
        cls.sfnPdf = haf.getPDFFilename(talkName)
        assert cls.sfnPdf is not None
        cls.pdfName = basenameWithoutExt(cls.sfnPdf)

        cls.sfnTranscript = haf.getTranscriptFilename(talkName)
        cls.sfnTalk = haf.getTalkFilename(talkName)

        # "names" are the filenames, without the path and extentions
        cls.talkName = talkName
        cls.transcriptName = basenameWithoutExt(cls.sfnTranscript)
        cls.talkName = basenameWithoutExt(cls.sfnTalk)

        # NOTE that any of the files might be None
        cls.transcriptPage = cls.talkPage = None
        return cls()


    def loadTranscriptPage(self):
        assert os.path.exists(self.sfnTranscript)
        self.transcriptPage = TranscriptPage(self.sfnTranscript)

    def loadTalkPage(self):
        assert os.path.exists(self.sfnTalk)
        self.talkPage = TalkPage(self.sfnTalk)


