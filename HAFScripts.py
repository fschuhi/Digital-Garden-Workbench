#!/usr/bin/env python3

import re
import os

from LinkNetwork import LinkNetwork
from Publishing import Publishing
from TranscriptModel import TranscriptModel
from consts import HAF_PUBLISH_YAML, HAF_YAML, RB_YAML
from TranscriptIndex import TranscriptIndex
from summaries import updateParagraphsListPages
from util import *
from HAFEnvironment import HAFEnvironment


# *********************************************
# main
# *********************************************

def get_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--scripts', action="store_true")
    parser.add_argument('--script')
    parser.add_argument('--retreatName')
    parser.add_argument('--talkName')
    parser.add_argument('--out')
    parser.add_argument('--old')
    parser.add_argument('--new')
    return parser.parse_args()


if __name__ == "__main__":
    args = get_arguments()
    if args.scripts:
        dumpScripts(__file__)
        exit()

    def isScript(check):
        return isScriptArg(args, check)

    haf = HAFEnvironment(HAF_YAML)
    haf_publish = HAFEnvironment(HAF_PUBLISH_YAML)

    script = args.script
    retreatName = args.retreatName
    talkname = args.talkName
    old = args.old
    new = args.new
    
    transcriptIndex = TranscriptIndex(RB_YAML)
    if isScript(['transferFilesToPublish', 'top10']):
        transcriptModel = TranscriptModel(transcriptIndex)
    if isScript(['replaceNoteLink']):
        network = LinkNetwork(haf)

    if False:
        pass


    # publish

    elif isScript('transferFilesToPublish'):
        # in principle that's a good idea: make sure that the main vault is in a finalised shape
        # but this may take time, especially when we work on a particular retreats or talk - - no need to update everything

        # for retreatName in haf.retreatNames:
        #     applySpacyToTranscriptParagraphsForRetreat(haf, retreatName, transcriptModel)
        # print("reindexed")
        
        # talkNames = haf.collectSummaryTalknames()
        # for talkname in talkNames:
        #     updateSummary(haf, talkname, transcriptModel)
        # print("summaries updated")

        updateParagraphsListPages(haf)

        publishing = Publishing()
        publishing.transferFilesToPublish()
        publishing.replaceLinksInAllSummaries()
        publishing.replaceLinksInAllRootFilenames()
        publishing.replaceLinksInSpecialFiles()
        print("files transferred to publish vault")


    # search & replace

    elif isScript('replaceNoteLink'): 

        def replaceNoteLink(network: LinkNetwork, oldNote, newNote):
            oldNote = args.old
            newNote = args.new
            assert oldNote and newNote
            changed = 0
            unchanged = 0
            linkingNotes = network.getBacklinksByNote(oldNote)
            found = len(linkingNotes)
            for linkingNote in linkingNotes:
                markdown = network.getMarkdownByNote(linkingNote)
                oldText = markdown.text
                matches = network.getLinkMatchesByNote(linkingNote, oldNote)
                retainShown = linkingNote != 'index'
                markdown.replaceMatches(matches, lambda match: matchedObsidianLinkToString(match, newNote, retainShown))
                # sfn = os.path.join("tmp", os.path.basename(network.getFilenameByNote(linkingNote)))        
                if (newText := markdown.text) == oldText:
                    unchanged += 1
                    pass
                else:
                    changed += 1
                    sfn = network.getFilenameByNote(linkingNote)
                    bak = os.path.splitext(sfn)[0]+'.bak'
                    os.rename(sfn, bak)
                    saveStringToTextFile(sfn, newText)
            return (found, changed, unchanged)

        # needs args "old", "new"
        oldNote = args.old
        newNote = args.new
        (found, changed, unchanged) = replaceNoteLink(network, oldNote, newNote)
        if not found:
            print('not found')
        else:
            print(f"found {found}, {changed} changed, {unchanged} unchanged")


    elif isScript('replace'):
        assert old and new
        print("old", old)
        print("new", new)

        newlines = []
        for md in haf.vault.allNotes():
            text = loadStringFromTextFile(md)
            before = text
            text = re.sub(old, new, text)
            if text != before:
                print(basenameWithoutExt(md))
                saveStringToTextFile(md, text)


    elif isScript('search'):
        old = args.old
        assert old
        print("old", old)

        newlines = []
        for md in haf.vault.allNotes():
            lines = loadLinesFromTextFile(md)
            for index, line in enumerate(lines):
                if (matches := list(re.finditer(old, line))):
                    if matches:
                        print(basenameWithoutExt(md))
                        for match in matches:
                            (start, end) = match.span()
                            print(f"{index}, {start}, {end}")
                            print(line)
                            print('-'*50)


    # misc


    else:
        print("unknown script")
