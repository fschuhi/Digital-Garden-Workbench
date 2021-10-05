#!/usr/bin/env python3

import unittest
from HAFEnvironment import HAFEnvironment
from ObsidianNote import ObsidianNoteType, ObsidianNote
from consts import HAF_YAML, HAF_YAML_TESTING

# *********************************************
# Publishing
# *********************************************

class Test_ObsidianNote(unittest.TestCase):

    def getNote(self, haf, talkName):
        md = haf.getSummaryFilename(talkName)
        return ObsidianNote(ObsidianNoteType.SUMMARY, md)


    def test_yaml(self):
        haf = HAFEnvironment(HAF_YAML_TESTING)
        note = self.getNote(haf, "Samadhi in Metta Practice")        
        self.assertDictEqual(note.yaml, {'obsidianUIMode': 'preview'})
        note.yaml['bla'] = 'heul'
        self.assertDictEqual(note.yaml, {'bla': 'heul', 'obsidianUIMode': 'preview'})


    def test_changeLine(self):
        haf = HAFEnvironment(HAF_YAML_TESTING)
        note = self.getNote(haf, "Samadhi in Metta Practice")

        lines = note.collectTextLines()
        lines[4] = "asdfasdf"
        note.assignTextLines(lines)

        lines = note.collectTextLines()
        self.assertEqual(lines[4], "asdfasdf")


    def test_markdownSnippets(self):
        haf = HAFEnvironment(HAF_YAML)
        note = self.getNote(haf, "Samadhi in Metta Practice")

        snippets = note.collectMarkdownLines()

        assert snippets.asText() == note.text

        res = snippets.searchSpan("^#+ Index", "^#+ Paragraphs")
        assert res is not None
        (start, end) = res
        self.assertEqual(snippets[start].text, "## Index")
        self.assertEqual(snippets[end].text, "## Paragraphs")

        matchedSnippets = snippets[start:end]
        self.assertEqual(matchedSnippets[0].text, "## Index")
        self.assertNotEqual(matchedSnippets[-1].text, "## Paragraphs")

        (start, end) = snippets.searchSpan("^#+ asdf", "^#+ wert")
        self.assertIsNone(start)

        res = snippets.searchSpan("^#+ Index", "^#+ blabla", allowEOF=True)
        assert res is not None
        (start, end) = res
        self.assertEqual(snippets[start].text, "## Index")
        self.assertEqual(end, len(snippets))

        (start, end) = snippets.searchSpan("^#+ Index", "^#+ blabla", allowEOF=False)
        self.assertIsNone(start)



if __name__ == "__main__":
    unittest.main()