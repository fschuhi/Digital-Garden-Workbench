#!/usr/bin/env python3

import os
import yaml
from util import *
from MarkdownLine import MarkdownLine, MarkdownLines
from util import *


from enum import Enum
class ObsidianNoteType(Enum):
    UNKNOWN = 0
    TRANSCRIPT = 1
    SUMMARY = 2
    INDEX_ENTRY = 3
    INDEX = 4


# *********************************************
# class ObsidianNote
# *********************************************

class ObsidianNote:
    def __init__(self, type: ObsidianNoteType, path):
        self.type = type # type: ObsidianNoteType

        self.path = path
        self.filename = os.path.splitext(os.path.basename(path))[0]
        self.notename = basenameWithoutExt(self.filename)

        textLines = loadLinesFromTextFile(path)

        self.markdownLines = None # type: MarkdownLines

        # IMPORTANT: frontmatter is *not* markdown
        self.yaml = extractYaml(textLines)
        if self.yaml:
            skipAtBeginning = len(self.yaml) + 2
            textLines = [line for index, line in enumerate(textLines) if index >= skipAtBeginning]

        self.assignTextLines(textLines)


    @property
    def text(self):
        return self.markdownLines.asText()

    @text.setter
    def text(self, text):
        self.markdownLines = MarkdownLines.fromText(text)


    def getYamlValue(self, key: str) -> str:
        if self.yaml and (key in self.yaml):
            return self.yaml[key]

    def collectTextLines(self) -> list[str]:
        return self.markdownLines.collectTextLines()
    
    def assignTextLines(self, textLines: list[str]):
        self.markdownLines = MarkdownLines(textLines)


    def collectMarkdownLines(self) -> MarkdownLines:
        return MarkdownLines.fromText(self.text)

    def assignMarkdownLines(self, markdownLines: MarkdownLines):
        self.text = markdownLines.asText()


    def determineTags(self) -> list[str]:        
        tags = []
        for ml in self.markdownLines:
            if re.match("^ *#[A-Za-z]+", ml.text):
                tagsInLine = [x.strip(' ') for x in ml.text[1:].split('#')]
                tags.extend(tagsInLine)
        return tags


    def save(self, path=None):
        if path is None: path = self.path
        out = []
        if self.yaml:
            out.append("---")
            out.extend(yaml.dump(self.yaml).splitlines())
            out.append("---")

        markdownTextLines = self.markdownLines.collectTextLines()
        out.extend(markdownTextLines)
        saveLinesToTextFile(path, out)


if __name__ == "__main__":
    pass
