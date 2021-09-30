#!/usr/bin/env python3

from TranscriptPage import TranscriptPage
from types import SimpleNamespace
from HAFEnvironment import HAFEnvironment, determineTalkname
from TranscriptIndex import TranscriptIndex
from TranscriptModel import TranscriptModel
from TranscriptSummaryPage import SummaryLineMatch, TranscriptSummaryPage, SummaryLineParser, createNewSummaryPage
from consts import HAF_YAML_TESTING, RB_YAML_TESTING
import unittest
import filecmp

# *********************************************
# anonymous class
# *********************************************

# https://stackoverflow.com/questions/1123000/does-python-have-anonymous-classes
Bunch = SimpleNamespace

class Test_AnonymousClass(unittest.TestCase):

    def test_2(self):
        foo = dict(bla = "asdf", heul = 1)
        bar = dict(heul = 1, bla = "asdf")
        self.assertEqual(foo, bar)


    def test_3(self):
        foo = Bunch(bla = "asdf", heul = 1)
        bar = Bunch(heul = 1, bla = "asdf")
        #print(foo.bla)
        self.assertEqual(foo, bar)


    def test_4(self):
        foo = SimpleNamespace(bla = "asdf", heul = 1)
        bar = SimpleNamespace(heul = 1, bla = "asdf")
        #print(foo.bla)
        self.assertEqual(foo, bar)


class Test_SummaryLineParser(unittest.TestCase):
    
    headerLine1 = "###### It's going to be about movement, gesture, and voice"
    countsLine1a = "**[[0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1#^1-3|1-3]]**: _[[Preliminaries]], [[Embodiment]] (2)_"
    countsLine1b = "**[[0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1#1-3|1-3]]**: _[[Preliminaries]], [[Embodiment]] (2)_"
    countsLine2 = "[[0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1#1-3|1-3]]"
    countsLine3 = "<span class=\"counts\">**[[0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1#1-3|1-3]]**: _[[Preliminaries]], [[Embodiment]] (2)_</span>"

    headerLine2 = "### Index"
    keywordsLine4 = "<span class=\"counts\">_[[Compassion]] (3) · [[Dukkha]] (2) · [[Contraction]] (2) · [[The Self]]_</span>"

    def test_SummaryLineParser1a(self):
        parser = SummaryLineParser()
        self.assertEqual(parser.matchLine(self.headerLine1), SummaryLineMatch.HEADER)
        self.assertEqual(parser.matchLine(self.countsLine1a), SummaryLineMatch.PARAGRAPH_COUNTS)

        self.assertEqual(parser.headerText, "It's going to be about movement, gesture, and voice") # ((ATRDIWI))
        self.assertEqual(parser.level, 6)
        self.assertEqual(parser.transcriptName, "0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1")
        self.assertEqual(parser.pageNr, 1)
        self.assertEqual(parser.paragraphNr, 3)
        self.assertEqual(parser.shownLinkText, "1-3")
        self.assertEqual(parser.blockId, "1-3")
        self.assertEqual(parser.canonicalParagraphCounts(targetType='#^'), self.countsLine1a)


    def test_SummaryLineParser1b(self):
        parser = SummaryLineParser()
        self.assertEqual(parser.matchLine(self.headerLine1), SummaryLineMatch.HEADER)
        self.assertEqual(parser.matchLine(self.countsLine1a), SummaryLineMatch.PARAGRAPH_COUNTS)
        self.assertEqual(parser.canonicalParagraphCounts(targetType='#'), self.countsLine1b)


    def test_SummaryLineParser2(self):
        parser = SummaryLineParser()
        self.assertEqual(parser.matchLine(self.countsLine2), SummaryLineMatch.PARAGRAPH_COUNTS)

        self.assertEqual(parser.transcriptName, "0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1")
        self.assertEqual(parser.pageNr, 1)
        self.assertEqual(parser.paragraphNr, 3)
        self.assertEqual(parser.shownLinkText, "1-3")
        self.assertEqual(parser.blockId, "1-3")
        self.assertEqual(parser.canonicalParagraphCounts(), self.countsLine2)


    def test_SummaryLineParser3(self):
        parser = SummaryLineParser()
        self.assertEqual(parser.matchLine(self.headerLine1), SummaryLineMatch.HEADER)
        self.assertEqual(parser.matchLine(self.countsLine3), SummaryLineMatch.PARAGRAPH_COUNTS)

        self.assertEqual(parser.headerText, "It's going to be about movement, gesture, and voice") # ((ATRDIWI))
        self.assertEqual(parser.level, 6)
        self.assertEqual(parser.transcriptName, "0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1")
        self.assertEqual(parser.pageNr, 1)
        self.assertEqual(parser.paragraphNr, 3)
        self.assertEqual(parser.shownLinkText, "1-3")
        self.assertEqual(parser.blockId, "1-3")
        self.assertEqual(parser.canonicalParagraphCounts(), self.countsLine3)


    def test_SummaryLineParser4(self):
        parser = SummaryLineParser()
        self.assertEqual(parser.matchLine(self.headerLine2), SummaryLineMatch.HEADER)
        self.assertEqual(parser.matchLine(self.keywordsLine4), SummaryLineMatch.INDEX_COUNTS)



# *********************************************
# TranscriptSummaryPage
# *********************************************

class Test_TranscriptSummaryPage(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.haf = HAFEnvironment(HAF_YAML_TESTING)
        cls.transcriptIndex = TranscriptIndex(RB_YAML_TESTING)
        cls.transcriptModel = TranscriptModel(cls.transcriptIndex)        
        return super().setUpClass()

    transcriptName = "0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1"

    def test_updateWithOldTargetType(self):
        sfnTranscriptMd = self.haf.getTranscriptFilename(self.transcriptName)
        transcriptPage = TranscriptPage(sfnTranscriptMd)
        transcriptPage.applySpacy(self.transcriptModel)
    
        sfnSummaryMd = self.haf.getSummaryFilename(self.transcriptName)
        summaryPage = TranscriptSummaryPage(sfnSummaryMd)
    
        summaryPage.update(transcriptPage, targetType='#^')
        summaryPage.save("tmp/tmp.md")
        self.assertTrue(filecmp.cmp("tmp/tmp.md", sfnSummaryMd))
        self.assertTrue(filecmp.cmp("tmp/tmp.md", "testing/data/Test_TranscriptSummaryPage.test_updateWithOldTargetType.md"))


    def test_updateWithNewTargetType(self):
        sfnTranscriptMd = self.haf.getTranscriptFilename(self.transcriptName)
        transcriptPage = TranscriptPage(sfnTranscriptMd)
        transcriptPage.applySpacy(self.transcriptModel)
    
        sfnSummaryMd = self.haf.getSummaryFilename(self.transcriptName)
        summaryPage = TranscriptSummaryPage(sfnSummaryMd)
    
        summaryPage.update(transcriptPage, targetType='#')
        summaryPage.save("tmp/tmp.md")
        #self.assertTrue(filecmp.cmp("tmp/tmp.md", sfnSummaryMd))
        self.assertTrue(filecmp.cmp("tmp/tmp.md", "testing/data/Test_TranscriptSummaryPage.test_updateWithNewTargetType.md"))


    def test_createNew(self):
        talkName = determineTalkname(self.transcriptName)
        createNewSummaryPage(talkName, self.haf, self.transcriptModel, "tmp/tmp.md")
        self.assertTrue(filecmp.cmp("tmp/tmp.md", "testing/data/Test_TranscriptSummaryPage.test_createNew.md"))


    def test_collectMissingParagraphHeaderTexts(self):
        talkName = "From Insight to Love"
        sfnSummaryMd = self.haf.getSummaryFilename(talkName)
        summaryPage = TranscriptSummaryPage(sfnSummaryMd)
        self.assertEqual(summaryPage.collectMissingParagraphHeaderTexts(), 2)


if __name__ == "__main__":
    unittest.main()
