#!/usr/bin/env python3

import re
from collections import namedtuple

from typing import Tuple
from HAFEnvironment import HAFEnvironment, determineTalkname
from TalkPageLineParser import TalkPageLineMatch, TalkPageLineParser
from TalkPage import TalkPage
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
# class TalkParagraph
# *********************************************

# talkname, headerText, blockid

ParagraphTuple = namedtuple('ParagraphTuple', 'talkname headerText blockid term count')

class TalkParagraph():

    def __init__(self, parser: TalkPageLineParser):
        self.transcriptName = parser.transcriptName
        self.talkname = determineTalkname(parser.transcriptName)
        self.blockid = parser.blockId
        self.headerText = parser.headerText
        self.countsString = parser.counts
        self.counts = collectCounts(self.countsString) # list[Tuple[str,int]]
        self.countByTerm = {term: count for (term, count) in self.counts}
        self._occurrences = None


# *********************************************
# class TalkParagraphs
# *********************************************

class TalkParagraphs():

    def __init__(self, haf: HAFEnvironment):
        self.haf = haf
        self.paragraphs = [] # type: list[TalkParagraph]
        self._occurrences = None

        for filename in haf.collectTalkFilenames():
            talk = TalkPage(filename)
            parser = TalkPageLineParser()
            for ml in talk.markdownLines:
                match = parser.match(ml)
                if match == TalkPageLineMatch.PARAGRAPH_COUNTS:
                    self.paragraphs.append(TalkParagraph(parser))

    @property
    def occurrences(self) -> list[ParagraphTuple]:
        if self._occurrences is None:
            self._occurrences = self.collectOccurrences()
        return self._occurrences


    def collectOccurrences(self) -> list[ParagraphTuple]:
        occurrences = []
        for paragraph in self.paragraphs:
            for (term, count) in paragraph.counts:
                pt = ParagraphTuple(paragraph.talkname, paragraph.headerText, paragraph.blockid, term, count)
                occurrences.append(pt)
        return occurrences
        
    def collectTermOccurrences(self, term) -> list[ParagraphTuple]:
        #return [o for o in self.collectOccurrences() if o.term == term]
        return [o for o in self.occurrences if o.term == term]
        
    def createOccurrencesByTermDict(self) -> dict[str,list[ParagraphTuple]]:
        from collections import defaultdict
        dict = defaultdict(list)
        #descendingOccurrences = sorted(self.collectOccurrences(), key=lambda o: o.count, reverse=True)
        descendingOccurrences = sorted(self.occurrences, key=lambda o: o.count, reverse=True)
        for o in descendingOccurrences:
            dict[o.term].append(o)
        return dict


    def collectCooccurringParagraphs(self) -> dict[str,dict[str,list[TalkParagraph]]]:
        from itertools import combinations
        cooccurrences = {} # type: dict[str,dict[str,list[TalkParagraph]]]
        for paragraph in self.paragraphs:
            combos = list(combinations(paragraph.countByTerm.keys(), 2))
            for (term1, term2) in combos:
                if term1 in cooccurrences:
                    dict2 = cooccurrences[term1]
                else:
                    dict2 = {}
                    cooccurrences[term1] = dict2
                if not term2 in dict2:
                    dict2[term2] = []
                dict2[term2].append(paragraph)

        return cooccurrences


