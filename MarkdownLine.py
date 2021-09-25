#!/usr/bin/env python3

import os
import spacy
from TranscriptModel import TranscriptModel
from util import *
from typing import Tuple
import re

# *********************************************
# class MarkdownLine
# *********************************************

class MarkdownLine:

    def __init__(self, text) -> None:
        self.text = text
        self.footnotes = None # type: TFootnotes
        self.termCounts = None # type: dict[str,int]
        self.shownLinks = None # type: list[str]
        self.hasAppliedSpacy = False


# links

    def removeAllLinks(self):
        if not self.footnotes:
            self.footnotes = []
        while True:
            matchLink = re.search(r"\[\[.+?\]\]", self.text)
            if not matchLink:
                break

            link = matchLink[0]        
            matchLinkParts = re.search(r"\[\[([^|]+)(\|(.+))?\]\]", link)
            linkReference = matchLinkParts[1]
            linkDisplayText = matchLinkParts[3] if matchLinkParts[3] else linkReference

            start = matchLink.start()
            end = matchLink.end()
            self.replace(start, end, linkDisplayText)


    def collectLinkMatches(self)  -> list[re.Match]:
        return list(re.finditer(ObsidianLinkPattern, self.text))


    def collectLinkSpans(self) -> list[tuple[int, int]]:
        return [m.span() for m in self.collectLinkMatches()]


    def searchMarkupLink(self, start=0) -> re.Match:
        return searchObsidianLink(self.text[start:])


    def replaceMatches(self, matches: list[re.Match], func, ignoreFootnotes=True):
        if ignoreFootnotes:
            self.removeFootnotes()
        delta = 0
        for match in matches:
            span = match.span()
            (start, end) = span
            replaced = func(match)
            self.replace(start+delta, end+delta, replaced)
            delta += len(replaced) - (end-start)
        if ignoreFootnotes:
            self.restoreFootnotes()


    def replaceLinks(self, func, ignoreFootnotes=True):
        if ignoreFootnotes:
            self.removeFootnotes()
        matches = self.collectLinkMatches()
        self.replaceMatches(matches, func)
        if ignoreFootnotes:
            self.restoreFootnotes() # not necessary because replaceMatches() also does it, but it doesn't hurt


# cut, insert, replace

    def cutSpan(self, span) -> str:
        (start, end) = span
        return self.cut(start, end)

    def cut(self, start, end) -> str:
        cutText = self.text[start:end]
        if self.footnotes:
            lenDelta = -len(cutText)
            self.__updateFootnotePositions(start, lenDelta)
        self.text = self.text[:start] + self.text[end:]
        return cutText


    def insertText(self, pos, textToInsert):
        self.text = self.text[:pos] + textToInsert + self.text[pos:]
        if self.footnotes:
            lenDelta = +len(textToInsert)
            self.__updateFootnotePositions(pos, lenDelta)


    def replace(self, start, end, textToInsert):
        self.text = self.text[:start] + textToInsert + self.text[end:]
        if self.footnotes:
            # (end-start) == len(self.text[start:end])
            lenDelta = len(textToInsert) - (end-start)
            self.__updateFootnotePositions(start, lenDelta)


# removing links, parallel update of footnotes

    def applySpacy(self, model: TranscriptModel, force: bool = False):
        if self.hasAppliedSpacy and not force:
            return

        # footnotes might contain links, so they must be off-limits for the indexing
        self.removeFootnotes()

        # ASSUMPTION: we are fed with transcript files which contain blocks, where the blocks might contain links from earlier indexing
        # IMPORTANT: we always start indexing from a clean slate, i.e. as if the text was read from PDF (i.e. no links, no footnotes)
        # ((PWECFSR)) reversed below
        self.removeAllLinks()

        self.shownLinks = [] # type: list[str]
        self.termCounts = {} # type: dict[str,int]

        # each paragraph is a doc, 1 PhraseMatcher is used for all of the paragraph docs
        doc = model.nlp(self.text)

        # we move from left to right through the matches and replace each one with the link
        # the links are usually longer than the matched text, so we need to track that to adjust the string position for later matches
        lenDelta = 0

        # matches from PhraseMatcher might overlap, use the longest span in that case
        matches = model.matcher(doc)
        spans = [doc[start:end] for _, start, end in matches]

        for span in spacy.util.filter_spans(spans):

            # start/end are token positions
            matchText = doc[span.start:span.end].text

            # ((HISPIZN)) by definition we know the match because adding patterns and links is done in tandem
            if matchText.lower() in model.ignored:
                pass
            else:
                link = model.transcriptIndex.patternLinks[matchText.lower()]
                if link in self.termCounts:                
                    self.termCounts[link] += 1
                    # only link once to a particular page/heading on page
                else:
                    self.termCounts[link] = 1
                    self.shownLinks.append(link)
                    
                    if matchText.lower() == link.lower():
                        # no need to have a piped link, because Obsidian is case insensitive for links
                        linkText = "[[" + matchText + "]]"
                    else:
                        # NOTE: the link can contain a #, i.e. point to a heading on the page
                        linkText = "[[" + link + "|" + matchText + "]]"

                    # sync the position in the original text and the text with the links
                    start = doc[span.start].idx + lenDelta
                    end = start + len(matchText)
                    self.replace(start, end, linkText)
                    lenDelta += len(linkText) - len(matchText)
                    

        # ((PWECFSR)) from above
        # The paragraph now contains links, but not yet footnotes =>  add footnotes to the paragraph
        # NOTE: character position of the footnotes will have changed, due to inserting links; see ((XYYSBMS))
        self.restoreFootnotes()

        self.hasAppliedSpacy = True


# using spacy results (previously in TranscriptParagraph)

    # ((JJFZHVO)) Keywords section on summary page

    def collectShownLinks(self) -> str:
        assert self.hasAppliedSpacy, "must first apply spacy to this paragraph"
        entryFunc = lambda entry : f"[[{entry}]]" if self.termCounts[entry] == 1 else f"[[{entry}]] ({self.termCounts[entry]})"
        links = [entryFunc(link) for link in self.shownLinks]
        return " · ".join(links)

    def countTerm(self, term: str) -> int:
        assert self.hasAppliedSpacy, "must first apply spacy to this paragraph"        
        return self.termCounts[term] if term in self.termCounts else 0



# footnotes

    def removeFootnotes(self):
        # footnotes might contain links, so they must be off-limits for the indexing
        if not self.footnotes:
            self.__hideAndCollectFootnotes()

    def restoreFootnotes(self):
        if self.footnotes:
            self.__unhideFootnotes()
            self.footnotes = None


    def __hideAndCollectFootnotes(self):
        self.footnotes = []
        #self.text = self.text
        lenDelta = 0
        while True:
            (match, replacement, start) = self._hideFirstFootnote()
            if start == -1:
                break        
            self.footnotes.append( (match, start + lenDelta) )
            lenDelta += len(match)
            self.text = replacement


    def _hideFirstFootnote(self) -> Tuple[str, str, int]:
        start = self.text.find("^[")
        match = ""
        replacement = ""
        if start != -1:
            pos = start+2
            open = 1
            while open > 0:
                if self.text[pos] == "[":
                    open += 1
                if self.text[pos] == "]":
                    open -= 1
                pos += 1
            match = self.text[start:pos]
            replacement = self.text[:start] + self.text[pos:]
        return (match, replacement, start)


    def __updateFootnotePositions(self, startChar: int, lenDelta: int) -> None:
        for index, footnote in enumerate(self.footnotes):
            (text, pos) = footnote
            if pos >= startChar:
                self.footnotes[index] = (text, pos+lenDelta)


    def __unhideFootnotes(self):
        for (match, start) in self.footnotes:
            self.text = self.text[:start] + match + self.text[start:]


# tags

    def collectTagMatches(self) -> list[re.Match]:
        pattern = r"( |^)#(?P<tag>\b\w+(/\w+)*)"
        return list(re.finditer(pattern, self.text, re.MULTILINE))

    def collectTags(self) -> list[str]:
        return [match.group('tag') for match in self.collectTagMatches()]


# *********************************************
# class MarkdownLines
# *********************************************

class MarkdownLines:
    def __init__(self, textLines: list[str]):
        self.markdownLines = [MarkdownLine(textLine) for textLine in textLines] # type: list[MarkdownLine]

    @classmethod
    def fromLines(cls, textLines: list[str]):
        return cls(textLines)

    @classmethod
    def fromFile(cls, sfn):
        assert os.path.exists(sfn)
        textLines = loadLinesFromTextFile(sfn)
        return cls(textLines)

    @classmethod
    def fromText(cls, text):
        textLines = text.splitlines()
        return cls(textLines)


    def __getitem__(self, key):
        return self.markdownLines[key]

    def __len__(self):
        return len(self.markdownLines)


    def asText(self) -> str:
        return '\n'.join( [markdownLine.text for markdownLine in self.markdownLines] ) + '\n'

    def collectTextLines(self) -> list[str]:
        return [markdown.text for markdown in self.markdownLines]


    def search(self, pattern, startIndex=0) -> Tuple[int, re.Match]:
        indexes = range(startIndex, len(self.markdownLines))
        for index in indexes:
            markdownLine = self.markdownLines[index]
            match = re.search(pattern, markdownLine.text)
            if match:
                return (index, match)
        return (None, None)


    def searchSection(self, fromPattern, toPattern, startIndex=0) -> Tuple[int, int, re.Match, re.Match]:
        (fromIndex, fromMatch) = self.search(fromPattern, startIndex)
        if fromIndex is not None:
            (toIndex, toMatch) = self.search(toPattern, fromIndex+1)
            if toIndex:
                #print((fromIndex, toIndex, fromMatch, toMatch))
                return (fromIndex, toIndex, fromMatch, toMatch)
        return (None, None, None, None)
        
    
