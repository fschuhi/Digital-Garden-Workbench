#!/usr/bin/env python3

from MarkdownLine import MarkdownLine
from ObsidianNote import ObsidianNote, ObsidianNoteType
from TranscriptIndex import TranscriptIndex
from genericpath import exists
from TranscriptModel import TranscriptModel
from util import *

from HAFEnvironment import HAFEnvironment, determineTalkname
from TranscriptPage import TranscriptPage
import os
import re


# *********************************************
# class SummaryLineParser
# *********************************************

from enum import Enum
class SummaryLineMatch(Enum):
    NONE = 0
    HEADER = 1
    PARAGRAPH_COUNTS = 2
    INDEX_COUNTS = 3


class SummaryLineParser:

    def __init__(self) -> None:
        self.reset()

    def reset(self):
        self.headerLine = self.level = self.headerText = self.transcriptName = self.blockId = self.pageNr = self.paragraphNr = self.shownLinkText = self.counts = None

    def match(self, ml: MarkdownLine):
        return self.matchLine(ml.text)

    def matchLine(self, line) -> SummaryLineMatch:
        
        if (match := re.match(r"(#+ )(.+)", line)):
            self.headerLine = line        
            self.level = len(match.group(1).strip())
            self.headerText = match.group(2)

            # wait for the next keyword
            self.spanStart = self.transcriptName = self.blockId = self.pageNr = self.paragraphNr = self.shownLinkText = self.counts = self.spanEnd = None
            return SummaryLineMatch.HEADER

        # **[[0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1#^1-3|1-3]]**: _[[Preliminaries]], [[Embodiment]] (2)_
        pattern = r"(?P<spanStart><span class=\"(keywords|counts)\">)?(\*\*)?\[\[(?P<transcriptName>[0-9]+ [^#]+)#\^?(?P<blockId>(?P<pageNr>[0-9]+)-(?P<paragraphNr>[0-9]+))(\|(?P<shownLinkText>[0-9]+-[0-9]+))?\]\](\*\*)?(: _)?(?P<counts>[^_<]*)_?(?P<spanEnd></span>)?$"        
        if (match := re.match(pattern, line)):
            self.spanStart = match.group('spanStart')
            if self.spanStart:
                self.spanStart = self.spanStart.replace('"keywords"', '"counts"')
            self.transcriptName = match.group('transcriptName')
            self.blockId = match.group('blockId') 
            self.pageNr = int(match.group('pageNr')) 
            self.paragraphNr = int(match.group('paragraphNr'))
            self.shownLinkText = match.group('shownLinkText')
            self.counts = match.group('counts')
            self.spanEnd = match.group('spanEnd')
            return SummaryLineMatch.PARAGRAPH_COUNTS

        # <span class="counts">_[[Compassion]] (3) · [[Dukkha]] (2) · [[Contraction]] (2) · [[The Self]]_</span>
        pattern = r"(?P<spanStart><span class=\"counts\">)?_?(?P<counts>\[\[[^\]]+\]\] \([0-9]+\)( · \[\[[^\]]+\]\]( \([0-9]+\))?)*)_?(?P<spanEnd></span>)?$"        
        if (match := re.match(pattern, line)):
            if self.headerText != 'Index':
                pass
            else:
                self.spanStart = match.group('spanStart')
                self.counts = match.group('counts')
                self.spanEnd = match.group('spanEnd')
                return SummaryLineMatch.INDEX_COUNTS

        return SummaryLineMatch.NONE


    def canonicalParagraphCounts(self, forceSpan=False, targetType='#'):
        bold = '**' if self.counts else ''
        inside = f"{bold}[[{self.transcriptName}{targetType}{self.blockId}|{self.blockId}]]{bold}" + (f": _{self.counts}_" if self.counts else "")
        if (not self.spanStart) and forceSpan:
            assert not self.spanEnd
            self.spanStart = "<span class=\"counts\">"
            self.spanEnd = "</span>"
        return self.spanStart + inside + self.spanEnd if self.spanStart else inside


    def canonicalIndexCounts(self, forceSpan=True):
        inside = f"_{self.counts}_"
        if (not self.spanStart) and forceSpan:
            assert not self.spanEnd
            self.spanStart = "<span class=\"counts\">"
            self.spanEnd = "</span>"
        return self.spanStart + inside + self.spanEnd if self.spanStart else inside



# *********************************************
# class TranscriptSummaryPage
# *********************************************

class TranscriptSummaryPage(ObsidianNote):

    def __init__(self, path: str):
        super().__init__(ObsidianNoteType.SUMMARY, path)


    def update(self, transcriptPage: TranscriptPage, targetType='#') -> None:
        # IMPORTANT: number of makdown lines
        parser = SummaryLineParser()

        transcriptPage.bufferParagraphs = True
        try:
            for index, ml in enumerate(self.markdownLines):
                if (match := parser.match(ml)) == SummaryLineMatch.PARAGRAPH_COUNTS:
                    assert parser.transcriptName == transcriptPage.filename
                    # headers on a summary page refer to paragraphs in the transcript
                    pageNr = parser.pageNr
                    paragraphNr = parser.paragraphNr

                    mlParagraph = transcriptPage.findParagraph(pageNr, paragraphNr)
                    assert mlParagraph, f"cannot find ^{pageNr}-{paragraphNr}"
                    parser.counts = mlParagraph.collectShownLinks() if mlParagraph.shownLinks else ""

                    self.markdownLines[index].text = parser.canonicalParagraphCounts(forceSpan=True, targetType=targetType)
                    parser.reset()

                elif match == SummaryLineMatch.INDEX_COUNTS:
                    allTermCounts = {} # type: dict[str,int]
                    for mlParagraph in transcriptPage.markdownLines:
                        if (termCounts := mlParagraph.termCounts):
                            for entry, count in termCounts.items():
                                if entry in allTermCounts:
                                    allTermCounts[entry] += count
                                else:
                                    allTermCounts[entry] = count

                    # resulting tuples is sorted descending by counts, for each count ascending by index entry
                    tuples = sorted(allTermCounts.items(), key=lambda x: x[0])
                    tuples = sorted(tuples, key=lambda x: x[1], reverse=True)

                    entryFunc = lambda entry : f"[[{entry}]]" if allTermCounts[entry] == 1 else f"[[{entry}]] ({allTermCounts[entry]})"
                    links = [entryFunc(tuple[0]) for tuple in tuples]
                    parser.counts = " · ".join(links)
                    self.markdownLines[index].text = parser.canonicalIndexCounts(forceSpan=True)
                    parser.reset()
        finally:
            transcriptPage.bufferParagraphs = False


    def collectMissingParagraphHeaderTexts(self) -> int:
        pageNrs = set()
        parser = SummaryLineParser()
        for ml in self.markdownLines:
            if parser.match(ml) == SummaryLineMatch.PARAGRAPH_COUNTS:
                if (not parser.headerText) or parser.headerText == '...':
                    pageNrs.add(parser.pageNr)
        return len(pageNrs)


    def collectParagraphHeaderTargets(self) -> dict[str,str]:
        targets = {}
        parser = SummaryLineParser()
        for ml in self.markdownLines:
            if (match := parser.match(ml)) == SummaryLineMatch.PARAGRAPH_COUNTS:
                headerTarget = determineHeaderTarget(parser.headerText)
                blockid = f"{parser.pageNr}-{parser.paragraphNr}"
                targets[blockid] = headerTarget
        return targets


# *********************************************
# factory
# *********************************************

def createNewSummaryPage(talkName, haf: HAFEnvironment, model: TranscriptModel, sfn: str = None):
    sfnTranscriptMd = haf.getTranscriptFilename(talkName)    
    transcriptPage = TranscriptPage(sfnTranscriptMd)
    transcriptPage.applySpacy(model)

    sfnPdf = haf.getPDFFilename(talkName)

    pdfName = basenameWithoutExt(sfnPdf)
    transcriptName = basenameWithoutExt(sfnTranscriptMd)
    retreatName = transcriptPage.retreatname
    markdownLines = transcriptPage.markdownLines
    
    newLines = []
    newLines.extend([ \
        "---", \
        "obsidianUIMode: preview", \
        "ParagraphsListPage: false", \
        "---", \
        "#TranscriptSummary", \
        "", \
        f"[[prev|prev 🡄]] | [[{retreatName}|🡅]] | [[next|🡆 next]]", \
        "", \
        f"Series: {retreatName}\n", \
        f"Transcript: [[{transcriptName}]]", \
        f"Transcript PDF: [[{pdfName}.pdf]]", \
        "", \
        "![[audio goes here.mp3]]"
        "", \
        "## Index", \
        "<span class=\"counts\">_[[some keyword]] (99)_</span>"
        "<br/>\n", \
        "### Paragraphs", \
        "", \
        ])
        
    for markdownLine  in markdownLines:
        (pageNr, paragraphNr, _) = parseParagraph(markdownLine.text)
        if pageNr:
            blockId = f"{pageNr}-{paragraphNr}"
            counts = f": _{markdownLine.collectShownLinks()}_" if markdownLine.shownLinks else ""
            newLines.extend([ \
                "###### ...", \
                f"**[[{transcriptName}#^{blockId}|{blockId}]]**{counts}\n", \
                "---", \
                ])
    saveLinesToTextFile(sfn, newLines)


