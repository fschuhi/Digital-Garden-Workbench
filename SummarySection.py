#!/usr/bin/env python3

from MarkdownLine import MarkdownLines
from util import *

from HAFEnvironment import HAFEnvironment
from TranscriptPage import TranscriptPage
from SummaryLineParser import SummaryLineParser
from SummaryLineParser import SummaryLineMatch


class SummarySection():

    def __init__(self, sourceLines: MarkdownLines):
        textLines = []
        for sourceLine in sourceLines:
            textLines.append(sourceLine.text)

        parser = SummaryLineParser()
        assert parser.matchText(textLines[0]) == SummaryLineMatch.HEADER
        assert parser.matchText(textLines[1]) == SummaryLineMatch.PARAGRAPH_COUNTS
        #assert textLines[-1] == '---'

        self.markdownLines = MarkdownLines(textLines)

