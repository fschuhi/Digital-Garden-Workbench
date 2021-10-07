#!/usr/bin/env python3

from MarkdownLine import MarkdownLine
from util import *
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

    def     match(self, ml: MarkdownLine):
        return self.matchText(ml.text)

    def matchText(self, text) -> SummaryLineMatch:
        
        # intentionally capture any header
        if (match := re.match(r"(#+ )(.+)", text)):
            self.headerLine = text        
            self.level = len(match.group(1).strip())
            self.headerText = match.group(2)

            # wait for the next keyword
            self.spanStart = self.transcriptName = self.blockId = self.pageNr = self.paragraphNr = self.shownLinkText = self.counts = self.spanEnd = None

            # not all headers are a HEADER match
            # in the testcases we use "old style" level 6, normally 5
            return SummaryLineMatch.HEADER if self.level >= 5 else SummaryLineMatch.NONE

        # **[[0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1#^1-3|1-3]]**: _[[Preliminaries]], [[Embodiment]] (2)_
        pattern = r"(?P<spanStart><span class=\"(keywords|counts)\">)?(\*\*)?\[\[(?P<transcriptName>[0-9]+ [^#]+)#\^?(?P<blockId>(?P<pageNr>[0-9]+)-(?P<paragraphNr>[0-9]+))(\|(?P<shownLinkText>[0-9]+-[0-9]+))?\]\](\*\*)?(: _)?(?P<counts>[^_<]*)_?(?P<spanEnd></span>)?$"        
        if (match := re.match(pattern, text)):
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
        if (match := re.match(pattern, text)):
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


