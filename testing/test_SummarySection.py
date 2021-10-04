#!/usr/bin/env python3

import unittest
from TranscriptSummaryPage import TranscriptSummaryPage

# *********************************************
# SummarySection
# *********************************************

class Test_SummarySection(unittest.TestCase):

    def test_1(self):
        pTranscript = r"s:\work\Python\HAF\tmp\1229 What is Insight (source).md"
        pSummary = r"s:\work\Python\HAF\tmp\What is Insight (source).md"
        summary = TranscriptSummaryPage(pSummary)
        sections = summary.collectSections()
        #print(sections)

if __name__ == "__main__":
    unittest.main()