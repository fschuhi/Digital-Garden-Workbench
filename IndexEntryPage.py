#!/usr/bin/env python3

from MarkdownLine import MarkdownLine, SpacyMode
from ObsidianNote import ObsidianNote, ObsidianNoteType
from TranscriptModel import TranscriptModel
from genericpath import exists

from TranscriptPage import TranscriptPage
import re
from util import *


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
        if not (match := re.match(pattern, headerLine)):
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
        self.citationParagraph = self.citation = self.sourceStart = self.markdownLink = self.transcriptName = self.blockId = self.pageNr = self.paragraphNr = self.sourceEnd = self.linkTarget = None

        self.citationParagraph = citationParagraph

        linkPattern = r"(?P<markdownLink>\[\[(?P<transcriptName>[^#[]+)#\^?(?P<blockId>(?P<pageNr>[0-9]+)-(?P<paragraphNr>[0-9]+))\|[0-9]+-[0-9]+\]\])"
        pattern = r"^> *(?P<citation>.+?)((?P<sourceStart>(<p/>)?[_(]+)(?P<sourceText>[^[]*))" + linkPattern + r"(?P<sourceEnd>[_)]+)$"        
        if (match := re.match(pattern, citationParagraph)):

            self.citation = match.group('citation')
            self.sourceStart = match.group('sourceStart')
            self.sourceText = match.group('sourceText')
            self.markdownLink = match.group('markdownLink')
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

class IndexEntryPage(ObsidianNote):
    def __init__(self, path: str) -> None:
        super().__init__(ObsidianNoteType.INDEX_ENTRY, path)

        self.citationLinkTargets = set() # type: set[str]
        citationParagraphParser = CitationParagraphParser()
        for ml in self.markdownLines:
            if citationParagraphParser.matchCitationParagraph(ml.text):
                self.citationLinkTargets.add(citationParagraphParser.linkTarget)


    def determineYamlSection(self) -> str:
        for index, tag in enumerate(tags := self.determineTags()):
            # tag immediately after the IndexEntry entry tag signifies the section, see ((XMWFBBI))
            if tag == 'IndexEntry':
                return tags[index+1]


    def updateCitations(self, transcriptModel: TranscriptModel) -> None:        
        citationParagraphParser = CitationParagraphParser()
        for index, ml in enumerate(self.markdownLines):
            if (match := citationParagraphParser.matchCitationParagraph(ml.text)):
                oldCitation = match.group('citation')
                markdown = MarkdownLine(oldCitation)
                markdown.applySpacy(transcriptModel, mode=SpacyMode.ONLY_FIRST, forec=False)
                citationParagraphParser.citation = markdown.text
                self.markdownLines[index].text = citationParagraphParser.canonicalCitationParagraph()


    def updateHeadersAndOccurrences(self, transcripts: dict[str, TranscriptPage]) -> None:
        # IMPORTANT: we replace lines (header, occurrences), but number of lines remains unchanged
        self.transcriptsSet = set()
    
        headerParser = IndexEntryPageHeaderParser()

        waitingForCounts = False
        currentTranscriptName = None
        for index, ml in enumerate(self.markdownLines):

            if headerParser.matchHeaderLine(ml.text):
                currentTranscriptName = headerParser.transcriptName
                self.transcriptsSet.add(currentTranscriptName)
                self.markdownLines[index].text = headerParser.canonicalHeaderLine()
                waitingForCounts = True
                continue

            if waitingForCounts:
                match = re.match(r"(?P<head>(?P<spanStart><span class=\"(keywords|counts)\">)?_?(occurrences: )?)(?P<counts>[^_>]*)(?P<tail>_?(?P<spanEnd></span>)?)$", ml.text)
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
                    newCounts = transcriptPage.collectTermLinks(self.notename, self.citationLinkTargets)
                    if spanStart:
                        self.markdownLines[index].text = head + newCounts + tail
                    else:
                        self.markdownLines[index].text = "<span class=\"counts\">" + head + newCounts + tail + "</span>"

                    #print(self.lines[index])
                    waitingForCounts = False
                    continue


    def addMissingTranscripts(self, transcripts: dict[str, TranscriptPage]) -> None:
        self.updateHeadersAndOccurrences(transcripts)
        
        textLinesToAppend = []

        # there's not necessarily a yaml section on the page
        excludeStrings = value if (value := self.getYamlValue('ignore-transcript-for-crossref')) else []

        for transcriptName in transcripts.keys():
            if not transcriptName in self.transcriptsSet:
                transcriptPage = transcripts[transcriptName]

                include = True
                for excludeString in excludeStrings:
                    if excludeString in transcriptPage.path:
                        include = False
                        break

                if include:
                    occurrences = transcriptPage.collectTermLinks(self.notename, self.citationLinkTargets)
                    if occurrences:
                        headerLine = canonicalHeaderLineFromParams(None, f"{ transcriptPage.retreatname}: {transcriptPage.talkname}", transcriptName, None, None, None)
                        textLinesToAppend.append('')
                        textLinesToAppend.append(headerLine)
                        textLinesToAppend.append(f"_occurrences: {occurrences}_")

        if textLinesToAppend:
            from datetime import datetime
            self.markdownLines.append("\n#### added " + datetime.now().strftime("%d.%m.%y %H:%M:%S"))
            self.markdownLines.extend(textLinesToAppend)
