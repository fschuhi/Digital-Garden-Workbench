#!/usr/bin/env python3

from numpy import flatiter
from consts import HAF_YAML
from HAFEnvironment import HAFEnvironment
import sys
import os
import re
import yaml
from util import extractYaml, loadLinesFromTextFile, loadStringFromTextFile, saveStringToTextFile
from MarkdownLine import MarkdownLine, MarkdownLines
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
    def __init__(self, type: ObsidianNoteType, textLines: list[str]):
        self.type = type
        self.assignTextLines(textLines)

    @classmethod
    def fromLines(cls, type: ObsidianNoteType, textLines: list[str]):
        return cls(type, textLines)

    @classmethod
    def fromFile(cls, type: ObsidianNoteType, sfn: str):
        assert os.path.exists(sfn)
        textLines = loadLinesFromTextFile(sfn)
        return cls(type, textLines)

    @classmethod
    def fromText(cls, type: ObsidianNoteType, text: str):
        textLines = text.splitlines()
        return cls(type, textLines)


    @property
    def text(self):
        return self.markdownLines.asText()

    @text.setter
    def text(self, text):
        self.markdownLines = MarkdownLines.fromText(text)


    def collectTextLines(self) -> list[str]:
        return self.markdownLines.collectTextLines()
    
    def assignTextLines(self, textLines: list[str]):
        self.markdownLines = MarkdownLines(textLines)


    def collectYaml(self) -> dict[str,str]:
        yaml = extractYaml(self.collectTextLines())
        return yaml if yaml else {}
    
    def assignYaml(self, newYaml: dict[str,str]):
        # could probably use the * splat operator somewhere in this method
        newLines = []
        if yaml:
            newLines.append('---')
            newLines.extend(yaml.dump(newYaml).splitlines())
            newLines.append('---')
        lines = self.collectTextLines()
        oldYaml = extractYaml(lines)
        firstAfterYaml = 0 if not oldYaml else len(oldYaml) + 2
        newLines.extend(lines[firstAfterYaml:])
        self.assignTextLines(newLines)


    def collectMarkdownLines(self) -> MarkdownLines:
        return MarkdownLines.fromText(self.text)

    def assignMarkdownLines(self, markdownLines: MarkdownLines):
        self.text = markdownLines.asText()



if __name__ == "__main__":
    pass
