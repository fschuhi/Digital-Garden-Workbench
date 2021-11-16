#!/usr/bin/env python3

from HAFEnvironment import HAFEnvironment
from util import saveLinesToTextFile
from Publishing import Publishing
from consts import HAF_YAML_TESTING
import unittest
import filecmp


# *********************************************
# Publishing
# *********************************************

class Test_Publishing(unittest.TestCase):

    def test_convertMarkdown(self):
        publishing = Publishing(transcriptModel=None)
        haf_publish = HAFEnvironment(HAF_YAML_TESTING)
        sfnTalk = haf_publish.getTalkFilename("Preliminaries Regarding Voice, Movement, and Gesture - Part 1")
        convertedLines = publishing.convertMarkdownFile(sfnTalk)
        saveLinesToTextFile("tmp/tmp.md", convertedLines)
        self.assertTrue(filecmp.cmp("tmp/tmp.md", "testing/data/Test_Publishing.test_convertMarkdown.md"))


if __name__ == "__main__":
    unittest.main()
