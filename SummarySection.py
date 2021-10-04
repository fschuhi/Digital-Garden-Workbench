#!/usr/bin/env python3

from util import *
from MarkdownLine import MarkdownLines
from SummaryLineParser import SummaryLineParser
from SummaryLineParser import SummaryLineMatch
from typing import Iterable


# *********************************************
# SummarySection
# *********************************************

class SummarySection():

    def __init__(self, sourceLines: MarkdownLines, start, end):
        # create a copy of the passed MarkdownLines
        textLines = []
        for sourceLine in sourceLines:
            textLines.append(sourceLine.text)
        self.start = start
        self.end = end
        assert end-start == len(sourceLines)

        # make sure we conform to a section: header and counts
        parser = SummaryLineParser()        
        
        assert parser.matchText(textLines[0]) == SummaryLineMatch.HEADER
        self.headerText = parser.headerText
        self.level = parser.level
        
        assert parser.matchText(textLines[1]) == SummaryLineMatch.PARAGRAPH_COUNTS
        self.pageNr = parser.pageNr
        self.paragraphNr = parser.paragraphNr

        # an hr is nice to have but it can be missing
        if textLines[-1] != '---':
            textLines.append('---')

        # create the copy    
        self.markdownLines = MarkdownLines(textLines)
        self.header = self.markdownLines[0]
        self.counts = self.markdownLines[1]


    def changeHeader(self, newHeader):
        self.headerText = f"{self.level * '#'} {newHeader}"
        self.header.text = self.headerText


    def firstAudioLink(self):
        for ml in self.markdownLines:
            match = re.match(r" *!\[\[", ml.text)
            if match:
                return ml
        return None

    def hasAudioLink(self):
        return self.firstAudioLink() is not None


    def setAudioLink(self, fnAudio, timestamp: str = None):
        timestamp = "00:00" if not timestamp else canonicalTimestamp(timestamp)
        mlAudio = self.firstAudioLink()
        newAudioLinkLine = f"![[{fnAudio}#t={timestamp}]]"
        if mlAudio:
            mlAudio.text = newAudioLinkLine
        else:
            self.markdownLines.insert(2, "")
            self.markdownLines.insert(3, newAudioLinkLine)


    def addAdmonition(self, type: str, textLines: list[str]):
        textLines = [line.strip() for line in textLines]
        if not textLines[0].startswith("```"):
            textLines.insert(0, f"```ad-{type}")
        if textLines[-1] != "```":
            textLines.append("```")
        textLines.append("")
        self.markdownLines.insert(len(self.markdownLines)-1, textLines)
        


# *********************************************
# SummarySections
# *********************************************

class SummarySections(Iterable[SummarySection]):

    def __init__(self):
        self.sections = [] # type: list[SummarySection]
        pass

    def __iter__(self):
        for section in self.sections:
            yield section

    def __getitem__(self, key):
        return self.sections[key]

    def __len__(self):
        return len(self.sections)

    def append(self, sourceLines: MarkdownLines, start, end) -> SummarySection:
        newSection = SummarySection(sourceLines, start, end)
        self.sections.append(newSection)
        return newSection

    def findParagraph(self, pageNr: int, paragraphNr: int) -> SummarySection:
        for section in self.sections:
            if section.pageNr == pageNr and section.paragraphNr == paragraphNr:
                return section
        return None

