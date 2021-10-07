#!/usr/bin/env python3

import re
from collections import namedtuple

from typing import Tuple
from HAFEnvironment import HAFEnvironment, determineTalkname
from SummaryLineParser import SummaryLineMatch, SummaryLineParser
from TranscriptSummaryPage import TranscriptSummaryPage
from util import determineHeaderTarget


def collectCounts(countsString: str) -> list[Tuple[str,int]]:
    counts = []
    singleCounts = countsString.split(' · ')
    for singleCount in singleCounts:
        if singleCount:
            match = re.match(r"\[\[(?P<entry>[^]]+)\]\]( \((?P<count>[0-9]+)\))?", singleCount)
            if not match:
                print(singleCounts)
                print(countsString)
                print("!!!!" + singleCount)
                assert False
            assert match
            count = int(suppliedCount) if (suppliedCount := match.group('count')) else 1
            counts.append( (match.group('entry'), count) )
    return counts


# *********************************************
# class SummaryParagraph
# *********************************************

# summaryName, headerText, blockid

ParagraphTuple = namedtuple('ParagraphTuple', 'summaryName headerText blockid term count')

class SummaryParagraph():

    def __init__(self, parser: SummaryLineParser):
        self.transcriptName = parser.transcriptName
        self.summaryName = determineTalkname(parser.transcriptName)
        self.blockid = parser.blockId
        self.headerText = parser.headerText
        self.countsString = parser.counts
        self.counts = collectCounts(self.countsString) # list[Tuple[str,int]]
        self.countByTerm = {term: count for (term, count) in self.counts}
        self._occurrences = None


# *********************************************
# class SummaryParagraph
# *********************************************

class SummaryParagraphs():

    def __init__(self, haf: HAFEnvironment):
        self.haf = haf
        self.paragraphs = [] # type: list[SummaryParagraph]

        for filename in haf.collectSummaryFilenames():
            summary = TranscriptSummaryPage(filename)
            parser = SummaryLineParser()
            for ml in summary.markdownLines:
                match = parser.match(ml)
                if match == SummaryLineMatch.PARAGRAPH_COUNTS:
                    self.paragraphs.append( SummaryParagraph(parser))

    @property
    def occurrences(self) -> list[ParagraphTuple]:
        if self._occurrences is None:
            self._occurrences = self.collectOccurrences()
        return self._occurrences


    def collectOccurrences(self) -> list[ParagraphTuple]:
        occurrences = []
        for paragraph in self.paragraphs:
            for (term, count) in paragraph.counts:
                pt = ParagraphTuple(paragraph.summaryName, paragraph.headerText, paragraph.blockid, term, count)
                occurrences.append(pt)
        return occurrences
        
    def collectTermOccurrences(self, term) -> list[ParagraphTuple]:
        return [o for o in self.collectOccurrences() if o.term == term]
        
    def createOccurrencesByTermDict(self) -> dict[str,list[ParagraphTuple]]:
        from collections import defaultdict
        dict = defaultdict(list)
        descendingOccurrences = sorted(self.collectOccurrences(), key=lambda o: o.count, reverse=True)
        for o in descendingOccurrences:
            dict[o.term].append(o)
        return dict


