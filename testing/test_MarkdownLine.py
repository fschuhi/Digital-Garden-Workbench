#!/usr/bin/env python3

from TranscriptModel import TranscriptModel
from TranscriptIndex import TranscriptIndex
from util import convertMatchedObsidianLink, loadStringFromTextFile, parseParagraph, saveLinesToTextFile, saveStringToTextFile, searchObsidianLink
from HAFEnvironment import HAFEnvironment
from MarkdownLine import MarkdownLine
from consts import HAF_YAML, HAF_YAML_TESTING, RB_YAML_TESTING
import unittest

import filecmp

# *********************************************
# MarkdownSnippet
# *********************************************

class Test_MarkdownSnippet(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.transcriptIndex = TranscriptIndex(RB_YAML_TESTING)
        cls.transcriptModel = TranscriptModel(cls.transcriptIndex)        
        return super().setUpClass()


    def test_searchMarkupLink(self):
        match = searchObsidianLink("asdf [[Link1]] wert und [[weiterer Link]]")
        self.assertEqual(match.group('note'), "Link1")

        match = searchObsidianLink("ein [[Link2#header]] und [[weiterer Link]]")
        self.assertEqual(match.group('note'), "Link2")
        self.assertEqual(match.group('target'), "#header")

        match = searchObsidianLink("ein [[Link3#header|bla]] und [[weiterer Link]]")
        self.assertEqual(match.group('note'), "Link3")
        self.assertEqual(match.group('target'), "#header")
        self.assertEqual(match.group('shown'), "bla")

        match = searchObsidianLink("ein [[Link4#^reier|reier]] und [[weiterer Link]]")
        self.assertEqual(match.group('note'), "Link4")
        self.assertEqual(match.group('target'), "#^reier")
        self.assertEqual(match.group('blockid'), "reier")
        self.assertEqual(match.group('shown'), "reier")


    def test_collectLinkMatches(self):
        ms = MarkdownLine("Das ist ein [[Link]] und noch ein [[Link]] das war es.")
        spans = [m.span() for m in ms.collectLinkMatches()]
        self.assertListEqual(spans, [(12,20), (34,42)])


    def test_collectLinkSpans(self):
        ms = MarkdownLine("Das ist ein [[Link]] und noch ein [[Link]] das war es.")
        spans = ms.collectLinkSpans()
        self.assertListEqual(spans, [(12,20), (34,42)])


    def test_removeFootnotes(self):
        originalText = "Das ist ein [[Link]] und noch ein [[Link]] das war es."
        ms = MarkdownLine(originalText)
        ms.removeFootnotes()
        self.assertEqual(ms.text, originalText)
        self.assertEqual(ms.footnotes, [])

        ms = MarkdownLine("Das ist ein [[Link]] hier^[ist eine Footnote] noch ein [[Link]] das war es.")
        ms.removeFootnotes()
        self.assertEqual(ms.text, "Das ist ein [[Link]] hier noch ein [[Link]] das war es.")
        self.assertEqual(ms.footnotes, [('^[ist eine Footnote]', 25)])


    def test_removeAllLinks(self):
        originalText = "Das ist ein [[Link]] hier^[ist eine Footnote] noch ein [[Link]] das war es."

        ms = MarkdownLine(originalText)
        ms.removeAllLinks()
        self.assertEqual(ms.text, "Das ist ein Link hier^[ist eine Footnote] noch ein Link das war es.")

        ms = MarkdownLine(originalText)
        ms.removeFootnotes()
        self.assertEqual(ms.footnotes, [('^[ist eine Footnote]', 25)])
        ms.removeAllLinks()
        self.assertEqual(ms.text, "Das ist ein Link hier noch ein Link das war es.")
        self.assertEqual(ms.footnotes, [('^[ist eine Footnote]', 21)])

        ms.restoreFootnotes()
        self.assertEqual(ms.text, "Das ist ein Link hier^[ist eine Footnote] noch ein Link das war es.")


    def test_cutSpanWithoutFootnotes(self):
        ms = MarkdownLine("Das ist ein [[Link1]] und noch ein [[Link2]] das war es.")
        spans = ms.collectLinkSpans()
        self.assertListEqual(spans, [(12,21), (35,44)])

        match = ms.searchMarkupLink()
        self.assertIsNotNone(match)
        cutText1 = ms.cutSpan(match.span())
        self.assertEqual(cutText1, "[[Link1]]")
        self.assertEqual(ms.text, "Das ist ein  und noch ein [[Link2]] das war es.")

        match = ms.searchMarkupLink()
        self.assertIsNotNone(match)
        cutText2 = ms.cutSpan(match.span())
        self.assertEqual(cutText2, "[[Link2]]")
        self.assertEqual(ms.text, "Das ist ein  und noch ein  das war es.")


    def test_cutSpanWithFootnotes(self):
        originalText = "Das ist ein [[Link1]] hier^[ist eine Footnote] noch ein [[Link2]] das war es."
        ms = MarkdownLine(originalText)
        ms.removeFootnotes()
        self.assertEqual(ms.text, "Das ist ein [[Link1]] hier noch ein [[Link2]] das war es.")
        self.assertEqual(ms.footnotes, [('^[ist eine Footnote]', 26)])

        cutText1 = ms.cutSpan(ms.searchMarkupLink().span())
        cutText2 = ms.cutSpan(ms.searchMarkupLink().span())
        self.assertEqual(ms.text, "Das ist ein  hier noch ein  das war es.")

        ms.restoreFootnotes()
        self.assertEqual(ms.text, "Das ist ein  hier^[ist eine Footnote] noch ein  das war es.")


    def test_replaceLinksWithoutFootnote(self):
        ms = MarkdownLine("Das ist ein [[Link1]][[Link2]] das war es.")
        ms.replaceLinks(lambda match: f"/{match.group('complete')}/")
        self.assertEqual(ms.text, "Das ist ein /Link1//Link2/ das war es.")


    def test_replaceLinksWithFootnote(self):
        root = "https://publish.obsidian.md/rob-burbea/"

        ms = MarkdownLine("Das ist ein [[Link1]] hier^[ist eine Footnote] noch ein [[Link2]] das war es.")
        ms.replaceLinks(lambda match: f"/{match.group('note')}/")
        self.assertEqual(ms.text, "Das ist ein /Link1/ hier^[ist eine Footnote] noch ein /Link2/ das war es.")

        haf = HAFEnvironment(HAF_YAML)
        links = []
        ms = MarkdownLine("Das ist ein [[0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1#^1-1|1-1]] hier^[ist eine Footnote] Link.")
        ms.replaceLinks(lambda match: f"{convertMatchedObsidianLink(match, root)}")
        links.append(ms.text)

        ms = MarkdownLine("[[Digital Gardens#Shannon]]")
        ms.replaceLinks(lambda match: f"{convertMatchedObsidianLink(match, root)}")
        links.append(ms.text)

        ms = MarkdownLine("[[Digital Gardens#Magic Dust]]")
        ms.replaceLinks(lambda match: f"{convertMatchedObsidianLink(match, root)}")
        links.append(ms.text)

        saveLinesToTextFile("tmp/ms.txt", links)
        self.assertTrue(filecmp.cmp("tmp/ms.txt", "testing/data/Test_MarkdownSnippet.test_replaceLinksWithFootnote.txt"))


    def test_convertMatchedObsidianLink(self):
        text = loadStringFromTextFile("testing/data/Test_MarkdownSnippet.test_convertMatchedObsidianLink.md")
        ms = MarkdownLine(text)
        root = "https://publish.obsidian.md/rob-burbea/"
        ms.replaceLinks(lambda match: f"{convertMatchedObsidianLink(match, root)}")
        saveStringToTextFile("tmp/tmp.md", ms.text)
        self.assertTrue(filecmp.cmp("tmp/tmp.md", "testing/data/Test_MarkdownSnippet.test_convertMatchedObsidianLink_converted.md"))


    def test_replaceLinksInOneTranscript(self):
        haf = HAFEnvironment(HAF_YAML_TESTING)
        talkName = "0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1"        
        sfnTranscriptMd = haf.getTranscriptFilename(talkName)
        text = loadStringFromTextFile(sfnTranscriptMd)
        ms = MarkdownLine(text)
        root = "https://publish.obsidian.md/rob-burbea/"
        ms.replaceLinks(lambda match: f"{convertMatchedObsidianLink(match, root)}")
        saveStringToTextFile("tmp/tmp.md", ms.text)
        self.assertTrue(filecmp.cmp("tmp/tmp.md", "testing/data/Test_MarkdownSnippet.test_replaceLinksInOneTranscript.md"))

    def test_tags(self):
        haf = HAFEnvironment(HAF_YAML_TESTING)
        talkName = "0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1"        
        sfnTranscriptMd = haf.getTranscriptFilename(talkName)
        text = loadStringFromTextFile(sfnTranscriptMd)
        ms = MarkdownLine(text)
        self.assertListEqual(ms.collectTags(), ['Transcript'])


    # originally in test_TranscriptParagraph

    def defaultText(self):
        return "It's about preliminaries, if you know that word that's used in Tibetan Buddhist circles, preliminary excercises."

    def expectedText(self):
        return "It's about [[preliminaries]], if you know that word that's used in [[Tibetan Buddhism|Tibetan Buddhist]] circles, preliminary excercises."

    def test_parseParagraph(self):
        paragraphOnPage = self.defaultText() + " ^5-3"
        pageNr, paragraphNr, paragraphText = parseParagraph(paragraphOnPage)
        self.assertEqual(pageNr, 5)
        self.assertEqual(paragraphNr, 3)


    def test_ReplaceIndexEntries(self):
        # applying Spacy inserts links to index entries
        markdown = MarkdownLine(self.defaultText())
        markdown.applySpacy(self.transcriptModel)
        self.assertEqual(markdown.text, self.expectedText())


    def test_ReplaceIndexEntriesWithFootnotes(self):
        textWithFootnotes = self.defaultText().replace(",", "^[footnote in middle]") + "^[footnote at end]"
        markdown = MarkdownLine(textWithFootnotes)
        markdown.applySpacy(self.transcriptModel)
        self.assertEqual(markdown.text, self.expectedText().replace(",", "^[footnote in middle]") + "^[footnote at end]")


    def test_CheckTermCounts(self):
        markdown = MarkdownLine(self.defaultText())
        markdown.applySpacy(self.transcriptModel)
        self.assertEqual(repr(markdown.shownLinks), "['Preliminaries', 'Tibetan Buddhism']")
        self.assertEqual(markdown.termCounts['Preliminaries'], 2)
        self.assertEqual(markdown.termCounts['Tibetan Buddhism'], 1)



if __name__ == "__main__":
    unittest.main()