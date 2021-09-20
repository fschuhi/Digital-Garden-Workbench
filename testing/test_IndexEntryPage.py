#!/usr/bin/env python3

from HAFScripts import addMissingCitations
import unittest
from testing import MyTestClass
from consts import HAF_YAML_TESTING, RB_YAML_TESTING

from TranscriptIndex import TranscriptIndex
from TranscriptModel import TranscriptModel
from IndexEntryPage import IndexEntryPage, IndexEntryPageHeaderParser, CitationParagraphParser, canonicalHeaderLineFromParams
from HAFEnvironment import HAFEnvironment
import logging
import os

# *********************************************
# IndexEntryPageHeadePParser
# *********************************************

class Test_IndexEntryPageHeaders(MyTestClass):

    def test_canonicalHeaderLine(self):
        self.assertEqual(canonicalHeaderLineFromParams(None, "wert", "asdf", None, None, None), "###### wert [[asdf|(Transcript)]]")

    def test_IndexEntryPageHeaderParser1(self):        
        headerLine = "###### Vajra Music - Preliminaries - Part 1 [[0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1|(Transcript)]] 🟢 ^some-block-pointer"
        parser = IndexEntryPageHeaderParser(headerLine)
        self.assertEqual(parser.headerText1, "Vajra Music - Preliminaries - Part 1")
        self.assertEqual(parser.level, 6)
        self.assertEqual(parser.transcriptName, "0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1")
        self.assertEqual(parser.headerText2, "🟢")
        self.assertEqual(parser.trailingBlockId, "some-block-pointer")
        self.assertEqual(parser.canonicalHeaderLine(), headerLine)

    def test_IndexEntryPageHeaderParser2(self):        
        headerLine = "###### Vajra Music - Preliminaries - Part 1 [[0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1|(Transcript)]] ^some-block-pointer"
        parser = IndexEntryPageHeaderParser(headerLine)
        self.assertEqual(parser.headerText1, "Vajra Music - Preliminaries - Part 1")
        self.assertEqual(parser.level, 6)
        self.assertEqual(parser.transcriptName, "0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1")
        self.assertEqual(parser.headerText2, None)
        self.assertEqual(parser.trailingBlockId, "some-block-pointer")
        self.assertEqual(parser.canonicalHeaderLine(), headerLine)

    def test_IndexEntryPageHeaderParser3(self):        
        headerLine = "###### [[0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1|Vajra Music: Prelims Part 1 (Transcript)]]"
        parser = IndexEntryPageHeaderParser(headerLine)
        self.assertEqual(parser.headerText1, None)
        self.assertEqual(parser.level, 6)
        self.assertEqual(parser.transcriptName, "0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1")
        self.assertEqual(parser.linkText, "Vajra Music: Prelims Part 1")
        self.assertEqual(parser.headerText2, None)
        self.assertEqual(parser.trailingBlockId, None)
        self.assertEqual(parser.canonicalHeaderLine(), headerLine)


# *********************************************
# CitationParagraphParser
# *********************************************

class Test_CitationParagraphParser(MyTestClass):

    def test_CitationParagraphParser(self):        
        citationParagraph  = "> So for the one who is blessed, it's a task in sensitivity. <p/>_Vajra Music: Preliminaries Part 3, [[0303 Preliminaries Regarding Voice, Movement, and Gesture - Part 3#^12-2|12-2]]_"
        parser = CitationParagraphParser(citationParagraph)
        self.assertEqual(parser.sourceStart, "<p/>_")
        self.assertEqual(parser.sourceText, "Vajra Music: Preliminaries Part 3, ")
        self.assertEqual(parser.transcriptName, "0303 Preliminaries Regarding Voice, Movement, and Gesture - Part 3")
        self.assertEqual(parser.blockId, "12-2")
        self.assertEqual(parser.pageNr, 12)
        self.assertEqual(parser.paragraphNr, 2)
        self.assertEqual(parser.sourceEnd, "_")
        self.assertEqual(parser.linkTarget, "0303 Preliminaries Regarding Voice, Movement, and Gesture - Part 3#^12-2")


# *********************************************
# IndexEntryPage
# *********************************************

class Test_IndexEntryPage(MyTestClass):

    @classmethod
    def setUpClass(cls) -> None:
        cls.haf = HAFEnvironment(HAF_YAML_TESTING)
        cls.transcriptIndex = TranscriptIndex(RB_YAML_TESTING)
        cls.transcriptModel = TranscriptModel(cls.transcriptIndex)        
        return super().setUpClass()


    def test_determineTags(self):
        indexEntryPage = IndexEntryPage(self.haf.dirIndexEntries, 'Inertia')
        indexEntryPage.loadIndexEntryMd()
        tags = indexEntryPage.determineTags()
        self.assertListEqual(tags, ['IndexEntry', 'Robology'])


    def test_determineYamlSection(self):
        indexEntryPage = IndexEntryPage(self.haf.dirIndexEntries, 'Inertia')
        indexEntryPage.loadIndexEntryMd()
        self.assertEquals(indexEntryPage.determineYamlSection(), 'Robology')


    def test_extractYaml(self):
        indexEntryPage = IndexEntryPage(self.haf.dirIndexEntries, 'Energy Body')
        indexEntryPage.loadIndexEntryMd()
        yamlDict = indexEntryPage.extractYaml()
        self.assertTrue('ignore-transcript-for-crossref' in yamlDict)
        ignored = yamlDict['ignore-transcript-for-crossref']
        self.assertListEqual(ignored, ['The Way of Non-Clinging', 'Preliminaries Regarding Voice, Movement, and Gesture - Part 5', '0126 Eros Unfettered Part 4'])


if __name__ == "__main__":
    unittest.main()
