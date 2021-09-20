#!/usr/bin/env python3

import os
import re

import yaml

from util import *

# *********************************************
# HAFEnvironment
# *********************************************

def determineTalkname(transcriptName):
    match = re.match('[0-9_]+ +', transcriptName)
    return transcriptName[match.end():] if match else transcriptName

class HAFEnvironment():
    def __init__(self, sfnHAFYaml) -> None:
        self.dict = loadYaml(sfnHAFYaml)

        self.dirRoot = self.dict['Root']
        self.retreatNames = self.dict['Retreats']
        self.dirIndexEntries = os.path.join(self.dirRoot, 'Index')

        self.retreatLookup = {}

        self.transcriptFilenamesByRetreat = {}
        self.summaryFilenamesByRetreat = {}
        self.rootFilenamesByRetreat = {}

        self.rootFilenameByTalk = self.__createTalknameLookup(self.dirRetreat)
        self.transcriptFilenameByTalk = self.__createTalknameLookup(self.dirTranscripts)
        self.summaryFilenameByTalk = self.__createTalknameLookup(self.dirSummaries)        
        self.pdfFilenameByTalk = self.__createTalknameLookup(self.dirPDF)

        # https://thispointer.com/python-how-to-get-list-of-files-in-directory-and-sub-directories/
        self.allFiles = list()
        for (dirpath, dirnames, filenames) in os.walk(self.dirRoot):
            self.allFiles += [os.path.join(dirpath, file) for file in filenames]

        #saveLinesToTextFile("tmp/tmp.dir", listOfFiles)
        #saveLinesToTextFile("tmp/root.dir", self.retreatRootFilenameLookup['2020 Vajra Music'])
        

    def __createTalknameLookup(self, funcSubdir) -> dict[str,str]:
        allFilenames = []
        for retreatName in self.retreatNames:
            subdir = funcSubdir(retreatName)
            filenamesForRetreat = collectFilenames(subdir)

            # this is ugly
            if funcSubdir == self.dirTranscripts:
                self.transcriptFilenamesByRetreat[retreatName] = filenamesForRetreat
            if funcSubdir == self.dirSummaries:
                self.summaryFilenamesByRetreat[retreatName] = filenamesForRetreat
            if funcSubdir == self.dirRetreat:
                self.rootFilenamesByRetreat[retreatName] = filenamesForRetreat

            allFilenames.extend(filenamesForRetreat)

            for filename in filenamesForRetreat:
                talkNameKey = determineTalkname(baseNameWithoutExt(filename)).lower()
                self.retreatLookup[talkNameKey] = retreatName

        lookup = {}
        for filename in allFilenames:
            talkNameKey = determineTalkname(baseNameWithoutExt(filename)).lower()
            lookup[talkNameKey] = filename
        return lookup


    def talkExists(self, talkName):
        talkNameKey = determineTalkname(talkName).lower()
        return talkNameKey in self.transcriptFilenameByTalk


    def dirRetreat(self, retreatName):
        return os.path.join(self.dirRoot, retreatName)

    def dirPDF(self, retreatName):
        dirRetreat = self.dirRetreat(retreatName)
        return os.path.join(dirRetreat, 'PDF')

    def dirTranscripts(self, retreatName):
        dirRetreat = self.dirRetreat(retreatName)
        return os.path.join(dirRetreat, 'Transcripts')

    def dirSummaries(self, retreatName):
        dirRetreat = self.dirRetreat(retreatName)
        return os.path.join(dirRetreat, 'Summaries')

    def dirAudio(self, retreatName):
        dirRetreat = self.dirRetreat(retreatName)
        return os.path.join(dirRetreat, 'Audio')

    def dirImages(self, retreatName):
        dirRetreat = self.dirRetreat(retreatName)
        return os.path.join(dirRetreat, 'Images')


    def getIndexEntryFilename(self, pageName):
        return os.path.join(self.dirIndexEntries, pageName)

    def collectIndexEntryFilenames(self) -> list[str]:
        return collectFilenames(self.dirIndexEntries)

    def collectTranscriptNameSet(self) -> set[str]:
        names = set()
        filenames = list(self.transcriptFilenameByTalk.values())
        for filename in filenames:
            pageName = baseNameWithoutExt(filename)
            names.add(pageName)
        return names


    def collectIndexEntryNameSet(self) -> set[str]:
        names = set()
        filenames = self.collectIndexEntryFilenames()
        for filename in filenames:
            pageName = baseNameWithoutExt(filename)
            names.add(pageName)
        return names


    def getPDFFilename(self, talkName):
        talkNameKey = determineTalkname(talkName).lower()
        return self.pdfFilenameByTalk[talkNameKey] if talkNameKey in self.pdfFilenameByTalk else None


    def getTranscriptFilename(self, talkName):
        talkNameKey = determineTalkname(talkName).lower()
        return self.transcriptFilenameByTalk[talkNameKey] if talkNameKey in self.transcriptFilenameByTalk else self.createTranscriptFilename(talkName)

    def createTranscriptFilename(self, talkName):
        sfnPDF = self.getPDFFilename(talkName)
        if sfnPDF is None:
            print("PROBLEM: " + talkName)
        assert sfnPDF is not None
        pdfName = baseNameWithoutExt(sfnPDF)
        match = re.match(r'[0-9]+_([0-9]+)', pdfName)
        assert match
        date = match.group(1)

        talkNameKey = determineTalkname(talkName).lower()
        assert talkNameKey in self.retreatLookup
        retreatName = self.retreatLookup[talkNameKey]
        dirTranscripts = self.dirTranscripts(retreatName)
        
        return os.path.join(dirTranscripts, f"{date} {talkName}.md")


    def getSummaryFilename(self, talkName):
        talkNameKey = determineTalkname(talkName).lower()
        return self.summaryFilenameByTalk[talkNameKey] if talkNameKey in self.summaryFilenameByTalk else self.createSummaryFilename(talkName)

    def createSummaryFilename(self, talkName):
        talkNameKey = determineTalkname(talkName).lower()
        assert talkNameKey in self.retreatLookup
        retreatName = self.retreatLookup[talkNameKey]
        dirSummaries = self.dirSummaries(retreatName)
        return os.path.join(dirSummaries, talkName + '.md')


    def collectTranscriptFilenames(self, retreatName = None) -> list[str]:
        return list(self.transcriptFilenameByTalk.values()) if retreatName is None else self.transcriptFilenamesByRetreat[os.path.basename(retreatName)]

    def website(self):
        # Obsidian Publish doesn't need the website address in <a href ...
        # return self.dict['Website']
        return ''