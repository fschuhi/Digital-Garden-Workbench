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


# *********************************************
# main
# *********************************************

def get_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('script')
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
    old = args.old
    new = args.new
    pattern = args.s
    note = args.n
    path = args.p
    
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
        publishing = Publishing()
        publishing.transferFilesToPublish()
        publishing.replaceLinksInAllTalks()
        publishing.replaceLinksInAllRootFilenames()
        publishing.replaceLinksInSpecialFiles()
        print("files transferred to publish vault")


    # search & replace

    elif isScript('replaceNoteLink'): 

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
        assert note
        assert pattern
        note = note if note.endswith('.md') else note + '.md'
        path = haf.vault.findFile(note)
        print(path)
        lines = loadLinesFromTextFile(path)
        n = 0
        for line in lines:
            if re.search(pattern, line):
                n += 1
        print(n)


    elif isScript('delLF'):
        clp = pyperclip.paste()
        clp = re.sub(r"\n|\r\n", " ", clp)
        clp = canonicalizeText(clp)
        pyperclip.copy(clp)


    elif isScript('canonicalUnderline'):
        # Usually applied to Brainstorming/Untitled.md, which we use to set up a new talk by copying from a Word document.
        # Some docs throw Obsidian off-track with regard to underlines (which have to be paired in Obsidian), so this tries to rectify that.
        assert path
        lines = loadLinesFromTextFile(path)
        newlines = []
        for line in lines:
            # intentionally not canonicalize, so that we can find page breaks easier
            # newline = canonicalizeText(line)            
            newline = re.sub(r"_ _( ?[^_]+? ?)_ ?_", r" _\1_ ", newline)
            if (match := re.match(r"^ *?_(.+)_$", newline)):
                newline = match.group(1)
            print(newline)
            newline = re.sub(r"_([.,;()])_", r"\1", newline)
            newline = re.sub(r"__\)_", r")_", newline)
            newline = re.sub(r"_ ([.,;])", r"_\1", newline)
            newline = newline.replace("_.’_", ".’")
            newlines.append(newline)
        saveLinesToTextFile("tmp/" + basenameWithoutExt(path) + '.md', newlines)
        


    else:
        print("unknown script")
