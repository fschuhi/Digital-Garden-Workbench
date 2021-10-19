#!/usr/bin/env python3

from util import *

from typing import Tuple
TPatterns = list[Tuple[str,list[str]]]
TSections = dict[str, list[str]]

# *********************************************
# class TranscriptIndex
# *********************************************

class TranscriptIndex:
    def __init__(self, sfnDictionaryYAML) -> None:

        self.dictionary = loadYaml(sfnDictionaryYAML)
        self.patternLinks = {}
        self.pages = [] # type: list[str]
        self.pagesSet = set()
        self.sections = {} # type: TSections
        self.patterns = [] # type: TPatterns
        self.sectionFromPage = {} # type: dict[str,str]
        self.alphabetical = {} # type: dict[str,str]
        self.reverseAlphabetical = {} # type: dict[str,str]
        
        self.buildIndex()


    def buildIndex(self) -> None:
        # we collect a dictionary of {pattern,link}

        # terminology yaml is organised in pages grouped by Persons, Robology, Buddhology, Philosophy
        for section, pageList in self.dictionary.items():

            # string patterns for each group will be converted into match docs
            patternsInSection = []
            pagesInSection = []

            for pageListEntry in pageList:
                if type(pageListEntry) is dict:

                    # this page has multiple patterns associated with it
                    # each of those patterns point to the page
                    pageWithMultiplePatterns = next(iter(pageListEntry))
                    pagesInSection.append(pageWithMultiplePatterns)
                    self.sectionFromPage[pageWithMultiplePatterns] = section

                    # page name is always its own alias, i.e. is matcheable
                    patternsInSection.append(pageWithMultiplePatterns)

                    # each pattern has 1 and only 1 associated link
                    # ((HISPIZN)) patterns and patternLinks are populated in tandem
                    # IMPORTANT: lower(), otherwise the dictionary might raise an exception on some matches
                    self.patternLinks[pageWithMultiplePatterns.lower()] = pageWithMultiplePatterns

                    patternList = pageListEntry[pageWithMultiplePatterns]
                    for patternListEntry in patternList:
                        if type(patternListEntry) is dict:

                            # pattern is combined w/ heading to link to on the page
                            pattern = next(iter(patternListEntry))
                            heading = patternListEntry[pattern]
                            if heading == ".":
                                heading = pattern[0].upper() + pattern[1:]
                            patternsInSection.append(pattern)
                            self.patternLinks[pattern.lower()]= pageWithMultiplePatterns + "#" + heading

                        else:
                            if patternListEntry.startswith('/'):
                                # page "Albert Einstein" should appear as "Einstein, Albert" in the index
                                alphabetical = patternListEntry[1:]
                                self.alphabetical[pageWithMultiplePatterns] = alphabetical
                                self.reverseAlphabetical[alphabetical] = pageWithMultiplePatterns
                            else:
                                # no heading qualification, so just point the pattern to the page
                                patternsInSection.append(patternListEntry)
                                self.patternLinks[patternListEntry.lower()] = pageWithMultiplePatterns

                else:
                    # just a list entry (pattern), without multiple patterns
                    patternsInSection.append(pageListEntry)
                    pagesInSection.append(pageListEntry)
                    self.sectionFromPage[pageListEntry] = section
                    self.patternLinks[pageListEntry.lower()] = pageListEntry                    

            self.patterns.append( (section, patternsInSection) )
            self.sections[section] = pagesInSection
            self.pages.extend(pagesInSection)
            self.pagesSet.update(self.pages)


    def createObsidianIndexEntryFiles(self, path, exclude=None):
        # iterate through dictionary keys, check if page exists in _Markdown, if not create it

        import os.path
    
        for section, pages in self.sections.items():
            for page in pages:
                fname = path + "\\" + page + ".md"
                if os.path.isfile(fname):
                    pass
                else:
                    if section == "ignored":
                        # TODO: could check for ignored index entry files if they exist and delete it, or it least print the name to stdout
                        pass
                    else:
                        if exclude and page in exclude:
                            print(f"exclude {page}")
                        else:
                            print(f"creating page {page}...")
                            f = open(fname, 'w', encoding='utf8', newline='\n')
                            # ((XMWFBBI)) tag immediately after the IndexEntry is the section
                            f.write(f"#IndexEntry #{section}\n")
                            f.close()


