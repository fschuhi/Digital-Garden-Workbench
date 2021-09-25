#!/usr/bin/env python3

import os
import re
import glob
import yaml

from consts import HAF_YAML
from util import *
from ObsidianVault import ObsidianVault


# *********************************************
# helpers
# *********************************************

def determineTalkname(transcriptName):
    match = re.match('[0-9_]+ +', transcriptName)
    return transcriptName[match.end():] if match else transcriptName

def talknameFromFilename(filename):
    return determineTalkname(basenameWithoutExt(filename))

def talknameKeyFromFilename(filename):
    return talknameFromFilename(filename).lower()


# *********************************************
# HAFEnvironment
# *********************************************

class HAFEnvironment():
    def __init__(self, sfnHAFYaml) -> None:
        self.yaml = loadYaml(sfnHAFYaml)
        self.root = self.yaml['Root']
        self.vault = ObsidianVault(self.root)
        self.retreatNames = self.yaml['Retreats']
        self.dirIndex = os.path.join(self.root, 'Index')


    def allFiles(self):
        return self.vault.allFiles()

    def retreatNotes(self, retreat):
        return self.vault.pathnames(retreat, '**/*.md')


    def retreatNameFromTalkname(self, talkname):
        filename = self.getTranscriptFilename(talkname)
        return self.vault.toplevelFolder(filename) if filename else None

    def transcriptExists(self, talkname):
        return self.retreatNameFromTalkname(talkname) is not None


    def collectNotesInRetreatsFolders(self):
        notesInAllToplevelFolders = self.vault.pathnames('*/*.md')
        notesInRetreatToplevelFolders = includeFiles(notesInAllToplevelFolders, rf"\\{'|'.join(self.retreatNames)}\\")
        return notesInRetreatToplevelFolders


    def collectPDFFilenames(self, retreat=None):
        return self.vault.folderFiles(os.path.join(retreat if retreat else '', 'PDF'), 'pdf')

    def collectTranscriptFilenames(self, retreat=None):
        return self.vault.folderNotes(os.path.join(retreat if retreat else '', 'Transcripts'))

    def collectSummaryFilenames(self, retreat=None):
        return self.vault.folderNotes(os.path.join(retreat if retreat else '', 'Summaries'))


    def collectTranscriptTalknames(self, retreat=None):
        return [talknameFromFilename(filename) for filename in self.collectTranscriptFilenames(retreat)]

    def collectSummaryTalknames(self, retreat=None):
        return [talknameFromFilename(filename) for filename in self.collectSummaryFilenames(retreat)]


    def retreatFolder(self, retreatName):
        return os.path.join(self.root, retreatName)

    def retreatSubfolder(self, retreatName, folder):
        return os.path.join(self.retreatFolder(retreatName), folder)

    def pdfFolder(self, retreatName):
        return self.retreatSubfolder(retreatName, 'PDF')

    def transcriptsFolder(self, retreatName):
        return self.retreatSubfolder(retreatName, 'Transcripts')

    def summariesFolder(self, retreatName):
        return self.retreatSubfolder(retreatName, 'Summaries')

    def audioFolder(self, retreatName):
        return self.retreatSubfolder(retreatName, 'Audio')

    def imagesFolder(self, retreatName):
        return self.retreatSubfolder(retreatName, 'Images')


    def collectIndexEntryNameSet(self):
        indexEntryFilenames = self.vault.pathnames('Index/*.md')
        return set([basenameWithoutExt(filename) for filename in indexEntryFilenames])

    def collectTranscriptNameSet(self):
        return set([basenameWithoutExt(filename) for filename in self.collectTranscriptFilenames()])


    def determineFilenameFromTalkname(self, filenames, talkname):
        talknameKey = determineTalkname(talkname).lower()
        foundFilenames = [filename for filename in filenames if talknameKeyFromFilename(filename) == talknameKey]
        return foundFilenames[0] if foundFilenames else None

    def getPDFFilename(self, talkname):
        return self.determineFilenameFromTalkname(self.collectPDFFilenames(), talkname)

    def getTranscriptFilename(self, talkname):
        return self.determineFilenameFromTalkname(self.collectTranscriptFilenames(), talkname)

    def getSummaryFilename(self, talkname):
        return self.determineFilenameFromTalkname(self.collectSummaryFilenames(), talkname)


    def createTranscriptFilename(self, talkName):
        sfnPDF = self.getPDFFilename(talkName)
        assert sfnPDF is not None, "PROBLEM: " + talkName
        
        pdfName = basenameWithoutExt(sfnPDF)
        match = re.match(r'[0-9]+_([0-9]+)', pdfName)
        assert match
        date = match.group(1)

        retreatName = self.retreatNameFromTalkname(talkName)
        dirTranscripts = self.transcriptsFolder(retreatName)
        
        return os.path.join(dirTranscripts, f"{date} {talkName}.md")


    def createSummaryFilename(self, talkName):
        retreatName = self.retreatNameFromTalkname(talkName)
        dirSummaries = self.summariesFolder(retreatName)
        return os.path.join(dirSummaries, talkName + '.md')

    def website(self):
        # Obsidian Publish doesn't need the website address in <a href ...
        # return self.dict['Website']
        return ''