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
from TranscriptSummaryPage import SummaryLineMatch, SummaryLineParser, TranscriptSummaryPage, createNewSummaryPage
from util import *
from HAFEnvironment import HAFEnvironment, determineTalkname, talknameFromFilename

# *********************************************
# Talk summaries (Kanban)
# *********************************************

def addMissingTranscriptParagraphHeaderTextCardsForSummariesInRetreat(sfnKanban, haf: HAFEnvironment, retreatName):
    kb = KanbanNote(sfnKanban)
    filenames = filterExt(haf.collectSummaryFilenames(retreatName), '.md')
    for sfnSummaryMd in filenames:
        # load the summary page
        summary = TranscriptSummaryPage(sfnSummaryMd)
        talkName = basenameWithoutExt(sfnSummaryMd)

        # talks can contain brackets, which we need to "escape" for regex searching
        safeTalkname = re.sub("[()]", ".", talkName)

        # collect number of missing paragraph header texts
        missing = summary.collectMissingParagraphHeaderTexts()
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
# Summaries
# *********************************************

def createNewTranscriptSummariesForRetreat(haf: HAFEnvironment, retreatName):
    filenames = haf.collectTranscriptFilenames(retreatName)
    for sfnTranscriptMd in filenames:        
        talkname = talknameFromFilename(sfnTranscriptMd)
        sfnSummaryMd = haf.getSummaryFilename(talkname)
        if sfnSummaryMd is not None:
            summary = loadStringFromTextFile(sfnSummaryMd)
            if re.search(r'#Talk', summary):
                #print(markupName + " - continue")
                continue

        sfnSummaryMd = haf.createSummaryFilename(talkname)
        print("creating " + sfnSummaryMd)

        if re.search(r'#Transcript', transcript := loadStringFromTextFile(sfnTranscriptMd)):
            # we need to deitalize manually
            talkName = determineTalkname(talkname)
            #print(talkName + " - createNew")
            createNewSummaryPage(talkName, haf, transcriptModel, sfnSummaryMd)
        else:
            # it's a transcript page in the making - - not indexed yet, thus we can't do a summary on it yet
            pass


def addAudioLinksToSummaryWithDecoratedTranscript(summary: TranscriptSummaryPage, transcript: TranscriptPage):
    summaryLineParser = SummaryLineParser()

    index = 0
    timestampTranscript = None
    audioDate = audioMiddle = audioId = None
    foundFirstAudio = False
    changed = False
    mlTranscriptHeader = None
    while True:
        if index >= len(summary.markdownLines):
            break
        ml = summary.markdownLines[index]

        # assumption: first audio link in the summary points to the audio for this talk
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
                    oldTimestampSummary = canonicalTimestamp(matchAudio.group('timestamp'))
                    if oldTimestampSummary == timestampTranscript:
                        ml.text = audioLink
                    else:
                        print(f"retained {oldTimestampSummary} (transcript: {timestampTranscript})")
                else:
                    summary.markdownLines.insert(index, audioLink)
                    summary.markdownLines.insert(index+1, "")
                    index += 2
                timestampTranscript = None

        # other matchers which manipulate timestampTranscript go here

        if summaryLineParser.match(ml) == SummaryLineMatch.HEADER:
            # collect for ((WMZAZUR)) below
            mlTranscriptHeader = ml

        if summaryLineParser.match(ml) == SummaryLineMatch.PARAGRAPH_COUNTS:
            # pull the timestamp from the beginning of the transcript paragraph
            mlTranscript = transcript.findParagraph(summaryLineParser.pageNr, summaryLineParser.paragraphNr)
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
                    assert summaryLineParser.headerLine == mlTranscriptHeader.text

                    # we only overwrite ... headers (i.e. not yet entered)                                
                    if summaryLineParser.headerText == '...':
                        # go back up and change the header
                        mlTranscriptHeader.text = f"{summaryLineParser.level * '#'} {headerTranscript}"
                    else:
                        print(f"retained header for {summaryLineParser.blockId}")
                    mlTranscriptHeader = None

                # regardless of the type of match (timestamp or header), remove the paragraph decoration from the transcript
                (_, end) = match.span()
                mlTranscript.text = mlTranscript.text[end:].strip()
                changed = True

        index += 1

    if changed:
        summary.save()
        transcript.save()


def updateSummary(haf, talkName, transcriptModel, sfn=None):
    sfnTranscriptMd = haf.getTranscriptFilename(talkName)
    transcriptPage = TranscriptPage(sfnTranscriptMd)
    transcriptPage.applySpacy(transcriptModel)

    sfnSummaryMd = haf.getSummaryFilename(talkName)
    summaryPage = TranscriptSummaryPage(sfnSummaryMd)
    print(talkName)
    summaryPage.update(transcriptPage, targetType='#^')
    
    if not sfn: sfn = sfnSummaryMd
    summaryPage.save(sfn)


# *********************************************
# breadcrumbs
# *********************************************

def updateBreadcrumbsInSummaries():
    for retreatName in haf.retreatNames:
        transcripts = haf.collectTranscriptFilenames(retreatName)
        assert transcripts
        for index, transcript in enumerate(transcripts):
            talkname = talknameFromFilename(transcript)
            summary = haf.getSummaryFilename(talkname)
            if not summary:
                continue
            note = ObsidianNote(ObsidianNoteType.SUMMARY, summary)
            for markdownLine in note.markdownLines:
                if re.search(r"[⬅️⬆️➡️🡄🡅🡆]", markdownLine.text):
                    if len(transcripts) == 1:
                        pass
                    else:
                        if index == 0:
                            prevSummary = None
                            nextSummary = haf.getSummaryFilename(talknameFromFilename(transcripts[1])) if len(transcripts) > 1 else None
                        elif index == len(transcripts)-1:
                            prevSummary = haf.getSummaryFilename(talknameFromFilename(transcripts[-2])) if len(transcripts) > 1 else None
                            nextSummary = None
                        else:
                            prevSummary = haf.getSummaryFilename(talknameFromFilename(transcripts[index-1]))
                            nextSummary = haf.getSummaryFilename(talknameFromFilename(transcripts[index+1]))
                            pass

                        prevLink = f"[[{basenameWithoutExt(prevSummary)}|{basenameWithoutExt(prevSummary)} 🡄]]" if prevSummary else ''
                        nextLink = f"[[{basenameWithoutExt(nextSummary)}|🡆 {basenameWithoutExt(nextSummary)}]]" if nextSummary else ''
                        
                        newline = f"{prevLink} | [[{retreatName}|🡅]] | {nextLink}"
                        markdownLine.text = newline
                    
            note.save(summary)


# *********************************************
# List folder
# *********************************************

def collectParagraphsListPage(haf, talkname) -> list[str]:
    paragraphs = []
    paragraphs.append("---")
    paragraphs.append("obsidianUIMode: preview")
    paragraphs.append("---")
    paragraphs.append(f"## Paragraphs in [[{talkname}]]")
    sfnSummaryMd = haf.getSummaryFilename(talkname)
    summary = TranscriptSummaryPage(sfnSummaryMd)
    for ml in summary.markdownLines:
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
    summaries = haf.collectSummaryFilenames()
    for sfnSummaryMd in summaries:
        talkname = talknameFromFilename(sfnSummaryMd)        
        note = ObsidianNote(ObsidianNoteType.SUMMARY, sfnSummaryMd)
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
    parser.add_argument('--script')
    parser.add_argument('--retreatName')
    parser.add_argument('--talkName')
    parser.add_argument('--scripts', action="store_true")
    return parser.parse_args()

def isScript(check):
    if isinstance(check, list):
        lower = [s.lower() for s in check]
        return args.script.lower() in lower
    else:
        return args.script.lower() == check.lower()


if __name__ == "__main__":
    args = get_arguments()
    if args.scripts:
        dumpScripts(__file__)
        exit()

    def isScript(check):
        return isScriptArg(args, check)

    haf = HAFEnvironment(HAF_YAML)

    script = args.script
    retreatName = args.retreatName
    talkname = args.talkName

    transcriptIndex = TranscriptIndex(RB_YAML)
    if isScript(['updateSummary', 'createNewSummaries']):
        transcriptModel = TranscriptModel(transcriptIndex)

    if False:
        pass


    # Kanban stuff

    elif isScript('addMissingSummaryCards'):
        assert retreatName
        sfnKanban = haf.vault.findFile('Talk summaries (Kanban).md')
        addMissingTranscriptParagraphHeaderTextCardsForSummariesInRetreat(sfnKanban, haf, retreatName)
        print('done')


    # updating

    elif isScript('updateSummary'):
        if talkname:
            updateSummary(haf, talkname, transcriptModel)
            print(f"updated talk summary")
        else:
            if retreatName:
                # talkNames = [basenameWithoutExt(sfn) for sfn in haf.summaryFilenamesByRetreat[retreatName]]
                # talkNames = [basenameWithoutExt(sfn) for sfn in haf.retreatSummaries(retreatName)]
                talkNames = [basenameWithoutExt(sfn) for sfn in haf.collectSummaryFilenames(retreatName)]
            else:
                #talkNames = list(haf.summaryFilenameByTalk.keys())
                talkNames = haf.collectSummaryTalknames()
            for talkname in talkNames:
                updateSummary(haf, talkname, transcriptModel)
            print(f"updated all talk summaries")

    elif isScript('unspanSummary'):
        assert talkname
        sfn = haf.getSummaryFilename(talkname)
        lines = loadLinesFromTextFile(sfn)
        for index, line in enumerate(lines):
            match = re.match(r"<span class=\"(counts|keywords)\">(?P<inside>[^<]+)</span>", line)
            if match:
                lines[index] = match.group('inside')
        saveLinesToTextFile(sfn, lines)
        print("removed <span>")


    # creating files

    elif isScript('createNewSummaries'):
        assert retreatName
        createNewTranscriptSummariesForRetreat(haf, retreatName)
        updateBreadcrumbsInSummaries()
        print("created")


    # modifiying summaries

    elif isScript('handleDecorations'):
        assert talkname
        transcript = TranscriptPage(haf.getTranscriptFilename(talkname))
        summary = TranscriptSummaryPage(haf.getSummaryFilename(talkname))
        summary.handleTranscriptDecorations(transcript)
        summary.save()
        transcript.save()


    elif isScript('updateBreadcrumbs'):
        updateBreadcrumbsInSummaries()
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

        parser = SummaryLineParser()
        for fnSummary in haf.collectSummaryFilenames():
            summary = TranscriptSummaryPage(fnSummary)
            print(summary.filename)
            for ml in summary.markdownLines:
                match = parser.match(ml)
                if match == SummaryLineMatch.PARAGRAPH_COUNTS:                    
                    if (countsString := parser.counts):
                        counts = collectCounts(countsString)
                        print(counts)
                    pass
            exit()


    # misc

    else:
        print("unknown script")


    