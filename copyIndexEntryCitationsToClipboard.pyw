#!/usr/bin/env python3

import tkinter
from util import *
from TranscriptPage import TranscriptPage
import pyperclip
from HAFEnvironment import HAFEnvironment
from consts import HAF_YAML


def copyIndexEntryCitationsToClipboard(gui = True):
    haf = HAFEnvironment(HAF_YAML)    
    
    data = pyperclip.paste()
    
    import re

    links = re.split(r"\]\]\*?\*?", data)
    linkPattern = r"\[\[([^#]+)#\^?(([0-9]+)-([0-9]+))\|"

    citationMarkups = []
    for link in links:        
        if (match := re.search(linkPattern, link)):

            transcriptName = match.group(1)
            pageNr = int(match.group(3))
            paragraphNr = int(match.group(4))

            if not haf.transcriptExists(transcriptName):
                pass
            else:
                sfnTranscriptMd = haf.getTranscriptFilename(transcriptName)

                page = TranscriptPage.fromTranscriptFilename(sfnTranscriptMd)

                markdownLine = page.findParagraph(pageNr, paragraphNr)
                (_, _, text) = parseParagraph(markdownLine.text)

                blockId = f"{pageNr}-{paragraphNr}"

                # 22.09.21 changed to header target
                #citationMarkup = f"> {text} _([[{transcriptName}#^{blockId}|{blockId}]])_"
                citationMarkup = f"> {text} _([[{transcriptName}#{blockId}|{blockId}]])_"

                citationMarkups.append(citationMarkup)

    clipboardText = '\n' + '\n\n'.join(citationMarkups) + '\n'
    #print(clipboardText)
    pyperclip.copy(clipboardText)

    if gui:
        showMessageBox(f"copied {len(citationMarkups)} citations to clipboard ({len(clipboardText)} chars)", thisFunctionName())


if __name__ == "__main__":
    copyIndexEntryCitationsToClipboard()