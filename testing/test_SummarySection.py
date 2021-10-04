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
        lastSection = sections[-1]
        self.assertListEqual(lastSection.markdownLines.collectTextLines(), ['##### ...', '[[1229 What is Insight#^16-1|16-1]]', '', '---'])
        section = sections.findParagraph(16,1)
        self.assertEqual(section, lastSection)
        self.assertFalse(section.hasAudioLink())

        section.setAudioLink("fnAudio", "10:11")
        section.changeHeader("asdfadsf")
        self.assertListEqual(section.markdownLines.collectTextLines(), ['##### asdfadsf', '[[1229 What is Insight#^16-1|16-1]]', '', '![[fnAudio#t=10:11]]', '', '---'])

        section.addAdmonition('warning', ["first line", "second line"])
        self.assertListEqual(section.markdownLines.collectTextLines(), ['##### asdfadsf', '[[1229 What is Insight#^16-1|16-1]]', '', '![[fnAudio#t=10:11]]', '', '```ad-warning', 'first line', 'second line', '```', '---'])


if __name__ == "__main__":
    unittest.main()