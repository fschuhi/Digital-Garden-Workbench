#!/usr/bin/env python3

from HAFEnvironment import HAFEnvironment
from TalkParagraph import TalkParagraphs
from TranscriptPage import TranscriptPage
from util import basenameWithoutExt, determineHeaderTarget, parseBlockId, saveLinesToTextFile
from Publishing import Publishing
from consts import HAF_YAML, HAF_YAML_TESTING
import unittest
import filecmp


# *********************************************
# TalkParagraph
# *********************************************

class Test_TalkParagraph(unittest.TestCase):

    def test_1(self):
        haf = HAFEnvironment(HAF_YAML)
        paragraphs = TalkParagraphs(haf)
        #occurrences = sorted(paragraphs.collectTermOccurrences('Preliminaries'), key=lambda o: o[3], reverse=True)
        #print(occurrences)

        dict = paragraphs.createOccurrencesByTermDict()
        occurrences = dict['Craving']

        min = 2

        section = []
        section.append(f"### Paragraphs with {min}+ mentions")
        section.append("talk | description | count")
        section.append(":- | : - | -")
        for o in [_ for _ in occurrences if _.count >= min]:
            sfnTranscript = haf.getTranscriptFilename(o.talkname)
            transcript = TranscriptPage(sfnTranscript)

            (pageNr, paragraphNr) = parseBlockId(o.blockid)
            thisParagraph = f"[[{transcript.notename}#^{o.blockid}\\|.]]"

            (prevPageNr, prevParagraphNr) = transcript.prevParagraph(pageNr, paragraphNr)
            (nextPageNr, nextParagraphNr) = transcript.nextParagraph(pageNr, paragraphNr)
            prevParagraph = '' if prevPageNr == None else f"[[{transcript.notename}#^{prevPageNr}-{prevParagraphNr}\|.]]"
            nextParagraph = '' if nextPageNr == None else f"[[{transcript.notename}#^{nextPageNr}-{nextParagraphNr}\|.]]"
            paragraphLink = f"[[{o.talkname}#{determineHeaderTarget(o.headerText)}\\|{o.headerText}]] {prevParagraph} **{thisParagraph}** {nextParagraph}"

            section.append( f"[[{o.talkname}]] | {paragraphLink} | {o.count}" )

        saveLinesToTextFile(r"M:/Brainstorming/Untitled.md", section)


if __name__ == "__main__":
    unittest.main()
