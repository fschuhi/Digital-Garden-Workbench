#!/usr/bin/env python3

import logging
import re
import fitz

from typing import Tuple
TBlock = Tuple[int, int, str]
TBlocks = list[TBlock]

from util import canonicalizeText, decontractText

# *********************************************
# PDF to blocks
# *********************************************

class TranscriptPdfLoader:
    def __init__(self, sfnPdf) -> None:
        #logging.info(f"TranscriptLoader: load from '{sfnPdf}'")
        self.rawBlocks = self.loadPdf(sfnPdf)

        self.frontmatterLines = []
        self.frontmatter = {}
        self.mergedBlocks = self.mergeBlocksSplitWithPageBreak(self.rawBlocks)


    def loadPdf(self, sfnPdf) -> TBlocks:
        doc = fitz.open(sfnPdf)
        blocks = []
        for pageNr in range(doc.pageCount):
            page = doc[pageNr]

            # https://pymupdf.readthedocs.io/en/latest/textpage.html#TextPage.extractBLOCKS
            fitzBlocks = page.get_text("blocks")
            for fitzBlock in fitzBlocks:
                (x0, y0, x1, y1, blockText, blockNr, blockType) = fitzBlock
                # blockText = canonicalizeText(blockText)
                # blockText = decontractText(blockText)
                
                # internally, the pages and blocks on a page are zero-based                        
                blocks.append( (pageNr+1, blockNr+1, blockText) )
        return blocks


    def handleFrontmatterLine(self, line) -> bool:
        isLastFrontmatterLine = False
        self.frontmatterLines.append(line)

        if line.__contains__("https://dharmaseed.org"):
            match = re.match("^(.+) Rob Burbea (.+) ([0-9]?[0-9]), (20[012][0-9]) (.+)$", line)
            if match:
                self.frontmatter["title"] = match.group(1)
                month = match.group(2)
                day = match.group(3)
                year = match.group(4)
                import dateparser
                self.frontmatter["date of talk"] = dateparser.parse(f"{month} {day}, {year}")
                self.frontmatter["Dharmaseed"] = match.group(5)
            isLastFrontmatterLine = True

        elif line == "Rob Burbea":
            self.frontmatter["title"] = self.frontmatterLines[0]
            isLastFrontmatterLine = True
        
        return isLastFrontmatterLine


    def mergeBlocksSplitWithPageBreak(self, blocks: TBlocks) -> TBlocks:
        handledFrontmatter = False
        linkedBlocks = []
        blockToAdd = None # type: TBlock
        currentBlockText = ""
        currentPageNr = 0
        currentBlockNr = 0
        lastPageNr = -1

        for block in blocks:
            # NOTE: we don't use fitz block numbers but generate own ones
            # IMPORTANT: own block number 1 == first new paragraph on a page            
            (thisPageNr, _, thisBlockText) = block

            if not handledFrontmatter:
                handledFrontmatter = self.handleFrontmatterLine(thisBlockText)
            else:
                thisBlockText = canonicalizeText(thisBlockText)
                # thisBlockText = decontractText(thisBlockText)
                if currentBlockText == "":
                    # merge buffer empty, start a new one
                    currentBlockText = thisBlockText
                    currentPageNr = thisPageNr
                    if thisPageNr != lastPageNr:
                        currentBlockNr = 0
                        lastPageNr = thisPageNr            
                else:
                    # append to merge buffer
                    currentBlockText += " " + thisBlockText

                if thisBlockText.endswith(('.', '?', '!')):            
                    # block ends with a char which indicates that it is the end of a paragraph

                    # NOTE: we don't use fitz pagenumbers and blocknumbers
                    currentBlockNr += 1
                    blockToAdd = (currentPageNr, currentBlockNr, currentBlockText)
                    
                    linkedBlocks.append(blockToAdd)

                    # we might have had to merge blocks, so start with a fresh buffer
                    currentBlockText = ""

        # assumption: frontmatter is only a couple of lines, neve the whole page

        if currentBlockText != "":
            # flush pending buffer
            blockToAdd = (currentPageNr, currentBlockNr, currentBlockText)
            linkedBlocks.append(blockToAdd)
        return linkedBlocks


