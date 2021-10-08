#!/usr/bin/env python3

import re
import os

from LinkNetwork import LinkNetwork
from TranscriptPage import TranscriptPage
from TranscriptModel import TranscriptModel
from shutil import copyfile
from consts import HAF_YAML, RB_YAML
from TranscriptIndex import TranscriptIndex
from TranscriptPage import createTranscriptsDictionary
from IndexEntryPage import IndexEntryPage
from util import *
from HAFEnvironment import HAFEnvironment, determineTalkname, talknameFromFilename
from SummaryParagraph import SummaryParagraph, SummaryParagraphs, ParagraphTuple
from collections import defaultdict


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


# *********************************************
# top referrers section builder
# *********************************************

def changeTopReferrersSection(patternStart, yamlKey, func, nTopDefault):
    paragraphs = SummaryParagraphs(haf)
    dict = paragraphs.createOccurrencesByTermDict() # type: dict[str,list[ParagraphTuple]]

    # vertical span for the section
    # markdown lines in the section will be replaced (with bigger or smaller number or rows
    # see ((UVLQMRI)) below
    patternEnd = r"^#+"

    for term in list(haf.collectIndexEntryNameSet()):
        indexEntry = IndexEntryPage(haf.getIndexEntryFilename(term))

        # create the complete backlink section
        section = []

        # index entry page can change either by deletion only (if the yaml flag was set to False) or w/ a replaced section
        changed = False

        # ((UVLQMRI)) try to find the span of the top-mentions-section
        (start, end) = indexEntry.markdownLines.searchSpan(patternStart, patternEnd)
        if start:
            # found it
            match = re.match(patternStart, indexEntry.markdownLines[start].text)
            nTop = int(match.group(1))

            # there is already a backlink section - - delete it
            indexEntry.markdownLines.delete(start, end)
            insert = start

            # we deleted something, which has to be reflected by saving
            changed = True
        else:
            # no section yet                    
            nTop = nTopDefault

            # will be added at the end, not just replaced -> have an empty line before the new last section of the page
            section.append("")
            insert = len(indexEntry.markdownLines)

        showTop = value if ((value := indexEntry.getYamlValue(yamlKey)) is not None) else True
        if showTop:

            # now we definitely now that we have changed
            changed = True

            # get all occurrences for the term
            # those are paragraphs, i.e. multiple mentions for a talk            
            occurrences = dict[term] # type: list[ParagraphTuple]

            func(occurrences, section, nTop)

            # empty line ends the section
            section.append("")

            # insert or append the section
            indexEntry.markdownLines.insert(insert, section)

        if changed:
            indexEntry.save()


# *********************************************
# main
# *********************************************

def get_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--script')
    parser.add_argument('--indexEntry')
    parser.add_argument('--scripts', action="store_true")
    parser.add_argument("--sectionsort", action='store_true')
    return parser.parse_args()

if __name__ == "__main__":
    args = get_arguments()
    if args.scripts:
        dumpScripts(__file__)
        exit()

    def isScript(check):
        return isScriptArg(args, check)

    haf = HAFEnvironment(HAF_YAML)

    script = args.script
    indexEntry = args.indexEntry

    transcriptIndex = TranscriptIndex(RB_YAML)
    if isScript(['addMissingCitations', 'top10']):
        transcriptModel = TranscriptModel(transcriptIndex)
    if isScript(['createIndexEntryFiles', 'showOrphansInIndexFolder', 'showOrphansInRBYaml']):
        network = LinkNetwork(haf)

    if False:
        pass


    # index stuff

    elif isScript('addMissingCitations'):
        assert indexEntry
        addMissingCitations(haf, indexEntry, transcriptModel)
        print(f"added citations to '{indexEntry}'")

    elif isScript('updateAlphabeticalIndex'):
        updateAlphabeticalIndex(haf, transcriptIndex)
        print("updated")


    # RB.yaml

    elif isScript('sortRBYaml'):
        sortRBYaml(transcriptIndex, args)
        print("sorted and saved")

    elif isScript('createIndexEntryFiles'):
        transcriptIndex.createObsidianIndexEntryFiles(haf.dirIndex)
        updateAlphabeticalIndex(haf, transcriptIndex)
    
    elif isScript('showOrphansInIndexFolder'):
        showOrphansInIndexFolder(haf, network, transcriptIndex, haf.dirIndex)
        print("copied to clipboard")

    elif isScript('showOrphansInRBYaml'):
        showOrphansInRBYaml(haf, network, transcriptIndex, haf.dirIndex)
        print("copied to clipboard")


    elif isScript('topParagraphs'):
        nTopDefault = 3

        # we need to access previous and next paragraphs of the ones shown in the rows
        # see ((KJQBZMS)) below
        talknames = [basenameWithoutExt(fn) for fn in haf.collectSummaryFilenames()]
        transcriptByTalkname = {talkname: TranscriptPage(haf.getTranscriptFilename(talkname)) for talkname in talknames}

        dateByTalkname = haf.createDateByTalknameLookup()

        def func(occurrences, section, nTop):
            # Obsidian table
            section.append(f"### Paragraphs with {nTop}+ mentions")
            section.append("description | count | talk")
            section.append(":- | : - | :-")

            # prune if necessary
            if len(occurrences) > 10:
                occurrences = [o for o in occurrences if o.count >= nTop]

            # build a list with the necessary fields for sorting and display
            topMentions = []
            for o in occurrences:
                date = dateByTalkname[o.summaryName]
                topMentions.append( (o.summaryName, o.headerText, o.blockid, o.count, date))

            # sort by dates, descending
            # NOTE: date is not displayed
            topMentions = sorted(topMentions, key=lambda x: x[4], reverse=True)

            # main sort by count, descending
            topMentions = sorted(topMentions, key=lambda x: x[3], reverse=True)

            for (talkname, headerText, blockid, count, date) in topMentions:
                if headerText != '...':
                    (pageNr, paragraphNr) = parseBlockId(blockid)

                    # ((KJQBZMS)) get the transcript w/o going via the filesystem
                    transcript = transcriptByTalkname[talkname]
                    thisParagraph = f"[[{transcript.notename}#^{blockid}\\|.]]"

                    # determine previous and next paragraphs, if there are any
                    (prevPageNr, prevParagraphNr) = transcript.prevParagraph(pageNr, paragraphNr)
                    (nextPageNr, nextParagraphNr) = transcript.nextParagraph(pageNr, paragraphNr)
                    prevParagraph = '' if prevPageNr == None else f"[[{transcript.notename}#^{prevPageNr}-{prevParagraphNr}\|.]]"
                    nextParagraph = '' if nextPageNr == None else f"[[{transcript.notename}#^{nextPageNr}-{nextParagraphNr}\|.]]"

                    # 3 dots (or 2, if first or last paragraph), with the actual one in the list in bold
                    paragraphLink = f"[[{talkname}#{determineHeaderTarget(headerText)}\\|{headerText}]] &nbsp;&nbsp;{prevParagraph} &nbsp; **{thisParagraph}** &nbsp; {nextParagraph}"

                    section.append( f"{paragraphLink} | {count} | [[{talkname}]]" )

        # now delete, add or replace the section
        yamlKey = 'showTopReferringParagraphs'
        patternStart = r"^#+ Paragraphs with ([0-9]+)\+ mentions"
        changeTopReferrersSection(patternStart, yamlKey, func, nTopDefault)

        print("done")


    elif isScript('topTalks'):
        nTopDefault = 10

        # occurrences neither have retreats nor dates
        retreatByTalkname = haf.createRetreatByTalknameLookup()
        dateByTalkname = haf.createDateByTalknameLookup()

        def func(occurrences, section, nTop):
            # Obsidian table
            section.append(f"### Top {nTop} referring talks")
            section.append("talk | count | series")
            section.append(":- | - |: -")

            # sum the multiple mentions for each talk
            dictCounts = defaultdict(int) # dict[summaryName, count]
            for pt in occurrences:
                dictCounts[pt.summaryName] += pt.count

            # just use the top occurrences
            dictCountsItems = sorted(dictCounts.items(), key=lambda x: x[1], reverse=True)[:nTop]

            # build a list with the necessary fields for sorting and display
            topMentions = [(talkname, count, retreatByTalkname[talkname], dateByTalkname[talkname]) for (talkname, count) in dictCountsItems]

            # sort by dates, descending
            # NOTE: date is not displayed
            topMentions = sorted(topMentions, key=lambda x: x[3], reverse=True)

            # main sort by count, descending
            topMentions = sorted(topMentions, key=lambda x: x[1], reverse=True)

            for (talkname, count, retreatName, date) in topMentions:
                section.append(f"[[{talkname}]] | {count} | [[{retreatName}]]")

        # now delete, add or replace the section
        yamlKey = 'showTopReferringTalks'
        patternStart = r"^#+ Top ([0-9]+) referring talks"
        changeTopReferrersSection(patternStart, yamlKey, func, nTopDefault)

        print("done")

    else:
        print("unknown script")


    