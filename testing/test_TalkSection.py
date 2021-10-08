#!/usr/bin/env python3

import unittest
from TranscriptPage import TranscriptPage
from TalkPage import TalkPage
import filecmp

# *********************************************
# TalkSection
# *********************************************

class TestTalkSection(unittest.TestCase):

    def test_1(self):
        fnTalk = r"testing/data/Test_TalkSection.What is Insight (before).md"
        talk = TalkPage(fnTalk)
        sections = talk.collectSections()
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
        fnTalk = r"testing/data/Test_TalkSection.What is Insight (before).md"
        talk = TalkPage(fnTalk)


        pTranscript = r"testing/data/Test_TalkSection.1229 What is Insight (before).md"
        transcript = TranscriptPage(pTranscript)
        talk.handleTranscriptDecorations(transcript)
        talk.save("tmp/tmp.md")
        self.assertTrue(filecmp.cmp("tmp/tmp.md", r"testing/data/Test_TalkSection.What is Insight (after).md"))

        transcript.save("tmp/tmp.md")
        self.assertTrue(filecmp.cmp("tmp/tmp.md", r"testing/data/Test_TalkSection.1229 What is Insight (after).md"))

if __name__ == "__main__":
    unittest.main()