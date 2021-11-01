#!/usr/bin/env python3

from collections import defaultdict
import unittest
import re
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


    def test_parseCounts(self):
        #fnTalk = r"testing/data/Test_TalkSection.What is Insight (before).md"
        fnTalk = r"m:\2019 Practising the Jhanas\Talks\Orienting to This Jhana Retreat.md"
        talk = TalkPage(fnTalk)
        sections = talk.collectSections()
        admonitionTuplesByTerm = {}
        for section in sections:
            #section.parseCounts()
            section.parseLines()
            if section.counts:
                for admonition in section.admonitions:
                    (start, end, admonitionType, admonitionTitle) = admonition
                    admonitionBody = "\n".join([ml.text for ml in section.markdownLines[start+1:end-1]])
                    admonitionTuple = (section, admonitionType, admonitionBody)
                    for term in section.counts.keys():
                        if section.pageNr == 12 and section.paragraphNr == 1:
                            print(term)
                        if term in admonitionTuplesByTerm:
                            l = admonitionTuplesByTerm[term]
                        else:
                            l = []
                            admonitionTuplesByTerm[term] = l
                        #if term == 'Awakening':
                        #    print(admonitionTuple)
                        l.append(admonitionTuple)
        print(admonitionTuplesByTerm['Awakening'])

if __name__ == "__main__":
    unittest.main()