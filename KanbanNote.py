#!/usr/bin/env python3

from typing import Tuple
from util import *
from HAFEnvironment import HAFEnvironment

import re

# *********************************************
# KanbanNote
# *********************************************

class KanbanNote():
    def __init__(self, sfnKanbanNote: str) -> None:
        self.sfnKanbanNote = sfnKanbanNote
        self.lines = loadLinesFromTextFile(sfnKanbanNote)
        self.yaml = extractYaml(self.lines) # type: dict[str,str]

        self.lists = []
        self.cardsByList = {} # type: dict[str, list[Tuple[str,bool]]]
        self.complete = set()
        self.parseLines()


    def parseLines(self):        
        currentList = None
        currentCards = None
        for line in self.lines:
            match = re.match(r"#+ (?P<list>.+)", line)
            if match:
                if currentList is not None:
                    self.cardsByList[currentList] = currentCards
                currentList = match.group('list')
                self.lists.append(currentList)
                currentCards = []
            else:
                match = re.match(r"- \[(?P<todo>[ x])\] +(?P<card>.*)", line)
                if match:
                    done = match.group('todo') == 'x'
                    card = match.group('card')
                    currentCards.append( (card, done) )
                elif line == '**Complete**':
                    assert currentList
                    self.complete.add(currentList)

        if currentList is not None:
            self.cardsByList[currentList] = currentCards


    def save(self, sfn=None):
        newLines = []
        newLines.extend( ["---", "kanban-plugin: basic", "---"] )
        for listName in self.lists:
            if listName == 'Archive':
                newLines.append('***')
            newLines.append("## " + listName)
            if listName in self.complete:
                newLines.append('**Complete**')
            cards = self.cardsByList[listName]
            for (card, done) in cards:
                newLines.append(f"- [{'x' if done else ' '}] {card}")

        sfn = self.sfnKanbanNote if sfn is None else sfn
        saveLinesToTextFile(sfn, newLines)


    def findCards(self, searchFunc) -> list[Tuple[str, str,bool]]:
        foundCards = []
        assert searchFunc
        for listName in self.lists:
            cards = self.cardsByList[listName]
            for (card, done) in cards:
                if searchFunc(listName, card):
                    foundCards.append( (listName, card, done) )
        return foundCards


    def replaceCard(self, listName, oldCard, newCard, newDone=None):
        cardsInList = self.cardsByList[listName]
        for index, (card, done) in enumerate(cardsInList):                
            if card == oldCard:
                cardsInList[index] = (newCard, newDone if newDone else done)
                return                


    def addCard(self, listName, card, done):
        assert listName in self.lists
        searchFunc = lambda ln, c: ln == listName and c == card
        assert not self.findCards(searchFunc)
        cards = self.cardsByList[listName]
        cards.append((card, done))

