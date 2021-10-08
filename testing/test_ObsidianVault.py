#!/usr/bin/env python3

from HAFEnvironment import HAFEnvironment
import unittest
import os
from consts import HAF_YAML_TESTING
from ObsidianVault import ObsidianVault
from util import *


# *********************************************
# HAF
# *********************************************

class Test_ObsidianVault(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        yaml = loadYaml(HAF_YAML_TESTING)
        root = yaml['Root']
        cls.vault = ObsidianVault(root)
        return super().setUpClass()


    def test_relative(self):
        self.assertEqual(self.vault.root, r'testing\data\_Markdown')
        sfn = os.path.join(self.vault.root, r"2006 New Year's Retreat\Transcripts\1228 Equanimity (talk).md")
        self.assertEqual(self.vault.relative(sfn), r"2006 New Year's Retreat\Transcripts\1228 Equanimity (talk).md")
        self.assertEqual(self.vault.toplevelFolder(sfn), "2006 New Year's Retreat")


    def test_collectNotes(self):
        self.assertListEqual( self.vault.folderNotes('2020 Vajra Music'), ['testing\\data\\_Markdown\\2020 Vajra Music\\2020 Vajra Music.md'])
        self.assertListEqual( self.vault.folderNotes('2020 Vajra Music/**'), \
            ['testing\\data\\_Markdown\\2020 Vajra Music\\2020 Vajra Music.md', \
            'testing\\data\\_Markdown\\2020 Vajra Music\\Talks\\Preliminaries Regarding Voice, Movement, and Gesture - Part 1.md', \
            'testing\\data\\_Markdown\\2020 Vajra Music\\Talks\\Preliminaries Regarding Voice, Movement, and Gesture - Part 2.md', \
            'testing\\data\\_Markdown\\2020 Vajra Music\\Transcripts\\0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1.md', \
            'testing\\data\\_Markdown\\2020 Vajra Music\\Transcripts\\0302 Preliminaries Regarding Voice, Movement, and Gesture - Part 2.md'])

        self.assertListEqual( self.vault.folderNotes('2020 Vajra Music/Transcripts'), \
            ['testing\\data\\_Markdown\\2020 Vajra Music\\Transcripts\\0301 Preliminaries Regarding Voice, Movement, and Gesture - Part 1.md', \
            'testing\\data\\_Markdown\\2020 Vajra Music\\Transcripts\\0302 Preliminaries Regarding Voice, Movement, and Gesture - Part 2.md'])


if __name__ == "__main__":
    unittest.main()
