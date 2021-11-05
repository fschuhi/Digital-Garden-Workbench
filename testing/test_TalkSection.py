#!/usr/bin/env python3

from collections import defaultdict
from typing import Tuple
import unittest
import re
from HAFEnvironment import HAFEnvironment
from TalkSection import TalkSection
from TranscriptIndex import TranscriptIndex
from TranscriptPage import TranscriptPage
from TalkPage import TalkPage
import filecmp
from consts import *
from index import buildAdmonitionInfosByTermForTalk, buildQuoteTuplesByTermForAllTalks, buildAlternativeSpellingsByTerm
from util import basenameWithoutExt, determineHeaderTarget, saveLinesToTextFile


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
        import time
        transcriptIndex = TranscriptIndex(RB_YAML)
        alternativesByTerm = buildAlternativeSpellingsByTerm(transcriptIndex)

        haf = HAFEnvironment(HAF_YAML)        
        filenames = [fnTalk for p in haf.collectTranscriptFilenames() if (fnTalk := haf.getTalkFilename(basenameWithoutExt(p))) is not None]

        tic = time.perf_counter()
        mergedAdmonitionTuplesByTerm = buildQuoteTuplesByTermForAllTalks(filenames, alternativesByTerm, lambda section, type, title: type == 'quote')
        toc = time.perf_counter()
        print(100*(toc-tic))

        #print(admonitionTuplesByTerm)

        l = []

        def outputQuoteRow(tuple: Tuple[TalkPage, TalkSection, str, str, str]):
            (talk, section, admonitionType, admonitionTitle, admonitionBody) = tuple
            blockid = f"{section.pageNr}-{section.paragraphNr}"
            headerText = section.headerText
            headerTarget = determineHeaderTarget(headerText)
            safeAdmonitionBody = admonitionBody.replace('|', '\|')
            l.append(f"[[{talk.notename}]] | [[{talk.notename}#{headerTarget}\|{headerText}]] | {safeAdmonitionBody}")

        lastTalk = None
        def outputQuote(tuple: Tuple[TalkPage, TalkSection, str, str, str]):
            (talk, section, admonitionType, admonitionTitle, admonitionBody) = tuple

            nonlocal lastTalk
            if talk != lastTalk:
                l.append(f"##### [[{talk.notename}]]")
                retreatName = haf.retreatNameFromTalkname(talk.notename)
                l.append(f'<span class="counts">[[{retreatName}]]</span>')
                lastTalk = talk
            headerText = section.headerText
            headerTarget = determineHeaderTarget(headerText)
            l.append(f'> {admonitionBody} &nbsp;&nbsp;<span class="counts">([[{talk.notename}#{headerTarget}|{headerText}]])</span>')
            l.append("")

        createTable = False

        if createTable:
            l.append("talk | paragraph | quote")
            l.append("- | - | -")

        lg = mergedAdmonitionTuplesByTerm['Love']
        for quote in lg:
            if createTable:
                outputQuoteRow(quote)
            else:
                outputQuote(quote)
        saveLinesToTextFile(r"M:\Brainstorming\Untitled.md", l)
        

if __name__ == "__main__":
    unittest.main()