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
            newline = re.sub(r"_ _( ?[^_]+? ?)_ ?_", r" _\1_ ", line)
            if (match := re.match(r"^ *?_(.+)_$", newline)):
                newline = match.group(1)
            newline = re.sub(r"_([.,;()])_", r"\1", newline)
            newline = re.sub(r"__\)_", r")_", newline)
            newline = re.sub(r"_ ([.,;])", r"_\1", newline)
            newline = newline.replace("_.’_", ".’")
            newline = newline.replace("__", "")
            newline = newline.replace("** **", " ")
            print(newline)
            newlines.append(newline)
        saveLinesToTextFile("tmp/" + basenameWithoutExt(path) + '.md', newlines)


    elif isScript('writeCsv'):
        talkname = "Samadhi in Metta Practice"
        talk = TalkPage(haf.getTalkFilename(talkname))
        transcript = TranscriptPage(haf.getTranscriptFilename(talkname))
        import csv
        tuples = []
        tuples.append(('bla', 'heul'))
        sections = talk.collectSections()
        for section in sections:
            ml = transcript.findParagraph(section.pageNr, section.paragraphNr)
            assert ml
            ml.removeAllLinks()
            tuples.append((section.headerText, ml.text))
        saveTuplesToCsv("tmp/bla.csv", tuples)


    elif isScript('readCsv'):
        talkname2007 = "Samadhi in Metta Practice"
        talk2007 = TalkPage(haf.getTalkFilename(talkname2007))
        sections2007 = talk2007.collectSections()
        transcript2007 = TranscriptPage(haf.getTranscriptFilename(talkname2007))

        talkname2008 = "The Place of Samadhi in Metta Practice"
        talk2008 = TalkPage(haf.getTalkFilename(talkname2008))
        sections2008 = talk2008.collectSections()
        transcript2008 = TranscriptPage(haf.getTranscriptFilename(talkname2008))

        path = "data/2008 vs 2007.csv"
        tuples = []
        import csv
        tuples = loadTuplesFromCsv(path)
        del tuples[0]

        lines = []
        lines.append("---")
        lines.append("obsidianUIMode: preview")
        lines.append("---")
        lines.append("")
        lines.append("## Synopsis")
        lines.append("")
        lines.append(f"left:\t[[{transcript2008.notename}]] (==[[{transcript2008.retreatname}|{transcript2008.retreatname[:4]}]]==)")
        lines.append(f"right:\t[[{transcript2007.notename}]] ([[{transcript2007.retreatname}|{transcript2007.retreatname[:4]}]])")
        lines.append("")
        lines.append(f"==[[{transcript2008.notename}\\|2008]]== | [[{transcript2007.notename}\\|2007]]")
        lines.append("- | -")

        for tuple in tuples:
            (blockid2008, blockid2007, ref2007, comment) = tuple                        
            cell2008 = cell2007 = ""
            if blockid2008 or ref2007 or comment:
                if blockid2008:
                    section2008 = sections2008.findParagraph(*parseBlockId(blockid2008))
                    headerText2008 = section2008.headerText
                    paragraph2008 = transcript2008.findParagraph(*parseBlockId(blockid2008))
                    paragraph2008.removeAllLinks()
                    (_, _, paragraph2008text) = parseParagraph(paragraph2008.text)
                    talkLink2008 = f"[[{talkname2008}#{determineHeaderTarget(headerText2008)}\\|{headerText2008}]]"
                    transcriptLink2008 = f"[[{transcript2008.notename}#^{blockid2008}\\|{blockid2008}]]"
                    cell2008 = f"<span class=\"blockid\">{blockid2008}</span>&nbsp;&nbsp;{talkLink2008}<br/><hr class=\"cell\">{paragraph2008text}"
                if comment:
                    cell2008 = f"{cell2008}<br/><hr class=\"cell\"><span style=\"color:red\">{comment}</span>"
            if blockid2007 or ref2007:
                if blockid2007:
                    section2007 = sections2007.findParagraph(*parseBlockId(blockid2007))
                    headerText2007 = section2007.headerText
                    paragraph2007 = transcript2007.findParagraph(*parseBlockId(blockid2007))
                    paragraph2007.removeAllLinks()
                    (_, _, paragraph2007text) = parseParagraph(paragraph2007.text)
                    talkLink2007 = f"[[{talkname2007}#{determineHeaderTarget(headerText2007)}\\|{headerText2007}]]"
                    transcriptLink2007 = f"[[{transcript2007.notename}#^{blockid2007}\\|{blockid2007}]]"
                    cell2007 = f"<span class=\"blockid\">{blockid2007}</span>&nbsp;&nbsp;{talkLink2007}<br/><hr class=\"cell\">{paragraph2007text}"
                if ref2007:
                    section2007ref = sections2007.findParagraph(*parseBlockId(ref2007))
                    headerText2007ref = section2007ref.headerText
                    talkLink2007ref = f"<span style=\"color:red\">also</span> [[{talkname2007}#{determineHeaderTarget(headerText2007ref)}\\|{headerText2007ref}]]"
                    cell2007 = f"{cell2007}<br/><hr class=\"cell\">{talkLink2007ref}"
            lines.append(f"| {cell2008} | {cell2007} |")

        saveLinesToTextFile("M:/Brainstorming/Untitled.md", lines)

    else:
        print("unknown script")
