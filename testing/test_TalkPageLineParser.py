#!/usr/bin/env python3

from types import SimpleNamespace
from TalkPageLineParser import TalkPageLineMatch, TalkPageLineParser
import unittest

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


class Test_TalkPageLineParser(unittest.TestCase):
    
    headerLine1 = "###### It's going to be about movement, gesture, and voice"
    countsLine1a = "**[[0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1#^1-3|1-3]]**: _[[Preliminaries]], [[Embodiment]] (2)_"
    countsLine1b = "**[[0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1#1-3|1-3]]**: _[[Preliminaries]], [[Embodiment]] (2)_"
    countsLine2 = "[[0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1#1-3|1-3]]"
    countsLine3 = "<span class=\"counts\">**[[0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1#1-3|1-3]]**: _[[Preliminaries]], [[Embodiment]] (2)_</span>"

    headerLine2 = "### Index"
    keywordsLine4 = "<span class=\"counts\">_[[Compassion]] (3) · [[Dukkha]] (2) · [[Contraction]] (2) · [[The Self]]_</span>"

    def test_TalkPageLineParser1a(self):
        parser = TalkPageLineParser()
        self.assertEqual(parser.matchText(self.headerLine1), TalkPageLineMatch.DESCRIPTION)
        self.assertEqual(parser.matchText(self.countsLine1a), TalkPageLineMatch.PARAGRAPH_COUNTS)

        self.assertEqual(parser.headerText, "It's going to be about movement, gesture, and voice") # ((ATRDIWI))
        self.assertEqual(parser.level, 6)
        self.assertEqual(parser.transcriptName, "0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1")
        self.assertEqual(parser.pageNr, 1)
        self.assertEqual(parser.paragraphNr, 3)
        self.assertEqual(parser.shownLinkText, "1-3")
        self.assertEqual(parser.blockId, "1-3")
        self.assertEqual(parser.canonicalParagraphCounts(targetType='#^'), self.countsLine1a)


    def test_TalkPageLineParser1b(self):
        parser = TalkPageLineParser()
        self.assertEqual(parser.matchText(self.headerLine1), TalkPageLineMatch.DESCRIPTION)
        self.assertEqual(parser.matchText(self.countsLine1a), TalkPageLineMatch.PARAGRAPH_COUNTS)
        self.assertEqual(parser.canonicalParagraphCounts(targetType='#'), self.countsLine1b)


    def test_TalkPageLineParser2(self):
        parser = TalkPageLineParser()
        self.assertEqual(parser.matchText(self.countsLine2), TalkPageLineMatch.PARAGRAPH_COUNTS)

        self.assertEqual(parser.transcriptName, "0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1")
        self.assertEqual(parser.pageNr, 1)
        self.assertEqual(parser.paragraphNr, 3)
        self.assertEqual(parser.shownLinkText, "1-3")
        self.assertEqual(parser.blockId, "1-3")
        self.assertEqual(parser.canonicalParagraphCounts(), self.countsLine2)


    def test_TalkPageLineParser3(self):
        parser = TalkPageLineParser()
        self.assertEqual(parser.matchText(self.headerLine1), TalkPageLineMatch.DESCRIPTION)
        self.assertEqual(parser.matchText(self.countsLine3), TalkPageLineMatch.PARAGRAPH_COUNTS)

        self.assertEqual(parser.headerText, "It's going to be about movement, gesture, and voice") # ((ATRDIWI))
        self.assertEqual(parser.level, 6)
        self.assertEqual(parser.transcriptName, "0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1")
        self.assertEqual(parser.pageNr, 1)
        self.assertEqual(parser.paragraphNr, 3)
        self.assertEqual(parser.shownLinkText, "1-3")
        self.assertEqual(parser.blockId, "1-3")
        self.assertEqual(parser.canonicalParagraphCounts(), self.countsLine3)


    def test_TalkPageLineParser4(self):
        parser = TalkPageLineParser()

        # must be either 5 or 6 '#'
        self.assertEqual(parser.matchText(self.headerLine2), TalkPageLineMatch.HEADER)
        
        self.assertEqual(parser.matchText(self.keywordsLine4), TalkPageLineMatch.INDEX_COUNTS)



if __name__ == "__main__":
    unittest.main()
