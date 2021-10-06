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
from HAFEnvironment import HAFEnvironment


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


    # top 10 backlinks

    elif isScript('top10FirstTryWithLinkNetwork'):

        # PROBLEM: LinkNetwork doesn't know how often a transcript refers to an index entry
        # without applying spacy, this info is only available via the summaries
        # so a better way is to create the IndexEntryNetwork from the available summaries, checking for the count lines and parsing them

        network = LinkNetwork(haf)
        indexEntry = 'Vessel'
        linkingNotes = network.collectReferencedNoteMatches(indexEntry)

        # summaries are duplicate all links we have, so ignore them
        # also ignore self-links 
        summaries = haf.collectSummaryNameSet()
        linkingNotes = [(note, x) for (note,x) in linkingNotes if note.lower() != indexEntry.lower() and not note in summaries]

        # https://stackoverflow.com/questions/45476509/group-list-of-tuples-efficiently/45476721
        from itertools import groupby
        from operator import itemgetter
        b = [(k, [x for _, x in g]) for k, g in groupby(linkingNotes, itemgetter(0))]

        for (referrer, matches) in b:
            markdown = network.getMarkdownByNote(referrer)
            for match in matches:
                visible = shown if (shown := match.group('shown')) else match.group('note')
                print(referrer, visible)


    elif isScript('top10'):
        # dict[term, list[Tuple[transcript name, count]]]
        dict = {} # type: dict[str,list[Tuple[str,int]]]

        for fnTranscript in haf.collectTranscriptFilenames():
            transcript = TranscriptPage(fnTranscript)
            transcriptName = transcript.filename
            transcript.applySpacy(transcriptModel)
            allTermCounts = transcript.collectAllTermCounts()
            for (term, count) in allTermCounts.items():
                if term in dict:
                    counts = dict[term]
                else:
                    counts = []
                    dict[term] = counts
                counts.append((transcriptName, count))
        
        top10Header = "Top 10 referring transcripts"
        yamlValue = 'showTop10ReferringTranscripts'

        terms = [term for term in sorted(list(haf.collectIndexEntryNameSet())) if term in dict]
        for term in terms:            
            indexEntry = IndexEntryPage(haf.getIndexEntryFilename(term))            
            if (showTop10ReferringTranscripts := value if ((value := indexEntry.getYamlValue(yamlValue)) is not None) else True):
                tuples = sorted(dict[term], key=lambda x: x[1], reverse=True)
                # func = lambda note, count: f"[[{note}]] ({count})"
                # links = [func(note, count) for (note, count) in tuples]                    
                links = [f"[[{note}]] ({count})" for (note, count) in tuples]                    
                top10Links = links[:10]

                # create the complete backlink section
                section = []
                section.append('### ' + top10Header)
                section.extend(top10Links)
                section.append("")

                (start, end) = indexEntry.markdownLines.searchSpan(r"^#+ " + top10Header, r"^#+")
                if start:
                    # there is already a backlink section - - delete it
                    indexEntry.markdownLines.delete(start, end)
                    insert = start
                else:
                    section.insert(0, "")
                    insert = len(indexEntry.markdownLines)

                # insert or append the section
                indexEntry.markdownLines.insert(insert, section)

                indexEntry.save()


    # misc


    else:
        print("unknown script")


    