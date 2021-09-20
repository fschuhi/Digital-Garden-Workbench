#!/usr/bin/env python3

import filecmp
import unittest
from util import saveStringToTextFile
from testing import MyTestClass

from copyIndexEntryCitationsToClipboard import copyIndexEntryCitationsToClipboard

# *********************************************
# tests
# *********************************************

class Test_copyIndexEntryCitationsToClipboard(MyTestClass):

    def test_copyIndexEntryCitationsToClipboard(self):
        occurances = "_occurrences: **[[0302 Preliminaries Regarding Voice, Movement, and Gesture - Part 2#^3-4|3-4 (1)]]**, [[0302 Preliminaries Regarding Voice, Movement, and Gesture - Part 2#^4-1|4-1 (1)]]_"
        import pyperclip
        pyperclip.copy(occurances)

        copyIndexEntryCitationsToClipboard(gui=False)
        citations = pyperclip.paste()
        saveStringToTextFile("tmp/tmp.txt", citations)
        self.assertTrue(filecmp.cmp("tmp/tmp.txt", "testing/data/test_copyIndexEntryCitationsToClipboard.txt"))


if __name__ == "__main__":
    unittest.main()
