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


    # top backlinks

    elif isScript('topTalks'):
        nTopDefault = 10

        from collections import defaultdict
        paragraphs = SummaryParagraphs(haf)

        # ((ZAIVSGG))
        dict = paragraphs.createOccurrencesByTermDict() # type: dict[str,list[ParagraphTuple]]
        
        yamlKey = 'showTopReferringTalks'

        # vertical span for the section
        # markdown lines in the section will be replaced (with bigger or smaller number or rows
        # see ((UVLQMRI)) below
        patternStart = r"^#+ Top ([0-9]+) referring talks"
        patternEnd = r"^#+"
        
        # occurrences ((ZAIVSGG)) neither have retreats nor dates
        retreatByTalkname = haf.createRetreatByTalknameLookup()
        dateByTalkname = haf.createDateByTalknameLookup()

        for term in list(haf.collectIndexEntryNameSet()):
            indexEntry = IndexEntryPage(haf.getIndexEntryFilename(term))

            showTopReferringTalks = value if ((value := indexEntry.getYamlValue(yamlKey)) is not None) else True
            if showTopReferringTalks:
                # create the complete backlink section
                section = []

                # ((UVLQMRI)) try to find the span of the top-mentions-section
                (start, end) = indexEntry.markdownLines.searchSpan(patternStart, patternEnd)
                if start:
                    # found it
                    match = re.match(patternStart, indexEntry.markdownLines[start].text)
                    nTop = int(match.group(1))

                    # there is already a backlink section - - delete it
                    indexEntry.markdownLines.delete(start, end)
                    insert = start
                else:
                    # no section yet                    
                    nTop = nTopDefault

                    # will be added at the end, not just replaced -> have an empty line before the new last section of the page
                    section.append("")
                    insert = len(indexEntry.markdownLines)

                # Obsidian table
                section.append(f"### Top {nTop} referring talks")
                section.append("talk | count | series | date")
                section.append(":- | - |: - | -")

                # get all occurrences for the term
                # those are paragraphs, i.e. multiple mentions for a talk            
                tuples = dict[term] # type: list[ParagraphTuple]

                # sum the multiple mentions for each talk
                dictCounts = defaultdict(int) # dict[summaryName, count]
                for pt in tuples:
                    dictCounts[pt.summaryName] += pt.count

                # top mentions is sorted descending
                topMentions = sorted(dictCounts.items(), key=lambda x: x[1], reverse=True)[:nTop]

                # create table rows
                for (talkname, count) in topMentions:
                    retreatName = retreatByTalkname[talkname]                    
                    date = dateByTalkname[talkname]
                    section.append(f"[[{talkname}]] | {count} | [[{retreatName}]] | {date}")

                # empty line ends the section
                section.append("")

                # insert or append the section
                indexEntry.markdownLines.insert(insert, section)

                indexEntry.save()

        print("done")


    else:
        print("unknown script")


    