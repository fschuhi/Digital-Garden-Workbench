#!/usr/bin/env python3

from TranscriptIndex import TranscriptIndex
from consts import RB_YAML_TESTING
import unittest

# *********************************************
# index entries
# *********************************************

class Test_IndexEntries(unittest.TestCase):

    def test_TranscriptIndex(self):
        transcriptIndex = TranscriptIndex(RB_YAML_TESTING)
        pages = transcriptIndex.pages
        self.assertTrue('Energy Body' in pages)
        self.assertFalse('Energy Bodya' in pages)

        # IMPORTANT 20.09.21 
        # In the production Obsidian vault there is no section "Authors" anymore, it's superseded by "Persons".
        # In the testing vault, we stick w/ Authors (for now)

        sections = transcriptIndex.sections
        self.assertTrue('Authors' in sections)
        self.assertTrue('Buddhology' in sections)
        self.assertTrue('Philosophy' in sections)
        self.assertTrue('Robology' in sections)
        self.assertTrue('Retreats' in sections)
        self.assertTrue('Talks' in sections)
        self.assertTrue('Practices' in sections)

        persons = transcriptIndex.sections['Authors']
        self.assertTrue('Henry Corbin' in persons)

        # print(transcriptIndex.sectionFromPage)

        self.assertEqual(transcriptIndex.sectionFromPage['Energy Body'], 'Robology')
        self.assertEqual(transcriptIndex.sectionFromPage['Henry Corbin'], 'Authors')


if __name__ == "__main__":
    unittest.main()
