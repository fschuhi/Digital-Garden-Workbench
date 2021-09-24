#!/usr/bin/env python3

import re

from TranscriptPdfLoader import TBlock
from TranscriptModel import TranscriptModel
from MarkdownLine import MarkdownLine

# *********************************************
# class TranscriptParagraph
# *********************************************

class TranscriptParagraph:
    def __init__(self, pageNr, paragraphNr, text) -> None:
        self.pageNr = pageNr
        self.paragraphNr = paragraphNr
        self.markdown = MarkdownLine(text)


    @classmethod
    def fromBlock(cls, block: TBlock):
        (pageNr, paragraphNr, blockText) = block
        return cls(pageNr, paragraphNr, blockText)


    @classmethod
    def fromParagraph(cls, paragraphOnPage: str):
        match = re.search(r"^(.+) \^([0-9]+)-([0-9]+)$", paragraphOnPage)
        assert match
        paragraphText = match.group(1)
        pageNr = int(match.group(2))
        paragraphNr = int(match.group(3))
        return cls(pageNr, paragraphNr, paragraphText)


    @property
    def text(self): 
        return self.markdown.text

    @property
    def termCounts(self):
        return self.markdown.termCounts

    @property
    def shownLinks(self):
        return self.markdown.shownLinks


    # ((JJFZHVO)) Keywords section on summary page
    def collectShownLinks(self) -> str:
        return self.markdown.collectShownLinks()

    def countTerm(self, term: str) -> int:
        return self.markdown.countTerm(term)


    def applySpacy(self, model: TranscriptModel, force: bool = False) -> None:
        self.markdown.applySpacy(model)


# *********************************************
# applySpacy...
# *********************************************

def applySpacyToParagraphs(model: TranscriptModel, paragraphs: list[TranscriptParagraph], force: bool = False) -> None:
    for paragraph in paragraphs:            
        paragraph.applySpacy(model, force)

