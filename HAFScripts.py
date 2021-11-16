#!/usr/bin/env python3

from argparse import HelpFormatter
import re
import os
import pyperclip

from LinkNetwork import LinkNetwork
from Publishing import Publishing
from TalkPageLineParser import TalkPageLineMatch, TalkPageLineParser
from TranscriptModel import TranscriptModel
from consts import HAF_PUBLISH_YAML, HAF_YAML, RB_YAML
from TranscriptIndex import TranscriptIndex
from util import *
from HAFEnvironment import HAFEnvironment
from TalkPage import TalkPage
from typing import Tuple


# *********************************************
# main
# *********************************************

def get_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('script')
    parser.add_argument('-help', dest='scriptHelp', action='store_true')
    parser.add_argument('-old')
    parser.add_argument('-n')
    parser.add_argument('-s')
    parser.add_argument('-new')
    parser.add_argument('-p')
    return parser.parse_args()


if __name__ == "__main__":
    args = get_arguments()

    def isScript(check):
        return isScriptArg(args, check)

    haf = HAFEnvironment(HAF_YAML)
    haf_publish = HAFEnvironment(HAF_PUBLISH_YAML)

    script = args.script
    scriptHelp = args.scriptHelp
    old = args.old
    new = args.new
    pattern = args.s
    note = args.n
    path = args.p

    if not scriptHelp:
        transcriptIndex = TranscriptIndex(RB_YAML)
        if isScript(['transferFilesToPublish', 'top10']):
            transcriptModel = TranscriptModel(transcriptIndex)
        if isScript(['replaceNoteLink']):
            network = LinkNetwork(haf)

    if isScript('scripts'):
        dumpScripts(__file__)
        exit()


    # publish

    elif isScript('transferFilesToPublish'):
        if scriptHelp: exitHelp([
            "has no parameters\n",
            "Operations:",
            "- createSynopses()",
            "- transferFilesToPublish()",
            "  _mirrorRetreatFiles()"
            "  _mirrorIndex()",
            "  _mirrorHelp()",
            "  _quoteOfTheDay()",
            "  _convertTalks()",
            "  _removeLinksFromAllTranscripts()",
            "  _copyFiles()",
            "  mirror images",
            "  mirror css",
            "- modifyFullstopsInTranscripts()",
            "- replaceLinksInTalkPages()",
            "- replaceLinksOnSpecialPages()",
            "- replaceLinksOnIndexEntryPages()",
            "- replaceLinksOnTranscriptPages()",
        ])

        publishing = Publishing(transcriptModel)

        # we need to recreate all synopses, because the headers might have changed
        publishing.createSynopses()

        # nothing more to create or modify in work, so copy to publish
        publishing.transferFilesToPublish()

        # link fullstops in transcript paragraphs to the paragraph infos on talk pages
        publishing.modifyFullstopsInTranscripts()

        # now all files are exact copies of the _Markdown vault
        # need to convert audio links and admonitions
        publishing.convertAllMarkdownFiles()

        publishing.replaceLinksInTalkPages()
        publishing.replaceLinksOnSpecialPages()
        publishing.replaceLinksOnIndexEntryPages()
        publishing.replaceLinksOnTranscriptPages()
        print("files transferred to publish vault")


    # search & replace

    elif isScript('replaceNoteLink'): 
        if scriptHelp: exitHelp([
            "-old: note (name) to replace",
            "-new: new note name",
        ])

        def replaceNoteLink(network: LinkNetwork, oldNote, newNote):
            oldNote = old
            newNote = new
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
        oldNote = old
        newNote = new
        (found, changed, unchanged) = replaceNoteLink(network, oldNote, newNote)
        if not found:
            print('not found')
        else:
            print(f"found {found}, {changed} changed, {unchanged} unchanged")


    elif isScript('replace'):
        if scriptHelp: exitHelp([
            "-old: regex pattern to search for, across all notes",
            "-new: replacement string",
        ])
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
        if scriptHelp: exitHelp("-s: regex pattern to search for, across all notes")
        assert pattern
        print("pattern: " + pattern)

        newlines = []
        for md in haf.vault.allNotes():
            lines = loadLinesFromTextFile(md)
            for index, line in enumerate(lines):
                if (matches := list(re.finditer(pattern, line))):
                    if matches:
                        print(basenameWithoutExt(md))
                        for match in matches:
                            (start, end) = match.span()
                            print(f"{index}, {start}, {end}")
                            print(line)
                            print('-'*50)


    # misc

    elif isScript('count'):
        if scriptHelp: exitHelp([
            "-n: note name",
            "-s: regex pattern to search for\n",
            "Prints number of found occurences of pattern in note.",
        ])
        assert note
        assert pattern
        note = note if note.endswith('.md') else note + '.md'
        path = haf.vault.findFile(note)
        # print(path)
        lines = loadLinesFromTextFile(path)
        n = 0
        for line in lines:
            if re.search(pattern, line):
                n += 1
        print(f"{n} occurrences in {path}")


    elif isScript('delLF'):
        if scriptHelp: exitHelp("takes clipboard content, removes CRLF and does canonicalizeText(), result replaces clipboard content")
        clp = pyperclip.paste()
        clp = re.sub(r"\n|\r\n", " ", clp)
        clp = canonicalizeText(clp)
        pyperclip.copy(clp)


    elif isScript('canonicalUnderline'):
        if scriptHelp: exitHelp([
            "-p: any markdown file\n"
            "Tries to remove certain spurious markdown formattings (from copying from Word in Obsidian).",
            "Result is saved w/ same filename to tmp/",
        ])
        # Usually applied to Brainstorming/Untitled.md, which we use to set up a new talk by copying from a Word document.
        # Some docs throw Obsidian off-track with regard to underlines (which have to be paired in Obsidian), so this tries to rectify that.
        assert path
        lines = loadLinesFromTextFile(path)
        newlines = []
        for line in lines:
            # intentionally not canonicalize, so that we can find page breaks easier
            # newline = canonicalizeText(line)            
            newline = re.sub(r"_ _( ?[^_]+? ?)_ ?_", r" _\1_ ", line)
            if (match := re.match(r"^ *?_(.+)_$", newline)):
                newline = match.group(1)
            newline = re.sub(r"_([.,;()])_", r"\1", newline)
            newline = re.sub(r"__\)_", r")_", newline)
            newline = re.sub(r"_ ([.,;])", r"_\1", newline)
            newline = newline.replace("_.’_", ".’")
            newline = newline.replace("__", "")
            newline = newline.replace("** **", " ")
            newline = newline.replace("****", "")
            # print(newline)
            newlines.append(newline)
        saveLinesToTextFile("tmp/" + basenameWithoutExt(path) + '.md', newlines)


    elif isScript('changeJournalBreadcrumbs'):
        exitError("temporary")
        journals = haf.vault.folderNotes('Journal')
        for journal in journals:
            text = loadStringFromTextFile(journal)
            match = re.search(r"<< \[\[(?P<prevdate>[^|]+)\|(?P<prevday>[^]]+)\]\] \| \[\[(?P<nextdate>[^|]+)\|(?P<nextday>[^]]+)\]\] >>", text) # type: re.Match
            if match:
                (start, end) = match.span()
                new = f"[[{match.group('prevdate')}|{match.group('prevday')} 🡄]] | [[{match.group('nextdate')}|🡆 {match.group('nextday')}]]"
                text = text[:start] + new + text[end:]
                saveStringToTextFile(journal, text)


    elif isScript('bla'):
        print(haf.yaml['Synopses'][0])

    else:
        print("unknown script")
