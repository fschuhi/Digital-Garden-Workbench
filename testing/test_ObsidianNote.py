#!/usr/bin/env python3

import unittest
from HAFEnvironment import HAFEnvironment
from ObsidianNote import ObsidianNoteType, ObsidianNote
from consts import HAF_YAML

# *********************************************
# Publishing
# *********************************************

class Test_ObsidianNote(unittest.TestCase):

    haf = HAFEnvironment(HAF_YAML)

    def createNote(self, talkName):
        md = self.haf.getSummaryFilename(talkName)
        return ObsidianNote(ObsidianNoteType.SUMMARY, md)


    def test_yaml(self):
        note = self.createNote("Samadhi in Metta Practice")        
        self.assertDictEqual(note.yaml, {'obsidianUIMode': 'preview'})
        note.yaml['bla'] = 'heul'
        self.assertDictEqual(note.yaml, {'bla': 'heul', 'obsidianUIMode': 'preview'})


    def test_changeLine(self):
        note = self.createNote("Samadhi in Metta Practice")

        lines = note.collectTextLines()
        lines[4] = "asdfasdf"
        note.assignTextLines(lines)

        lines = note.collectTextLines()
        self.assertEqual(lines[4], "asdfasdf")


    def test_markdownSnippets(self):
        note = self.createNote("Samadhi in Metta Practice")

        snippets = note.collectMarkdownLines()

        assert snippets.asText() == note.text

        res = snippets.searchSection("^#+ Index", "^#+ Paragraphs")
        assert res is not None
        (start, end, matchFrom, matchTo) = res
        self.assertEqual(matchFrom.group(0), "## Index")
        self.assertEqual(matchTo.group(0), "## Paragraphs")

        matchedSnippets = snippets[start:end]
        self.assertEqual(matchedSnippets[0].text, "## Index")
        self.assertNotEqual(matchedSnippets[-1].text, "## Paragraphs")

        (start, end, matchFrom, matchTo) = snippets.searchSection("^#+ asdf", "^#+ wert")
        self.assertIsNone(start)



if __name__ == "__main__":
    unittest.main()