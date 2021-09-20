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

    def test_convertMarkup(self):
        publishing = Publishing()
        haf_publish = HAFEnvironment(HAF_YAML_TESTING)
        sfnSummary = haf_publish.getSummaryFilename("Preliminaries Regarding Voice, Movement, and Gesture - Part 1")
        convertedLines = publishing.convertMarkdownFile(sfnSummary)
        saveLinesToTextFile("tmp/tmp.md", convertedLines)
        self.assertTrue(filecmp.cmp("tmp/tmp.md", "testing/data/Test_Publishing.test_convertMarkup.md"))


if __name__ == "__main__":
    unittest.main()
