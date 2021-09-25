#!/usr/bin/env python3

import tkinter
from util import *


def copyIndexEntryCitationsToClipboard(gui = True):
    from HAFEnvironment import HAFEnvironment
    from consts import HAF_YAML
    haf = HAFEnvironment(HAF_YAML)    
    
    import pyperclip
    data = pyperclip.paste()
    
    import re

    # 22.09.21 we use dot now instead of comma
    #links = re.split('\]\]\*?\*?, ', data)
    links = re.split(r"\]\]\*?\*?", data)
    linkPattern = r"\[\[([^#]+)#\^?(([0-9]+)-([0-9]+))\|"

    citationMarkups = []
    for link in links:
        match = re.search(linkPattern, link)
        if match:

            transcriptName = match.group(1)
            pageNr = int(match.group(3))
            paragraphNr = int(match.group(4))

            if not haf.transcriptExists(transcriptName):
                pass
            else:
                sfnTranscriptMd = haf.getTranscriptFilename(transcriptName)

                from TranscriptPage import TranscriptPage
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