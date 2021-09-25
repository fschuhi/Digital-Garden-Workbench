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
from util import *


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
        self.type = type # type: ObsidianNoteType
        self.markdownLines = None # type: list[MarkdownLine]

        # IMPORTANT: frontmatter is *not* markdown
        self.yaml = extractYaml(textLines)
        if self.yaml:
            skipAtBeginning = len(self.yaml) + 2
            textLines = [line for index, line in enumerate(textLines) if index >= skipAtBeginning]

        self.assignTextLines(textLines)


    @classmethod
    def fromTextLines(cls, type: ObsidianNoteType, textLines: list[str]):
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


    def collectMarkdownLines(self) -> MarkdownLines:
        return MarkdownLines.fromText(self.text)

    def assignMarkdownLines(self, markdownLines: MarkdownLines):
        self.text = markdownLines.asText()


    def saveToFile(self, sfn):
        out = []
        if self.yaml:
            out.append("---")
            out.extend(yaml.dump(self.yaml).splitlines())
            out.append("---")

        markdownTextLines = self.markdownLines.collectTextLines()
        out.extend(markdownTextLines)
        saveLinesToTextFile(sfn, out)




if __name__ == "__main__":
    pass
