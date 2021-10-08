#!/usr/bin/env python3

from MarkdownLine import MarkdownLine
from TranscriptPage import TranscriptPage
from TranscriptSummaryPage import TranscriptSummaryPage
from util import *
from HAFEnvironment import HAFEnvironment, talknameFromFilename
from consts import HAF_PUBLISH_YAML, HAF_YAML

import os
import re
import shutil

# *********************************************
# class Publishing
# *********************************************

class Publishing:

    def __init__(self) -> None:
        self.hafWork = HAFEnvironment(HAF_YAML)
        self.hafPublish = HAFEnvironment(HAF_PUBLISH_YAML)


# mirroring

    def transferFilesToPublish(self):
        self.mirrorRetreatFiles()

        #print("2")
        self.mirrorIndex()
        self.mirrorHelp()

        #print("3")
        self.copyFile("Rob Burbea/Retreats.md", "/")
        self.copyFile("Rob Burbea/Index.md", "/")
        self.copyFile("Brainstorming/NoteStar.md", "/")
        self.copyFile("Rob Burbea/Gardening.md", "/")
        self.copyFile("Rob Burbea/Diacritics.md", "/")
        self.copyFile("Rob Burbea/Rob Burbea.md", "/")

        # self.copyFile("Images/Digital Garden/digital-garden-big.png", "Images")
        # self.copyFile("Images/Digital Garden/digital-garden-small.png", "Images")
        # self.copyFile("Images/Digital Garden/Rob Burbea.png", "Images")
        # self.copyFile("Images/Digital Garden/link.png", "Images")
        # self.copyFile("Images/Digital Garden/help1.png", "Images")
        # self.copyFile("Images/Digital Garden/help2.png", "Images")
        # self.copyFile("Images/Digital Garden/help3.png", "Images")
        # self.copyFile("Images/Digital Garden/help4.png", "Images")

        mirrorDir(os.path.join(self.hafWork.root, "Images/Digital Garden"), os.path.join(self.hafPublish.root, "Images"))
        mirrorDir(os.path.join(self.hafWork.root, "css-snippets"), os.path.join(self.hafPublish.root, "css-snippets"))
        self.copyFile("css-snippets/publish.css", "/")
        

        self.modifyFullstops()

        # we do not touch publish.css
        #print("4")
        # now all files are exact copies of the _Markdown vault
        # need to convert audio links and admonitions
        self.convertAllMarkdownFiles()


    def mirrorRetreatFiles(self):

        def mirrorRetreatsDir(funcSource, funcTarget, ext='.md'):
            nAdded = 0
            for retreatName in self.hafWork.retreatNames:            
                source = funcSource(retreatName)
                if not os.path.isdir(source):
                    continue
                target = funcTarget(retreatName)
                assert os.path.isdir(target)
                nAdded += mirrorDir(source, target, ext)
            return nAdded

        source = self.hafWork
        target = self.hafPublish
        # we intentionally disregard Audio
        mirrorRetreatsDir(lambda r: source.retreatFolder(r), lambda r: target.retreatFolder(r))
        mirrorRetreatsDir(lambda r: source.pdfFolder(r), lambda r: target.pdfFolder(r), '.pdf')
        mirrorRetreatsDir(lambda r: source.imagesFolder(r), lambda r: target.imagesFolder(r), None)
        mirrorRetreatsDir(lambda r: source.transcriptsFolder(r), lambda r: target.transcriptsFolder(r))
        mirrorRetreatsDir(lambda r: source.summariesFolder(r), lambda r: target.summariesFolder(r))
        mirrorRetreatsDir(lambda r: source.listsFolder(r), lambda r: target.listsFolder(r))


    def mirrorIndex(self):
        source = self.hafWork
        target = self.hafPublish
        mirrorDir(source.dirIndex, target.dirIndex)


    def mirrorHelp(self):
        source = self.hafWork
        target = self.hafPublish
        mirrorDir(source.dirHelp, target.dirHelp)


    def copyFile(self, source, target=None):
        if not target:
            # only call w/ 1 param to indicate that the file should be copied to the same position in the publish tree
            target = source
        elif target == '/':
            # pass '/' to move the file (with the same name) to the publish root folder
            target = ""

        source = os.path.join(self.hafWork.root, source)
        target = os.path.join(self.hafPublish.root, target)

        # make sure that we have a target _filename_, even if path was passed (which is usually the case)
        if os.path.isdir(target):
            target = os.path.join(target, os.path.basename(source))

        #shutil.copy2(source, target)
        shutil.copy2(source, target)

    
# audio, admonitions

    def convertAllMarkdownFiles(self):
        filenames = filterExt(self.hafPublish.allFiles(), '.md')
        for filename in filenames:
            convertedLines = self.convertMarkdownFile(filename)
            saveLinesToTextFile(filename, convertedLines)


    def convertMarkdownFile(self, sfn) -> list[str]:
        newLines = []
        lines = loadLinesFromTextFile(sfn)
        inAdmonition = False
        admonitionLines = []
        for line in lines:
            # ![[20200301-Rob_Burbea-GAIA-preliminaries_regarding_voice_movement_and_gesture_part_1-62452.mp3#t=13:09]]
            match = parseAudioLink(line)
            if match:
                date = match.group('date')
                middle = match.group('middle')
                audioid = match.group('audioid')
                timestamp = canonicalTimestamp(match.group('timestamp'))

                # https://stackoverflow.com/questions/13242877/stop-audio-buffering-in-the-audio-tag
                # https://developer.mozilla.org/en-US/docs/Web/HTML/Element/audio
                source = f"https://dharmaseed.org/talks/{audioid}/{date}-{middle}-{audioid}.mp3" + (f"#t={timestamp}" if timestamp else "")
                html5 = f'<audio controls preload=metadata style=" width:300px;" controlslist="nodownload"><source src="{source}" type="audio/mpeg">???</audio>'

                (start, end) = match.span()
                newLine = line[:start] + html5 + line[end:]
                newLines.append(newLine)
                continue

            match = re.match(r"```ad-(?P<admonition>.+)", line)
            if match:
                admonition = match.group('admonition')
                if admonition in ['note', 'quote', 'warning']:
                    pass
                elif admonition in ['danger', 'bug']:
                    admonition = 'important'
                else:
                    admonition = 'note'
                title = '❝' if admonition == 'quote' else admonition.upper()
                inAdmonition = True
                admonitionLines = []
                continue

            if inAdmonition:
                if line == "```":
                    newLines.append(f'<div class="admonition {admonition}"><div class="title">{title}</div><div class="content">')
                    newLines.extend(admonitionLines)
                    newLines.append('</div></div>')
                    inAdmonition = False
                elif line.startswith('title:'):
                    pluginTitle = line[7:].strip()
                    if pluginTitle:
                        title = pluginTitle
                else:
                    admonitionLines.append(line + '<br/>')
                continue
            
            newLines.append(line)
        return newLines


# fullstops in transcripts

    def modifyFullstops(self):
        summaryFilenames = self.hafWork.collectSummaryFilenames()
        for summaryFilename in summaryFilenames:
            summary = TranscriptSummaryPage(summaryFilename)
            headerTargets = summary.collectParagraphHeaderTargets()
            talkname = talknameFromFilename(summaryFilename)

            # intentionally from the publish 
            transcriptFilename = self.hafPublish.getTranscriptFilename(talkname)
            assert transcriptFilename

            transcript = TranscriptPage(transcriptFilename)
            for markdownLine in transcript.markdownLines: # type: MarkdownLine
                blockid = markdownLine.getBlockId()
                if not blockid:
                    # transcript has not only paragraphs
                    pass
                else:
                    if markdownLine.text.startswith('#'):
                        # make sure we don't accidently capture the header (which also has the block id, excluding leading ^, though)
                        pass
                    else:
                        if blockid not in headerTargets:
                            # we might have left out this particular paragraph from the summary
                            pass
                        else:
                            headerTarget = headerTargets[blockid]
                            if not headerTarget:
                                # probably ... (yet-missing paragraph description)
                                pass
                            else:
                                match = re.match(r'(.+)([.?!"]) \^' + blockid + "$", markdownLine.text)
                                if match:
                                    linkToSummary = f"[[{talkname}#{headerTarget}|{match.group(2)}]]"  # ∘∙⦿꘎᙮
                                    markdownLine.text = f"{match.group(1)}{linkToSummary} ^{blockid}"
            transcript.save(transcriptFilename)


# cut off internal links by converting them to html

    def __replaceLinks(self, filenames, replaceIndex):
        website = self.hafPublish.website()
        
        indexEntryNameSet = self.hafPublish.collectIndexEntryNameSet()
        transcriptNameSet = self.hafPublish.collectTranscriptNameSet()

        def filterLinks(match):
            note = match.group('note')
            assert note
            target = match.group('target')
            
            # convert links on summary to transcript
            if target and target.startswith('#^') and note in transcriptNameSet:
                return True

            # convert any index entry
            if replaceIndex and (note in indexEntryNameSet):
                return True

            return False

        for filename in filenames:
            # print(baseNameWithoutExt(sfnSummaryMd))
            text = loadStringFromTextFile(filename)
            markdown = MarkdownLine(text)
            markdown.replaceLinks(lambda match: f"{convertMatchedObsidianLink(match, website, filterLinks)}")
            saveStringToTextFile(filename, markdown.text)


    def replaceLinksInAllSummaries(self):
        filenames = self.hafPublish.collectSummaryFilenames()
        self.__replaceLinks(filenames, True)

    def replaceLinksInAllRootFilenames(self):
        filenames = self.hafPublish.collectNotesInRetreatsFolders()
        self.__replaceLinks(filenames, False)

    def replaceLinksInSpecialFiles(self):
        index = os.path.join(self.hafPublish.root, 'Index.md')
        assert os.path.exists(index)
        self.__replaceLinks([index], True)


