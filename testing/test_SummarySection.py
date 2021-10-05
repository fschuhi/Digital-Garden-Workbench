#!/usr/bin/env python3

import unittest
from TranscriptPage import TranscriptPage
from TranscriptSummaryPage import TranscriptSummaryPage
import filecmp

# *********************************************
# SummarySection
# *********************************************

class Test_SummarySection(unittest.TestCase):

    def test_1(self):
        pSummary = r"testing/data/Test_SummarySection.What is Insight (before).md"
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
        self.assertListEqual(section.markdownLines.collectTextLines(), ['##### asdfadsf', '[[1229 What is Insight#^16-1|16-1]]', '', '![[fnAudio#t=10:11]]', '', '```ad-warning', 'first line', 'second line', '```', '', '---'])


    def test_handleDecorations(self):
        pSummary = r"testing/data/Test_SummarySection.What is Insight (before).md"
        summary = TranscriptSummaryPage(pSummary)

        # spans = summary.collectSectionSpans()
        # (start, end) = spans[0]
        # for index in range(start, end):
        #     print(summary.markdownLines[index].text)
        # return

        pTranscript = r"testing/data/Test_SummarySection.1229 What is Insight (before).md"
        transcript = TranscriptPage(pTranscript)
        summary.handleTranscriptDecorations(transcript)
        summary.save("tmp/tmp.md")
        self.assertTrue(filecmp.cmp("tmp/tmp.md", r"testing/data/Test_SummarySection.What is Insight (after).md"))

        transcript.save("tmp/tmp.md")
        self.assertTrue(filecmp.cmp("tmp/tmp.md", r"testing/data/Test_SummarySection.1229 What is Insight (after).md"))

if __name__ == "__main__":
    unittest.main()