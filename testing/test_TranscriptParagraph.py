#!/usr/bin/env python3

from TranscriptIndex import TranscriptIndex
from TranscriptModel import TranscriptModel
from TranscriptParagraph import TranscriptParagraph, applySpacyToParagraphs
from testing import MyTestClass
from consts import RB_YAML_TESTING
import unittest

# *********************************************
# paragraphs
# *********************************************

class Test_Paragraph(MyTestClass):

    @classmethod
    def setUpClass(cls) -> None:
        cls.transcriptIndex = TranscriptIndex(RB_YAML_TESTING)
        cls.transcriptModel = TranscriptModel(cls.transcriptIndex)        
        return super().setUpClass()


    def defaultText(self):
        return "It's about preliminaries, if you know that word that's used in Tibetan Buddhist circles, preliminary excercises."

    def expectedText(self):
        return "It's about [[preliminaries]], if you know that word that's used in [[Tibetan Buddhism|Tibetan Buddhist]] circles, preliminary excercises."

    def test_CreateFromParagraphOnPage(self):
        paragraphOnPage = self.defaultText() + " ^5-3"
        paragraph = TranscriptParagraph.fromParagraph(paragraphOnPage)
        self.assertEqual(paragraph.pageNr, 5)
        self.assertEqual(paragraph.paragraphNr, 3)


    def test_ReplaceIndexEntries(self):
        pageNr = 10
        paragraphNr = 4
        paragraph = TranscriptParagraph( pageNr, paragraphNr, self.defaultText())
        self.assertEquals(paragraph.pageNr, pageNr)
        self.assertEquals(paragraph.paragraphNr, paragraphNr)

        # applying Spacy inserts links to index entries
        paragraph.applySpacy(self.transcriptModel)
        self.assertEqual(paragraph.text, self.expectedText())

        # reapply repeatedly returns the same result like the first applying of Spacy
        paragraph.applySpacy(self.transcriptModel)
        self.assertEqual(paragraph.text, self.expectedText())


    def test_ReplaceIndexEntriesWithFootnotes(self):
        textWithFootnotes = self.defaultText().replace(",", "^[footnote in middle]") + "^[footnote at end]"
        paragraph = TranscriptParagraph( 0, 0, textWithFootnotes)
        paragraph.applySpacy(self.transcriptModel)
        self.assertEqual(paragraph.text, self.expectedText().replace(",", "^[footnote in middle]") + "^[footnote at end]")


    def test_CheckTermCounts(self):
        paragraph = TranscriptParagraph( 0, 0, self.defaultText())
        paragraph.applySpacy(self.transcriptModel)
        self.assertEquals(repr(paragraph.shownLinks), "['Preliminaries', 'Tibetan Buddhism']")
        self.assertEquals(paragraph.termCounts['Preliminaries'], 2)
        self.assertEquals(paragraph.termCounts['Tibetan Buddhism'], 1)


if __name__ == "__main__":
    unittest.main()
