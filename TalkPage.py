#!/usr/bin/env python3

from MarkdownLine import MarkdownLine, SpacyMode
from ObsidianNote import ObsidianNote, ObsidianNoteType
from TranscriptIndex import TranscriptIndex
from genericpath import exists
from TranscriptModel import TranscriptModel
from util import *

from HAFEnvironment import HAFEnvironment, determineTalkname
from TranscriptPage import TranscriptPage
from TalkSection import TalkSection, TalkSections
from TalkPageLineParser import TalkPageLineParser, TalkPageLineMatch
import os
import re


# *********************************************
# class TalkPage
# *********************************************

class TalkPage(ObsidianNote):

    def __init__(self, path: str):
        super().__init__(ObsidianNoteType.TALK, path)
        self._sections = None


    @property
    def sections(self):
        if self._sections is None:
            self._sections = self.collectSections(autoparse=False)
        return self._sections


    def update(self, transcriptPage: TranscriptPage, targetType='#') -> None:
        # IMPORTANT: number of makdown lines
        parser = TalkPageLineParser()

        transcriptPage.bufferParagraphs = True
        try:
            for index, ml in enumerate(self.markdownLines):
                if (match := parser.match(ml)) == TalkPageLineMatch.PARAGRAPH_COUNTS:
                    assert parser.transcriptName == transcriptPage.notename
                    # headers on a talk page refer to paragraphs in the transcript
                    pageNr = parser.pageNr
                    paragraphNr = parser.paragraphNr

                    mlParagraph = transcriptPage.findParagraph(pageNr, paragraphNr)
                    assert mlParagraph, f"cannot find ^{pageNr}-{paragraphNr}"
                    parser.counts = mlParagraph.collectShownLinks() if mlParagraph.shownLinks else ""

                    self.markdownLines[index].text = parser.canonicalParagraphCounts(forceSpan=True, targetType=targetType)
                    parser.reset()

                elif match == TalkPageLineMatch.INDEX_COUNTS:
                    # the 
                    parser.counts = transcriptPage.collectAllTermLinks()
                    self.markdownLines[index].text = parser.canonicalIndexCounts(forceSpan=True)
                    parser.reset()
        finally:
            transcriptPage.bufferParagraphs = False


    def collectMissingParagraphHeaderTexts(self) -> int:
        pageNrs = set()
        parser = TalkPageLineParser()
        for ml in self.markdownLines:
            if parser.match(ml) == TalkPageLineMatch.PARAGRAPH_COUNTS:
                if (not parser.headerText) or parser.headerText == '...':
                    pageNrs.add(parser.pageNr)
        return len(pageNrs)


    def collectParagraphHeaderTexts(self) -> dict[str,str]:
        targets = {}
        parser = TalkPageLineParser()
        for ml in self.markdownLines:
            if (match := parser.match(ml)) == TalkPageLineMatch.PARAGRAPH_COUNTS:
                header = determineHeaderTarget(parser.headerText)
                blockid = f"{parser.pageNr}-{parser.paragraphNr}"
                targets[blockid] = header
        return targets


    def collectParagraphHeaderTargets(self) -> dict[str,str]:
        targets = {}
        parser = TalkPageLineParser()
        for ml in self.markdownLines:
            if (match := parser.match(ml)) == TalkPageLineMatch.PARAGRAPH_COUNTS:
                headerTarget = determineHeaderTarget(parser.headerText)
                blockid = f"{parser.pageNr}-{parser.paragraphNr}"
                targets[blockid] = headerTarget
        return targets


    def collectSectionSpans(self) -> list[Tuple[int,int]]:
        parser = TalkPageLineParser()
        sectionsSpans = []
        lastHeaderIndex = None
        nextCountsFound = None
        lastSectionHeaderIndex = None
        for index, ml in enumerate(self.markdownLines):
            if parser.match(ml) == TalkPageLineMatch.PARAGRAPH_COUNTS:
                # we never have 2 counts after the other
                assert not nextCountsFound
                nextCountsFound = True

                # there is always a header with the description (usually level 5, but can also be lower)
                # assume this header is the last encountered header before the counts
                lastSectionHeaderIndex = lastHeaderIndex

            elif ml.text.startswith('#'):
                # regardless of the header's function (description or structuring header), note that we've encountered one
                lastHeaderIndex = index

                if nextCountsFound:
                    # section is still "open", i.e. we've found the counts but not the end of the section yet
                    # when encountering the counts we had also found the header
                    assert lastSectionHeaderIndex

                    # current header line is not part of the section, but part of the span
                    sectionsSpans.append((lastSectionHeaderIndex, index))

                    # reset for the next section
                    lastSectionHeaderIndex = None
                    nextCountsFound = None 

        # quite likely that the last section is terminated not by a header but by the end of the file
        if nextCountsFound:
            # close the section
            assert lastSectionHeaderIndex
            sectionsSpans.append((lastSectionHeaderIndex, index+1))
        return sectionsSpans


    def collectSections(self, autoparse=False) -> TalkSections:
        self._sections = TalkSections(autoparse)
        sectionSpans = self.collectSectionSpans()
        for start, end in sectionSpans:
            sourceLines = self.markdownLines[start:end]
            self._sections.append(sourceLines, start, end)
        return self._sections


    def getAudioFilename(self):
        for mlTalk in self.markdownLines:
            if (matchAudio := parseAudioLink(mlTalk.text)):
                return matchAudio.group('filename')


    def handleTranscriptDecorations(self, transcript: TranscriptPage):
        fnAudio = self.getAudioFilename()

        # get the current sections
        # the sections will be expanded by additional lines, determined from the decorations of the associated transcript paragraph
        #sections = self.collectSections()
        sections = self.sections

        # sections are modified in the original object
        # section start and end index into self.markdownLines will change incrementally => track total delta
        delta = 0

        for section in sections:
            # each section has an associated transcript paragraph, determined from the counts line
            mlTranscript = transcript.findParagraph(section.pageNr, section.paragraphNr)
            if mlTranscript is None:
                print(section.pageNr, section.paragraphNr)
                assert mlTranscript is not None

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

            # replace section in this talk
            deleted = section.end - section.start
            self.markdownLines.delete(section.start+delta, section.end+delta)
            insertedTextLines = section.markdownLines.collectTextLines()
            inserted = len(insertedTextLines)
            self.markdownLines.insert(section.start+delta, insertedTextLines)
            delta += inserted - deleted


# *********************************************
# factory
# *********************************************

def createNewTalkPage(talkname, haf: HAFEnvironment, model: TranscriptModel, sfn: str = None):
    sfnTranscriptMd = haf.getTranscriptFilename(talkname)    
    transcriptPage = TranscriptPage(sfnTranscriptMd)
    transcriptPage.applySpacy(model, mode=SpacyMode.ONLY_FIRST, force=False)

    sfnPdf = haf.getPDFFilename(talkname)

    pdfName = basenameWithoutExt(sfnPdf)
    transcriptName = basenameWithoutExt(sfnTranscriptMd)
    retreatName = transcriptPage.retreatname
    markdownLines = transcriptPage.markdownLines

    timestamp = pdfName[:4] + transcriptName[:2] + transcriptName[2:4]
    pAudio = haf.vault.findFile(timestamp + '*')
    audioname = os.path.basename(pAudio) if pAudio else "audio goes here.mp3"
    
    newLines = []
    newLines.extend([ \
        "---", \
        "obsidianUIMode: preview", \
        "ParagraphsListPage: true", \
        f"Series: {retreatName}", \
        "---", \
        "#Talk", \
        "", \
        f"[[prev|prev 🡄]] | [[{retreatName}|🡅]] | [[next|🡆 next]]", \
        "", \
        f"Series: [[{retreatName}]]", \
        f"Transcript: [[{transcriptName}]]", \
        f"Transcript PDF: [[{pdfName}.pdf]]", \
        "", \
        f"![[{audioname}]]", \
        "", \
        "## Index", \
        "<span class=\"counts\">_[[some keyword]] (99)_</span>", \
        "<br/>\n", \
        "## Paragraphs", \
        f"[[{talkname} -|plain list]]", \
        "", \
        "---", \
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


