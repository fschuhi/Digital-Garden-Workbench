#!/usr/bin/env python3

from MarkdownLine import MarkdownLine, MarkdownLines
from genericpath import exists
from util import *
# from util import canonicalizeText, deitalicizeTermsWithDiacritics, extractYaml, loadLinesFromTextFile, saveLinesToTextFile

import os
import re
import logging
import sys

from TranscriptModel import TranscriptModel

from typing import Tuple

# ErosUnfetteredPath = 's:/Dropbox/Papers/_Markdown/Eros Unfettered/'

# *********************************************
# class TranscriptPage
# *********************************************

class TranscriptPage:
    def __init__(self, sfnTranscriptMd: str, markdownLines: list[MarkdownLine]) -> None:        
        self.sfnTranscriptMd = sfnTranscriptMd
        self.transcriptName = os.path.splitext(os.path.basename(sfnTranscriptMd))[0]
        self.markdownLines = markdownLines
        self.yaml = None


    @classmethod
    def fromTranscriptFilename(cls, sfnTranscriptMd)  :
        assert os.path.exists(sfnTranscriptMd), "cannot find " + sfnTranscriptMd
        # TODO: do more logging like this (or remove everything :)
        # logging.info(f"TranscriptPage.fromTranscriptMD( {sfnTranscriptMd} )")
      
        markdownLines = [] # type: list[markdownLine]
        lines = loadLinesFromTextFile(sfnTranscriptMd)
        
        cls.yaml = extractYaml(lines)
        skipAtBeginning = len(cls.yaml) + 2 if cls.yaml else 0

        for index, line in enumerate(lines):
            if index < skipAtBeginning:
                continue
            line = line.strip()
            if line:
                # IMPORTANT: empty lines are not retained as paragraph
                # TranscriptPage and its paragraphs is an internal object, not meant to reflect visuals
                if line.startswith("#"):
                    # tags (and headers, since 22.09.21) are not paragraphs per se 
                    # ((VABTJZS)) store tags in page
                    pass
                else:
                    markdownLine = MarkdownLine(line)
                    markdownLines.append(markdownLine)

        return cls(sfnTranscriptMd, markdownLines)

    
    @classmethod
    def fromPlainMarkup(cls, sfnPlainMd):
        lines = loadLinesFromTextFile(sfnPlainMd)
        return cls.fromPlainMarkupLines(sfnPlainMd, lines)
    
    @classmethod
    def fromPlainMarkupLines(cls, sfnPlainMd, lines: list[str]):
        # IMPORTANT: passed sfnPlainMd is a sfnTranscriptMd, but contains only raw markup
        # we generate trailing blockids for the paragraphs in this method

        markdownLines = []

        nPageIndicators = 0
        pageNr = 0
        paragraphNr = 0
        firstLine = True
        for line in lines:
            line = line.strip()            
            if line:
                # doing the indexing as a reindexing (i.e. there are block indicators) is allowed
                line = re.sub(r" \^[0-9]+-[0-9]+$", "", line)
                line = canonicalizeText(line)
                line = deitalicizeTermsWithDiacritics(line)
                if firstLine or line == "#":
                    # line w/ a single # marks a new page
                    pageNr += 1
                    paragraphNr = 0
                    firstLine = False                

                if line == "#":
                    nPageIndicators += 1
                else:
                    # this is a regular line, to be turned into a paragraph
                    paragraphNr += 1
                    paragraphAsIfOnPage  = line + f" ^{pageNr}-{paragraphNr}"
                    markdownLine = MarkdownLine(paragraphAsIfOnPage)
                    markdownLines.append(markdownLine)
                
        # we need "#" new page indicators, otherwise the danger is too high that we wreck a properly blockid-indexed transcript
        assert nPageIndicators != 0

        return cls(sfnPlainMd, markdownLines)


    def findMarkdownLine(self, thePageNr, theParagraphNr) -> MarkdownLine:
        for markdownLine in self.markdownLines:
            (pageNr, paragraphNr, _) = parseParagraph(markdownLine.text)
            #if (paragraph.pageNr == thePageNr) and (paragraph.paragraphNr == theParagraphNr):
            if (pageNr == thePageNr) and (paragraphNr == theParagraphNr):
                return markdownLine
        return None


    def saveToObsidian(self, sfnTranscriptMd):
        logging.info(f"writing to '{sfnTranscriptMd}'")
        f = open(sfnTranscriptMd, 'w', encoding='utf-8', newline='\n')        
        # ((GDPHRFQ))
        print("---", file=f)
        print("obsidianUIMode: preview", file=f)
        print("---", file=f)
        print("#Transcript\n", file=f)
        for markdownLine in self.markdownLines:
            print(markdownLine.text + '\n', file=f)
        f.close()


    def applySpacy(self, model: TranscriptModel, force: bool = False):
        for markdownLine in self.markdownLines:
            markdownLine.applySpacy(model, force)


    def collectTermLinks(self, term: str, boldLinkTargets: set[str] = None, targetType='#') -> str:
        links = []
        for markdownLine in self.markdownLines:
            count = markdownLine.countTerm(term)
            (pageNr, paragraphNr, _) = parseParagraph(markdownLine.text)
            blockId = f"{pageNr}-{paragraphNr}"
            linkTarget = f"{self.transcriptName}{targetType}{blockId}"
            link = f"[[{linkTarget}|{blockId}]]"
            if boldLinkTargets and linkTarget in boldLinkTargets:
                link = '**' + link + '**'
            if count > 1:
                link += f" ({count})"
            links.append(link)
        return " · ".join(links)

    # def collectTermCounts(self, term: str) -> list[tuple[TranscriptParagraph, int]]:
    #     counts = []
    #     for paragraph in self.paragraphs:
    #         count = paragraph.markdownLine.countTerm(term)
    #         if count:
    #             counts.append((paragraph, count))
    #     return counts

    # def collectTermLinks2(self, term: str, boldLinkTargets: set[str] = None, targetType='#') -> str:
    #     counts = self.collectTermCounts(term)
    #     links = []
    #     for paragraph, count in counts:
    #         (pageNr, paragraphNr, _) = parseParagraph(paragraph.markdown.text)
    #         blockId = f"{pageNr}-{paragraphNr}"
    #         linkTarget = f"{self.transcriptName}{targetType}{blockId}"
    #         link = f"[[{linkTarget}|{blockId}]]"
    #         if boldLinkTargets and linkTarget in boldLinkTargets:
    #             link = '**' + link + '**'
    #         if count > 1:
    #             link += f" ({count})"
    #         links.append(link)
    #     return " · ".join(links)


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

