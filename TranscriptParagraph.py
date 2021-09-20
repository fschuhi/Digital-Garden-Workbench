#!/usr/bin/env python3

import re

from TranscriptPdfLoader import TBlock
from TranscriptModel import TranscriptModel
from MarkdownSnippet import MarkdownSnippet

# *********************************************
# class TranscriptParagraph
# *********************************************

class TranscriptParagraph:
    def __init__(self, pageNr, paragraphNr, text) -> None:
        self.pageNr = pageNr
        self.paragraphNr = paragraphNr
        self.snippet = MarkdownSnippet(text)
        self.hasAppliedSpacy = False


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
        return self.snippet.text

    @property
    def termCounts(self):
        return self.snippet.termCounts

    @property
    def shownLinks(self):
        return self.snippet.shownLinks


    # ((JJFZHVO)) Keywords section on summary page
    def collectShownLinks(self) -> str:
        assert self.hasAppliedSpacy, "must first apply spacy to this paragraph"
        entryFunc = lambda entry : f"[[{entry}]]" if self.termCounts[entry] == 1 else f"[[{entry}]] ({self.termCounts[entry]})"
        links = [entryFunc(link) for link in self.shownLinks]
        # return ", ".join(links)
        return " · ".join(links)

    def countTerm(self, term: str) -> int:
        assert self.hasAppliedSpacy, "must first apply spacy to this paragraph"        
        return self.termCounts[term] if term in self.termCounts else 0


    def applySpacy(self, model: TranscriptModel, force: bool = False) -> None:
        if (not self.hasAppliedSpacy) or force:
            self.snippet.applySpacy(model)
            self.hasAppliedSpacy = True


# *********************************************
# applySpacy...
# *********************************************

def applySpacyToParagraphs(model: TranscriptModel, paragraphs: list[TranscriptParagraph], force: bool = False) -> None:
    for paragraph in paragraphs:            
        paragraph.applySpacy(model, force)

