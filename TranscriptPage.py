#!/usr/bin/env python3

from ObsidianNote import ObsidianNote, ObsidianNoteType
from MarkdownLine import MarkdownLine, MarkdownLines
from genericpath import exists
from util import *

import os
import re

from TranscriptModel import TranscriptModel

from typing import Tuple

# ErosUnfetteredPath = 's:/Dropbox/Papers/_Markdown/Eros Unfettered/'

# *********************************************
# class TranscriptPage
# *********************************************

class TranscriptPage(ObsidianNote):
    def __init__(self, sfnTranscriptMd: str, textLines: list[str]) -> None:
        # even a new transcript page is never empty, e.g. has #Transcript tag at the beginning etc.
        assert textLines

        # ObsidianNote generates a MarkdownLines object from the passed list[str]
        self.markdownLines = None # type: MarkdownLines
        self.yaml = None # type: dict[str,str]
        super().__init__(ObsidianNoteType.TRANSCRIPT, textLines)
        assert self.markdownLines

        self.sfnTranscriptMd = sfnTranscriptMd
        self.transcriptName = os.path.splitext(os.path.basename(sfnTranscriptMd))[0]


    @classmethod
    def fromTranscriptFilename(cls, sfnTranscriptMd)  :
        assert os.path.exists(sfnTranscriptMd), "cannot find " + sfnTranscriptMd
        textLines = loadLinesFromTextFile(sfnTranscriptMd)
        return cls(sfnTranscriptMd, textLines)

    
    @classmethod
    def fromPlainMarkdownFile(cls, sfnPlainMd):
        lines = loadLinesFromTextFile(sfnPlainMd)
        return cls.fromPlainMarkdownLines(sfnPlainMd, lines)
    
    @classmethod
    def fromPlainMarkdownLines(cls, sfnPlainMd, lines: list[str]):
        # IMPORTANT: passed sfnPlainMd is a sfnTranscriptMd, but contains only raw markdown
        # we generate trailing blockids for the paragraphs in this method

        textLines = []
        textLines.append("---")
        textLines.append("obsidianUIMode: preview")
        textLines.append("---")
        textLines.append("#Transcript")
        textLines.append('')

        nPageIndicators = 0
        pageNr = 1
        paragraphNr = 0
        for line in lines:
            line = line.strip()            
            if not line:
                textLines.append('')
            else:
                # doing the indexing as a reindexing (i.e. there are block indicators) is allowed
                line = re.sub(r" \^[0-9]+-[0-9]+$", "", line)
                line = canonicalizeText(line)
                line = deitalicizeTermsWithDiacritics(line)

                if line == "#":
                    pageNr += 1
                    paragraphNr = 0
                    textLines.append('')
                    nPageIndicators += 1
                else:
                    # this is a regular line, to be turned into a paragraph
                    paragraphNr += 1
                    paragraphAsIfOnPage  = line + f" ^{pageNr}-{paragraphNr}"
                    textLines.append(paragraphAsIfOnPage)
                
        # we need "#" new page indicators, otherwise the danger is too high that we wreck a properly blockid-indexed transcript
        assert nPageIndicators != 0

        return cls(sfnPlainMd, textLines)


    def collectParagraphs(self):
        # https://realpython.com/python-walrus-operator/        
        return [(v[0], v[1], markdownLine) for markdownLine in self.markdownLines if (v := parseParagraph(markdownLine.text)) != (None, None, None)]


    def findParagraph(self, thePageNr, theParagraphNr) -> MarkdownLine:
        for (pageNr, paragraphNr, markdownLine) in self.collectParagraphs():
            if (pageNr == thePageNr) and (paragraphNr == theParagraphNr):
                return markdownLine
        return None


    def applySpacy(self, model: TranscriptModel, force: bool = False):
        for (_, _, markdownLine) in self.collectParagraphs():
            markdownLine.applySpacy(model, force)      


    def collectTermLinks(self, term: str, boldLinkTargets: set[str] = None, targetType='#') -> str:

        def collectTermCounts(term: str) -> list[tuple[int,int, int]]:
            counts = []
            for (pageNr, paragraphNr, markdownLine) in self.collectParagraphs():
                count = markdownLine.countTerm(term)
                if count:
                    counts.append( (pageNr, paragraphNr, count) )
            return counts

        counts = collectTermCounts(term)
        links = []
        for pageNr, paragraphNr, count in counts:
            blockId = f"{pageNr}-{paragraphNr}"
            linkTarget = f"{self.transcriptName}{targetType}{blockId}"
            link = f"[[{linkTarget}|{blockId}]]"
            if boldLinkTargets and linkTarget in boldLinkTargets:
                link = '**' + link + '**'
            if count > 1:
                link += f" ({count})"
            links.append(link)
        return " · ".join(links)        

    # ist das was für HAFEnvironment?

    def determineRetreat(self) -> str:
        return os.path.normpath(self.sfnTranscriptMd).split(os.path.sep)[-3]

    def determineTalkName(self) -> str:
        return re.match(r"^([0-9]+ )?(.+)", self.transcriptName).group(2)


# *********************************************
# factory
# *********************************************

def createTranscriptsDictionary(filenames: list[str], transcriptModel: TranscriptModel) -> dict[str,TranscriptPage]:
    transcripts = {}
    for filename in filenames:
        transcriptPage = TranscriptPage.fromTranscriptFilename(filename)
        transcriptPage.applySpacy(transcriptModel)
        transcripts[transcriptPage.transcriptName] = transcriptPage
    return transcripts

