#!/usr/bin/env python3

from consts import HAF_YAML
import os
import re
import glob

import yaml

from util import *

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
# ObsidianVault
# *********************************************

class ObsidianVault:

    def __init__(self, sfnHAFYaml):
        self.yaml = loadYaml(sfnHAFYaml)
        self.root = os.path.normpath(self.yaml['Root'])
        self.rootDepth = len(splitall(self.root))
        self.retreatNames = self.yaml['Retreats']

    def relative(self, sfn):
        parts = splitall(sfn)[self.rootDepth:]
        return os.path.join(*parts)

    def toplevelFolder(self, sfn):
        parts = splitall(sfn)[self.rootDepth:]
        return parts[0]

    def pathnames(self, *paths):
        return glob.glob(os.path.join(self.root, *paths), recursive=True)

    def allFiles(self):
        return self.pathnames('**/*.*')

    def allNotes(self):
        return self.pathnames('**/*.md')

    def folderFiles(self, folder, ext):
        if not ext.startswith('*.'):
            ext = '*.' + ext
        return self.pathnames(f'**/{folder}/{ext}')

    def folderNotes(self, folder):
        return self.folderFiles(folder, 'md')


# *********************************************
# HAFEnvironment
# *********************************************

class HAFEnvironment():
    def __init__(self, sfnHAFYaml) -> None:
        self.vault = ObsidianVault(sfnHAFYaml)
        self.yaml = loadYaml(sfnHAFYaml)
        self.root = self.yaml['Root']
        self.retreatNames = self.yaml['Retreats']
        self.dirIndex = os.path.join(self.root, 'Index')


    def allFiles(self):
        return self.vault.allFiles()


    def PDFs(self):
        return self.vault.folderFiles('PDF', 'pdf')

    def transcriptNotes(self):
        return self.vault.folderNotes('Transcripts')

    def summaryNotes(self):
        return self.vault.folderNotes('Summaries')


    def retreatNotes(self, retreat):
        return self.vault.pathnames(retreat, '**/*.md')

    def retreatPDFs(self, retreat):
        return self.vault.folderNotes(os.path.join(retreat, 'PDF'))

    def retreatTranscripts(self, retreat):
        return self.vault.folderNotes(os.path.join(retreat, 'Transcripts'))

    def retreatSummaries(self, retreat):
        return self.vault.folderNotes(os.path.join(retreat, 'Summaries'))


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
        return self.retreatPDFs(retreat) if retreat else self.PDFs()

    def collectTranscriptFilenames(self, retreat=None):
        return self.retreatTranscripts(retreat) if retreat else self.transcriptNotes()

    def collectSummaryFilenames(self, retreat=None):
        return self.retreatSummaries(retreat) if retreat else self.summaryNotes()

    def collectTranscriptTalknames(self, retreat=None):
        return [talknameFromFilename(filename) for filename in self.collectTranscriptFilenames(retreat)]

    def collectSummaryTalknames(self, retreat=None):
        return [talknameFromFilename(filename) for filename in self.collectSummaryFilenames(retreat)]


    def dirRetreat(self, retreatName):
        return os.path.join(self.root, retreatName)

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


    def collectIndexEntryNameSet(self):
        indexEntryFilenames = self.vault.pathnames('Index/*.md')
        return set([basenameWithoutExt(filename) for filename in indexEntryFilenames])


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
        dirTranscripts = self.dirTranscripts(retreatName)
        
        return os.path.join(dirTranscripts, f"{date} {talkName}.md")


    def createSummaryFilename(self, talkName):
        retreatName = self.retreatNameFromTalkname(talkName)
        dirSummaries = self.dirSummaries(retreatName)
        return os.path.join(dirSummaries, talkName + '.md')




if __name__ == "__main__":
    haf = HAFEnvironment(HAF_YAML)
    dict = loadYaml(HAF_YAML)
    root = os.path.normpath(dict['Root'])
    rootDepth = len(splitall(root))
    retreatNames = dict['Retreats']

    retreat = '2020 Vajra Music'
    talkname = 'Samadhi in Metta Practice'

    vault = ObsidianVault(HAF_YAML)
    pathnames = []

    print(haf.createTranscriptFilename(talkname))

    sfn = haf.getTranscriptFilename(talkname)
    print(sfn)
    print(vault.toplevelFolder(sfn))
    print(haf.retreatNameFromTalkname(talkname))

    #print(vault.collectSummaryTalknames())

    #pathnames = glob.glob(os.path.join(root, '*/*.md'), recursive=True)
    #pathnames = vault.pathnames('*/*.md')
    #pathnames = includeFiles(pathnames, rf"\\{'|'.join(retreatNames)}\\")

    #notes = excludeFiles(notes, r"\\(Amazon Kindle|css-snippets|Journal|Python|templates|Work)\\")
    # pathnames = includeFiles(pathnames, rf"\\{'|'.join(retreatNames)}\\")
    #saveLinesToTextFile("tmp/dir.lst", pathnames)
    exit()


    sfn = r"_Markdown\2006 New Year's Retreat\Transcripts\1228 Equanimity (talk).md"
    print(splitall(sfn)[rootDepth:])
    print(vault.relative(sfn))
    print(vault.toplevelFolder(sfn))

    talkName = 'Samadhi in Metta Practice'
    print(haf.retreatLookup[talkName.lower()])
    print(haf.retreatNameFromTalkName(talkName))
    print(vault.retreatNameFromTalkName(talkName))
