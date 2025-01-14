#!/usr/bin/env python3

from ObsidianNote import ObsidianNote, ObsidianNoteType
from MarkdownLine import MarkdownLine, SpacyMode
from util import *

import os
import re

from TranscriptModel import TranscriptModel

# *********************************************
# class TranscriptPage
# *********************************************

class TranscriptPage(ObsidianNote):
    def __init__(self, path: str) -> None:
        super().__init__(ObsidianNoteType.TRANSCRIPT, path)

        self._bufferParagraphs = False
        self.bufferedParagraphs = None


    @property 
    def retreatname(self):
        return os.path.normpath(self.path).split(os.path.sep)[-3]

    @property
    def talkname(self):
        return re.match(r"^([0-9]+ )?(.+)", self.notename).group(2)


    @classmethod
    def fromPlainMarkdownLines(cls, lines: list[str], talkname):
        # IMPORTANT: passed sfnPlainMd is a sfnTranscriptMd, but contains only raw markdown
        # we generate trailing blockids for the paragraphs in this method

        textLines = []
        textLines.append("---")
        textLines.append("obsidianUIMode: preview")
        textLines.append("---")
        textLines.append("#Transcript")
        textLines.append('')
        textLines.append(f"[[{talkname}]]")
        textLines.append('')
        textLines.append('---')
        textLines.append('<br/>')
        textLines.append('')
        textLines.append('')

        nPageIndicators = 0
        pageNr = 1
        paragraphNr = 0
        for index, line in enumerate(lines):
            if not (line := line.strip()):
                textLines.append('')
            else:
                # doing the indexing as a reindexing (i.e. there are block indicators) is allowed
                line = re.sub(r" \^[0-9]+-[0-9]+$", "", line)
                line = canonicalizeText(line)
                # line = deitalicizeTermsWithDiacritics(line)

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

                    # replace the empty line immediately before the paragraph w/ the target header
                    if textLines[-2] != '':
                        print(index)
                        assert textLines[-2] == ''
                    textLines[-2] = f"###### {pageNr}-{paragraphNr}"
                
        # we need "#" new page indicators, otherwise the danger is too high that we wreck a properly blockid-indexed transcript
        assert nPageIndicators != 0

        tmp = createTempfile()
        saveLinesToTextFile(tmp.name, textLines)
        return cls(tmp.name)


    @property
    def bufferParagraphs(self):
        return self._bufferParagraphs

    @bufferParagraphs.setter
    def bufferParagraphs(self, value):
        if value and not self._bufferParagraphs:
            self.bufferedParagraphs = self.collectParagraphs(force=True)
        else:
            self.bufferedParagraphs = None
        self._bufferParagraphs = value

    def collectParagraphs(self, force=False) -> list[Tuple[int,int,MarkdownLine]]:
        if force or not self.bufferedParagraphs:
            paragraphs =[(v[0], v[1], markdownLine) for markdownLine in self.markdownLines if (v := parseParagraph(markdownLine.text)) != (None, None, None)]
        return self.bufferedParagraphs if self.bufferedParagraphs else paragraphs;


    def findParagraph(self, thePageNr, theParagraphNr) -> MarkdownLine:
        for (pageNr, paragraphNr, markdownLine) in self.collectParagraphs():
            if (pageNr == thePageNr) and (paragraphNr == theParagraphNr):
                return markdownLine
        return None

    def prevParagraph(self, thePageNr, theParagraphNr) -> Tuple[int,int]:
        lastPageNr = None
        lastParagraphNr = None
        for (pageNr, paragraphNr, markdownLine) in self.collectParagraphs():
            if (pageNr == thePageNr) and (paragraphNr == theParagraphNr):
                return (lastPageNr, lastParagraphNr)
            lastPageNr = pageNr
            lastParagraphNr = paragraphNr
        return (lastPageNr, lastParagraphNr)

    def nextParagraph(self, thePageNr, theParagraphNr) -> Tuple[int,int]:
        found = False
        for (pageNr, paragraphNr, markdownLine) in self.collectParagraphs():
            if found:
                return (pageNr, paragraphNr)
            found = (pageNr == thePageNr) and (paragraphNr == theParagraphNr)
        return (None, None)


    def applySpacy(self, model: TranscriptModel, mode: SpacyMode, force: bool):
        for (_, _, markdownLine) in self.collectParagraphs():
            markdownLine.applySpacy(model, mode, force)


    def collectTermCounts(self, term: str) -> list[tuple[int,int, int]]:
        counts = []
        for (pageNr, paragraphNr, markdownLine) in self.collectParagraphs():
            if (count := markdownLine.countTerm(term)):
                counts.append( (pageNr, paragraphNr, count) )
        return counts

    def collectTermLinks(self, term: str, boldLinkTargets: set[str] = None, targetType='#') -> str:
        counts = self.collectTermCounts(term)
        links = []
        for pageNr, paragraphNr, count in counts:
            blockId = f"{pageNr}-{paragraphNr}"
            linkTarget = f"{self.notename}{targetType}{blockId}"
            link = f"[[{linkTarget}|{blockId}]]"
            if boldLinkTargets and linkTarget in boldLinkTargets:
                link = '**' + link + '**'
            if count > 1:
                link += f" ({count})"
            links.append(link)
        return ' · '.join(links)        


    def collectAllTermCounts(self) -> dict[str,int]:
        allTermCounts = {} # type: dict[str,int]
        for mlParagraph in self.markdownLines:
            if (termCounts := mlParagraph.termCounts):
                for entry, count in termCounts.items():
                    if entry in allTermCounts:
                        allTermCounts[entry] += count
                    else:
                        allTermCounts[entry] = count
        return allTermCounts

    def collectAllTermLinks(self):
        allTermCounts = self.collectAllTermCounts()
        tuples = sorted(allTermCounts.items(), key=lambda x: x[0])
        tuples = sorted(tuples, key=lambda x: x[1], reverse=True)
        entryFunc = lambda entry : f"[[{entry}]]" if allTermCounts[entry] == 1 else f"[[{entry}]] ({allTermCounts[entry]})"
        links = [entryFunc(tuple[0]) for tuple in tuples]
        return ' · '.join(links)


# *********************************************
# factory
# *********************************************

def createTranscriptsDictionary(filenames: list[str], transcriptModel: TranscriptModel) -> dict[str,TranscriptPage]:
    transcripts = {}
    for filename in filenames:
        transcriptPage = TranscriptPage(filename)
        transcriptPage.applySpacy(transcriptModel, mode=SpacyMode.ONLY_FIRST, force=False)
        transcripts[transcriptPage.notename] = transcriptPage
    return transcripts

