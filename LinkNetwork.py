#!/usr/bin/env python3

from typing import Tuple
from MarkdownSnippet import MarkdownSnippet
from util import basenameWithoutExt, filterExt, loadStringFromTextFile
from HAFEnvironment import HAFEnvironment

import re
import os

# *********************************************
# class LinkNetwork
# *********************************************

class LinkNetwork:

    def __init__(self, haf: HAFEnvironment) -> None:
        self.haf = haf
        
        self.allMd = filterExt(haf.allFiles, '.md')
        self.allNotes = [basenameWithoutExt(md) for md in self.allMd]
        self.actualNoteNameByNote = {n.lower(): n for n in self.allNotes}

        self.filenameByNote = {} # type: dict[str,str]
        self.markdownSnippetByNote = {} # type: dict[str, MarkdownSnippet]
        self.linkMatchesByNote = {} # type: dict[str,list[re.Match]]
        self.linksByNote = {} # type: dict[str,set[str]]
        self.backlinksByNote = {} # type: dict[str,set[str]]

        for md in self.allMd:
            note = basenameWithoutExt(md)
            noteKey = note.lower()

            self.filenameByNote[noteKey] = md
        
            markup = loadStringFromTextFile(md)
            markdownSnippet = MarkdownSnippet(markup)
            self.markdownSnippetByNote[noteKey] = markdownSnippet

            matches = markdownSnippet.collectLinkMatches()
            self.linkMatchesByNote[noteKey] = matches

            # create sets for all outgoing links to notes (linksByNote) and refererencing links back from other notes (backlinksByNote)            
            linksByNote = set()
            for match in matches:
                linkedNote = match.group('note')
                linkedNoteKey = linkedNote.lower()
                linksByNote.add(linkedNoteKey)
                if linkedNoteKey in self.backlinksByNote:
                    backlinksByNote = self.backlinksByNote[linkedNoteKey]
                else:
                    backlinksByNote = set()
                    self.backlinksByNote[linkedNoteKey] = backlinksByNote
                backlinksByNote.add(noteKey)

            # linksByNote[for this note] is complete
            # NOTE that the backlinks are collected across all the notes, so they are only done after the for md
            self.linksByNote[noteKey] = linksByNote


    def getActualNoteNameByNote(self, note) -> str:
        return self.actualNoteNameByNote[note.lower()]

    def getFilenameByNote(self, note) -> str:
        return self.filenameByNote[note.lower()]

    def getMarkdownSnippetByNote(self, note) -> MarkdownSnippet:
        return self.markdownSnippetByNote[note.lower()]


    def getLinksByNote(self, note) -> set[str]:
        return self.linksByNote[note.lower()]


    def getBacklinksByNote(self, note, exclude: list[str]=None) -> set[str]:
        if not exclude:
            return self.backlinksByNote[note.lower()] if note.lower() in self.backlinksByNote else []
        else:
            excludeSet = set(n.lower() for n in exclude)
            backlinks = self.getBacklinksByNote(note)
            return [linkingNote for linkingNote in backlinks if linkingNote not in excludeSet]

    def hasBacklinks(self, note, exclude: list[str]=None):
        return len(self.getBacklinksByNote(note, exclude)) > 0


    def getLinkMatchesByNote(self, note, linkedNote=None) -> list[re.Match]:
        matches = self.linkMatchesByNote[note.lower()]
        if not linkedNote:
            return matches
        else:
            linkedNote = linkedNote.lower()
            return [match for match in matches if match.group('note').lower() == linkedNote]

    def collectReferencedNoteMatches(self, referencedNote) -> list[Tuple[str, re.Match]]:
        matches = [] # type: Tuple[str, re.Match]
        for note in self.allNotes:
            for match in self.getLinkMatchesByNote(note):
                noteInLink = match.group('note')
                if noteInLink.lower() == referencedNote.lower():
                    matches.append( (note, match) )
        return matches
