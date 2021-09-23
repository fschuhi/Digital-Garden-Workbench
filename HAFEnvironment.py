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

    def allNotes(self):
        return self.pathnames('**/*.md')

    def folderFiles(self, folder, ext):
        if not ext.startswith('*.'):
            ext = '*.' + ext
        return self.pathnames(f'**/{folder}/{ext}')

    def folderNotes(self, folder):
        return self.folderFiles(folder, 'md')

    # HAF specific

    def transcriptNotes(self):
        return self.folderNotes('Transcripts')

    def summaryNotes(self):
        return self.folderNotes('Summaries')

    def retreatNotes(self, retreat):
        return self.pathnames(retreat, '**/*.md')

    def retreatTranscripts(self, retreat):
        return self.folderNotes(os.path.join(retreat, 'Transcripts'))

    def retreatSummaries(self, retreat):
        return self.folderNotes(os.path.join(retreat, 'Summaries'))

    # see HAFEnvironment

    def allFiles(self):
        return self.pathnames('**/*.*')

    def collectIndexEntryFilenames(self):
        return self.pathnames('Index/*.md')

    def collectIndexEntryNameSet(self):
        return set([basenameWithoutExt(filename) for filename in vault.pathnames('Index/*.md')])

    def collectTranscriptFilenames(self, retreat=None):
        return self.retreatTranscripts(retreat) if retreat else self.transcriptNotes()

    def collectSummaryFilenames(self, retreat=None):
        return self.retreatSummaries(retreat) if retreat else self.summaryNotes()


    _retreatNameByTalknameKey = None # type: dict[str,str]

    def safeRetreatNameByTalknameKey(self) -> dict[str,str]:
        if not ObsidianVault._retreatNameByTalknameKey:
            ObsidianVault._retreatNameByTalknameKey = {talknameKeyFromFilename(pathname): self.toplevelFolder(pathname) for pathname in self.transcriptNotes()}
        return ObsidianVault._retreatNameByTalknameKey

    def retreatNameFromTalkname(self, talkName):
        return self.safeRetreatNameByTalknameKey[talknameKeyFromFilename(talkName)]

    def transcriptExists(self, talkname):
        talknameKey = determineTalkname(talkname).lower()
        return self.safeRetreatNameByTalknameKey()[talknameKey]


    def collectNotesInToplevelFolder(self):
        notesInAllToplevelFolders = self.pathnames('*/*.md')
        notesInRetreatToplevelFolders = includeFiles(notesInAllToplevelFolders, rf"\\{'|'.join(self.retreatNames)}\\")
        return notesInRetreatToplevelFolders

    def collectSummaryTalknames(self, retreat=None):
        return [talknameFromFilename(filename) for filename in self.collectSummaryFilenames(retreat)]


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

        self.retreatLookup = {}

        self.transcriptFilenamesByRetreat = {}
        self.summaryFilenamesByRetreat = {}

        self.rootFilenameByTalk = self.__createTalknameLookup(self.dirRetreat)
        self.transcriptFilenameByTalk = self.__createTalknameLookup(self.dirTranscripts)
        self.summaryFilenameByTalk = self.__createTalknameLookup(self.dirSummaries)        
        self.pdfFilenameByTalk = self.__createTalknameLookup(self.dirPDF)

        # https://thispointer.com/python-how-to-get-list-of-files-in-directory-and-sub-directories/
        self.allFiles = list()
        for (dirpath, dirnames, filenames) in os.walk(self.root):
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

            allFilenames.extend(filenamesForRetreat)

            for filename in filenamesForRetreat:
                talkNameKey = determineTalkname(basenameWithoutExt(filename)).lower()
                self.retreatLookup[talkNameKey] = retreatName

        lookup = {}
        for filename in allFilenames:
            talkNameKey = determineTalkname(basenameWithoutExt(filename)).lower()
            lookup[talkNameKey] = filename
        return lookup


    def retreatTranscripts(self, retreat):
        # return self.transcriptFilenamesByRetreat[retreat]
        return self.vault.retreatTranscripts(retreat)

    def retreatSummaries(self, retreat):
        #return self.summaryFilenamesByRetreat[retreat]
        return self.vault.retreatSummaries(retreat)


    def retreatNameFromTalkname(self, talkName):
        key = determineTalkname(talkName).lower()
        return self.retreatLookup[key]


    def collectNotesInToplevelFolder(self):
        #return list(haf.rootFilenameByTalk.values())
        return self.vault.collectNotesInToplevelFolder()

    def collectSummaryFilenames(self):
        #return list(haf.summaryFilenameByTalk.values())
        return self.vault.collectSummaryFilenames()

    def collectSummaryTalknames(self):
        #return list(haf.summaryFilenameByTalk.keys())
        return self.vault.collectSummaryTalknames()


    def transcriptExists(self, talkname):
        #talkNameKey = determineTalkname(talkname).lower()
        #return talkNameKey in self.transcriptFilenameByTalk
        return self.vault.transcriptExists(talkname)


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


    def collectIndexEntryNameSet(self) -> set[str]:
        return self.vault.collectIndexEntryNameSet()
        if False:
            names = set()
            filenames = collectFilenames(self.dirIndex)
            for filename in filenames:
                pageName = basenameWithoutExt(filename)
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
        pdfName = basenameWithoutExt(sfnPDF)
        match = re.match(r'[0-9]+_([0-9]+)', pdfName)
        assert match
        date = match.group(1)

        #talkNameKey = determineTalkname(talkName).lower()
        #assert talkNameKey in self.retreatLookup
        #retreatName = self.retreatLookup[talkNameKey]
        retreatName = self.retreatNameFromTalkname(talkName)
        dirTranscripts = self.dirTranscripts(retreatName)
        
        return os.path.join(dirTranscripts, f"{date} {talkName}.md")


    def getSummaryFilename(self, talkName):
        talkNameKey = determineTalkname(talkName).lower()
        return self.summaryFilenameByTalk[talkNameKey] if talkNameKey in self.summaryFilenameByTalk else self.createSummaryFilename(talkName)

    def createSummaryFilename(self, talkName):
        #talkNameKey = determineTalkname(talkName).lower()
        #assert talkNameKey in self.retreatLookup
        #retreatName = self.retreatLookup[talkNameKey]
        retreatName = self.retreatNameFromTalkname(talkName)
        dirSummaries = self.dirSummaries(retreatName)
        return os.path.join(dirSummaries, talkName + '.md')


    def collectTranscriptFilenames(self, retreatName = None) -> list[str]:
        #return list(self.transcriptFilenameByTalk.values()) if retreatName is None else self.transcriptFilenamesByRetreat[os.path.basename(retreatName)]
        return list(self.transcriptFilenameByTalk.values()) if retreatName is None else self.retreatTranscripts(os.path.basename(retreatName))



if __name__ == "__main__":
    haf = HAFEnvironment(HAF_YAML)
    dict = loadYaml(HAF_YAML)
    root = os.path.normpath(dict['Root'])
    rootDepth = len(splitall(root))
    retreatNames = dict['Retreats']

    retreat = '2020 Vajra Music'

    vault = ObsidianVault(HAF_YAML)
    pathnames = []

    print(haf.collectSummaryTalknames())
    print(vault.collectSummaryTalknames())

    #pathnames = glob.glob(os.path.join(root, '*/*.md'), recursive=True)
    #pathnames = vault.pathnames('*/*.md')
    #pathnames = includeFiles(pathnames, rf"\\{'|'.join(retreatNames)}\\")

    #notes = excludeFiles(notes, r"\\(Amazon Kindle|css-snippets|Journal|Python|templates|Work)\\")
    # pathnames = includeFiles(pathnames, rf"\\{'|'.join(retreatNames)}\\")
    saveLinesToTextFile("tmp/dir.lst", pathnames)
    exit()


    sfn = r"_Markdown\2006 New Year's Retreat\Transcripts\1228 Equanimity (talk).md"
    print(splitall(sfn)[rootDepth:])
    print(vault.relative(sfn))
    print(vault.toplevelFolder(sfn))

    talkName = 'Samadhi in Metta Practice'
    print(haf.retreatLookup[talkName.lower()])
    print(haf.retreatNameFromTalkName(talkName))
    print(vault.retreatNameFromTalkName(talkName))
