#!/usr/bin/env python3

from util import *
from HAFEnvironment import HAFEnvironment
from TranscriptIndex import TranscriptIndex
from TranscriptModel import TranscriptModel
from TranscriptPage import TranscriptPage
from consts import HAF_YAML_TESTING, RB_YAML_TESTING
import filecmp
import unittest

# *********************************************
# TranscriptPage
# *********************************************

class Test_TranscriptPage(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.haf = HAFEnvironment(HAF_YAML_TESTING)
        cls.transcriptIndex = TranscriptIndex(RB_YAML_TESTING)
        cls.transcriptModel = TranscriptModel(cls.transcriptIndex)        

        cls.sfnTranscriptMd1 = cls.haf.getTranscriptFilename("Preliminaries Regarding Voice, Movement, and Gesture - Part 1")
        return super().setUpClass()


    def test_walrus(self):
        # https://realpython.com/python-walrus-operator/
        page = TranscriptPage(self.sfnTranscriptMd1)
        paragraphs = page.collectParagraphs()
        self.assertTrue(paragraphs[0][0] == 1 and paragraphs[0][1] == 1)
        self.assertTrue(paragraphs[1][0] == 1 and paragraphs[1][1] == 2)
        self.assertTrue(paragraphs[5][0] == 2 and paragraphs[5][1] == 1)


    def test_hasCorrectNumberOfParagraphs(self):
        page = TranscriptPage(self.sfnTranscriptMd1)
        paragraphs = [markdownLine for markdownLine in page.markdownLines if parseParagraph(markdownLine.text) != (None, None, None)]
        self.assertEqual(len(paragraphs), 85)


    def test_applySpacyToParagraphs(self):
        page = TranscriptPage(self.sfnTranscriptMd1)
        page.applySpacy(self.transcriptModel)
        #applySpacyToParagraphs(self.transcriptModel, page.paragraphs)
        page.save("tmp/tmp.md")
        import filecmp
        self.assertTrue(filecmp.cmp("tmp/tmp.md", self.sfnTranscriptMd1))
        self.assertTrue(filecmp.cmp("tmp/tmp.md", "testing/data/Test_TranscriptPage.test_transcript_1.md"))

    
    def test_findParagraph(self):
        page = TranscriptPage(self.sfnTranscriptMd1)
        markdownLine = page.findParagraph(4,4)
        self.assertTrue(markdownLine.text.startswith('**(1)**'))


    def test_collectTermLinks(self):
        page = TranscriptPage(self.sfnTranscriptMd1)
        page.applySpacy(self.transcriptModel)

        markdownLine = page.findParagraph(1,3)
        self.assertEqual(markdownLine.countTerm('History'), 0)
        
        markdownLine = page.findParagraph(1,4)
        self.assertEqual(markdownLine.countTerm('History'), 1)

        self.assertEqual(page.collectTermLinks('History'), \
            "[[0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1#1-4|1-4]] · "\
            "[[0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1#4-5|4-5]] · "\
            "[[0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1#13-2|13-2]] · "\
            "[[0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1#14-2|14-2]]")

        self.assertEqual(page.collectTermLinks('Devotion'), "[[0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1#2-3|2-3]] (2)")


    def test_saveToObsidian(self):
        page = TranscriptPage(self.sfnTranscriptMd1)
        page.applySpacy(self.transcriptModel)

        # check that TranscriptPage is "idempotent", i.e. exactly the same if saved w/o any changes from the version we loaded
        page.save("tmp/tmp.md")
        self.assertTrue(filecmp.cmp("tmp/tmp.md", self.sfnTranscriptMd1))


    def test_fromPlainMarkdownLines(self):
        sfnPlainMdInput = "testing/data/Test_TranscriptPage.test_fromPlainMarkdownLines.plain.md"

        # target is not exactly like the transcript in 2020 Vajra Music/Transcript, because _jhana_ is not deitalicised
        sfnPlainMdCompare = "testing/data/Test_TranscriptPage.test_fromPlainMarkdownLines.compare.md"

        lines = loadLinesFromTextFile(sfnPlainMdInput)
        page = TranscriptPage.fromPlainMarkdownLines(lines, 'SomeTalkname')
        page.save("tmp/tmp.md")        
        self.assertTrue(filecmp.cmp("tmp/tmp.md", sfnPlainMdCompare))



if __name__ == "__main__":
    unittest.main()
