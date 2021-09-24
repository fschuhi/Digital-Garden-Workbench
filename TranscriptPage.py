#!/usr/bin/env python3

from genericpath import exists
from util import *
# from util import canonicalizeText, deitalicizeTermsWithDiacritics, extractYaml, loadLinesFromTextFile, saveLinesToTextFile

import os
import re
import logging
import sys

from TranscriptModel import TranscriptModel
from TranscriptParagraph import TranscriptParagraph, applySpacyToParagraphs

from typing import Tuple

# ErosUnfetteredPath = 's:/Dropbox/Papers/_Markdown/Eros Unfettered/'

# *********************************************
# class TranscriptPage
# *********************************************

class TranscriptPage:
    def __init__(self, sfnTranscriptMd: str, paragraphs: list[TranscriptParagraph]) -> None:        
        self.sfnTranscriptMd = sfnTranscriptMd
        self.transcriptName = os.path.splitext(os.path.basename(sfnTranscriptMd))[0]
        self.paragraphs = paragraphs
        self.yaml = None


    @classmethod
    def fromTranscriptFilename(cls, sfnTranscriptMd)  :
        assert os.path.exists(sfnTranscriptMd), "cannot find " + sfnTranscriptMd
        # TODO: do more logging like this (or remove everything :)
        # logging.info(f"TranscriptPage.fromTranscriptMD( {sfnTranscriptMd} )")
      
        paragraphs = [] # type: list[TranscriptParagraph]
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
                    paragraph = TranscriptParagraph.fromParagraph(line)
                    paragraphs.append(paragraph)

        return cls(sfnTranscriptMd, paragraphs)


    @classmethod
    def fromPlainMarkup(cls, sfnPlainMd):
        lines = loadLinesFromTextFile(sfnPlainMd)
        return cls.fromPlainMarkupLines(sfnPlainMd, lines)
    
    @classmethod
    def fromPlainMarkupLines(cls, sfnPlainMd, lines: list[str]):
        # IMPORTANT: passed sfnPlainMd is a sfnTranscriptMd, but contains only raw markup
        # we generate trailing blockids for the paragraphs in this method

        paragraphs = []

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
                    paragraph = TranscriptParagraph.fromParagraph(paragraphAsIfOnPage)
                    paragraphs.append(paragraph)
                
        # we need "#" new page indicators, otherwise the danger is too high that we wreck a properly blockid-indexed transcript
        assert nPageIndicators != 0

        return cls(sfnPlainMd, paragraphs)


    def findParagraph(self, pageNr, paragraphNr) -> TranscriptParagraph:
        for paragraph in self.paragraphs:
            if (paragraph.pageNr == pageNr) and (paragraph.paragraphNr == paragraphNr):
                return paragraph
        return None

    
    def saveToObsidian(self, sfnTranscriptMd):
        logging.info(f"writing to '{sfnTranscriptMd}'")
        f = open(sfnTranscriptMd, 'w', encoding='utf-8', newline='\n')        
        # ((GDPHRFQ))
        print("---", file=f)
        print("obsidianUIMode: preview", file=f)
        print("---", file=f)
        print("#Transcript\n", file=f)
        for paragraph in self.paragraphs:
            print(f"{paragraph.text} ^{paragraph.pageNr}-{paragraph.paragraphNr}\n", file=f)
        f.close()


    def applySpacy(self, model: TranscriptModel, force: bool = False):
        applySpacyToParagraphs(model, self.paragraphs, force)


    def collectTermCounts(self, term: str) -> list[tuple[TranscriptParagraph, int]]:
        counts = []
        for paragraph in self.paragraphs:
            count = paragraph.countTerm(term)
            if count:
                counts.append((paragraph, count))
        return counts

    def collectTermLinks(self, term: str, boldLinkTargets: set[str] = None, targetType='#') -> str:
        counts = self.collectTermCounts(term)
        links = []
        for paragraph, count in counts:
            blockId = f"{paragraph.pageNr}-{paragraph.paragraphNr}"
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

