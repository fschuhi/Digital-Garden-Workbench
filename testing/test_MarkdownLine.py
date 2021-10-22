#!/usr/bin/env python3

from TranscriptModel import TranscriptModel
from TranscriptIndex import TranscriptIndex
from util import *
from HAFEnvironment import HAFEnvironment
from MarkdownLine import MarkdownLine, SpacyMode
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


    def test_searchMarkdownLink(self):
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
        markdown = MarkdownLine("Das ist ein [[Link]] und noch ein [[Link]] das war es.")
        spans = [m.span() for m in markdown.collectLinkMatches()]
        self.assertListEqual(spans, [(12,20), (34,42)])


    def test_collectLinkSpans(self):
        markdown = MarkdownLine("Das ist ein [[Link]] und noch ein [[Link]] das war es.")
        spans = markdown.collectLinkSpans()
        self.assertListEqual(spans, [(12,20), (34,42)])


    def test_removeFootnotes(self):
        originalText = "Das ist ein [[Link]] und noch ein [[Link]] das war es."
        markdown = MarkdownLine(originalText)
        markdown.removeFootnotes()
        self.assertEqual(markdown.text, originalText)
        self.assertEqual(markdown.footnotes, [])

        markdown = MarkdownLine("Das ist ein [[Link]] hier^[ist eine Footnote] noch ein [[Link]] das war es.")
        markdown.removeFootnotes()
        self.assertEqual(markdown.text, "Das ist ein [[Link]] hier noch ein [[Link]] das war es.")
        self.assertEqual(markdown.footnotes, [('^[ist eine Footnote]', 25)])


    def test_removeAllLinks(self):
        originalText = "Das ist ein [[Link]] hier^[ist eine Footnote] noch ein [[Link]] das war es."

        markdown = MarkdownLine(originalText)
        markdown.removeAllLinks()
        self.assertEqual(markdown.text, "Das ist ein Link hier^[ist eine Footnote] noch ein Link das war es.")

        markdown = MarkdownLine(originalText)
        markdown.removeFootnotes()
        self.assertEqual(markdown.footnotes, [('^[ist eine Footnote]', 25)])
        markdown.removeAllLinks()
        self.assertEqual(markdown.text, "Das ist ein Link hier noch ein Link das war es.")
        self.assertEqual(markdown.footnotes, [('^[ist eine Footnote]', 21)])

        markdown.restoreFootnotes()
        self.assertEqual(markdown.text, "Das ist ein Link hier^[ist eine Footnote] noch ein Link das war es.")


    def test_cutSpanWithoutFootnotes(self):
        markdown = MarkdownLine("Das ist ein [[Link1]] und noch ein [[Link2]] das war es.")
        spans = markdown.collectLinkSpans()
        self.assertListEqual(spans, [(12,21), (35,44)])

        match = markdown.searchMarkdownLink()
        self.assertIsNotNone(match)
        cutText1 = markdown.cutSpan(match.span())
        self.assertEqual(cutText1, "[[Link1]]")
        self.assertEqual(markdown.text, "Das ist ein  und noch ein [[Link2]] das war es.")

        match = markdown.searchMarkdownLink()
        self.assertIsNotNone(match)
        cutText2 = markdown.cutSpan(match.span())
        self.assertEqual(cutText2, "[[Link2]]")
        self.assertEqual(markdown.text, "Das ist ein  und noch ein  das war es.")


    def test_cutSpanWithFootnotes(self):
        originalText = "Das ist ein [[Link1]] hier^[ist eine Footnote] noch ein [[Link2]] das war es."
        markdown = MarkdownLine(originalText)
        markdown.removeFootnotes()
        self.assertEqual(markdown.text, "Das ist ein [[Link1]] hier noch ein [[Link2]] das war es.")
        self.assertEqual(markdown.footnotes, [('^[ist eine Footnote]', 26)])

        cutText1 = markdown.cutSpan(markdown.searchMarkdownLink().span())
        cutText2 = markdown.cutSpan(markdown.searchMarkdownLink().span())
        self.assertEqual(markdown.text, "Das ist ein  hier noch ein  das war es.")

        markdown.restoreFootnotes()
        self.assertEqual(markdown.text, "Das ist ein  hier^[ist eine Footnote] noch ein  das war es.")


    def test_replaceLinksWithoutFootnote(self):
        markdown = MarkdownLine("Das ist ein [[Link1]][[Link2]] das war es.")
        markdown.replaceLinks(lambda match: f"/{match.group('complete')}/")
        self.assertEqual(markdown.text, "Das ist ein /Link1//Link2/ das war es.")


    def test_replaceLinksWithFootnote(self):
        root = "https://publish.obsidian.md/rob-burbea/"

        markdown = MarkdownLine("Das ist ein [[Link1]] hier^[ist eine Footnote] noch ein [[Link2]] das war es.")
        markdown.replaceLinks(lambda match: f"/{match.group('note')}/")
        self.assertEqual(markdown.text, "Das ist ein /Link1/ hier^[ist eine Footnote] noch ein /Link2/ das war es.")

        haf = HAFEnvironment(HAF_YAML)
        links = []
        markdown = MarkdownLine("Das ist ein [[0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1#^1-1|1-1]] hier^[ist eine Footnote] Link.")
        markdown.replaceLinks(lambda match: f"{convertMatchedObsidianLink(match, root)}")
        links.append(markdown.text)

        markdown = MarkdownLine("[[Digital Gardens#Shannon]]")
        markdown.replaceLinks(lambda match: f"{convertMatchedObsidianLink(match, root)}")
        links.append(markdown.text)

        markdown = MarkdownLine("[[Digital Gardens#Magic Dust]]")
        markdown.replaceLinks(lambda match: f"{convertMatchedObsidianLink(match, root)}")
        links.append(markdown.text)

        saveLinesToTextFile("tmp/ms.txt", links)
        self.assertTrue(filecmp.cmp("tmp/ms.txt", "testing/data/Test_MarkdownSnippet.test_replaceLinksWithFootnote.txt"))


    def test_convertMatchedObsidianLink(self):
        text = loadStringFromTextFile("testing/data/Test_MarkdownSnippet.test_convertMatchedObsidianLink.md")
        markdown = MarkdownLine(text)
        root = "https://publish.obsidian.md/rob-burbea/"
        markdown.replaceLinks(lambda match: f"{convertMatchedObsidianLink(match, root)}")
        saveStringToTextFile("tmp/tmp.md", markdown.text)
        self.assertTrue(filecmp.cmp("tmp/tmp.md", "testing/data/Test_MarkdownSnippet.test_convertMatchedObsidianLink_converted.md"))


    def test_replaceLinksInOneTranscript(self):
        haf = HAFEnvironment(HAF_YAML_TESTING)
        talkName = "0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1"        
        sfnTranscriptMd = haf.getTranscriptFilename(talkName)
        text = loadStringFromTextFile(sfnTranscriptMd)
        markdown = MarkdownLine(text)
        root = "https://publish.obsidian.md/rob-burbea/"
        markdown.replaceLinks(lambda match: f"{convertMatchedObsidianLink(match, root)}")
        saveStringToTextFile("tmp/tmp.md", markdown.text)
        self.assertTrue(filecmp.cmp("tmp/tmp.md", "testing/data/Test_MarkdownSnippet.test_replaceLinksInOneTranscript.md"))

    def test_tags(self):
        haf = HAFEnvironment(HAF_YAML_TESTING)
        talkName = "0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1"        
        sfnTranscriptMd = haf.getTranscriptFilename(talkName)
        text = loadStringFromTextFile(sfnTranscriptMd)
        markdown = MarkdownLine(text)
        self.assertListEqual(markdown.collectTags(), ['Transcript'])


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
        markdown.applySpacy(self.transcriptModel, mode=SpacyMode.ONLY_FIRST, force=True)
        self.assertEqual(markdown.text, self.expectedText())


    def test_ReplaceIndexEntriesWithFootnotes(self):
        textWithFootnotes = self.defaultText().replace(",", "^[footnote in middle]") + "^[footnote at end]"
        markdown = MarkdownLine(textWithFootnotes)
        markdown.applySpacy(self.transcriptModel, mode=SpacyMode.ONLY_FIRST, force=True)
        self.assertEqual(markdown.text, self.expectedText().replace(",", "^[footnote in middle]") + "^[footnote at end]")


    def test_CheckTermCounts(self):
        markdown = MarkdownLine(self.defaultText())
        markdown.applySpacy(self.transcriptModel, mode=SpacyMode.ONLY_FIRST, force=True)
        self.assertEqual(repr(markdown.shownLinks), "['Preliminaries', 'Tibetan Buddhism']")
        self.assertEqual(markdown.termCounts['Preliminaries'], 2)
        self.assertEqual(markdown.termCounts['Tibetan Buddhism'], 1)


    # reindex problem

    def test_reindexProblem1(self):
        #print("")
        #print("0         1         2         3         4")
        #print("01234567890123456789012345678901234567890")
        bla = 'bla^[asdf] and heul^[3] bla [[desire]] in'
        #print(bla, '\n')

        ml = MarkdownLine(bla)

        ml.removeFootnotes()
        self.assertEqual(ml.text, "bla and heul bla [[desire]] in")
        self.assertListEqual(ml.footnotes, [('^[asdf]', 3), ('^[3]', 12)])

        ml.removeAllLinks()
        self.assertEqual(ml.text, "bla and heul bla desire in")
        self.assertListEqual(ml.footnotes, [('^[asdf]', 3), ('^[3]', 12)])

        ml.restoreFootnotes()
        self.assertEqual(ml.text, "bla^[asdf] and heul^[3] bla desire in")

    def test_reindexProblem2(self):
        bla = loadStringFromTextFile("testing/data/Test_MarkdownSnippet.test_reindexProblem2.md")
        ml = MarkdownLine(bla)
        ml.applySpacy(self.transcriptModel, mode=SpacyMode.ALL_LINKS, force=True)
        saveStringToTextFile("tmp/tmp.md", ml.text)
        # output = input
        self.assertTrue(filecmp.cmp("tmp/tmp.md", "testing/data/Test_MarkdownSnippet.test_reindexProblem2.md"))


if __name__ == "__main__":
    unittest.main()