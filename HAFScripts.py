#!/usr/bin/env python3

from ObsidianNote import ObsidianNote, ObsidianNoteType
import re
import os

from LinkNetwork import LinkNetwork
from MarkdownLine import MarkdownLine
from Publishing import Publishing
from TranscriptModel import TranscriptModel
from shutil import copyfile
from consts import HAF_PUBLISH_YAML, HAF_YAML, RB_YAML
from KanbanNote import KanbanNote
from TranscriptIndex import TranscriptIndex
from TranscriptPage import TranscriptPage, createTranscriptsDictionary
from TranscriptSummaryPage import SummaryLineMatch, SummaryLineParser, TranscriptSummaryPage, createNewSummaryPage
from IndexEntryPage import IndexEntryPage
from util import *
from HAFEnvironment import HAFEnvironment, determineTalkname, talknameFromFilename
import pyperclip

#import sys
#import codecs
# sys.stdout = codecs.getwriter('utf8')(sys.stdout)

# *********************************************
# Talk summaries (Kanban)
# *********************************************

def addMissingTranscriptParagraphHeaderTextCardsForSummariesInRetreat(sfnKanban, haf: HAFEnvironment, retreatName):
    kb = KanbanNote(sfnKanban)
    # look at factory methods to collect all summary pages
    # filenames = filterExt(haf.summaryFilenamesByRetreat[retreatName], '.md')
    # filenames = filterExt(haf.retreatSummaries(retreatName), '.md')
    filenames = filterExt(haf.collectSummaryFilenames(retreatName), '.md')
    for sfnSummaryMd in filenames:
        (filenameWithoutExt, ext) = os.path.splitext(sfnSummaryMd)                
        # load the summary page
        summary = TranscriptSummaryPage(sfnSummaryMd)
        talkName = basenameWithoutExt(sfnSummaryMd)

        # talks can contain brackets, which we need to "escape" for regex searching
        talkName = re.sub("[()]", ".", talkName)

        # collect number of missing paragraph header texts
        missing = summary.collectMissingParagraphHeaderTexts()
        newCard = f"[[{talkName}]] ({missing if missing else 'ok'})"
        searchFunc = lambda ln, c: re.match(r"\[\[" + talkName + r"\]\] \([0-9ok]+\)", c)
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
# Transcripts
# *********************************************

def applySpacyToTranscriptParagraphsForRetreat(haf: HAFEnvironment, retreatName, transcriptModel: TranscriptModel):
    # filenames = filterExt(haf.transcriptFilenamesByRetreat[retreatName], '.md')
    # filenames = filterExt(haf.retreatTranscripts(retreatName), '.md')
    filenames = filterExt(haf.collectTranscriptFilenames(retreatName), '.md')
    for sfnTranscriptMd in filenames:
        (filenameWithoutExt, ext) = os.path.splitext(sfnTranscriptMd)                
        if ext == '.md':
            markdownName = basenameWithoutExt(sfnTranscriptMd)
            if re.match(r'[0-9][0-9][0-9][0-9] ', markdownName):
                transcript = loadStringFromTextFile(sfnTranscriptMd)
                if re.search(r'#Transcript', transcript):
                    page = TranscriptPage(sfnTranscriptMd)
                    page.applySpacy(transcriptModel)
                    page.save(sfnTranscriptMd)


def replaceLinks(haf_publish, filenames, replaceIndex):
    website = haf_publish.website()
    
    indexEntryNameSet = haf_publish.collectIndexEntryNameSet()
    transcriptNameSet = haf_publish.collectTranscriptNameSet()

    def filterLinks(match):
        note = match.group('note')
        assert note
        target = match.group('target')
        
        # convert links on summary to transcript
        if target and target.startswith('#^') and note in transcriptNameSet:
            return True

        # convert any index entry
        if replaceIndex and (note in indexEntryNameSet):
            return True

        return False

    for filename in filenames:
        # print(baseNameWithoutExt(sfnSummaryMd))
        text = loadStringFromTextFile(filename)
        markdown = MarkdownLine(text)
        markdown.replaceLinks(lambda match: f"{convertMatchedObsidianLink(match, website, filterLinks)}")
        saveStringToTextFile(filename, markdown.text)


def replaceLinksInAllSummaries():
    haf_publish = HAFEnvironment(HAF_PUBLISH_YAML)
    #filenames = list(haf_publish.summaryFilenameByTalk.values())
    filenames = haf_publish.collectSummaryFilenames()
    replaceLinks(haf_publish, filenames, True)

def replaceLinksInAllRootFilenames():
    haf_publish = HAFEnvironment(HAF_PUBLISH_YAML)
    #filenames = list(haf_publish.rootFilenameByTalk.values())
    filenames = haf_publish.collectNotesInRetreatsFolders()
    replaceLinks(haf_publish, filenames, False)

def replaceLinksInSpecialFiles():
    haf_publish = HAFEnvironment(HAF_PUBLISH_YAML)
    index = os.path.join(haf_publish.root, 'Index.md')
    assert os.path.exists(index)
    replaceLinks(haf_publish, [index], True)


# *********************************************
# new transcripts
# *********************************************

def convertPlainMarkdownToTranscript(haf: HAFEnvironment, talkName):
    sfnTranscriptMd = haf.getTranscriptFilename(talkName)
    lines = loadLinesFromTextFile(sfnTranscriptMd)
    page = TranscriptPage.fromPlainMarkdownLines(lines)
    page.save(sfnTranscriptMd)


def firstIndexingOfRetreatFolder(haf: HAFEnvironment, retreatName):
    # filenames = filterExt(haf.transcriptFilenamesByRetreat[retreatName], '.md')
    #filenames = filterExt(haf.retreatTranscripts(retreatName), '.md')
    filenames = filterExt(haf.collectTranscriptFilenames(retreatName), '.md')
    for sfnTranscriptMd in filenames:
        (filenameWithoutExt, ext) = os.path.splitext(sfnTranscriptMd)                
        if re.match(r'[0-9][0-9][0-9][0-9] ', markdownName := basenameWithoutExt(sfnTranscriptMd)): 
            if re.search(r'#Transcript', transcript := loadStringFromTextFile(sfnTranscriptMd)):
                # it's a regular transcript page - - already indexed
                pass
            else:
                # we need to deitalize manually
                transcript = deitalicizeTermsWithDiacritics(transcript)
                lines = transcript.splitlines()
                page = TranscriptPage.fromPlainMarkdownLines(lines)

                # create backup (if it doesn't exist yet)
                from shutil import copyfile                
                if not os.path.exists(bak := filenameWithoutExt + '.bak'):
                    copyfile(sfnTranscriptMd, bak)

                page.save(sfnTranscriptMd)


def deitalicizeTranscript(haf: HAFEnvironment, talkName):
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
# Summaries
# *********************************************

def createNewTranscriptSummariesForRetreat(haf, retreatName):
    filenames = filterExt(haf.retreatTranscriptFilenameLookup[retreatName], '.md')
    for sfnTranscriptMd in filenames:
        (filenameWithoutExt, ext) = os.path.splitext(sfnTranscriptMd)                
        markdownName = basenameWithoutExt(sfnTranscriptMd)
        sfnSummaryMd = haf.getSummaryFilename(markdownName)
        if os.path.exists(sfnSummaryMd):
            summary = loadStringFromTextFile(sfnSummaryMd)
            if re.search(r'#TranscriptSummary', summary):
                #print(markupName + " - continue")
                continue

        if re.match(r'[0-9][0-9][0-9][0-9] ', markdownName):            
            if re.search(r'#Transcript', transcript := loadStringFromTextFile(sfnTranscriptMd)):
                # we need to deitalize manually
                talkName = determineTalkname(markdownName)
                #print(talkName + " - createNew")
                createNewSummaryPage(talkName, haf, transcriptModel)
            else:
                # it's a transcript page in the making - - not indexed yet, thus we can't do a summary on it yet
                pass


def updateSummary(haf, talkName, transcriptModel, sfn=None):
    sfnTranscriptMd = haf.getTranscriptFilename(talkName)
    transcriptPage = TranscriptPage(sfnTranscriptMd)
    transcriptPage.applySpacy(transcriptModel)

    sfnSummaryMd = haf.getSummaryFilename(talkName)
    summaryPage = TranscriptSummaryPage(sfnSummaryMd)
    summaryPage.update(transcriptPage, targetType='#^')
    
    if not sfn: sfn = sfnSummaryMd
    summaryPage.save(sfn)


# *********************************************
# IndexEntryPage
# *********************************************

def addMissingCitations(haf: HAFEnvironment, indexEntry, transcriptIndex, transcriptModel):
    # ACHTUNG: index entry is case sensitive!
    indexEntryPage = IndexEntryPage(haf.getIndexEntryFilename(indexEntry))

    #filenames = haf.collectTranscriptFilenamesForRetreat('Vajra Music')
    filenames = haf.collectTranscriptFilenames()

    indexEntryPage.updateCitations(transcriptModel)

    transcripts = createTranscriptsDictionary(filenames, transcriptModel)
    indexEntryPage.addMissingTranscripts(transcripts)
    indexEntryPage.save()


# *********************************************
# index management
# *********************************************

def updateAlphabeticalIndex(haf: HAFEnvironment, transcriptIndex: TranscriptIndex):
    # contains "Albert Einstein"
    pages = list(transcriptIndex.pagesSet - set(transcriptIndex.sections['ignored']))

    # "Albert Einstein" needs to show up as "Einstein, Albert" (i.e. not in A but in E)
    alphabeticalPages = []
    for page in pages:
        alphabeticalPage = page if page not in transcriptIndex.alphabetical else transcriptIndex.alphabetical[page]
        alphabeticalPages.append(alphabeticalPage)

    # now sort the complete list
    alphabeticalPages.sort()

    # group "Einstein, Albert" in E
    from itertools import groupby
    groupby = ([(k, list(g)) for k, g in groupby(alphabeticalPages, key=lambda x: x[0])])
    sortedPagesByFirstChar = {} # type: dict[str,str]
    for c, l in groupby:
        sortedPagesByFirstChar[c] = l

    #indexMd = r"s:\work\Python\HAF\_Markdown\Rob Burbea\Index.md"
    indexMd = haf.vault.pathnames(r"**/Index.md")[0]

    lines = loadLinesFromTextFile(indexMd)
    for index, line in enumerate(lines):        
        if (match := re.match(r"#+ (?P<char>[A-Z]) *$", line)):            
            if (char := match.group('char')) in sortedPagesByFirstChar:

                # contains "Einstein, Albert"
                pages = sortedPagesByFirstChar[char]

                # get the true md name using reverseAlphatical, i.e. resolve to "Albert Einstein"
                links = ['[[' + (p if not p in transcriptIndex.reverseAlphabetical else (transcriptIndex.reverseAlphabetical[p] + '|' + p)) + ']]' for p in pages]
                lines[index+1] = ' &nbsp;·&nbsp; '.join(links)
            else:
                lines[index+1] = '<br/>'

    saveLinesToTextFile(indexMd, lines)


# ((XEFDXYJ)) move sorting to TranscriptIndex
def sortRBYaml(transcriptIndex: TranscriptIndex, args):
    dict = transcriptIndex.dictionary

    sections = list(dict.keys())
    if args.sectionsort:
        sections.sort()

    sorted = []        
    for section in sections:

        sorted.append(section + ":")
        lst = dict[section]
        lst.sort(key=lambda x: next(iter(x)) if isinstance(x,type(dict)) else x)

        for el in lst:
            if isinstance(el, type(dict)):
                elWithSublist = next(iter(el))
                sorted.append("  - " + elWithSublist + ":")
                sublist = el[elWithSublist]
                for sublistel in sublist:
                    if isinstance(sublistel,type(dict)):
                        key = next(iter(sublistel))
                        value = sublistel[key]
                        sorted.append( "      - " + key + ": " + value)
                    else:
                        sorted.append( "      - " + sublistel)
            else:
                sorted.append("  - " + el)

        sorted.append("")    
    sorted.pop()
    
    sfnOut = args.out if args.out else RB_YAML

    if os.path.abspath(sfnOut) == os.path.abspath(RB_YAML):
        path = os.path.dirname(os.path.abspath(RB_YAML))
        bak = os.path.join(path, basenameWithoutExt(RB_YAML) + '.bak.yaml')
        copyfile(RB_YAML, bak)

    saveLinesToTextFile(sfnOut, sorted)


def showOrphansInIndexFolder(haf: HAFEnvironment, network: LinkNetwork, transcriptIndex: TranscriptIndex, dirIndexEntries):
    filenames = filterExt(os.listdir(dirIndexEntries), '.md')
    outLines = []
    outLines.append('note | has content | has backlinks')
    outLines.append('- | - | -')
    for filename in filenames:
        basename = os.path.splitext(filename)[0]
        note = basename
        
        inPagesSet = note in transcriptIndex.pagesSet
        sfnNote = os.path.join(dirIndexEntries, filename)
        lines = loadLinesFromTextFile(sfnNote)

        hasContent = len(lines) > 1 # exclude the tag line
        hasBacklinks = network.hasBacklinks(note, ['Index'])

        if inPagesSet and hasBacklinks:
            pass
        else:
            outLines.append('|'.join( [note, str(hasContent), str(hasBacklinks)]))

    out ='\n'.join(outLines)
    # print(out)
    import pyperclip
    pyperclip.copy(out)


def showOrphansInRBYaml(haf: HAFEnvironment, network: LinkNetwork, transcriptIndex: TranscriptIndex, dirIndexEntries):
    indexEntryNameSet = set(n.lower() for n in haf.collectIndexEntryNameSet())
    allNotesSet = set(n.lower() for n in network.allNotes)

    outLines = []
    outLines.append('entry | md exists | has same name | has content | backlinks ')
    outLines.append('- | - | - | - | - ')
    notes = list(transcriptIndex.pagesSet - set(transcriptIndex.sections['ignored']))
    for note in sorted(notes):
        noteKey = note.lower()
        indexMdExists = noteKey in indexEntryNameSet        
        if (mdExists := noteKey in allNotesSet):
            hasSameName = network.getActualNoteNameByNote(note) == note
            sfnPage = network.getFilenameByNote(noteKey)
            assert os.path.exists(sfnPage)
            lines = loadLinesFromTextFile(sfnPage)
            hasContent = len(lines) > 1 # exclude the tag line
        else:
            hasSameName = ''
            hasContent = ''
        
        backlinks = network.getBacklinksByNote(noteKey)
        hasBacklinks = len(backlinks) > 0

        if indexMdExists and hasSameName and hasBacklinks:
            pass
        else:
            outLines.append('|'.join( [note, str(mdExists), str(hasSameName), str(hasContent), str(hasBacklinks)] ))

    out ='\n'.join(outLines)
    # print(out)
    import pyperclip
    pyperclip.copy(out)



def replaceNoteLink(haf: HAFEnvironment, network: LinkNetwork, args):
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

def collectParagraphsListPage(talkname) -> list[str]:
    paragraphs = []
    paragraphs.append("---")
    paragraphs.append("obsidianUIMode: preview")
    paragraphs.append("---")
    paragraphs.append(f"### Paragraphs in [[{talkname}]]")
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


def collectParagraphsListPageToClipboard(talkname):
    pageLines = collectParagraphsListPage()
    pyperclip.copy('\n'.join(pageLines))        


def updateParagraphsListPages(haf: HAFEnvironment):
    summaries = haf.collectSummaryFilenames()
    for sfnSummaryMd in summaries:
        talkname = talknameFromFilename(sfnSummaryMd)        
        note = ObsidianNote(ObsidianNoteType.SUMMARY, sfnSummaryMd)
        createPage = note.getYamlValue('ParagraphsListPage')
        if (createPage is None) or createPage:
            pageLines = collectParagraphsListPage(talkname)
            sfn = haf.createListFilename(talkname)
            saveLinesToTextFile(sfn, pageLines)
        else:
            print("skipped", talkname)


# *********************************************
# Publishing
# *********************************************

def transferFilesToPublish():
    #print("0")
    publishing = Publishing()

    # each retreat is mirrored, for some subdirs also paying attention to file extensions
    #print("1")
    publishing.mirrorRetreatFiles()

    #print("2")
    publishing.mirrorIndex()
    publishing.mirrorHelp()

    #print("3")
    publishing.copyFile("Rob Burbea/Retreats.md", "/")
    publishing.copyFile("Rob Burbea/Index.md", "/")
    publishing.copyFile("Brainstorming/NoteStar.md", "/")
    publishing.copyFile("Rob Burbea/Gardening.md", "/")
    publishing.copyFile("Rob Burbea/Diacritics.md", "/")
    publishing.copyFile("Rob Burbea/Rob Burbea.md", "/")

    publishing.copyFile("Images/Digital Garden/digital-garden-big.png", "Images")
    publishing.copyFile("Images/Digital Garden/digital-garden-small.png", "Images")
    publishing.copyFile("Images/Digital Garden/Rob Burbea.png", "Images")
    publishing.copyFile("Images/Digital Garden/link.png", "Images")

    publishing.copyFile("Images/Digital Garden/help1.png", "Images")
    publishing.copyFile("Images/Digital Garden/help2.png", "Images")
    publishing.copyFile("Images/Digital Garden/help3.png", "Images")
    publishing.copyFile("Images/Digital Garden/help4.png", "Images")

    modifyFullstops()

    # we do not touch publish.css
    #print("4")
    # now all files are exact copies of the _Markdown vault
    # need to convert audio links and admonitions
    publishing.convertAllMarkdownFiles()
    #print("5")


def convertAllMarkdownFiles():
    # standalone conversion for summary files
    publishing = Publishing()
    publishing.convertAllMarkdownFiles()


def modifyFullstops():
    summaryFilenames = haf.collectSummaryFilenames()
    for summaryFilename in summaryFilenames:
        summary = TranscriptSummaryPage(summaryFilename)
        headerTargets = summary.collectParagraphHeaderTargets()
        talkname = talknameFromFilename(summaryFilename)

        # intentionally from the publish 
        transcriptFilename = haf_publish.getTranscriptFilename(talkname)
        assert transcriptFilename

        transcript = TranscriptPage(transcriptFilename)
        for markdownLine in transcript.markdownLines: # type: MarkdownLine
            blockid = markdownLine.getBlockId()
            if not blockid:
                # transcript has not only paragraphs
                pass
            else:
                if markdownLine.text.startswith('#'):
                    # make sure we don't accidently capture the header (which also has the block id, excluding leading ^, though)
                    pass
                else:
                    if blockid not in headerTargets:
                        # we might have left out this particular paragraph from the summary
                        pass
                    else:
                        headerTarget = headerTargets[blockid]
                        if not headerTarget:
                            # probably ... (yet-missing paragraph description)
                            pass
                        else:
                            match = re.match(r'(.+)([.?!"]) \^' + blockid + "$", markdownLine.text)
                            if match:
                                linkToSummary = f"[[{talkname}#{headerTarget}|{match.group(2)}]]"  # ∘∙⦿꘎᙮
                                markdownLine.text = f"{match.group(1)}{linkToSummary} ^{blockid}"
        transcript.save(transcriptFilename)


def addAudioLinksToSummaryWithDecoratedTranscript(path):
    summary = TranscriptSummaryPage(path)
    talkname = talknameFromFilename(path)
    transcriptFilename = haf.getTranscriptFilename(talkname)
    transcript = TranscriptPage(transcriptFilename)

    summaryLineParser = SummaryLineParser()

    index = 0
    timestampTranscript = None
    audioDate = audioMiddle = audioId = None
    foundFirstAudio = False
    changed = False
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

        if summaryLineParser.match(ml) == SummaryLineMatch.PARAGRAPH_COUNTS:
            # pull the timestamp from the beginning of the transcript paragraph
            mlTranscript = transcript.findParagraph(summaryLineParser.pageNr, summaryLineParser.paragraphNr)
            assert mlTranscript
            match = re.match(r"\[(?P<timestamp>[0-9:]+) *\]", mlTranscript.text)
            timestampTranscript = match.group('timestamp') if match else None
            if match:
                (_, end) = match.span()
                mlTranscript.text = mlTranscript.text[end+1:]
                changed = True

        index += 1

    if changed:
        summary.save()
        transcript.save()


# *********************************************
# main
# *********************************************

def get_arguments():
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('--script')
    parser.add_argument('--retreatName')
    parser.add_argument('--talkName')
    parser.add_argument('--indexEntry')
    parser.add_argument('--out')
    parser.add_argument('--old')
    parser.add_argument('--new')
    parser.add_argument('--level')
    parser.add_argument('--scripts', action="store_true")

    # sortRBYaml
    parser.add_argument("--sectionsort", action='store_true')

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
        lines = loadLinesFromTextFile("HAFScripts.py")
        lastcomment = ''
        first = True
        for line in lines:
            match = re.match(r"    # (.+)", line)
            if match:
                lastcomment = match.group(1)
            match = re.match(r"    elif script == '(.+)'", line)
            if match:
                if lastcomment != '':
                    print(('' if first else '\n') + '# ' + lastcomment)
                    lastcomment = ''
                    first = False
                script = match.group(1)
                print('  ' + script)
        exit()


    haf = HAFEnvironment(HAF_YAML)

    haf_publish = HAFEnvironment(HAF_PUBLISH_YAML)

    #retreatName = args.retreatName if args.retreatName else '2007 Lovingkindness and Compassion As a Path to Awakening'
    #talkName = args.talkName if args.talkName else 'From Insight to Love'
    #indexEntry = args.indexEntry if args.indexEntry else 'Energy Body'

    retreatName = args.retreatName
    talkname = args.talkName
    indexEntry = args.indexEntry
    level = args.level

    script = args.script

    transcriptIndex = TranscriptIndex(RB_YAML)

    if isScript(['reindexTranscripts', 'updateSummary', 'addMissingCitations', 'transferFilesToPublish']):
        transcriptModel = TranscriptModel(transcriptIndex)

    if isScript(['createIndexEntryFiles', 'showOrphansInIndexFolder', 'showOrphansInRBYaml', 'replaceNoteLink']):
        network = LinkNetwork(haf)


    # publish

    if isScript('transferFilesToPublish'):
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
        transferFilesToPublish()
        replaceLinksInAllSummaries()
        replaceLinksInAllRootFilenames()
        replaceLinksInSpecialFiles()
        print("files transferred to publish vault")


    # Kanban stuff

    elif isScript('addMissingSummaryCards'):
        assert retreatName
        sfnKanban = haf.vault.findFile('Talk summaries (Kanban).md')
        addMissingTranscriptParagraphHeaderTextCardsForSummariesInRetreat(sfnKanban, haf, retreatName)
        print('done')


    # reindexing, updating

    elif isScript('reindexTranscripts'):
        if retreatName:
            applySpacyToTranscriptParagraphsForRetreat(haf, retreatName, transcriptModel)
        else:
            for retreatName in haf.retreatNames:
                applySpacyToTranscriptParagraphsForRetreat(haf, retreatName, transcriptModel)
        print("reindexed")

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


    # index stuff

    elif isScript('addMissingCitations'):
        assert indexEntry
        addMissingCitations(haf, indexEntry, transcriptIndex, transcriptModel)
        print(f"added citations to '{indexEntry}'")

    elif isScript('updateAlphabeticalIndex'):
        updateAlphabeticalIndex(haf, transcriptIndex)
        print("updated")

    elif isScript('sortRBYaml'):
        sortRBYaml(transcriptIndex, args)
        print("sorted and saved")

    elif isScript('createIndexEntryFiles'):
        transcriptIndex.createObsidianIndexEntryFiles(haf.dirIndex)
    
    elif isScript('showOrphansInIndexFolder'):
        showOrphansInIndexFolder(haf, network, transcriptIndex, haf.dirIndex)
        print("copied to clipboard")

    elif isScript('showOrphansInRBYaml'):
        showOrphansInRBYaml(haf, network, transcriptIndex, haf.dirIndex)
        print("copied to clipboard")

    elif isScript('replaceNoteLink'): 
        # needs args "old", "new"
        (found, changed, unchanged) = replaceNoteLink(haf, network, args)
        if not found:
            print('not found')
        else:
            print(f"found {found}, {changed} changed, {unchanged} unchanged")


    # conversion helpers

    elif isScript('convertAllMarkdownFiles'):
        convertAllMarkdownFiles()
        print("converted")

    elif isScript("canonicalize"):
        assert talkname
        canonicalizeTranscript(haf, talkname)
        print("canonicalized")

    elif isScript("deitalicizeTranscript"):
        assert talkname
        deitalicizeTranscript(haf, talkname)
        print("deitalizised")


    # temporary stuff

    elif isScript('showH'):
        assert level
        
        filenames = filterExt(haf.allFiles(), '.md')
        filenames = [filename for filename in filenames if not re.search(r'Amazon Kindle|\(Kanban\)', filename)]
        for filename in filenames:
            found = False            
            for line in (lines := loadLinesFromTextFile(filename)):
                if re.match(r"^" + '#'*int(level) + ' ', line):
                    if not found:
                        print(filename)
                        found = True
                    print(line)

    elif isScript('addH'):
        
        for filename in (transcriptFilenames := haf.collectTranscriptFilenames()):
            for index, line in enumerate(lines := loadLinesFromTextFile(filename)):
                if (match := re.search(r" \^(?P<blockid>[0-9]+-[0-9]+)$", line)):
                    blockid = match.group('blockid')
                    lines[index-1] = '###### ' + blockid
            #sfnSave = os.path.join("tmp/h", os.path.basename(filename))
            sfnSave = filename
            saveLinesToTextFile(sfnSave, lines)

    # creating files

    elif isScript('convertPlainMarkdownToTranscript'):
        assert talkname
        convertPlainMarkdownToTranscript(haf, talkname)
        print("converted")

    elif isScript('firstIndexingOfRetreatFolder'):
        assert retreatName
        firstIndexingOfRetreatFolder(haf, retreatName)
        print("first reindexing done")

    elif isScript('createNewSummaries'):
        assert retreatName
        createNewTranscriptSummariesForRetreat(haf, retreatName)
        print("created")


    # modifiying summaries

    elif isScript('updateBreadcrumbs'):
        updateBreadcrumbsInSummaries()
        print("updated")

    elif isScript('collectParagraphs'):
        assert talkname
        collectParagraphsListPageToClipboard(talkname)

    elif isScript('updateParagraphsLists'):
        updateParagraphsListPages(haf)


    # journal

    elif isScript('changeJournalBreadcrumbsStyle'):
        for sfn in haf.vault.folderFiles("Journal", "md"):
            lines = loadLinesFromTextFile(sfn)
            for index, line in enumerate(lines):
                match = re.match(r"<< \[\[(?P<prevdate>.+)\|(?P<prevday>.+)\]\] \| \[\[(?P<nextdate>.+)\|(?P<nextday>.+)\]\]", line)
                if match:
                    prevdate = match.group('prevdate')
                    prevday = match.group('prevday')
                    nextdate = match.group('nextdate')
                    nextday = match.group('nextday')
                    newline = f"[[{prevdate}|{prevday} 🡄]] | [[{nextdate}|🡆 {nextday}]]"
                    lines[index] = newline
            saveLinesToTextFile(sfn, lines)

    elif isScript('modifyFullstops'):
        modifyFullstops()
        print("fullstops replaced")


    elif isScript('addAudioLinks'):
        assert talkname
        path = haf.getSummaryFilename(talkname)
        addAudioLinksToSummaryWithDecoratedTranscript(path)


    else:
        print("unknown script")


    