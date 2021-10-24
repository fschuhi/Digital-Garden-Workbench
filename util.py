#!/usr/bin/env python3

import os
import re
import shutil
import yaml
import csv
import consts

# *********************************************
# shared types
# *********************************************

from typing import Tuple
TFootnote = Tuple[str, int]
TFootnotes = list[TFootnote]


# *********************************************
# script support
# *********************************************

def isScriptArg(args, check):
    if isinstance(check, list):
        lower = [s.lower() for s in check]
        return args.script.lower() in lower
    else:
        return args.script.lower() == check.lower()

def dumpScripts(py):
    lines = loadLinesFromTextFile(py)
    lastcomment = ''
    first = True
    for line in lines:
        match = re.match(r"    # (.+)", line)
        if match:
            lastcomment = match.group(1)
        match = re.match(r"    elif isScript\('(.+)'\)", line)
        if match:
            if lastcomment != '':
                print(('' if first else '\n') + '# ' + lastcomment)
                lastcomment = ''
                first = False
            script = match.group(1)
            print('  ' + script)


def exitError(err: str):
    print(err)
    exit()

def exitHelp(help):
    if type(help) is str:
        print(help)
    elif type(help) is list:
        for line in help:
            if type(line) is str:
                print(line)
            elif type(line) is list:
                for subline in line:
                    print(subline)
    exit()

def exitIfNone(o, what):
    if not o:
        exitError("missing " + what)


# *********************************************
# deitalizise
# *********************************************

def deitalicizeWithReplace(text: str, term: str) -> str:
    text = text.replace('_' + term + '_', term)
    text = text.replace('_' + term + ',_', term + ',')
    text = text.replace('_' + term + '._', term + '.')
    text = text.replace('_' + term.capitalize() + '_', term.capitalize())
    text = text.replace('_' + term.capitalize() + ',_', term.capitalize() + ',')
    text = text.replace('_' + term.capitalize() + '._', term.capitalize() + '.')
    return text

def deitalicizeTerm(text: str, term: str) -> str:
    seps = '[,.:;– )’!-]*?'
    text = re.sub(f"_({term})({seps})_", "\\1\\2", text)
    capitalized = term.capitalize()
    text = re.sub(f"_({capitalized})({seps})_", "\\1\\2", text)
    text = re.sub(f"_({capitalized[0]})_+({capitalized[1:]})({seps})_", "\\1\\2\\3", text)
    return text

def deitalicizeTerms(text: str, terms: list[str]) -> str:
    for term in terms:
        text = deitalicizeTerm(text, term)
    return text

# ((IKTVHOR)) Deitalicize with yaml
def deitalicizeTermsWithDiacritics(text: str) -> str:
    return deitalicizeTerms(text, [\
        'anattā', 'arūparāga', 'āsavas', \
        'bodhicitta','brahmavihāra', 'brahmavihāras', \
        'chandarāga', \
        'dāna', 'dharma', 'dharmas', 'dukkha', \
        'jhāna', 'jhānas', \
        'kāma', 'kāmacchanda', 'kāmeti', 'karuṇā', \
        'mettā', 'muditā', 'mudrā', 'mudrās', \
        'papañca', 'pīti' \
        'rāga', 'rūpa', 'rūparāga', \
        'samādhi', 'samatha', 'saṃsāra', 'saṃyojanāni', 'Saṃyutta Nikāya', 'saṅkhārā', 'saṅkhāras', 'Satipaṭṭhāna Sutta', 'sīla', \
        'taṇhā', \
        'upādāna', 'upekkhā', \
        'vedanā', 'vibhava-taṇhā', \
        ] )


# *********************************************
# save/load text files
# *********************************************

trick = {} # type: dict[str,str]

def loadStringFromTextFile(sfn) -> str:
    if sfn in trick:
        text = trick[sfn]
    else:
        with open(sfn, 'r', encoding='utf-8') as f:
            text = f.read()
            f.close
        trick[sfn] = text
    return text


def loadLinesFromTextFile(sfn) -> list[str]:
    return loadStringFromTextFile(sfn).splitlines()


def saveStringToTextFile(sfn, text: str):
    trick[sfn] = text
    with open(sfn, 'w', encoding='utf-8', newline='\n') as f:
        print(text, file=f, end='')
        f.close()


def saveLinesToTextFile(sfn, lines: list[str]):
    text = '\n'.join(lines) + '\n'
    saveStringToTextFile(sfn, text)


# *********************************************
# csv read/write
# *********************************************

def loadTuplesFromCsv(path) -> list[Tuple]:
    tuples = []
    with open(path, newline='', encoding='utf8') as csvfile:
        reader = csv.reader(csvfile, delimiter=';', quotechar='"')
        for row in reader:
            tuples.append(tuple(row))
    return tuples

def saveTuplesToCsv(path, tuples: list[Tuple]):
    with open(path, 'w', newline='', encoding='utf8') as csvfile:
        csvfile.write('\ufeff')
        writer = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for tuple in tuples:
            writer.writerow(list(tuple))


# *********************************************
# file system
# *********************************************

def basenameWithoutExt(sfn):
    return os.path.splitext(os.path.basename(sfn))[0]


def collectFilenames(dir) -> list[str]:
    filenames = []
    for entry in os.scandir(dir):
        if os.path.isfile(entry):
            filenames.append(entry.path)
    return filenames


def filterExt(filenames: list[str], targetExt):
    targetExt = targetExt if targetExt.startswith('.') else '.' + targetExt
    filteredFilenames = []
    for filename in filenames:
        (filenameWithoutExt, ext) = os.path.splitext(filename)
        if ext == targetExt:
            filteredFilenames.append(filename)
    return filteredFilenames


def excludeFiles(files, pattern):
    # interesting other choice, using set differences: https://stackoverflow.com/questions/20638040/glob-exclude-pattern
    return [filename for filename in files if not re.search(pattern, filename)]

def includeFiles(files, pattern):
    return [filename for filename in files if re.search(pattern, filename)]


def splitall(path):
    # https://www.oreilly.com/library/view/python-cookbook/0596001673/ch04s16.html
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path: # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts


def createTempfile():
    import tempfile
    tmp = tempfile.TemporaryFile('w+t')
    tmp.close()
    return tmp


def mirrorDir(source, target, ext=None):
    if not (os.path.isdir(target) and os.path.isdir(source)):
        return

    nAdded = 0

    filenamesToDelete = [f for f in collectFilenames(target) if os.path.isfile(f)]
    for filename in filenamesToDelete:
        os.remove(filename)

    filenames = collectFilenames(source)
    if ext:
        filenames = filterExt(filenames, ext)
    for filename in filenames:
        # copy2 because want to copy all metadata, otherwise no automatic pickup by the Obsidian display frontend
        # would also work w/ copy and copyfile, though
        #print(filename, target)
        shutil.copy(filename, target)
        nAdded += 1

    return nAdded


# *********************************************
# yaml
# *********************************************

def loadYaml(sfnHAFYaml) -> dict[str,str]:
    dict = {}
    with open(sfnHAFYaml, 'r', encoding='utf-8', newline='\n') as stream:
        dict = yaml.load(stream, Loader=yaml.FullLoader)
        stream.close()
    return dict


def loadFrontmatter(lines: list[str]) -> list[str]:
    yamlLines = []
    if lines[0] != '---':
        return None
    for line in lines[1:]:
        if line == '---':
            break
        yamlLines.append(line)
    return yamlLines


def extractYaml(lines: list[str]) -> dict[str,str]:
    yamlLines = loadFrontmatter(lines)
    if not yamlLines:
        return
    from io import StringIO
    file_like_io = StringIO('\n'.join(yamlLines))
    import yaml
    dictYaml = yaml.load(file_like_io, Loader=yaml.FullLoader)
    return dictYaml
    

# *********************************************
# regex
# *********************************************

def setMatchField(obj, fieldName, match: re.match, func = None):
    m = match.group(fieldName)
    value = None if m is None else (m if func is None else func(m))
    setattr(obj, fieldName, value if value else None)


# *********************************************
# GUI
# *********************************************

import tkinter
from tkinter import messagebox

def showMessageBox(theMessage, theTitle=None):
    # https://stackoverflow.com/questions/2963263/how-can-i-create-a-simple-message-box-in-python
    window = tkinter.Tk()
    window.wm_withdraw()
    messagebox.showinfo(title=theTitle if theTitle else "showMessageBox", message=theMessage)

def askYesNoCancel(theMessage, theTitle=None):
    window = tkinter.Tk()
    window.wm_withdraw()
    return messagebox.askyesnocancel(title=theTitle if theTitle else "askYesNoCancel", message=theMessage)

def askRUN():
    global askRUN
    if askRUN is None:
        askRUN = True
    if not askRUN:
        return None
    res = askYesNoCancel("RUN  " + thisFunctionName(1) + " ?", "RUN")
    askRUN = res is not None
    return res

# *********************************************
# reflection
# *********************************************

def thisFunctionName(stackLevel: int = 0):
    # https://stackoverflow.com/questions/5067604/determine-function-name-from-within-that-function-without-using-traceback
    import inspect
    return inspect.stack()[1][3] if stackLevel == 0 else inspect.stack()[1+stackLevel][3]


# *********************************************
# canonicalize
# *********************************************

def canonicalizeText(text) -> str:
    text = text.replace('\n', ' ')
    text = text.rstrip()
    text = re.sub("  +", " ", text )
    text = re.sub("[“”“]", '"', text)
    text = re.sub("[‘’]", '\'', text)    
    text = re.sub("([^-])--([^-])", "\\1 - \\2", text)
    text = re.sub("[–-]+","-", text)  # short and long dash
    text = re.sub("([^ ])- ([^ ])", "\\1-\\2", text)
    #text = re.sub(r"\.\.\.+", "... ", text)
    text = re.sub(" \.\. ", "... ", text)
    text = re.sub("([^.])\.\.([^. ])", "\\1... \\2", text)
    text = re.sub("([^.])\.\. ", "\\1... ", text)
    text = re.sub("([^ ]) ,([^ ])", "\\1, \\2", text)
    text = re.sub("…", "...", text)

    # 04.10.21 no idea why the following; it removes normal figures
    # text = re.sub("^[0-9]+ ", "", text)
    # text = re.sub(" [0-9]+ ", "", text)

    return text


def decontractText(text) -> str:
    text = re.sub("I['’]m", "I am", text )
    text = re.sub("(I|you|You|We|we|They|they)['’]ve", "\\1 have", text )
    text = re.sub("(I|you|You|We|we|They|they)['’]ll", "\\1 will", text )
    text = re.sub("(What|what|It|it|There|there|That|that|She|He|s?he|Who|who|When|when|Here|here|[Ee]verything|cat)['’]s", "\\1 is", text )
    text = re.sub("(Let|let)['’]s", "\\1 us", text )
    text = re.sub("(You|you|We|we|They|they)['’]re", "\\1 are", text )
    text = re.sub("(You|you|We|we|They|they)['’]d", "\\1 would", text )
    text = re.sub("(Do|do|Does|does|Is|is|Have|have|Did|did|Would|would|Should|should|Could|could|Was|was)n['’]t", "\\1 not", text )
    text = re.sub("([Cc])an['’]t", "\\1an not", text)
    text = re.sub("([Ww])on['’]t", "\\1ill not", text)
    return text


def forceLFOnly(dir):
    for filename in collectFilenames(dir):
        lines = loadLinesFromTextFile(filename)
        saveLinesToTextFile(filename, lines)


# *********************************************
# Obsidian links
# *********************************************

def removeObsidianLinksFromText(text):
    while True:            
        if not (matchLink := re.search(r"\[\[.+?\]\]", text)):
            break

        link = matchLink[0]        
        matchLinkParts = re.search(r"\[\[([^|]+)(\|(.+))?\]\]", link)
        linkReference = matchLinkParts[1]
        linkDisplayText = matchLinkParts[3] if matchLinkParts[3] else linkReference

        start = matchLink.start()
        end = matchLink.end()
        text = text[:start] + linkDisplayText + text[end:]
    return text


# complete: link w/o [[ and ]]
#    link: note or note+target
#       note: md file (actually case insensitive)
#       target: either "#header" or "#^1-1"
#          header: #header
#          blockid: 1-1
#    shown: part of Obsidian link after |

#ObsidianLinkPattern = r"\[\[(?P<complete>(?P<link>(?P<note>[^#\]|]+)(?P<target>#((\^(?P<blockid>[^\]|]+))|(?P<header>[^\]|]+)))?)(\|(?P<shown>.+?))?)\]\]"
ObsidianLinkPattern = r"\[\[(?P<complete>(?P<link>(?P<note>[^#\]|]+)(?P<target>#(\^(?P<blockid>[^\]|]+))?[^\]|]*)?)(\|(?P<shown>.+?))?)\]\]"


def searchObsidianLink(text) -> re.Match:
    return re.search(ObsidianLinkPattern, text)


def matchedObsidianLinkToString(match: re.Match, newNote: str=None, retainShown: bool=True) -> str:
    # IMPORTANT: passing newNote might not only convert the link back to the original string but also does some replacement

    note = match.group('note')
    usedNote = newNote if (newNote and newNote.lower() != note.lower()) else note
    s = '[[' + usedNote

    target = match.group('target')
    if target:
        s += target

    shown = match.group('shown')
    if shown:
        if shown != usedNote:
            s += '|' + shown
    else:
        # IMPORTANT: We cannot just replace the originally referenced note (which is backed by an md file) w/ a new note, at least not in all situations.
        # Say, the original link was [[some link]] w/ the page "Some Link.md". That works because Obisidian note references are case-insensitive.
        # In this case we need to still show _some link_ in the preview, so the original needs to be swapped into the "shown" part.
        # Trivially, if we already have a shown part then we can simply replace the old note w/ the new one.
        if newNote and retainShown and newNote.lower() != note.lower():
            s += '|' + note

    return s + ']]'


def convertMatchedObsidianLink(match, root, css=None, filter=None):

    # ugly but pragmatic: pass either None or string or lambda as css
    # ((BADXOEH))
    isSimpleCss = (not css) or isinstance(css, str)

    if filter and not (filterResult:=filter(match)):        
        if isSimpleCss:
            # links
            return match.group(0)
    
    if not isSimpleCss:
        css = css(filterResult)

    import urllib.parse
    link = match.group('link')
    note = match.group('note')
    target = match.group('target')
    shownLink = match.group('shown')

    # pipe | in links in tables have to be escaped
    if link and link.endswith("\\"): link = link[:-1]
    if target and target.endswith("\\"): target = target[:-1]

    # ((TVPBHSJ)) need to make sure that we don't mess up a's attributes
    # note: only "", not '' (Perfection and Christ's Blessing)
    link = link.replace('"', '')

    encodedNote = urllib.parse.quote_plus(note)

    if not target:
        encodedTarget = ''
        ariaLabel = note
    elif target.startswith('#^'):
        blockid = target[2:]
        encodedTarget = '#^' + urllib.parse.quote_plus(blockid)
        shownLink = shownLink if shownLink else note
        ariaLabel = f"{note} > ^{blockid}"
    elif target.startswith('#'):
        header = target[1:]
        encodedTarget = '#' + urllib.parse.quote_plus(header)
        ariaLabel = f"{note} > {header}"
        shownLink = shownLink if shownLink else ariaLabel
    else:
        assert False
    
    if shownLink:
        assert ariaLabel
        # see ((TVPBHSJ)) above
        ariaLabel = ariaLabel.replace("'", "")
        ariaLabel = ariaLabel.replace('"', '')
        ariaAttributes = f'aria-label-position="top" aria-label="{ariaLabel}" '
    else:
        ariaAttributes = ""
        shownLink = note

    from html import escape
    shownLink = escape(shownLink)

    # ((DFMYOIR))
    # h.obsidian.md/rob-burbea/2020+Vajra+Music/Transcript+pages/0301+Preliminaries+Regarding+Voice%2C+Movement%2C+and+Gesture+-+Part+1#^1-1

    # 24.10.21 target="_blank" and rel="noopener" are added by Obsidian Publish to all links, so we don't have to add it manually (except for the test cases)
    # https://stackoverflow.com/questions/50709625/link-with-target-blank-and-rel-noopener-noreferrer-still-vulnerable
    # href is *also* not necessary, because that's also generated on the fly => we only need the data-href and the class
    if consts.long_a_attributes:
        a = '<a ' + ariaAttributes + f'data-href="{link}" href="{root}{encodedNote}{encodedTarget}" class="internal-link" target="_blank" rel="noopener">{shownLink}' + '</a>'
    else:
        a = '<a ' + ariaAttributes + f'data-href="{link}" class="internal-link">{shownLink}' + '</a>'

    return f'<span class="{css}">{a}</span>' if css else a


def parseParagraph(paragraphOnPage: str):
    match = re.search(r"^(.+) \^([0-9]+)-([0-9]+)$", paragraphOnPage)
    if not match:
        return (None, None, None)
    paragraphText = match.group(1)
    pageNr = int(match.group(2))
    paragraphNr = int(match.group(3))
    return pageNr, paragraphNr, paragraphText


def determineHeaderTarget(header):
    # IMPORTANT: the "..." for yet-missing paragraph description will be ''
    header = re.sub(r"[./]", " ", header)
    header = re.sub(r"[,:?=()]", "", header)
    header = re.sub(r"  +", " ", header)
    return header


def parseBlockId(blockid) -> Tuple[int,int]:
    match = re.match(r"([0-9]+)-([0-9]+)", blockid)
    return (int(match.group(1)), int(match.group(2))) if match else None


def parseAudioLink(text) -> re.Match:
    return re.search(r"!\[\[(?P<filename>(?P<date>[0-9]+)-(?P<middle>.+)-(?P<audioid>[0-9]+).mp3)(#t=(?P<timestamp>[0-9:]+))?\]\]", text)

def canonicalTimestamp(timestamp: str):
    if not timestamp: 
        return None
    else:
        parts = timestamp.split(':')
        canonicalParts = [part.rjust(2, '0') for part in parts]
        return ':'.join(canonicalParts)

def createAudioLink(date, middle, audioid, timestamp):
    return f"![[{date}-{middle}-{audioid}.mp3#t={timestamp}]]"

