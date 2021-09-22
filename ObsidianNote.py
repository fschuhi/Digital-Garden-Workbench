#!/usr/bin/env python3

from numpy import flatiter
from consts import HAF_YAML
from HAFEnvironment import HAFEnvironment
import sys
import os
import re
import yaml
from util import extractYaml, loadLinesFromTextFile, loadStringFromTextFile, saveStringToTextFile
from MarkdownSnippet import MarkdownSnippet, MarkdownSnippets
from typing import Tuple


from enum import Enum
class ObsidianNoteType(Enum):
    UNKNOWN = 0
    TRANSCRIPT = 1
    SUMMMARY = 2
    INDEX_ENTRY = 3
    INDEX = 4


# *********************************************
# class ObsidianNote
# *********************************************

class ObsidianNote:
    def __init__(self, type: ObsidianNoteType, text: str):
        self.type = type
        self.text = text


    @classmethod
    def fromFile(cls, type: ObsidianNoteType, sfn):
        assert os.path.exists(sfn)
        textFromFile = loadStringFromTextFile(sfn)
        return cls(type, textFromFile)


    def collectLines(self) -> list[str]:
        return self.text.splitlines()
    
    def assignLines(self, lines: list[str]):
        self.text = '\n'.join(lines) + '\n'


    def collectYaml(self) -> dict[str,str]:
        yaml = extractYaml(self.collectLines())
        return yaml if yaml else {}
    
    def assignYaml(self, newYaml: dict[str,str]):
        newLines = []
        if yaml:
            newLines.append('---')
            newLines.extend(yaml.dump(newYaml).splitlines())
            newLines.append('---')
        lines = self.collectLines()
        oldYaml = extractYaml(lines)
        firstAfterYaml = 0 if not oldYaml else len(oldYaml) + 2
        newLines.extend(lines[firstAfterYaml:])
        self.assignLines(newLines)


    def collectMarkdownSnippet(self) -> MarkdownSnippet:
        return MarkdownSnippet(self.text)    

    def assignMarkdownSnippet(self, snippet: MarkdownSnippet):
        self.text = snippet.text


    def collectMarkdownSnippets(self) -> MarkdownSnippets:
        return MarkdownSnippets(self.text)

    def assignMarkdownSnippets(self, snippets: MarkdownSnippets):
        self.text = snippets.asText()



if __name__ == "__main__":
    haf = HAFEnvironment(HAF_YAML)
    md = haf.getSummaryFilename("Samadhi in Metta Practice")
    note = ObsidianNote.fromFile(ObsidianNoteType.SUMMMARY, md)

