#!/usr/bin/env python3

from posixpath import basename
import re
import os
import pyperclip

from LinkNetwork import LinkNetwork
from Publishing import Publishing
from TranscriptModel import TranscriptModel
from consts import HAF_PUBLISH_YAML, HAF_YAML, RB_YAML
from TranscriptIndex import TranscriptIndex
from util import *
from HAFEnvironment import HAFEnvironment
from TalkPage import TalkPage
from TranscriptPage import TranscriptPage


# *********************************************
# main
# *********************************************

def get_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('script')
    parser.add_argument('-t')
    parser.add_argument('-left')
    parser.add_argument('-right')
    parser.add_argument('-p')
    parser.add_argument('-out')    
    return parser.parse_args()


if __name__ == "__main__":
    args = get_arguments()

    def isScript(check):
        return isScriptArg(args, check)

    haf = HAFEnvironment(HAF_YAML)
    haf_publish = HAFEnvironment(HAF_PUBLISH_YAML)

    script = args.script
    path = args.p
    talkname = args.t
    talknameLeft = args.left
    talknameRight = args.right
    out = args.out
    
    transcriptIndex = TranscriptIndex(RB_YAML)
    if isScript(['transferFilesToPublish', 'top10']):
        transcriptModel = TranscriptModel(transcriptIndex)
    if isScript(['replaceNoteLink']):
        network = LinkNetwork(haf)

    if isScript('scripts'):
        dumpScripts(__file__)
        exit()


    # synopsis

    elif isScript('writeCsv'):
        exitIfNone(talkname, "talkname (-t)")
        talk = TalkPage(haf.getTalkFilename(talkname))
        transcript = TranscriptPage(haf.getTranscriptFilename(talkname))
        tuples = []
        tuples.append(('description', 'paragraph'))
        aSections = talk.collectSections()
        for section in aSections:
            ml = transcript.findParagraph(section.pageNr, section.paragraphNr)
            assert ml
            ml.removeAllLinks()
            tuples.append((section.headerText, ml.text))
        outpath = out if out else f"tmp/{talkname}.csv"
        saveTuplesToCsv(outpath, tuples)


    elif isScript('readCsv'):
        # synopsis readCsv -left "The Place of Samadhi in Metta Practice" -right "Samadhi in Metta Practice" -p "data/2008 vs 2007.csv"
        exitIfNone(talknameLeft, "talk on the left (-left)")
        exitIfNone(talknameRight, "talk on the right (-right)")
        exitIfNone(path, "path to synopsis csv (-p)")

        tuples = []
        import csv
        tuples = loadTuplesFromCsv(path)
        del tuples[0]

        aTalkname = {}
        aTalk = {}
        aSections = {}
        aTranscript = {}
        aBlockid = {}
        aCell = {}

        def setup(tn: str, y: int):
            aTalkname[y] = tn
            aTalk[y] = TalkPage(haf.getTalkFilename(aTalkname[y]))
            aSections[y] = aTalk[y].collectSections()
            aTranscript[y] = TranscriptPage(haf.getTranscriptFilename(aTalkname[y]))

        setup(talknameLeft, 2008)
        setup(talknameRight, 2007)

        lines = []
        lines.append("---")
        lines.append("obsidianUIMode: preview")
        lines.append("---")
        lines.append("")
        lines.append("## Synopsis")
        lines.append("")
        lines.append(f"left: [[{aTranscript[2008].notename}]] (==[[{aTranscript[2008].retreatname}|{aTranscript[2008].retreatname[:4]}]]==)")
        lines.append(f"right: [[{aTranscript[2007].notename}]] ([[{aTranscript[2007].retreatname}|{aTranscript[2007].retreatname[:4]}]])")
        lines.append("")
        lines.append(f"==[[{aTranscript[2008].notename}\\|2008]]== | [[{aTranscript[2007].notename}\\|2007]]")
        lines.append("- | -")

        sectionRef = headerTextRef = talkLinkRef = {}

        def generateCellText(y: int) -> str:
            section = aSections[y].findParagraph(*parseBlockId(aBlockid[y]))
            headerText = section.headerText
            paragraph = aTranscript[y].findParagraph(*parseBlockId(aBlockid[y]))
            paragraph.removeAllLinks()
            (_, _, paragraphText) = parseParagraph(paragraph.text)
            talkLink = f"[[{aTalkname[y]}#{determineHeaderTarget(headerText)}\\|{headerText}]]"
            cell = f"<span class=\"blockid\">{aBlockid[y]}</span>&nbsp;&nbsp;{talkLink}<br/><hr class=\"cell\">{paragraphText}"
            return cell

        for tuple in tuples:
            (aBlockid[2008], aBlockid[2007], ref2007, comment) = tuple                        
            if aBlockid[2008] or aBlockid[2007]:

                # initialize the two cells in the row
                aCell[2008] = aCell[2007] = ""

                # 2008 and comments on the left
                if aBlockid[2008] or comment:
                    if aBlockid[2008]:
                        aCell[2008] = generateCellText(2008)
                    if comment:
                        aCell[2008] = f"{aCell[2008]}<br/><hr class=\"cell\"><span style=\"color:red\">{comment}</span>"

                # 2007 and ref2007 on the right
                if aBlockid[2007] or ref2007:
                    if aBlockid[2007]:
                        aCell[2007] = generateCellText(2007)
                    if ref2007:
                        sectionRef = aSections[2007].findParagraph(*parseBlockId(ref2007))
                        headerTextRef = sectionRef.headerText
                        talkLinkRef = f"<span style=\"color:red\">also</span> [[{aTalkname[2007]}#{determineHeaderTarget(headerTextRef)}\\|{headerTextRef}]]"
                        aCell[2007] = f"{aCell[2007]}<br/><hr class=\"cell\">{talkLinkRef}"
                lines.append(f"| {aCell[2008]} | {aCell[2007]} |")

        outpath = out if out else "M:/Brainstorming/Untitled.md"
        saveLinesToTextFile(outpath, lines)


    else:
        print("unknown script")
