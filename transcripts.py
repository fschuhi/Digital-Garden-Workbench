#!/usr/bin/env python3

import re
import os
from MarkdownLine import SpacyMode

from Publishing import Publishing
from TalkPage import TalkPage
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
        # we can assume it's a transcript
        transcript = loadStringFromTextFile(sfnTranscriptMd)
        if re.search(r'#Transcript', transcript):
            # better be sure that it really is a transcript
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


# *********************************************
# main
# *********************************************

def get_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('script')
    parser.add_argument('-help', dest='scriptHelp', action='store_true')
    parser.add_argument('-r')
    parser.add_argument('-t')
    parser.add_argument('-p')
    parser.add_argument('-out')
    parser.add_argument('-allLinks', dest='allLinks', action='store_true')
    parser.add_argument('-noLinks', dest='noLinks', action='store_true')
    return parser.parse_args()


if __name__ == "__main__":
    args = get_arguments()

    def isScript(check):
        return isScriptArg(args, check)

    haf = HAFEnvironment(HAF_YAML)

    script = args.script
    scriptHelp = args.scriptHelp
    retreatName = args.r
    talkname = args.t
    path = args.p
    out = args.out
    allLinks = args.allLinks
    noLinks = args.noLinks

    if isScript('scripts'):
        dumpScripts(__file__)
        exit()


    # reindexing, updating

    elif isScript('reindex'):
        if scriptHelp: exitHelp([
            "-noLinks / -allLinks: reindex without any links / with all links in transcripts; default (i.e. neither switch passed): only first link, rest suppressed",
            "-talkname: single talk (NOT transcript) to reindex, note: w/o trailing .md",
            "-r: only reindex talks from a particular retreat\n",
            "If neither talkname or retreat given, then reindex all transcripts across all retreats.",
            "NOTE that this changes the transcripts in place."
        ])

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
        if scriptHelp: exitHelp([
            "-t: name of talk or transcript to run canonicalizeText() on\n",
            "DANGER: replaces file with canonicalized text, without creating a backup"
        ])
        assert talkname
        sfnTranscriptMd = haf.getTranscriptFilename(talkname)
        lines = loadLinesFromTextFile(sfnTranscriptMd)
        newLines = [(line if line.strip() == '---' else canonicalizeText(line)) for line in lines]
        saveLinesToTextFile(sfnTranscriptMd, newLines)
        print("canonicalized")


    # creating files

    elif isScript('firstIndexingOfRetreatFolder'):
        exitError("not used anymore, do the creation of the files one by one")
        assert retreatName
        firstIndexingOfRetreatFolder(haf, retreatName)
        print("first reindexing done")


    # Shannon's feedback

    elif isScript('removeLevel6Headers'):
        exitError("temporary function")
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
        if scriptHelp: exitHelp([
            "-p: path to the raw transcript md, i.e. a plain md with additional '#' pagination markers\n",
            "Created full transcript file has yaml frontmatter, link to talk page, and correct page/paragraph info in headers and blockids.",
            "Saves the transcript with the same filename in tmp/"
        ])
        assert path
        lines = loadLinesFromTextFile(path)
        talkname = talknameFromFilename(path)
        page = TranscriptPage.fromPlainMarkdownLines(lines, talkname)        
        out = f"tmp/{basenameWithoutExt(path)}.md"
        page.save(out)
        print(f"\nsaved to '{out}'")


    elif isScript('changeParagraphIds'):
        if scriptHelp: exitHelp([
            "-t: talk or transcript name (without md)\n",
            "Looks for a csv with talk name in data/, then replaces the tuples across all notes in the vault.",
            "DANGER: this is obviously a dangerous operation, so prepare to rollback with git."
        ])
        assert talkname
        talkname = basenameWithoutExt(haf.getTranscriptFilename(talkname))
        import csv
        tuples = loadTuplesFromCsv(f'data/{talkname}.csv')
        del tuples[0]

        # first pass
        for md in haf.vault.allNotes():
            lines = loadLinesFromTextFile(md)
            pass1 = []
            changed = False
            for line in lines:
                newLine = line
                for old, strand, new in tuples:
                    newLine = newLine.replace(f"[[{talkname}#^{old}|{old}]]", strand)
                    changed = changed or (newLine != line)
                pass1.append(newLine)
            if changed:
                pass2 = []
                for line in pass1:
                    newLine = line
                    for old, strand, new in tuples:
                        newLine = newLine.replace(strand, f"[[{talkname}#^{new}|{new}]]")
                    pass2.append(newLine)
                saveLinesToTextFile(md, pass2)

    # misc


    elif isScript('collectFootnotes'):
        lines = []
        lines.append('transcript | id | footnote')
        lines.append('-|-|-')
        filenames = haf.collectTranscriptFilenames()
        for filename in filenames:
            transcript = TranscriptPage(filename)
            pTalk = haf.getTalkFilename(transcript.talkname)
            if not pTalk:
                continue
            talk = TalkPage(pTalk)
            headerTexts = talk.collectParagraphHeaderTexts()
            for ml in transcript.markdownLines:
                ml.removeFootnotes()
                for (footnote, pos) in ml.footnotes:
                    assert (match := re.match(r"\^\[(.+)\]$", footnote))
                    footnoteText = match.group(1)
                    blockid = ml.getBlockId()
                    if (blockid in headerTexts) and (headerText := headerTexts[blockid]):
                        headerTarget = determineHeaderTarget(headerText)
                        linkToTalk = f"[[{transcript.talkname}#{headerTarget} \| {headerText}]]"
                        line = f"[[{transcript.notename}]] | {linkToTalk} | {footnoteText}"
                    else:
                        linkToTranscript = f"[[{transcript.notename}#^{blockid} \| ({blockid})]]"
                        line = f"[[{transcript.notename}]] | {linkToTranscript} | {footnoteText}"
                    lines.append(line)

        pOut = out if out else r"M:\Brainstorming\Unassinged.md"
        saveLinesToTextFile(pOut, lines)


    elif isScript('next'):
        assert retreatName

        pdfs = haf.vault.folderFiles(haf.pdfFolder(retreatName), 'pdf')
        transcripts = haf.vault.folderFiles(haf.transcriptsFolder(retreatName), 'md') 

        pdfTuples = [(match.group(2), match.group(3)) for p in pdfs if (match := re.match(r"(20[0-9]+)_([0-9]+) (.+)", basenameWithoutExt(p)))]
        transcriptTuples = [(match.group(1), match.group(2)) for p in transcripts if (match := re.match(r"([0-9]+) (.+)", basenameWithoutExt(p)))]

        delta = sorted(list(set(pdfTuples) - set(transcriptTuples)), key=lambda tuple: (tuple[0], tuple[1]))
        if not delta:
            print("no next PDF found")
        else:
            if len(delta) > 1:
                print("additional PDFs:")
                for (date, talkname) in delta:
                    print(f"{date} {talkname}")
                print("")
            (date, talkname) = delta[0]
            print(f"{date} {talkname}")

    else:
        print("unknown script")


    