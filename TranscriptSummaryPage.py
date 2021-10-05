#!/usr/bin/env python3

from MarkdownLine import MarkdownLine
from ObsidianNote import ObsidianNote, ObsidianNoteType
from TranscriptIndex import TranscriptIndex
from genericpath import exists
from TranscriptModel import TranscriptModel
from util import *

from HAFEnvironment import HAFEnvironment, determineTalkname
from TranscriptPage import TranscriptPage
from SummarySection import SummarySection, SummarySections
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
                    # old:
                    # allTermCounts = {} # type: dict[str,int]
                    # for mlParagraph in transcriptPage.markdownLines:
                    #     if (termCounts := mlParagraph.termCounts):
                    #         for entry, count in termCounts.items():
                    #             if entry in allTermCounts:
                    #                 allTermCounts[entry] += count
                    #             else:
                    #                 allTermCounts[entry] = count

                    # new:
                    # allTermCounts = transcriptPage.collectAllTermCounts()

                    # # resulting tuples is sorted descending by counts, for each count ascending by index entry
                    # tuples = sorted(allTermCounts.items(), key=lambda x: x[0])
                    # tuples = sorted(tuples, key=lambda x: x[1], reverse=True)

                    # entryFunc = lambda entry : f"[[{entry}]]" if allTermCounts[entry] == 1 else f"[[{entry}]] ({allTermCounts[entry]})"
                    # links = [entryFunc(tuple[0]) for tuple in tuples]
                    # parser.counts = " · ".join(links)
                    parser.counts = transcriptPage.collectAllTermLinks()
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


    def collectSectionSpans(self) -> list[Tuple[int,int]]:
        parser = SummaryLineParser()
        sectionsSpans = []
        start = None
        for index, ml in enumerate(self.markdownLines):
            if parser.match(ml) == SummaryLineMatch.HEADER:
                # close the previous section and start new one
                if start:
                    #print(ml.text)
                    sectionsSpans.append((start, index))
                start = index
            elif ml.text.startswith('#'):
                # close the not-yet-closed section
                if start:
                    sectionsSpans.append((start, index))
                    start = None
        if start:
            # including very last line
            sectionsSpans.append((start, index+1))
        return sectionsSpans


    def collectSections(self) -> SummarySections:
        sections = SummarySections()
        sectionSpans = self.collectSectionSpans()
        for start, end in sectionSpans:
            sourceLines = self.markdownLines[start:end]
            sections.append(sourceLines, start, end)
        return sections


    def getAudioFilename(self):
        for mlSummary in self.markdownLines:
            if (matchAudio := parseAudioLink(mlSummary.text)):
                return matchAudio.group('filename')


    def handleTranscriptDecorations(self, transcript: TranscriptPage):
        fnAudio = self.getAudioFilename()

        # get the current sections
        # the sections will be expanded by additional lines, determined from the decorations of the associated transcript paragraph
        sections = self.collectSections()

        # sections are modified in the original object
        # section start and end index into self.markdownLines will change incrementally => track total delta
        delta = 0

        for section in sections:
            # each section has an associated transcript paragraph, determined from the counts line
            mlTranscript = transcript.findParagraph(section.pageNr, section.paragraphNr)

            # handle prepended timestamp and/or header
            while True:
                match = re.match(r"\[((?P<timestamp>(0?1:)?[0-9][0-9]:[0-9][0-9])|(?P<header>[^]]+)) *\]", mlTranscript.text)
                if not match:
                    break
                if (header := match.group('header')):
                    section.changeHeader(header)
                if (timestamp := match.group('timestamp')):
                    section.setAudioLink(fnAudio, timestamp)
                (_, end) = match.span()
                mlTranscript.text = mlTranscript.text[end:].strip()

            # handle admonitions
            while True:
                match = re.search(r"\{ *(?P<command>quote|warning|info|note|danger) +(?P<text>[^}]+)}", mlTranscript.text, re.IGNORECASE) 
                if not match:
                    break

                admonitionType = match.group('command').lower()
                text = removeObsidianLinksFromText(match.group('text'))

                section.addAdmonition(admonitionType, [text])

                (start, end) = match.span()
                mlTranscript.text = mlTranscript.text[:start] + (text if admonitionType == 'quote' else '') + mlTranscript.text[end:]

            # decorations might be separated by spaces => remove duplicate spaces
            mlTranscript.text = re.sub('  +', ' ', mlTranscript.text)

            # replace section in this summary
            deleted = section.end - section.start
            self.markdownLines.delete(section.start+delta, section.end+delta)
            insertedTextLines = section.markdownLines.collectTextLines()
            inserted = len(insertedTextLines)
            self.markdownLines.insert(section.start+delta, insertedTextLines)
            delta += inserted - deleted


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
        "## Paragraphs", \
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


