#!/usr/bin/env python3

from MarkdownLine import MarkdownLine
from TranscriptModel import TranscriptModel
from genericpath import exists

from TranscriptIndex import TranscriptIndex
from TranscriptPage import TranscriptPage
import os
import re
from util import *


def canonicalHeaderLineFromParams0(level, headerText1, transcriptName, linkText, headerText2, trailingBlockId) -> str:
    if linkText:
        linkText += ' '
    return ("#"*level if level else "######") \
        + (" " + headerText1 if headerText1 else "") \
        + f" [[{transcriptName}|{linkText}(Transcript)]]" \
        + (" " + headerText2 if headerText2 else "") \
        + (f" ^{trailingBlockId}" if trailingBlockId else "")


def canonicalHeaderLineFromParams(level, headerText1, transcriptName, linkText, headerText2, trailingBlockId) -> str:
    return ("#"*level if level else "######") \
        + (" " + headerText1 if headerText1 else "") \
        + f" [[{transcriptName}|" \
        + (f"{linkText} " if linkText else "") + "(Transcript)]]" \
        + (" " + headerText2 if headerText2 else "") \
        + (f" ^{trailingBlockId}" if trailingBlockId else "")


# *********************************************
# class IndexEntryPageHeaderParser
# *********************************************

class IndexEntryPageHeaderParser:

    def __init__(self, headerLine = None) -> None:
        if headerLine:
            self.matchHeaderLine(headerLine)


    def matchHeaderLine(self, headerLine):
        self.headerLine = headerLine        
        self.level = self.headerText1 = self.transcriptName = self.linkText = self.headerText2 = self.trailingBlockId = None

        # ###### Vajra Music - Preliminaries - Part 1 [[0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1|(Transcript)]] 🟢 ^some-block-pointer
        # ###### Vajra Music - Preliminaries - Part 1 [[0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1|(Transcript)]] ^some-block-pointer
        # ###### [[0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1|Vajra Music: Prelims Part 1 (Transcript)]]
        pattern = r"(?P<level>#+ )(?P<headerText1>[^[]+)?\[\[(?P<transcriptName>[0-9]+ [^|]+)\|(?P<linkText>[^(]+)?\(Transcript\)]\](?P<headerText2>[^^]+)?(\^(?P<trailingBlockId>.+))?"
        match = re.match(pattern, headerLine)
        if not match:
            return False

        setMatchField(self, "level", match, lambda m: len(m.strip()))
        setMatchField(self, "transcriptName", match)
        setMatchField(self, "headerText1", match, lambda m: m.strip())
        setMatchField(self, "linkText", match, lambda m: m.strip())
        setMatchField(self, "headerText2", match, lambda m: m.strip())
        setMatchField(self, "trailingBlockId", match)

        return True


    def canonicalHeaderLine(self):
        return canonicalHeaderLineFromParams(self.level, self.headerText1, self.transcriptName, self.linkText, self.headerText2, self.trailingBlockId)


# *********************************************
# class CitationParagraphParser
# *********************************************

class CitationParagraphParser:

    def __init__(self, citationParagraph = None, targetType='#') -> None:
        if citationParagraph:
            self.matchCitationParagraph(citationParagraph, targetType)

    def matchCitationParagraph(self, citationParagraph, targetType='#') -> re.Match:
        self.citationParagraph = self.citation = self.sourceStart = self.markupLink = self.transcriptName = self.blockId = self.pageNr = self.paragraphNr = self.sourceEnd = self.linkTarget = None

        self.citationParagraph = citationParagraph

        linkPattern = r"(?P<markupLink>\[\[(?P<transcriptName>[^#[]+)#\^?(?P<blockId>(?P<pageNr>[0-9]+)-(?P<paragraphNr>[0-9]+))\|[0-9]+-[0-9]+\]\])"
        pattern = r"^> *(?P<citation>.+?)((?P<sourceStart>(<p/>)?[_(]+)(?P<sourceText>[^[]*))" + linkPattern + r"(?P<sourceEnd>[_)]+)$"
        match = re.match(pattern, citationParagraph)
        if match:

            self.citation = match.group('citation')
            self.sourceStart = match.group('sourceStart')
            self.sourceText = match.group('sourceText')
            self.markupLink = match.group('markupLink')
            self.transcriptName = match.group('transcriptName')
            self.blockId = match.group('blockId')
            self.pageNr = int(match.group('pageNr'))
            self.paragraphNr = int(match.group('paragraphNr'))
            self.sourceEnd = match.group('sourceEnd')

            self.linkTarget = f"{self.transcriptName}{targetType}{self.blockId}"

        return match


    def canonicalCitationParagraph(self) -> None:
        link = f"[[{self.linkTarget}|{self.blockId}]]"
        return "> " + self.citation + self.sourceStart + self.sourceText + link + self.sourceEnd


# *********************************************
# class IndexEntryPage
# *********************************************

class IndexEntryPage:
    def __init__(self, dirIndexEntries: str, indexEntry: str) -> None:
        self.dirIndexEntries = dirIndexEntries
        self.indexEntry = indexEntry
        self.sfnIndexEntryMd = os.path.join(dirIndexEntries, indexEntry + '.md')

        # do not autoload
        self.lines = None # type: list[str]
        self.citationLinkTargets = None # type: set[str]


    def loadIndexEntryMd(self) -> None:        
        assert os.path.exists(self.sfnIndexEntryMd), self.sfnIndexEntryMd
        self.lines = loadLinesFromTextFile(self.sfnIndexEntryMd)
        assert self.lines
        self.citationLinkTargets = set()
        citationParagraphParser = CitationParagraphParser()
        for line in self.lines:
            match = citationParagraphParser.matchCitationParagraph(line)
            if match:
                #print("")
                #print(citationParagraphParser.linkTarget)
                self.citationLinkTargets.add(citationParagraphParser.linkTarget)


    def updateCitations(self, transcriptModel: TranscriptModel) -> None:        
        assert self.lines
        citationParagraphParser = CitationParagraphParser()
        for index, line in enumerate(self.lines):
            match = citationParagraphParser.matchCitationParagraph(line)
            if match:
                oldCitation = match.group('citation')
                markdown = MarkdownLine(oldCitation)
                markdown.applySpacy(transcriptModel)
                citationParagraphParser.citation = markdown.text
                self.lines[index] = citationParagraphParser.canonicalCitationParagraph()


    def updateHeadersAndOccurrences(self, transcripts: dict[str, TranscriptPage]) -> None:
        # IMPORTANT: we replace lines (header, occurrences), but number of lines remains unchanged
        assert self.lines

        self.transcriptsSet = set()
    
        headerParser = IndexEntryPageHeaderParser()

        waitingForCounts = False
        currentTranscriptName = None
        for index, line in enumerate(self.lines):

            match = headerParser.matchHeaderLine(line)
            if match:                
                #print(headerParser.canonicalHeaderLine())
                currentTranscriptName = headerParser.transcriptName
                self.transcriptsSet.add(currentTranscriptName)
                self.lines[index] = headerParser.canonicalHeaderLine()
                waitingForCounts = True
                continue

            if waitingForCounts:
                match = re.match(r"(?P<head>(?P<spanStart><span class=\"(keywords|counts)\">)?_?(occurrences: )?)(?P<counts>[^_>]*)(?P<tail>_?(?P<spanEnd></span>)?)$", line)
                if match:
                    spanStart = match.group('spanStart')
                    if spanStart:
                        spanStart = spanStart.replace('"keywords"', '"counts"')
                    head = match.group('head')
                    oldCounts = match.group('counts')
                    tail = match.group('tail')
                    spanEnd = match.group('spanEnd')

                    #head = head.replace('occurrences: ', '')
                    #head = head.replace('_', '')
                    #tail = tail.replace('_', '')

                    transcriptPage = transcripts[currentTranscriptName]
                    newCounts = transcriptPage.collectTermLinks(self.indexEntry, self.citationLinkTargets)
                    if spanStart:
                        self.lines[index] = head + newCounts + tail
                    else:
                        self.lines[index] = "<span class=\"counts\">" + head + newCounts + tail + "</span>"

                    #print(self.lines[index])
                    waitingForCounts = False
                    continue


    def determineTags(self) -> list[str]:        
        assert self.lines
        tags = []
        for line in self.lines:
            if re.match("^ *#[A-Za-z]+", line):
                tagsInLine = [x.strip(' ') for x in line[1:].split('#')]
                tags.extend(tagsInLine)
        return tags


    def determineYamlSection(self) -> str:
        tags = self.determineTags()
        for index, tag in enumerate(tags):
            # tag immediately after the IndexEntry entry tag signifies the section, see ((XMWFBBI))
            if tag == 'IndexEntry':
                return tags[index+1]

    def extractYaml(self) -> dict[str,str]:
        return extractYaml(self.lines)


    def addMissingTranscripts(self, transcriptIndex: TranscriptIndex, transcripts: dict[str, TranscriptPage]) -> None:
        self.updateHeadersAndOccurrences(transcripts)
        
        linesToAppend = []

        # there's not necessarily a yaml section on the page
        yamlDict = self.extractYaml()
        excludeStrings = yamlDict['ignore-transcript-for-crossref'] if (yamlDict and 'ignore-transcript-for-crossref' in yamlDict) else []

        for transcriptName in transcripts.keys():
            if not transcriptName in self.transcriptsSet:
                transcriptPage = transcripts[transcriptName]

                include = True
                for excludeString in excludeStrings:
                    if excludeString in transcriptPage.sfnTranscriptMd:
                        include = False
                        break

                if include:
                    occurrences = transcriptPage.collectTermLinks(self.indexEntry, self.citationLinkTargets)
                    if occurrences:
                        retreat = transcriptPage.determineRetreat()
                        talkName = transcriptPage.determineTalkName()
                        headerLine = canonicalHeaderLineFromParams(None, f"{retreat}: {talkName}", transcriptName, None, None, None)
                        linesToAppend.append('')
                        linesToAppend.append(headerLine)
                        linesToAppend.append(f"_occurrences: {occurrences}_")

        if linesToAppend:
            from datetime import datetime
            self.lines.append("\n#### added " + datetime.now().strftime("%d.%m.%y %H:%M:%S"))
            self.lines.extend(linesToAppend)


    def save(self, sfnIndexEntryMd = None):
        assert self.lines, "missing lines to save to index entry page"
        if not sfnIndexEntryMd:
            sfnIndexEntryMd = self.sfnIndexEntryMd
        # TODO: might not be necessary to write anything
        saveLinesToTextFile(sfnIndexEntryMd, self.lines)


