#!/usr/bin/env python3

import unittest

from KanbanNote import KanbanNote

import filecmp
import re
import os


# *********************************************
# KanbanNote
# *********************************************

class Test_KanbanNote(unittest.TestCase):

    def test_PythonPipelineKanbanNote(self):
        kb = KanbanNote("testing/data/Test_KanbanNote.Python pipeline (Kanban).md")
        # print(kb.lists['Done'])
        self.assertTrue('Done' in kb.complete)
        self.assertListEqual(kb.lists, ['Ideas', 'Pending', 'Working on it', 'Done', 'Archive'])
        kb.save("tmp/tmp.md")
        self.assertTrue(filecmp.cmp("tmp/tmp.md", "testing/data/Test_KanbanNote.test_PythonPipelineKanbanNote.md"))


    def test_findCard(self):
        kb = KanbanNote("testing/data/Test_KanbanNote.Python pipeline (Kanban).md")
        searchFunc = lambda listName, card: re.search("Kanban note management", card)
        foundCards = kb.findCards(searchFunc)
        self.assertListEqual(foundCards, [("Pending", "[[Kanban note management]]", False)])


    def test_replaceCard(self):
        kb = KanbanNote("testing/data/Test_KanbanNote.Python pipeline (Kanban).md")
        searchFunc = lambda listName, card: re.search("Kanban note management", card)
        self.assertEqual(len(kb.findCards(searchFunc)), 1)
        kb.replaceCard("Pending", "[[Kanban note management]]", "replaced card")
        kb.save("tmp/tmp.md")
        self.assertTrue(filecmp.cmp("tmp/tmp.md", "testing/data/Test_KanbanNote.test_replaceCard.md"))


    def test_addCard(self):
        kb = KanbanNote("testing/data/Test_KanbanNote.Python pipeline (Kanban).md")
        try: 
            kb.addCard("Pending", "[[Kanban note management]]", False)
        except AssertionError: pass
        kb.addCard("Pending", "added card", False)
        kb.save("tmp/tmp.md")
        #print(loadStringFromTextFile("tmp/tmp.md"))
        self.assertTrue(filecmp.cmp("tmp/tmp.md", "testing/data/Test_KanbanNote.test_addCard.md"))


if __name__ == "__main__":
    unittest.main()
