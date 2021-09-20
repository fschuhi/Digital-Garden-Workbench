#!/usr/bin/env python3

from util import collectFilenames, filterExt, loadLinesFromTextFile, saveLinesToTextFile
from HAFEnvironment import HAFEnvironment
from consts import HAF_PUBLISH_YAML, HAF_YAML

import os
import re
import shutil

def canonicalTimestamp(timestamp: str):
    if not timestamp: 
        return None
    else:
        parts = timestamp.split(':')
        canonicalParts = [part.rjust(2, '0') for part in parts]
        return ':'.join(canonicalParts)


# *********************************************
# class Publishing
# *********************************************

class Publishing:

    def __init__(self) -> None:
        self.hafWork = HAFEnvironment(HAF_YAML)
        self.hafPublish = HAFEnvironment(HAF_PUBLISH_YAML)


    def mirrorDir(self, funcSource, funcTarget, ext='.md'):
        for retreatName in self.hafWork.retreatNames:
            source = funcSource(retreatName)
            if not os.path.isdir(source):
                continue

            target = funcTarget(retreatName)

            if os.path.isdir(target):
                filenamesToDelete = [f for f in collectFilenames(target) if os.path.isfile(f)]
                for filename in filenamesToDelete:
                    os.remove(filename)

            filenames = collectFilenames(source)
            if ext:
                filenames = filterExt(filenames, ext)
            for filename in filenames:
                # copy2 because want to copy all metadata, otherwise no automatic pickup by the Obsidian display frontend
                # would also work w/ copy and copyfile, though
                shutil.copy2(filename, target)


    def mirrorRetreatFiles(self):
        source = self.hafWork
        target = self.hafPublish
        # we intentionally disregard Audio
        self.mirrorDir(lambda r: source.dirRetreat(r), lambda r: target.dirRetreat(r))
        self.mirrorDir(lambda r: source.dirPDF(r), lambda r: target.dirPDF(r), '.pdf')
        self.mirrorDir(lambda r: source.dirImages(r), lambda r: target.dirImages(r), None)
        self.mirrorDir(lambda r: source.dirTranscripts(r), lambda r: target.dirTranscripts(r))
        self.mirrorDir(lambda r: source.dirSummaries(r), lambda r: target.dirSummaries(r))


    def mirrorIndex(self):
        source = self.hafWork
        target = self.hafPublish
        self.mirrorDir(lambda d: source.dirIndexEntries, lambda d: target.dirIndexEntries)



    def copyFile(self, source, target=None):
        if not target:
            # only call w/ 1 param to indicate that the file should be copied to the same position in the publish tree
            target = source
        elif target == '/':
            # pass '/' to move the file (with the same name) to the publish root folder
            target = ""

        source = os.path.join(self.hafWork.dirRoot, source)
        target = os.path.join(self.hafPublish.dirRoot, target)

        # make sure that we have a target _filename_, even if path was passed (which is usually the case)
        if os.path.isdir(target):
            target = os.path.join(target, os.path.basename(source))

        shutil.copy2(source, target)

    
    def convertAllMarkdownFiles(self):
        filenames = filterExt(self.hafPublish.allFiles, '.md')
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
            match = re.search(r"!\[\[(?P<date>[0-9]+)-(?P<middle>.+)-(?P<audioid>[0-9]+).mp3(#t=(?P<timestamp>[0-9:]+))?\]\]", line)
            if match:
                date = match.group('date')
                middle = match.group('middle')
                audioid = match.group('audioid')
                timestamp = canonicalTimestamp(match.group('timestamp'))

                # <audio controls style=" width:300px;" controlslist="nodownload"><source src="https://dharmaseed.org/talks/62452/20200301-Rob_Burbea-GAIA-preliminaries_regarding_voice_movement_and_gesture_part_1-62452.mp3#t=00:13:09" type="audio/mpeg">???</audio>
                source = f"https://dharmaseed.org/talks/{audioid}/{date}-{middle}-{audioid}.mp3" + (f"#t={timestamp}" if timestamp else "")
                html5 = f'<audio controls style=" width:300px;" controlslist="nodownload"><source src="{source}" type="audio/mpeg">???</audio>'

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

