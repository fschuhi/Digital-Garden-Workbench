#!/usr/bin/env python3

from spacy.lang.en import English
from spacy.matcher import PhraseMatcher

from TranscriptIndex import TranscriptIndex


# *********************************************
# class TranscriptModel
# *********************************************

class TranscriptModel:
    # https://spacy.io/usage/rule-based-matching
    # https://explosion.ai/demos/matcher


    def __init__(self, transcriptIndex: TranscriptIndex) -> None:        
        self.nlp = English()        
        self.transcriptIndex = transcriptIndex

        self.ignored = set()

        # populate matcher
        self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        for (section, patterns) in self.transcriptIndex.patterns:
            # convert the patterns into docs and add them to the PhraseMatcher
            patternDocs = [self.nlp.make_doc(pattern) for pattern in patterns]
            self.matcher.add(section, patternDocs)
            if section.lower() == "ignored":
                for pattern in patterns:
                    self.ignored.add(pattern.lower())
