#!/usr/bin/env python3

from itertools import count
import re
import os
import time

from operator import itemgetter
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
from TalkParagraph import TalkParagraph, TalkParagraphs, ParagraphTuple
from collections import defaultdict, namedtuple
from TalkPage import TalkPage
from TalkSection import TalkSection, Admonition


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

def replaceIndexEntryPageSection(tuplesByTerm, patternStart, yamlKey, indexEntryPageHandler, nTopDefault=None):

    # vertical span for the section
    # markdown lines in the section will be replaced (with bigger or smaller number or rows
    # see ((UVLQMRI)) below
    patternEnd = r"^### "

    saves = 0

    terms = list(haf.collectIndexEntryNameSet())
    for term in terms:
        pIndexEntry = haf.getIndexEntryFilename(term)
        indexEntry = IndexEntryPage(pIndexEntry)

        # create the complete backlink section
        sectionLines = []

        # index entry page can change either by deletion only (if the yaml flag was set to False) or w/ a replaced section
        changed = False

        # ((UVLQMRI)) try to find the span of the top-mentions-section
        (start, end) = indexEntry.markdownLines.searchSpan(patternStart, patternEnd)
        if start:
            # found it
            match = re.match(patternStart, indexEntry.markdownLines[start].text)
            nTop = int(match.group(1)) if match.groups() else None

            # there is already a backlink section - - delete it
            indexEntry.markdownLines.delete(start, end)
            insert = start

            # we deleted something, which has to be reflected by saving
            changed = True
        else:
            # no section yet                    
            nTop = nTopDefault

            # will be added at the end, not just replaced -> have an empty line before the new last section of the page
            # 24.10.21 suspicion: doesn't need the empty line
            # section.append("")
            insert = len(indexEntry.markdownLines)

        showTop = value if ((value := indexEntry.getYamlValue(yamlKey)) is not None) else True
        if showTop:

            # get all occurrences for the term
            # those are paragraphs, i.e. multiple mentions for a talk
            if term in tuplesByTerm:
                # now we definitely know that we have changed
                changed = True

                tuples = tuplesByTerm[term] # type: list[ParagraphTuple]
                indexEntryPageHandler(term, tuples, sectionLines, nTop)

                # empty line ends the section
                sectionLines.append("")

                # insert or append the section
                indexEntry.markdownLines.insert(insert, sectionLines)

        if changed:
            indexEntry.save()
            saves += 1

    print(f"saved {saves} of {len(terms)} index entries")


# *********************************************
# top referrers section builder
# *********************************************

# Tuple[TalkPage, TalkSection, str, str, str]
AdmonitionInfo = namedtuple('AdmonitionInfo', 'talkPage talkSection admonitionType, admonitionTitle, admonitionBody')

def buildAdmonitionInfosByTermForTalk(pTalkPage, spellingAlternativesByTerm: dict[str,list[str]], filterAdmonition=None) -> dict[str,list[AdmonitionInfo]]:
    # filter(section, admonitionType, admonitionTitle)

    # on demand, we can look at a page with a focus on the paragraph infos, "sections"
    talk = TalkPage(pTalkPage)
    sections = talk.collectSections()
    admonitionTuplesByTerm = defaultdict(list[AdmonitionInfo])
    for section in sections:

        # use section semantics to extract summary, counts, audio (?), admonitions
        section.parse()
        if not section.counts:
            # there might be quotes, but we can't associate a particular term with it
            pass
        else:
            for admonition in section.admonitions:
                (start, end, admonitionType, admonitionTitle) = admonition
                if (filterAdmonition is None) or filterAdmonition(section, admonition.type, admonition.title):

                    # can be relaxed later, right now we're working on auto quotes
                    assert admonition.type.lower() == 'quote'

                    # provided tuple only has the span, not the body
                    admonitionBody = "\n".join([ml.text for ml in section.markdownLines[admonition.start+1:admonition.end-1]])

                    # admonitionBody stays raw, i.e. w/o changing e.g. the first letter (which could be part of a term)
                    # quotes shown are canonical, i.e. leading [.] and trailing ...
                    admonitionTuple = AdmonitionInfo(talk, section, admonition.type, admonition.title, canonicalQuoteText(admonitionBody))

                    # case-insensitive
                    admonitionBody = admonitionBody.lower()

                    # we take the information in the counts line to be up-to-date
                    for term in section.counts.keys():
                        for spellingAlternative in spellingAlternativesByTerm[term]:
                            if spellingAlternative in admonitionBody:
                                # at least one of the spellings of the term found in the quote
                                admonitionTuplesByTerm[term].append(admonitionTuple)
                                break
    return admonitionTuplesByTerm


def collectQuoteSectionLinesForTerm(tuplesForTerm, retreatByTalkname, createTable):
    sectionLines = []

    def outputQuoteRow(tuple: AdmonitionInfo):
        (talk, section, admonitionType, admonitionTitle, admonitionBody) = tuple
        blockid = f"{section.pageNr}-{section.paragraphNr}"
        headerText = section.headerText
        headerTarget = determineHeaderTarget(headerText)
        safeAdmonitionBody = admonitionBody.replace('|', '\|')
        sectionLines.append(f"[[{talk.notename}]] | [[{talk.notename}#{headerTarget}\|{headerText}]] | {safeAdmonitionBody}")
        #notename = talk.notename
        #if len(notename)<30: notename += "&nbsp;"*5
        #sectionLines.append(f"{safeAdmonitionBody} | [[{notename}]] | [[{talk.notename}#{headerTarget}\|{headerText}]]")

    lastTalk = None
    def outputQuote(tuple: AdmonitionInfo):
        (talk, section, admonitionType, admonitionTitle, admonitionBody) = tuple
        nonlocal lastTalk
        if talk != lastTalk:
            sectionLines.append(f"**[[{talk.notename}]]**")
            retreatName = retreatByTalkname[talk.notename]
            sectionLines.append(f'<span class="counts">[[{retreatName}]]</span>')
            lastTalk = talk
        headerText = section.headerText
        headerTarget = determineHeaderTarget(headerText)
        sectionLines.append(f'> {admonitionBody} &nbsp;&nbsp;<span class="counts">_[[{talk.notename}#{headerTarget}|{headerText}]]_</span>')
        sectionLines.append("")

    # we currently don't use a table, but we could
    assert not createTable
    if createTable:
        sectionLines.append("talk | paragraph | quote")
        sectionLines.append("- | - | -")

    #lg = mergedAdmonitionTuplesByTerm[term]
    for quote in tuplesForTerm:
        if createTable:
            outputQuoteRow(quote)
        else:
            outputQuote(quote)
    
    return sectionLines


def replaceQuoteSections(haf, transcriptIndex):
    filenames = [fnTalk for p in haf.collectTranscriptFilenames() if (fnTalk := haf.getTalkFilename(basenameWithoutExt(p))) is not None]

    # we do a quick check if any of the potential spellings of a term occurs in a quote body
    spellingAlternativesByTerm = defaultdict(list)
    for spellingAlternativeLC, term  in transcriptIndex.patternLinks.items():
        spellingAlternativesByTerm[term].append(spellingAlternativeLC)
    
    # build master lookup for all quotes by term
    admonitionInfosByTerm = defaultdict(list)
    for pTalk in filenames:
        # dict[term, list[AdmonitionInfo]]
        admonitionInfosByTermForTalk = buildAdmonitionInfosByTermForTalk(
            pTalk, 
            spellingAlternativesByTerm, 
            filterAdmonition=lambda section, type, title: type == 'quote')
        
        for term, admonitionInfo in admonitionInfosByTermForTalk.items():
            admonitionInfosByTerm[term].extend(admonitionInfo)

    patternStart = r"^### Quotes$"
    yamlKey = 'showQuotes'

    # DANGER: we need to do this, because live lookup via filesystem globs is *slow*
    retreatByTalkname = haf.createRetreatByTalknameLookup()

    # called from main via changeTopReferrersSection
    def __indexEntryPageHandler(term, tuplesForTerm, sectionLines, nTop):
        sectionLines.append(f"### Quotes")
        sectionLinesForTerm = collectQuoteSectionLinesForTerm(tuplesForTerm, retreatByTalkname, createTable=False)
        sectionLines.extend(sectionLinesForTerm)

    # main
    tic = time.perf_counter()
    replaceIndexEntryPageSection(admonitionInfosByTerm, patternStart, yamlKey, __indexEntryPageHandler)
    toc = time.perf_counter()
    print(f"in  {toc-tic:0.4}s")


# *********************************************
# main
# *********************************************

def get_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('script', nargs='?')
    parser.add_argument('-help', dest='scriptHelp', action='store_true')
    parser.add_argument('-i')
    parser.add_argument('-out')
    parser.add_argument("-sectionsort", action='store_true')
    return parser.parse_args()

if __name__ == "__main__":
    args = get_arguments()

    def isScript(check):
        return isScriptArg(args, check)

    haf = HAFEnvironment(HAF_YAML)

    script = args.script
    scriptHelp = args.scriptHelp
    indexEntry = args.i
    out = args.out

    if not scriptHelp:
        transcriptIndex = TranscriptIndex(RB_YAML)
        if isScript(['addMissingCitations', 'top10']):
            transcriptModel = TranscriptModel(transcriptIndex)
        if isScript(['createIndexEntryFiles', 'showOrphansInIndexFolder', 'showOrphansInRBYaml']):
            network = LinkNetwork(haf)

    if isScript('scripts'):
        dumpScripts(__file__)
        exit()


    # index stuff

    elif isScript('addMissingCitations'):
        if scriptHelp: exitHelp("-i\tindex entry (note name) where to add citations")
        assert indexEntry
        addMissingCitations(haf, indexEntry, transcriptModel)
        print(f"added citations to '{indexEntry}'")

    elif isScript('updateAlphabeticalIndex'):
        if scriptHelp: exitHelp("script takes no parameters")
        updateAlphabeticalIndex(haf, transcriptIndex)
        print("updated")


    # RB.yaml

    elif isScript('sortRBYaml'):
        if scriptHelp: exitHelp("script takes no parameters")
        sortRBYaml(transcriptIndex, args)
        print("sorted and saved")

    elif isScript('createIndexEntryFiles'):
        if scriptHelp: exitHelp("script takes no parameters")
        exclude = haf.collectTalknameSet()
        transcriptIndex.createObsidianIndexEntryFiles(haf.dirIndex, exclude)
        updateAlphabeticalIndex(haf, transcriptIndex)
    
    elif isScript('showOrphansInIndexFolder'):
        if scriptHelp: exitHelp("script takes no parameters\n\nresult copied to clipboard")
        showOrphansInIndexFolder(haf, network, transcriptIndex, haf.dirIndex)
        print("copied to clipboard")

    elif isScript('showOrphansInRBYaml'):
        if scriptHelp: exitHelp("script takes no parameters\n\nresult copied to clipboard")
        showOrphansInRBYaml(haf, network, transcriptIndex, haf.dirIndex)
        print("copied to clipboard")


    elif isScript('topParagraphs'):
        if scriptHelp: exitHelp("script takes no parameters")
        print("topParagraphs")
        nTopDefault = 4

        # we need to access previous and next paragraphs of the ones shown in the rows
        # see ((KJQBZMS)) below
        talknames = [basenameWithoutExt(fn) for fn in haf.collectTalkFilenames()]
        transcriptByTalkname = {talkname: TranscriptPage(haf.getTranscriptFilename(talkname)) for talkname in talknames}

        dateByTalkname = haf.createDateByTalknameLookup()

        def func(term, occurrences, section, nTop):
            # we don't even send the paragraphs which do not have a description yet
            occurrences = [o for o in occurrences if o.headerText != '...']

            # prune if necessary
            if len(occurrences) > 10:
                prunedOccurrences = [o for o in occurrences if o.count >= nTop]
                if prunedOccurrences and len(prunedOccurrences) > 10:
                    occurrences = prunedOccurrences
                else:
                    occurrences = occurrences[:10]

            # build a list with the necessary fields for sorting and display
            topMentions = []
            for o in occurrences:
                date = dateByTalkname[o.talkname]
                topMentions.append( (o.talkname, o.headerText, o.blockid, o.count, date))

            # sort by dates, descending
            # NOTE: date is not displayed
            topMentions = sorted(topMentions, key=lambda x: x[4], reverse=True)

            # main sort by count, descending
            topMentions = sorted(topMentions, key=lambda x: x[3], reverse=True)

            # Obsidian table
            section.append(f"### Paragraphs with {nTop}+ mentions")
            section.append("description | count | talk")
            section.append(":- | : - | :-")
            for (talkname, headerText, blockid, count, date) in topMentions:
                # enforced by caller
                assert headerText != '...'
                paragraphLink = f"[[{talkname}#{determineHeaderTarget(headerText)}\\|{headerText}]]"
                section.append( f"{paragraphLink} | {count} | [[{talkname}]]" )
            return True

        # now delete, add or replace the section
        yamlKey = 'showTopReferringParagraphs'
        patternStart = r"^#+ Paragraphs with ([0-9]+)\+ mentions"
        paragraphs = TalkParagraphs(haf)
        dict = paragraphs.createOccurrencesByTermDict() # type: dict[str,list[ParagraphTuple]]
        replaceIndexEntryPageSection(dict, patternStart, yamlKey, func, nTopDefault)


    elif isScript('topTalks'):
        if scriptHelp: exitHelp("script takes no parameters")
        print("topTalks")
        nTopDefault = 10

        # occurrences neither have retreats nor dates
        retreatByTalkname = haf.createRetreatByTalknameLookup()
        dateByTalkname = haf.createDateByTalknameLookup()

        def func(term, occurrences, section, nTop):
            # sum the multiple mentions for each talk
            dictCounts = defaultdict(int) # dict[talkname, count]
            for pt in occurrences:
                dictCounts[pt.talkname] += pt.count

            # just use the top occurrences
            dictCountsItems = sorted(dictCounts.items(), key=lambda x: x[1], reverse=True)[:nTop]

            # build a list with the necessary fields for sorting and display
            topMentions = [(talkname, count, retreatByTalkname[talkname], dateByTalkname[talkname]) for (talkname, count) in dictCountsItems]

            # sort by dates, descending
            # NOTE: date is not displayed
            topMentions = sorted(topMentions, key=lambda x: x[3], reverse=True)

            # main sort by count, descending
            topMentions = sorted(topMentions, key=lambda x: x[1], reverse=True)

            # Obsidian table
            section.append(f"### Top {nTop} referring talks")
            section.append("talk | count | series")
            section.append(":- | - |: -")
            for (talkname, count, retreatName, date) in topMentions:
                section.append(f"[[{talkname}]] | {count} | [[{retreatName}]]")

        # now delete, add or replace the section
        yamlKey = 'showTopReferringTalks'
        patternStart = r"^#+ Top ([0-9]+) referring talks"
        paragraphs = TalkParagraphs(haf)
        dict = paragraphs.createOccurrencesByTermDict() # type: dict[str,list[ParagraphTuple]]
        replaceIndexEntryPageSection(dict, patternStart, yamlKey, func, nTopDefault)


    elif isScript('topCooccurrences'):
        import collections
        import operator
        import time

        def func(term, occurrences, section, nTop):

            #dict2 = cooc['Love'] # type: dict[str,list[TalkParagraph]]

            # sort by name first, so that later outer sorts are inner-sorted by name
            l = sorted(occurrences.items(), key=itemgetter(0))

            # extend 2-tuple from the dict with how many co-occurrences we found
            l = [(term, len(paragraphs), paragraphs) for (term, paragraphs) in l]

            # outer sort: longest list of paragraphs first
            l = sorted(l, key=itemgetter(1), reverse=True)

            cooccurrenceCounts = []
            for (term, count, paragraphs) in l:
                # same talk can have multiple co-occurrences
                talknames = [paragraph.talkname for paragraph in paragraphs]

                # group by talknames, sorted descending by count, in the same counts alphabetically
                counter = collections.Counter(talknames)
                talknameCounts = [(talkname, count) for (talkname, count) in dict(counter).items()] 
                talknameCounts = sorted(talknameCounts, key=operator.itemgetter(0)) # inner
                talknameCounts = sorted(talknameCounts, key=operator.itemgetter(1), reverse=True) # outer
                cooccurrenceCounts.append((term, count, talknameCounts))

            minCount = nTop
            minLines = 10
            minTalkCount = 2
            minTalks = 4

            pruned = [t for t in cooccurrenceCounts if t[1] >= minCount]
            used = pruned if len(pruned) >= minLines else cooccurrenceCounts[:minLines]
            
            section.append(f"### Terms with {nTop}+ co-occurrences")
            section.append("term | count | talks")
            section.append("-|-|-")
            for (term, count, talknameCounts) in used:
                prunedTalknames = [(talkname, count) for (talkname, count) in talknameCounts if count >= minTalkCount]
                usedTalknames = prunedTalknames if len(prunedTalknames) >= minTalks else talknameCounts[:minTalks]
                l = [f"[[{talkname}]] ({count})" for (talkname, count) in usedTalknames]
                #s = '<br/>'.join(l)
                #s = ' · '.join(l)
                s = '<span class="counts">' + ' · '.join(l) + "</span>"                
                section.append(f"[[{term}]] | {count} | {s} ")

        paragraphs = TalkParagraphs(haf)
        cooc = paragraphs.collectCooccurringParagraphs()

        patternStart = r"^#+ Terms with ([0-9]+)\+ co-occurrences"
        yamlKey = 'showTopCooccurrences'
        nTopDefault = 20

        tic = time.perf_counter()
        replaceIndexEntryPageSection(cooc, patternStart, yamlKey, func, nTopDefault)
        toc = time.perf_counter()
        print(toc-tic)


    elif isScript('allQuotes'):
        replaceQuoteSections(haf, transcriptIndex)

    else:
        print("unknown script")

