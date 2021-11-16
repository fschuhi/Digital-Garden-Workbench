#!/usr/bin/env python3

from MarkdownLine import SpacyMode
from ObsidianNote import ObsidianNote, ObsidianNoteType
import re
import os

from TranscriptModel import TranscriptModel
from consts import HAF_YAML, RB_YAML
from KanbanNote import KanbanNote
from TranscriptIndex import TranscriptIndex
from TranscriptPage import TranscriptPage
from TalkPage import TalkPageLineMatch, TalkPageLineParser, TalkPage, createNewTalkPage
from util import *
from HAFEnvironment import HAFEnvironment, determineTalkname, talknameFromFilename
from MarkdownLine import MarkdownLines

# *********************************************
# Talks (Kanban)
# *********************************************

def addMissingTranscriptParagraphHeaderTextCardsForTalksInRetreat(sfnKanban, haf: HAFEnvironment, retreatName):
    kb = KanbanNote(sfnKanban)
    filenames = filterExt(haf.collectTalkFilenames(retreatName), '.md')
    for fnTalk in filenames:
        # load the talk page
        talk = TalkPage(fnTalk)
        talkName = basenameWithoutExt(fnTalk)

        # talks can contain brackets, which we need to "escape" for regex searching
        safeTalkname = re.sub("[()]", ".", talkName)

        # collect number of missing paragraph header texts
        missing = talk.collectMissingParagraphHeaderTexts()
        newCard = f"[[{talkName}]] ({missing if missing else 'ok'})"
        searchFunc = lambda ln, c: re.match(r"\[\[" + safeTalkname + r"\]\] \([0-9ok]+\)", c)
        foundCards = kb.findCards(searchFunc)
        # print(r"\[\[" + talkName + r"\]\] \([0-9ok]+\)")
        if missing:
            if foundCards:
                for (listName, card, done) in foundCards:
                    kb.replaceCard(listName, card, newCard)
            else:
                kb.addCard("Pending", newCard, False)
        else:
            for (listName, card, done) in foundCards:
                kb.replaceCard(listName, card, newCard)
    kb.save()


# *********************************************
# talks
# *********************************************

def createNewTalkPagesForRetreat(haf: HAFEnvironment, retreatName):
    filenames = haf.collectTranscriptFilenames(retreatName)
    for sfnTranscriptMd in filenames:        
        talkname = talknameFromFilename(sfnTranscriptMd)
        fnTalk = haf.getTalkFilename(talkname)
        if fnTalk is not None:
            talk = loadStringFromTextFile(fnTalk)
            if re.search(r'#Talk', talk):
                #print(markupName + " - continue")
                continue

        fnTalk = haf.createTalkFilename(talkname)
        print("creating " + fnTalk)

        if re.search(r'#Transcript', transcript := loadStringFromTextFile(sfnTranscriptMd)):
            # we need to deitalize manually
            talkName = determineTalkname(talkname)
            print(talkName + " - createNewTalkPage")
            createNewTalkPage(talkName, haf, transcriptModel, fnTalk)
        else:
            # it's a transcript page in the making - - not indexed yet, thus we can't do a talk on it yet
            pass


def addAudioLinksToTalkWithDecoratedTranscript(talk: TalkPage, transcript: TranscriptPage):
    talkPageLineParser = TalkPageLineParser()

    index = 0
    timestampTranscript = None
    audioDate = audioMiddle = audioId = None
    foundFirstAudio = False
    changed = False
    mlTranscriptHeader = None
    while True:
        if index >= len(talk.markdownLines):
            break
        ml = talk.markdownLines[index]

        # assumption: first audio link in the talk points to the audio for this talk
        if not foundFirstAudio:
            if (matchAudio := parseAudioLink(ml.text)):
                foundFirstAudio = True
                audioDate = matchAudio.group('date')
                audioMiddle = matchAudio.group('middle')
                audioId = matchAudio.group('audioid')

        if timestampTranscript:
            assert foundFirstAudio
            if ml.text:
                audioLink = createAudioLink(audioDate, audioMiddle, audioId, timestampTranscript)

                matchAudio = parseAudioLink(ml.text)
                if matchAudio and matchAudio.group('audioid') == audioId:
                    oldTimestampTalk = canonicalTimestamp(matchAudio.group('timestamp'))
                    if oldTimestampTalk == timestampTranscript:
                        ml.text = audioLink
                    else:
                        print(f"retained {oldTimestampTalk} (transcript: {timestampTranscript})")
                else:
                    talk.markdownLines.insert(index, audioLink)
                    talk.markdownLines.insert(index+1, "")
                    index += 2
                timestampTranscript = None

        # other matchers which manipulate timestampTranscript go here

        if talkPageLineParser.match(ml) == TalkPageLineMatch.DESCRIPTION:
            # collect for ((WMZAZUR)) below
            mlTranscriptHeader = ml

        if talkPageLineParser.match(ml) == TalkPageLineMatch.PARAGRAPH_COUNTS:
            # pull the timestamp from the beginning of the transcript paragraph
            mlTranscript = transcript.findParagraph(talkPageLineParser.pageNr, talkPageLineParser.paragraphNr)
            assert mlTranscript
            while True:
                match = re.match(r"\[((?P<timestamp>(0?1:)?[0-9][0-9]:[0-9][0-9])|(?P<header>[^]]+)) *\]", mlTranscript.text)
                if not match:
                    break

                if not timestampTranscript:
                    timestampTranscript = match.group('timestamp') if match else None
                headerTranscript = match.group('header') if match else None
                if headerTranscript:
                    # assert not timestampTranscript

                    # ((WMZAZUR)) make sure that we have (the right) header as object
                    assert mlTranscriptHeader
                    assert talkPageLineParser.headerLine == mlTranscriptHeader.text

                    # we only overwrite ... headers (i.e. not yet entered)                                
                    if talkPageLineParser.headerText == '...':
                        # go back up and change the header
                        mlTranscriptHeader.text = f"{talkPageLineParser.level * '#'} {headerTranscript}"
                    else:
                        print(f"retained header for {talkPageLineParser.blockId}")
                    mlTranscriptHeader = None

                # regardless of the type of match (timestamp or header), remove the paragraph decoration from the transcript
                (_, end) = match.span()
                mlTranscript.text = mlTranscript.text[end:].strip()
                changed = True

        index += 1

    if changed:
        talk.save()
        transcript.save()


def updateTalk(haf, talkName, transcriptModel, sfn=None):
    sfnTranscriptMd = haf.getTranscriptFilename(talkName)
    transcriptPage = TranscriptPage(sfnTranscriptMd)
    transcriptPage.applySpacy(transcriptModel, mode=SpacyMode.ONLY_FIRST, force=False)

    fnTalk = haf.getTalkFilename(talkName)
    talk = TalkPage(fnTalk)
    print(talkName)
    talk.update(transcriptPage, targetType='#^')
    
    if not sfn: sfn = fnTalk
    talk.save(sfn)


# *********************************************
# breadcrumbs
# *********************************************

def updateBreadcrumbsInTalks():
    for retreatName in haf.retreatNames:
        transcripts = haf.collectTranscriptFilenames(retreatName)
        assert transcripts
        for index, transcript in enumerate(transcripts):
            talkname = talknameFromFilename(transcript)
            talk = haf.getTalkFilename(talkname)
            if not talk:
                continue
            note = ObsidianNote(ObsidianNoteType.TALK, talk)
            for markdownLine in note.markdownLines:
                if re.search(r"[⬅️⬆️➡️🡄🡅🡆]", markdownLine.text):
                    if len(transcripts) == 1:
                        pass
                    else:
                        if index == 0:
                            prevTalk = None
                            nextTalk = haf.getTalkFilename(talknameFromFilename(transcripts[1])) if len(transcripts) > 1 else None
                        elif index == len(transcripts)-1:
                            prevTalk = haf.getTalkFilename(talknameFromFilename(transcripts[-2])) if len(transcripts) > 1 else None
                            nextTalk = None
                        else:
                            prevTalk = haf.getTalkFilename(talknameFromFilename(transcripts[index-1]))
                            nextTalk = haf.getTalkFilename(talknameFromFilename(transcripts[index+1]))
                            pass

                        prevLink = f"[[{basenameWithoutExt(prevTalk)}|{basenameWithoutExt(prevTalk)} 🡄]]" if prevTalk else ''
                        nextLink = f"[[{basenameWithoutExt(nextTalk)}|🡆 {basenameWithoutExt(nextTalk)}]]" if nextTalk else ''
                        
                        newline = f"{prevLink} | [[{retreatName}|🡅]] | {nextLink}"
                        markdownLine.text = newline
                    
            note.save(talk)


# *********************************************
# List folder
# *********************************************

def collectParagraphsListPage(haf, talkname) -> list[str]:
    paragraphs = []
    paragraphs.append("---")
    paragraphs.append("obsidianUIMode: preview")
    paragraphs.append("---")
    # paragraphs.append(f"## Paragraphs in [[{talkname}]]")
    paragraphs.append(f"Paragraph descriptions in **[[{talkname}]]**:")
    fnTalk = haf.getTalkFilename(talkname)
    talk = TalkPage(fnTalk)
    parser = TalkPageLineParser()
    lastHeaderText = None

    def addLinkToHeader(description):
        headerLink = determineHeaderTarget(description)
        fullstop = '' if re.search(r"[.?!)]$",description) else '.'
        linkToHeader = f"- [[{talkname}#{headerLink}|{description}{fullstop}]]"
        paragraphs.append(linkToHeader)

    for ml in talk.markdownLines:
        match = parser.match(ml)
        if match == TalkPageLineMatch.DESCRIPTION:
            description = parser.headerText
            addLinkToHeader(description)
            lastHeaderText = None
        elif match == TalkPageLineMatch.PARAGRAPH_COUNTS:
            if lastHeaderText:
                addLinkToHeader(lastHeaderText)
                lastHeaderText = None
        elif match == TalkPageLineMatch.HEADER:
            if parser.level >= 3:
                paragraphs.append(ml.text)
                lastHeaderText = parser.headerText
    return paragraphs


def updateParagraphsListPages(haf: HAFEnvironment):
    talkFilenames = haf.collectTalkFilenames()
    for fnTalk in talkFilenames:
        talkname = talknameFromFilename(fnTalk)        
        note = ObsidianNote(ObsidianNoteType.TALK, fnTalk)
        createPage = note.getYamlValue('ParagraphsListPage')
        if (createPage is None) or createPage:
            pageLines = collectParagraphsListPage(haf, talkname)
            sfn = haf.createListFilename(talkname)
            saveLinesToTextFile(sfn, pageLines)
        else:
            print("skipped", talkname)


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
    return parser.parse_args()

def isScript(check):
    if isinstance(check, list):
        lower = [s.lower() for s in check]
        return args.script.lower() in lower
    else:
        return args.script.lower() == check.lower()


if __name__ == "__main__":
    args = get_arguments()

    def isScript(check):
        return isScriptArg(args, check)

    haf = HAFEnvironment(HAF_YAML)

    script = args.script
    scriptHelp = args.scriptHelp
    retreatName = args.r
    talkname = args.t

    if not scriptHelp:
        transcriptIndex = TranscriptIndex(RB_YAML)
        if isScript(['bla', 'update', 'createNewTalks']):
            transcriptModel = TranscriptModel(transcriptIndex)

    if isScript('scripts'):
        dumpScripts(__file__)
        exit()


    # Kanban stuff

    elif isScript('updateKanban'):
        if scriptHelp: exitHelp([
            "-r\tadd and update cards on 'Talks (Kanban).md' for the particular retreat"
        ])
        assert retreatName
        sfnKanban = haf.vault.findFile('Talks (Kanban).md')
        addMissingTranscriptParagraphHeaderTextCardsForTalksInRetreat(sfnKanban, haf, retreatName)
        print('done')


    # updating

    elif isScript('update'):
        if scriptHelp: exitHelp([
            "-t\tupdate a particular talk",
            "-r\tupdate all talks in the retreat\n",
            "If called w/o -t and -r, updates all talks across all retreats.\n",
            "The script updates the counts in the 'Index' section as well as for all sections in 'Paragraphs'.",
            "NOTE that updating is done in place.",
        ])
        if talkname:
            updateTalk(haf, talkname, transcriptModel)
            print(f"updated talk")
        else:
            if retreatName:
                talkNames = [basenameWithoutExt(sfn) for sfn in haf.collectTalkFilenames(retreatName)]
            else:
                talkNames = haf.collectTalknames()
            for talkname in talkNames:
                updateTalk(haf, talkname, transcriptModel)
            print(f"updated all talks")

    elif isScript('unspan'):
        if scriptHelp: exitHelp([
            "-t\ttalk page where to remove the <span> around the counts"
        ])
        assert talkname
        sfn = haf.getTalkFilename(talkname)
        lines = loadLinesFromTextFile(sfn)
        for index, line in enumerate(lines):
            match = re.match(r"<span class=\"(counts|keywords)\">(?P<inside>[^<]+)</span>", line)
            if match:
                lines[index] = match.group('inside')
        saveLinesToTextFile(sfn, lines)
        print("removed <span>")


    # creating files

    elif isScript('createNewTalks'):
        if scriptHelp: exitHelp([
            "-r\tretreat to create new talk pages for"
        ])
        assert retreatName
        createNewTalkPagesForRetreat(haf, retreatName)
        updateBreadcrumbsInTalks()
        print("created")


    # modifiying talks

    elif isScript('handleDecorations'):
        if scriptHelp: exitHelp([
            "-t\ttalk for which to transfer the audio timestamp and paragraph descriptions from the transcript to the talk\n",
            "DANGER: done in place, i.e. transcript loses the decorations, so create bak and prepare git."
        ])
        assert talkname
        transcript = TranscriptPage(haf.getTranscriptFilename(talkname))
        talk = TalkPage(haf.getTalkFilename(talkname))
        talk.handleTranscriptDecorations(transcript)
        talk.save()
        transcript.save()


    elif isScript('updateBreadcrumbs'):
        if scriptHelp: exitHelp("no parameters")
        updateBreadcrumbsInTalks()
        print("updated")

    elif isScript('updateParagraphsLists'):
        if scriptHelp: exitHelp("no parameters")
        updateParagraphsListPages(haf)


    # top 10 backlinks (not used)

    elif isScript('Top10SecondTryWithParagrapCounts'):
        if scriptHelp: exitHelp("no parameters")

        def collectCounts(countsString: str) -> dict[str,int]:
            counts = {}
            singleCounts = countsString.split(' · ')
            for singleCount in singleCounts:
                match = re.match(r"\[\[(?P<entry>[^]]+)\]\]( \((?P<count>[0-9]+)\))?", singleCount)
                if not match:
                    print(countsString)
                    print("!!!!" + singleCount)
                assert match
                count = suppliedCount if (suppliedCount := match.group('count')) else 1
                counts[match.group('entry')] = count
            return counts

        parser = TalkPageLineParser()
        for fnTalk in haf.collectTalkFilenames():
            talk = TalkPage(fnTalk)
            print(talk.notename)
            for ml in talk.markdownLines:
                match = parser.match(ml)
                if match == TalkPageLineMatch.PARAGRAPH_COUNTS:                    
                    if (countsString := parser.counts):
                        counts = collectCounts(countsString)
                        print(counts)
                    pass
            exit()


    # misc

    elif isScript('bla'):
        talkname = "Preliminaries Regarding Voice, Movement, and Gesture - Part 5"
        talkname = "Using Insight to Deepen Love and Compassion"
        talk = TalkPage(haf.getTalkFilename(talkname))
        transcript = TranscriptPage(haf.getTranscriptFilename(talkname))

        talk.collectSections(autoparse=True)
        firstSection = talk.sections[0]
        lastSection = talk.sections[-1]

        # A: add everything (including yaml) before the first talk section
        newLines = []
        newLines.extend(talk.generateYamlLines())
        prolog = [ml.text for ml in talk.markdownLines[0:firstSection.start-1]]
        newLines.extend(prolog)

        # B: add sections
        paragraphs = transcript.collectParagraphs(True)
        lastParagraphAppendedonTheFly = False
        for paragraph in paragraphs:
            (pageNr, paragraphNr, mlParagraph) = paragraph            
            section = talk.sections.findParagraph(pageNr, paragraphNr)
            if not section:
                # paragraph is not included on work talk page
                (_, _, paragraphText) = parseParagraph(mlParagraph.text)
                newLines.append(f'<span class="paragraph">{paragraphText}</span>')
                lastParagraphAppendedonTheFly = True
            else:
                if lastParagraphAppendedonTheFly:
                    # we added the paragraph(s) above, so close the section with another hr
                    newLines.append('')
                    newLines.append('---')
                lastParagraphAppendedonTheFly = False

                # quotes are turned into marking, which we therefore need to skip when adding admonitions
                handledQuotes = set()

                # start of section needed to put first audio link before paragraph text
                sectionStart = len(newLines)

                # we need to adjust insertation point of == if we have multiple quotes in this section
                delta = 0

                # B1: header and counts always come first
                newLines.append(section.headerLine.text)
                newLines.append(section.countsLine.text)

                # B2: paragraph text, with marked quotes                
                if section.admonitions:
                    rawText = None
                    replaced = False
                    for admonition in section.admonitions:
                        if admonition.type == 'quote':
                            admonitionText = '\n'.join([ml.text for ml in section.markdownLines[admonition.start+1:admonition.end]])
                            if rawText is None:
                                # removeAllLinks only once
                                mlParagraph.removeAllLinks()
                                rawText = mlParagraph.text

                            # quote doesn't contain links, so we need to compare it with the paragraph where the links were removed (see above)
                            ixFound = rawText.find(admonitionText)
                            if ixFound >= 0:
                                mlParagraph.replace(ixFound+delta, ixFound+delta+len(admonitionText), f"=={admonitionText}==")
                                delta += 4
                                replaced = True
                                handledQuotes.add(admonition.start)
                    if replaced:
                        # we turned at least one quote admonition into a marking
                        # restore links and footnotes
                        mlParagraph.applySpacy(transcriptModel, SpacyMode.ALL_LINKS, force=False)
                        mlParagraph.restoreFootnotes()

                # now the markdown of the paragraph has quotes as ==...== markings

                # B3: add paragraph text
                
                (_, _, paragraphText) = parseParagraph(mlParagraph.text)
                newLines.append(f'<span class="paragraph">{paragraphText}</span>')

                # B4: transfer all lines from the section to the published section (except header, counts and quotes)
                firstAudioLink = section.firstAudioLink()
                inAdmonition = False
                lastAppendedLine = None
                for index, ml in enumerate(section.markdownLines):
                    if index < 2:
                        # skip header and counts
                        continue

                    if ml == firstAudioLink:
                        # audio link comes before paragraph text
                        newLines.insert(sectionStart+2, firstAudioLink.text)
                        continue

                    if index in handledQuotes:
                        # quote admonition which was successfully marked in the paragraph text starts...
                        inAdmonition = True
                    else:
                        if inAdmonition:
                            # ... skip it
                            pass
                        else:
                            mlText = ml.text
                            if lastAppendedLine == '' and mlText == '':
                                # duplicate whitespace removed
                                pass
                            else:
                                # add admonition line
                                newLines.append(mlText)
                            lastAppendedLine = mlText
                        if ml.text == '```':
                            inAdmonition = False                               

        # C: add the lines after the last section
        epilog = [ml.text for ml in talk.markdownLines[lastSection.end:]]
        newLines.extend(epilog)

        saveLinesToTextFile(r"M:\Brainstorming\Untitled.md", newLines)

    else:
        print("unknown script")


    