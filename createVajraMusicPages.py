#!/usr/bin/env python3

# This is not used anymore, just retained to for snippets relating to PDF management

import os
import logging
import re
from util import baseNameWithoutExt

from HAFEnvironment import determineTalkname
from TranscriptIndex import TranscriptIndex
from TranscriptPdfLoader import TranscriptPdfLoader
from TranscriptModel import TranscriptModel
from TranscriptParagraph import TranscriptParagraph, applySpacyToParagraphs
from TranscriptPage import TranscriptParagraph, TranscriptPage
from TranscriptSummaryPage import TranscriptSummaryPage
from consts import RB_YAML

# *********************************************
# class RetreatDirs
# *********************************************

class RetreatDirs:
    def __init__(self, dirRetreat: str) -> None:
        dirRetreat = dirRetreat.rstrip("\\")
        self.dirRetreat = dirRetreat
        self.dirPdfs = os.path.join(dirRetreat, "PDF")
        self.dirTranscripts = os.path.join(dirRetreat, "Transcripts")
        self.dirSummaries = os.path.join(dirRetreat, "Summaries")
        self.dirAudioFiles = os.path.join(dirRetreat, "Audio")


# *********************************************
# class TalkFiles
# *********************************************

class TalkFiles:

    def __init__(self) -> None:
        pass

    @classmethod    
    def fromTranscriptPdfName(cls, pdfName, dirs: RetreatDirs) -> None:
        cls.retreatDirs = dirs
        cls.pdfName = pdfName = pdfName if not pdfName.endswith(".pdf") else pdfName[:-len(".pdf")]
        cls.sfnPdf = os.path.join(dirs.dirPdfs, cls.pdfName + ".pdf")
        
        match = re.match("([0-9]+)_([0-9]+) (.+)", cls.pdfName)
        assert match
        cls.talkYear = match.group(1)
        cls.talkDate = match.group(2)
        cls.talkName = match.group(3)
        
        cls.transcriptName = f"{cls.talkDate} {cls.talkName}"
        cls.sfnSummaryMd = os.path.join(dirs.dirSummaries, cls.talkName + ".md")
        cls.sfnTranscriptMd = os.path.join(dirs.dirTranscripts, cls.transcriptName + ".md")
        return cls

    def assignAudio(self, audio) -> None:
        # 20200305-Rob_Burbea-GAIA-preliminaries_regarding_voice_movement_and_gesture_part_5-62456
        match = re.match("([0-9]+)-Rob_Burbea-GAIA-([A-Za-z0-9_]+)-([0-9]+)", audio)
        self.sfnAudio = audio
        self.audioTimestamp = match.group(1)
        self.audioTitle = match.group(2)
        self.audioIndex = match.group(3)

    @classmethod
    def fromQualifiedPdfFilename(cls, sfnPdf, dirs: RetreatDirs):
        # TODO: assert that passed qualified pdf has same path as in RetreatDirs
        pdfName = os.path.basename(sfnPdf)[:-len(".pdf")]
        return cls.fromTranscriptPdfName(pdfName, dirs)


# *********************************************
# main
# *********************************************

retreatDirs = RetreatDirs(r"s:\Dropbox\Papers\_Markdown\Vajra Music")
dirIndexEntries = r"s:\Dropbox\Papers\_Markdown\Index"
transcriptIndex = TranscriptIndex(RB_YAML)
transcriptModel = TranscriptModel(transcriptIndex)


def createVajraMusicTranscriptsAndTranscriptSummaries():
    for entry in os.scandir(retreatDirs.dirPdfs):
        if entry.is_file() and entry.path.endswith(".pdf"):

            sfnPdf = entry.path
            pdfName = entry.name[:-len(".pdf")]
            logging.info(f"pdf name is '{pdfName}'")

            talkFiles = TalkFiles.fromTranscriptPdfName(pdfName, retreatDirs)
            assert talkFiles.sfnPdf == sfnPdf
            transcriptName = talkFiles.transcriptName
            sfnTranscriptMd = talkFiles.sfnTranscriptMd
            sfnSummaryMd = talkFiles.sfnSummaryMd

            if os.path.isfile(talkFiles.sfnTranscriptMd):
            #if False:
                logging.info(f"transcript '{transcriptName}' exists")
                transcriptPage = TranscriptPage.fromTranscriptFilename(sfnTranscriptMd)
                paragraphs = transcriptPage.paragraphs
            else:
                logging.info(f"create transcript '{transcriptName}'")
                # could have this branch in a TranscriptPage constructor
                transcriptLoader = TranscriptPdfLoader(sfnPdf)
                paragraphs = []
                for block in transcriptLoader.mergedBlocks:
                    paragraph = TranscriptParagraph.fromBlock(block)
                    paragraphs.append(paragraph)
                # ((VDRQPFD)) we should be able to create a page from TranscriptParagraphs and talkFiles

            applySpacyToParagraphs(transcriptModel, paragraphs)

            # TODO: move to TranscriptPage
            # problem: we don't have a TranscriptPage here => need to create one in above else, see ((VDRQPFD)) 

            logging.info(f"writing to '{sfnTranscriptMd}'")
            f = open(sfnTranscriptMd, 'w', encoding='utf-8', newline='\n')
            print("#Transcript\n", file=f)
            for paragraph in paragraphs:
                print(f"{paragraph.text} ^{paragraph.pageNr}-{paragraph.paragraphNr}\n", file=f)
            f.close()

            transcriptPage = TranscriptPage.fromTranscriptFilename(sfnTranscriptMd)
            transcriptPage.applySpacy(transcriptModel)

            summaryPage = TranscriptSummaryPage.fromSummaryFilename(talkFiles.sfnSummaryMd)
            if os.path.exists(talkFiles.sfnSummaryMd):
            #if False:
                summaryPage.loadSummaryMd()
                summaryPage.update(transcriptPage)
            else:
                talkName = determineTalkname(transcriptName)
                summaryPage.createNew(talkName, pdfName, transcriptName, transcriptPage.paragraphs)

            summaryPage.save()

            #if os.path.isfile(dirTranscripts + )
        #if entry.is_dir:
        #    print( entry.name)
        #    print(entry.path)
        #if entry.path.endswith(".md") and entry.is_file():
        #    print(entry.path)


if __name__ == "__main__": 
    createVajraMusicTranscriptsAndTranscriptSummaries()
