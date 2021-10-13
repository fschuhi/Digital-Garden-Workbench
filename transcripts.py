#!/usr/bin/env python3

import re
import os
from MarkdownLine import SpacyMode

from Publishing import Publishing
from TranscriptModel import TranscriptModel
from consts import HAF_YAML, RB_YAML
from TranscriptIndex import TranscriptIndex
from TranscriptPage import TranscriptPage
from util import *
from HAFEnvironment import HAFEnvironment, talknameFromFilename


# *********************************************
# Transcripts
# *********************************************

def applySpacyToTranscriptParagraphsForPage(haf: HAFEnvironment, sfnTranscriptMd, transcriptModel: TranscriptModel, mode: SpacyMode):
    markdownName = basenameWithoutExt(sfnTranscriptMd)
    if re.match(r'[0-9][0-9][0-9][0-9] ', markdownName):
        transcript = loadStringFromTextFile(sfnTranscriptMd)
        if re.search(r'#Transcript', transcript):
            page = TranscriptPage(sfnTranscriptMd)
            page.applySpacy(transcriptModel, mode, force=False)
            page.save(sfnTranscriptMd)


def applySpacyToTranscriptParagraphsForRetreat(haf: HAFEnvironment, retreatName, transcriptModel: TranscriptModel, mode: SpacyMode):
    filenames = filterExt(haf.collectTranscriptFilenames(retreatName), '.md')
    for sfnTranscriptMd in filenames:
        applySpacyToTranscriptParagraphsForPage(haf, sfnTranscriptMd, transcriptModel, mode)


# *********************************************
# new transcripts
# *********************************************

# this is supersided by data/tmp based action
# don't create new transcripts in the vault, we can do this very well manually, one by one

def firstIndexingOfRetreatFolder(haf: HAFEnvironment, retreatName):
    filenames = filterExt(haf.collectTranscriptFilenames(retreatName), '.md')
    for sfnTranscriptMd in filenames:
        (filenameWithoutExt, ext) = os.path.splitext(sfnTranscriptMd)                
        if re.match(r'[0-9][0-9][0-9][0-9] ', markdownName := basenameWithoutExt(sfnTranscriptMd)): 
            if re.search(r'#Transcript', transcript := loadStringFromTextFile(sfnTranscriptMd)):
                # it's a regular transcript page - - already indexed
                pass
            else:
                # we need to deitalize manually
                # transcript = deitalicizeTermsWithDiacritics(transcript)
                lines = transcript.splitlines()
                talkname = talknameFromFilename(sfnTranscriptMd)
                page = TranscriptPage.fromPlainMarkdownLines(lines, talkname)

                # create backup (if it doesn't exist yet)
                from shutil import copyfile                
                if not os.path.exists(bak := filenameWithoutExt + '.bak'):
                    copyfile(sfnTranscriptMd, bak)

                page.save(sfnTranscriptMd)


def deitalicizeTranscript(haf: HAFEnvironment, talkName):
    assert False, "we do not deitalicize anymore"
    sfnTranscriptMd = haf.getTranscriptFilename(talkName)
    transcript = loadStringFromTextFile(sfnTranscriptMd)
    transcript = deitalicizeTermsWithDiacritics(transcript)
    saveStringToTextFile(sfnTranscriptMd, transcript)


def canonicalizeTranscript(haf: HAFEnvironment, talkName):
    sfnTranscriptMd = haf.getTranscriptFilename(talkName)
    lines = loadLinesFromTextFile(sfnTranscriptMd)
    newLines = [(line if line.strip() == '---' else canonicalizeText(line)) for line in lines]
    saveLinesToTextFile(sfnTranscriptMd, newLines)



# *********************************************
# main
# *********************************************

def get_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('script')
    parser.add_argument('-r')
    parser.add_argument('-t')
    parser.add_argument('-p')
    parser.add_argument('-allLinks', dest='allLinks', action='store_true')
    parser.add_argument('-noLinks', dest='noLinks', action='store_true')
    return parser.parse_args()


if __name__ == "__main__":
    args = get_arguments()

    def isScript(check):
        return isScriptArg(args, check)

    haf = HAFEnvironment(HAF_YAML)

    script = args.script
    retreatName = args.r
    talkname = args.t
    path = args.p
    allLinks = args.allLinks
    noLinks = args.noLinks

    if isScript('scripts'):
        dumpScripts(__file__)
        exit()


    # reindexing, updating

    elif isScript('reindex'):
        transcriptIndex = TranscriptIndex(RB_YAML)
        transcriptModel = TranscriptModel(transcriptIndex)
        if noLinks:
            mode = SpacyMode.NO_LINKS
        elif allLinks:
            mode = SpacyMode.ALL_LINKS
        else:
            mode = SpacyMode.ONLY_FIRST
        print(mode)
        if talkname:
            sfnTranscriptMd = haf.getTranscriptFilename(talkname)
            applySpacyToTranscriptParagraphsForPage(haf, sfnTranscriptMd, transcriptModel, mode)
        else:
            if retreatName:
                applySpacyToTranscriptParagraphsForRetreat(haf, retreatName, transcriptModel, mode)
            else:
                for retreatName in haf.retreatNames:
                    applySpacyToTranscriptParagraphsForRetreat(haf, retreatName, transcriptModel, mode)
        print("reindexed")


    # conversion helpers

    elif isScript('convertAllMarkdownFiles'):
        publishing = Publishing()
        publishing.convertAllMarkdownFiles()
        print("converted")

    elif isScript("canonicalize"):
        assert talkname
        canonicalizeTranscript(haf, talkname)
        print("canonicalized")

    elif isScript("deitalicize"):
        assert talkname
        deitalicizeTranscript(haf, talkname)
        print("deitalizised")


    # creating files

    elif isScript('firstIndexingOfRetreatFolder'):
        assert retreatName
        firstIndexingOfRetreatFolder(haf, retreatName)
        print("first reindexing done")


    # Shannon's feedback

    elif isScript('removeLevel6Headers'):
        #fn = r"m:\2007 New Years Retreat Insight Meditation\Transcripts\1229 What is Insight.md"
        fn = r"m:\Untitled.md"
        lines = loadLinesFromTextFile(fn)
        newlines = []
        for line in lines:
            if (not line.strip()) or line.startswith('#'):
                continue
            newlines.append(line)
        saveLinesToTextFile("tmp/tmp.md", newlines)

    elif isScript('createNewTranscript'):
        # see bat/createNewTranscript.bat
        assert path
        lines = loadLinesFromTextFile(path)
        talkname = talknameFromFilename(path)
        page = TranscriptPage.fromPlainMarkdownLines(lines, talkname)        
        out = f"tmp/{basenameWithoutExt(path)}.md"
        page.save(out)
        print(f"\nsaved to '{out}'")


    elif isScript('changeParagraphIds'):
        assert talkname
        transcriptName = basenameWithoutExt(haf.getTranscriptFilename(talkname))
        import csv
        tuples = loadTuplesFromCsv(f'data/{transcriptName}.csv')
        del tuples[0]

        # first pass
        for md in haf.vault.allNotes():
            lines = loadLinesFromTextFile(md)
            pass1 = []
            changed = False
            for line in lines:
                newLine = line
                for old, strand, new in tuples:
                    newLine = newLine.replace(f"[[{transcriptName}#^{old}|{old}]]", strand)
                    changed = changed or (newLine != line)
                pass1.append(newLine)
            if changed:
                pass2 = []
                for line in pass1:
                    newLine = line
                    for old, strand, new in tuples:
                        newLine = newLine.replace(strand, f"[[{transcriptName}#^{new}|{new}]]")
                    pass2.append(newLine)
                saveLinesToTextFile(md, pass2)


    # misc


    else:
        print("unknown script")


    