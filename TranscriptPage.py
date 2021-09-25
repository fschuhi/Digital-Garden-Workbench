#!/usr/bin/env python3

from ObsidianNote import ObsidianNote, ObsidianNoteType
from MarkdownLine import MarkdownLine, MarkdownLines
from genericpath import exists
from util import *
# from util import canonicalizeText, deitalicizeTermsWithDiacritics, extractYaml, loadLinesFromTextFile, saveLinesToTextFile

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

        # ObsidianNote generates a MarkdownLines object from the passed list[str]
        self.markdownLines = None #type: MarkdownLines
        super().__init__(ObsidianNoteType.TRANSCRIPT, textLines)
        assert self.markdownLines

        self.sfnTranscriptMd = sfnTranscriptMd
        self.transcriptName = os.path.splitext(os.path.basename(sfnTranscriptMd))[0]
        self.yaml = None


    @classmethod
    def fromTranscriptFilename(cls, sfnTranscriptMd)  :
        assert os.path.exists(sfnTranscriptMd), "cannot find " + sfnTranscriptMd
      
        textLines = [] # type: list[str]
        lines = loadLinesFromTextFile(sfnTranscriptMd)
        
        cls.yaml = extractYaml(lines)
        skipAtBeginning = len(cls.yaml) + 2 if cls.yaml else 0

        for index, line in enumerate(lines):
            if index < skipAtBeginning:
                continue
            line = line.strip()
            if True:
            #if line:
                # IMPORTANT: empty lines are not retained as paragraph
                # TranscriptPage and its paragraphs is an internal object, not meant to reflect visuals
                if line.startswith("#"):
                    # tags (and headers, since 22.09.21) are not paragraphs per se 
                    # ((VABTJZS)) store tags in page
                    pass
                else:
                    textLines.append(line)

        return cls(sfnTranscriptMd, textLines)

    
    @classmethod
    def fromPlainMarkdownFile(cls, sfnPlainMd):
        lines = loadLinesFromTextFile(sfnPlainMd)
        return cls.fromPlainMarkdownLines(sfnPlainMd, lines)
    
    @classmethod
    def fromPlainMarkdownLines(cls, sfnPlainMd, lines: list[str]):
        # IMPORTANT: passed sfnPlainMd is a sfnTranscriptMd, but contains only raw markup
        # we generate trailing blockids for the paragraphs in this method

        textLines = []
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
                # if firstLine or line == "#":
                #     # line w/ a single # marks a new page
                #     pageNr += 1
                #     paragraphNr = 0
                #     firstLine = False                

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


    def findParagraph(self, thePageNr, theParagraphNr) -> MarkdownLine:
        for markdownLine in self.markdownLines:
            (pageNr, paragraphNr, _) = parseParagraph(markdownLine.text)
            if (pageNr == thePageNr) and (paragraphNr == theParagraphNr):
                return markdownLine
        return None


    def saveToObsidian(self, sfnTranscriptMd):
        out = []
        out.append("---")
        out.append("obsidianUIMode: preview")
        out.append("---")
        out.append("#Transcript")

        markdownTextLines = self.markdownLines.collectTextLines()
        out.extend(markdownTextLines)
        saveLinesToTextFile(sfnTranscriptMd, out)

    # def saveToObsidian(self, sfnTranscriptMd):
    #     f = open(sfnTranscriptMd, 'w', encoding='utf-8', newline='\n')        
    #     # ((GDPHRFQ))
    #     print("---", file=f)
    #     print("obsidianUIMode: preview", file=f)
    #     print("---", file=f)
    #     print("#Transcript\n", file=f)
    #     for markdownLine in self.markdownLines:
    #         print(markdownLine.text + '\n', file=f)
    #     f.close()


    def applySpacy(self, model: TranscriptModel, force: bool = False):
        for markdownLine in self.markdownLines:
            markdownLine.applySpacy(model, force)


    def collectTermLinks(self, term: str, boldLinkTargets: set[str] = None, targetType='#') -> str:

        def collectTermCounts(term: str) -> list[tuple[int,int, int]]:
            counts = []
            for markdownLine in self.markdownLines:
                (pageNr, paragraphNr, _) = parseParagraph(markdownLine.text)
                if pageNr:
                    count = markdownLine.countTerm(term)
                    if count:
                        counts.append((pageNr, paragraphNr, count))
            return counts

        counts = collectTermCounts(term)
        links = []
        for pageNr, paragraphNr, count in counts:
            blockId = f"{pageNr}-{paragraphNr}"
            linkTarget = f"{self.transcriptName}{targetType}{blockId}"
            link = f"[[{linkTarget}|{blockId}]]"

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

