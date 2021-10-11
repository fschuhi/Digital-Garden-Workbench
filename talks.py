#!/usr/bin/env python3

from ObsidianNote import ObsidianNote, ObsidianNoteType
import re
import os

from LinkNetwork import LinkNetwork
from TranscriptModel import TranscriptModel
from consts import HAF_YAML, RB_YAML
from KanbanNote import KanbanNote
from TranscriptIndex import TranscriptIndex
from TranscriptPage import TranscriptPage
from TalkPage import TalkPageLineMatch, TalkPageLineParser, TalkPage, createNewTalkPage
from util import *
from HAFEnvironment import HAFEnvironment, determineTalkname, talknameFromFilename

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
            #print(talkName + " - createNew")
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

        if talkPageLineParser.match(ml) == TalkPageLineMatch.HEADER:
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
    transcriptPage.applySpacy(transcriptModel)

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
    paragraphs.append(f"## Paragraphs in [[{talkname}]]")
    fnTalk = haf.getTalkFilename(talkname)
    talk = TalkPage(fnTalk)
    for ml in talk.markdownLines:
        if (match := re.match(r"(?P<level>#+) *(?P<description>.+)", ml.text)):
            description = match.group("description") # type: str
            headerLink = determineHeaderTarget(description)
            level = match.group('level')
            if len(level) == 5:
                fullstop = '' if re.search(r"[.?!)]$",description) else '.'
                link = f"- [[{talkname}#{headerLink}|{description}{fullstop}]]"
                paragraphs.append(link)
            elif len(level) >= 3:
                paragraphs.append(ml.text)
            else:
                pass    
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
    retreatName = args.r
    talkname = args.t

    transcriptIndex = TranscriptIndex(RB_YAML)
    if isScript(['update', 'createNewTalks']):
        transcriptModel = TranscriptModel(transcriptIndex)

    if isScript('scripts'):
        dumpScripts(__file__)
        exit()


    # Kanban stuff

    elif isScript('addMissingTalkCards'):
        assert retreatName
        sfnKanban = haf.vault.findFile('Talks (Kanban).md')
        addMissingTranscriptParagraphHeaderTextCardsForTalksInRetreat(sfnKanban, haf, retreatName)
        print('done')


    # updating

    elif isScript('update'):
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
        assert retreatName
        createNewTalkPagesForRetreat(haf, retreatName)
        updateBreadcrumbsInTalks()
        print("created")


    # modifiying talks

    elif isScript('handleDecorations'):
        assert talkname
        transcript = TranscriptPage(haf.getTranscriptFilename(talkname))
        talk = TalkPage(haf.getTalkFilename(talkname))
        talk.handleTranscriptDecorations(transcript)
        talk.save()
        transcript.save()


    elif isScript('updateBreadcrumbs'):
        updateBreadcrumbsInTalks()
        print("updated")

    elif isScript('updateParagraphsLists'):
        updateParagraphsListPages(haf)


    # top 10 backlinks (not used)

    elif isScript('Top10SecondTryWithParagrapCounts'):

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
            print(talk.filename)
            for ml in talk.markdownLines:
                match = parser.match(ml)
                if match == TalkPageLineMatch.PARAGRAPH_COUNTS:                    
                    if (countsString := parser.counts):
                        counts = collectCounts(countsString)
                        print(counts)
                    pass
            exit()


    # misc

    else:
        print("unknown script")


    