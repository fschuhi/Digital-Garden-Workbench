#!/usr/bin/env python3

from MarkdownLine import MarkdownLine
from ObsidianNote import ObsidianNote, ObsidianNoteType
from TranscriptPage import TranscriptPage
from TalkPage import TalkPage
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

        self.indexEntryNameSet = self.hafPublish.collectIndexEntryNameSet()
        self.transcriptNameSet = self.hafPublish.collectTranscriptNameSet()



# creating files
    def createSynopses(self):
        # we need to recreate all synopses, because the headers might have changed
        from synopsis import createSynopsis
        createSynopsis(self.hafWork, "The Place of Samadhi in Metta Practice", "Samadhi in Metta Practice", "data/Synopsis 1/2008 vs 2007.csv", r"M:\2008 Lovingkindness and Compassion As a Path to Awakening\Synopsis 1.md")
        createSynopsis(self.hafWork, "Exploring the World of Loving Kindness", "Expressions of Metta", "data/Synopsis 2/2008 vs 2007.csv", r"M:\2008 Lovingkindness and Compassion As a Path to Awakening\Synopsis 2.md")


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

        mirrorDir(os.path.join(self.hafWork.root, "Images/Digital Garden"), os.path.join(self.hafPublish.root, "Images"))
        mirrorDir(os.path.join(self.hafWork.root, "css-snippets"), os.path.join(self.hafPublish.root, "css-snippets"))
        self.copyFile("css-snippets/publish.css", "/")


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
        mirrorRetreatsDir(lambda r: source.talksFolder(r), lambda r: target.talksFolder(r))
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
        website = self.hafPublish.website()
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
                    # enclosing <div>...</div> for admonitions suppresses Obsidian formatting, including links
                    # => replace some formatting inside admonitions w/ html
                    ml = MarkdownLine(line)
                    ml.convertFormattingToHtml()
                    ml.replaceLinks(lambda match: f"{convertMatchedObsidianLink(match, website)}")
                    admonitionLines.append(ml.text + '<br/>')
                continue
            
            newLines.append(line)
        return newLines


# fullstops in transcripts

    def modifyFullstopsInTranscripts(self):
        talkFilenames = self.hafWork.collectTalkFilenames()
        for talkFilename in talkFilenames:
            talk = TalkPage(talkFilename)
            headerTargets = talk.collectParagraphHeaderTargets()
            talkname = talknameFromFilename(talkFilename)

            # intentionally from the publish 
            print(talkname)
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
                            # we might have left out this particular paragraph from the talk
                            pass
                        else:
                            headerTarget = headerTargets[blockid]
                            if not headerTarget:
                                # probably ... (yet-missing paragraph description)
                                pass
                            else:
                                match = re.match(r'(.+)([.?!"]) \^' + blockid + "$", markdownLine.text)
                                if match:
                                    linkToTalk = f"[[{talkname}#{headerTarget}|{match.group(2)}]]"  # ∘∙⦿꘎᙮
                                    markdownLine.text = f"{match.group(1)}{linkToTalk} ^{blockid}"
            transcript.save(transcriptFilename)


# cut off internal links by converting them to html

    def __replaceLinks(self, filenames, css, filterFunc):
        website = self.hafPublish.website()        
        for filename in filenames:
            note = ObsidianNote(ObsidianNoteType.UNKNOWN, filename)
            for ml in note.markdownLines:
                ml.replaceLinks(lambda match: f"{convertMatchedObsidianLink(match, website, css, filterFunc)}")
            note.save()



    def replaceLinksInTalkPages(self):

        def filterLinksOnTalkPage(match):
            note = match.group('note')
            target = match.group('target')                                    
            if target and target.startswith('#^') and note in self.transcriptNameSet:
                # convert all links to blockid targets on transcripts
                return True            
            if note in self.indexEntryNameSet:
                # convert any index entry
                return True
            return False

        filenames = self.hafPublish.collectTalkFilenames()
        self.__replaceLinks(filenames, css=None, filterFunc=filterLinksOnTalkPage)


    def replaceLinksOnSpecialPages(self):
        index = os.path.join(self.hafPublish.root, 'Index.md')
        assert os.path.exists(index)
        self.__replaceLinks([index], css=None, filterFunc=lambda match: match.group('note') in self.indexEntryNameSet)

    def replaceLinksOnIndexEntryPages(self):
        filenames = self.hafPublish.collectIndexEntryFilenames()
        self.__replaceLinks(filenames, css=None, filterFunc=lambda match: match.group('note') not in self.indexEntryNameSet)


    def replaceLinksOnTranscriptPages(self):

        lastString = None
        notes = set()

        def filterLinksOnTranscriptPage(match):
            nonlocal lastString
            nonlocal notes

            note = match.group('note')
            if (match.string == lastString) and (note in notes):
                # recurring occurrences in the same paragraph will be filtered (i.e. have a special css class)
                return True
                
            if match.string != lastString:
                # next paragraph, next first occurrences will be shown as regular links
                notes = set()
                lastString = match.string

            # remember first note link and other "firsts" in the paragraph
            notes.add(note)
            return False

        filenames = self.hafPublish.collectTranscriptFilenames()
        self.__replaceLinks(filenames, css="transcript", filterFunc=filterLinksOnTranscriptPage)


