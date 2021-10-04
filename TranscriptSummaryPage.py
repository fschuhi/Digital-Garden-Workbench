#!/usr/bin/env python3

from MarkdownLine import MarkdownLine
from ObsidianNote import ObsidianNote, ObsidianNoteType
from TranscriptIndex import TranscriptIndex
from genericpath import exists
from TranscriptModel import TranscriptModel
from util import *

from HAFEnvironment import HAFEnvironment, determineTalkname
from TranscriptPage import TranscriptPage
from SummarySection import SummarySection
from SummaryLineParser import SummaryLineParser
from SummaryLineParser import SummaryLineMatch
import os
import re


# *********************************************
# class TranscriptSummaryPage
# *********************************************

class TranscriptSummaryPage(ObsidianNote):

    def __init__(self, path: str):
        super().__init__(ObsidianNoteType.SUMMARY, path)


    def update(self, transcriptPage: TranscriptPage, targetType='#') -> None:
        # IMPORTANT: number of makdown lines
        parser = SummaryLineParser()

        transcriptPage.bufferParagraphs = True
        try:
            for index, ml in enumerate(self.markdownLines):
                if (match := parser.match(ml)) == SummaryLineMatch.PARAGRAPH_COUNTS:
                    assert parser.transcriptName == transcriptPage.filename
                    # headers on a summary page refer to paragraphs in the transcript
                    pageNr = parser.pageNr
                    paragraphNr = parser.paragraphNr

                    mlParagraph = transcriptPage.findParagraph(pageNr, paragraphNr)
                    assert mlParagraph, f"cannot find ^{pageNr}-{paragraphNr}"
                    parser.counts = mlParagraph.collectShownLinks() if mlParagraph.shownLinks else ""

                    self.markdownLines[index].text = parser.canonicalParagraphCounts(forceSpan=True, targetType=targetType)
                    parser.reset()

                elif match == SummaryLineMatch.INDEX_COUNTS:
                    allTermCounts = {} # type: dict[str,int]
                    for mlParagraph in transcriptPage.markdownLines:
                        if (termCounts := mlParagraph.termCounts):
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
                    self.markdownLines[index].text = parser.canonicalIndexCounts(forceSpan=True)
                    parser.reset()
        finally:
            transcriptPage.bufferParagraphs = False


    def collectMissingParagraphHeaderTexts(self) -> int:
        pageNrs = set()
        parser = SummaryLineParser()
        for ml in self.markdownLines:
            if parser.match(ml) == SummaryLineMatch.PARAGRAPH_COUNTS:
                if (not parser.headerText) or parser.headerText == '...':
                    pageNrs.add(parser.pageNr)
        return len(pageNrs)


    def collectParagraphHeaderTexts(self) -> list[Tuple[int, int, str]]:
        targets = {}
        parser = SummaryLineParser()
        for ml in self.markdownLines:
            if (match := parser.match(ml)) == SummaryLineMatch.PARAGRAPH_COUNTS:
                header = determineHeaderTarget(parser.headerText)
                blockid = f"{parser.pageNr}-{parser.paragraphNr}"
                targets[blockid] = header
        return targets

    def collectParagraphHeaderTargets(self) -> dict[str,str]:
        targets = {}
        parser = SummaryLineParser()
        for ml in self.markdownLines:
            if (match := parser.match(ml)) == SummaryLineMatch.PARAGRAPH_COUNTS:
                headerTarget = determineHeaderTarget(parser.headerText)
                blockid = f"{parser.pageNr}-{parser.paragraphNr}"
                targets[blockid] = headerTarget
        return targets


    def collectSections(self) -> list[SummarySection]:
        parser = SummaryLineParser()
        sections = []

        def addSection(start, end):
            sourceLines = self.markdownLines[start:end]
            sections.append( SummarySection(sourceLines))

        start = None
        for index, ml in enumerate(self.markdownLines):
            if parser.match(ml) == SummaryLineMatch.HEADER:
                if start:
                    #print(ml.text)
                    addSection(start, index-1)
                start = index
            elif ml.text.startswith('#'):
                if start:
                    addSection(start, index-1)
                    start = None
        if start:
            addSection(start, index)
        return sections


# *********************************************
# factory
# *********************************************

def createNewSummaryPage(talkName, haf: HAFEnvironment, model: TranscriptModel, sfn: str = None):
    sfnTranscriptMd = haf.getTranscriptFilename(talkName)    
    transcriptPage = TranscriptPage(sfnTranscriptMd)
    transcriptPage.applySpacy(model)

    sfnPdf = haf.getPDFFilename(talkName)

    pdfName = basenameWithoutExt(sfnPdf)
    transcriptName = basenameWithoutExt(sfnTranscriptMd)
    retreatName = transcriptPage.retreatname
    markdownLines = transcriptPage.markdownLines
    
    newLines = []
    newLines.extend([ \
        "---", \
        "obsidianUIMode: preview", \
        "ParagraphsListPage: false", \
        f"Series: {retreatName}", \
        "---", \
        "#TranscriptSummary", \
        "", \
        f"[[prev|prev 🡄]] | [[{retreatName}|🡅]] | [[next|🡆 next]]", \
        "", \
        f"Series: [[{retreatName}]]", \
        f"Transcript: [[{transcriptName}]]", \
        f"Transcript PDF: [[{pdfName}.pdf]]", \
        "", \
        "![[audio goes here.mp3]]", \
        "", \
        "## Index", \
        "<span class=\"counts\">_[[some keyword]] (99)_</span>"
        "<br/>\n", \
        "### Paragraphs", \
        "", \
        ])
        
    for markdownLine  in markdownLines:
        (pageNr, paragraphNr, _) = parseParagraph(markdownLine.text)
        if pageNr:
            blockId = f"{pageNr}-{paragraphNr}"
            counts = f": _{markdownLine.collectShownLinks()}_" if markdownLine.shownLinks else ""
            newLines.extend([ \
                "##### ...", \
                f"**[[{transcriptName}#^{blockId}|{blockId}]]**{counts}\n", \
                "---", \
                ])

    saveLinesToTextFile(sfn, newLines)


