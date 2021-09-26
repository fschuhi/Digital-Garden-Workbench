#!/usr/bin/env python3

from MarkdownLine import MarkdownLine
from TranscriptIndex import TranscriptIndex
from genericpath import exists
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

class TranscriptSummaryPage:

    @classmethod
    def fromSummaryFilename(cls, sfnSummaryMd: str, load=False):
        cls.sfnSummaryMd = sfnSummaryMd        
        cls.lines = None # type: list[str] 
        if load:
            cls.loadSummaryMd()
        return cls()


    def loadSummaryMd(self) -> None:
        assert os.path.exists(self.sfnSummaryMd)
        self.lines = loadLinesFromTextFile(self.sfnSummaryMd)


    def update(self, transcriptPage: TranscriptPage, targetType='#') -> None:
        # IMPORTANT: number of lines remains unchanged
        assert self.lines
        transcriptName = transcriptPage.transcriptName
        parser = SummaryLineParser()

        for index, line in enumerate(self.lines):            
            if (match := parser.matchLine(line)) == SummaryLineMatch.PARAGRAPH_COUNTS:
                assert parser.transcriptName == transcriptName
                # headers on a summary page refer to paragraphs in the transcript
                pageNr = parser.pageNr
                paragraphNr = parser.paragraphNr

                markdownLine = transcriptPage.findParagraph(pageNr, paragraphNr)
                assert markdownLine, f"cannot find ^{pageNr}-{paragraphNr}"
                parser.counts = markdownLine.collectShownLinks() if markdownLine.shownLinks else ""

                self.lines[index] = parser.canonicalParagraphCounts(forceSpan=True, targetType=targetType)
                parser.reset()

            elif match == SummaryLineMatch.INDEX_COUNTS:
                allTermCounts = {} # type: dict[str,int]
                for markdownLine in transcriptPage.markdownLines:
                    if (termCounts := markdownLine.termCounts):
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
                self.lines[index] = parser.canonicalIndexCounts(forceSpan=True)
                parser.reset()


    def createNew(self, talkName: str, pdfName: str, transcriptName: str, markdownLines: list[MarkdownLine]) -> None:
        assert not self.lines, "can only create a fresh summary page (use update)"
        newLines = []
        newLines.extend([ \
            "#TranscriptSummary\n", \
            f"## {talkName}\n", \
            f"Transcript note: [[{transcriptName}]]", \
            f"Transcript PDF: [[{pdfName}.pdf]]", \
            "<br/>\n", \
            "### Paragraphs\n", \
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
        self.lines = newLines


    def save(self, sfnSummaryMd = None):
        assert self.lines, "missing lines to save to summary page"
        if not sfnSummaryMd:
            sfnSummaryMd = self.sfnSummaryMd
        assert sfnSummaryMd is not None
        # TODO: might not be necessary to write anything
        saveLinesToTextFile(sfnSummaryMd, self.lines)


    def collectMissingParagraphHeaderTexts(self) -> int:
        assert self.lines
        pageNrs = set()
        parser = SummaryLineParser()
        for line in self.lines:            
            if (match := parser.matchLine(line)) == SummaryLineMatch.PARAGRAPH_COUNTS:
                if (not parser.headerText) or parser.headerText == '...':
                    pageNrs.add(parser.pageNr)
        return len(pageNrs)


# *********************************************
# factory
# *********************************************

def createNewSummaryPage(talkName, haf: HAFEnvironment, model: TranscriptIndex, sfn: str = None):
    sfnTranscriptMd = haf.getTranscriptFilename(talkName)    
    transcriptPage = TranscriptPage.fromTranscriptFilename(sfnTranscriptMd)
    transcriptPage.applySpacy(model)

    sfnSummaryMd = haf.getSummaryFilename(talkName)
    sfnPdf = haf.getPDFFilename(talkName)
    summaryPage = TranscriptSummaryPage.fromSummaryFilename(sfnSummaryMd)

    pdfName = basenameWithoutExt(sfnPdf)
    transcriptName = basenameWithoutExt(sfnTranscriptMd)
    markdownLines = transcriptPage.markdownLines
    summaryPage.createNew(talkName, pdfName, transcriptName, markdownLines)

    summaryPage.save(sfn)

