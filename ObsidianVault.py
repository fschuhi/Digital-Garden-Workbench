#!/usr/bin/env python3

from consts import HAF_YAML_TESTING
import os
import glob
from util import *


# *********************************************
# ObsidianVault
# *********************************************

class ObsidianVault:

    def __init__(self, root):
        self.root = os.path.normpath(root)
        self.rootDepth = len(splitall(self.root))

    def pathnames(self, *paths):
        return glob.glob(os.path.join(self.root, *paths), recursive=True)

    def allFiles(self):
        return self.pathnames('**/*.*')

    def allNotes(self):
        return self.pathnames('**/*.md')

    def folderFiles(self, folder, ext):
        if not ext.startswith('*.'):
            ext = '*.' + ext
        return self.pathnames(f'**/{folder}/{ext}')

    def folderNotes(self, folder):
        return self.folderFiles(folder, 'md')

    def relative(self, sfn):
        parts = splitall(sfn)[self.rootDepth:]
        return os.path.join(*parts)

    def toplevelFolder(self, sfn):
        parts = splitall(sfn)[self.rootDepth:]
        return parts[0]


if __name__ == "__main__":
    dict = loadYaml(HAF_YAML_TESTING)
    root = os.path.normpath(dict['Root'])
    rootDepth = len(splitall(root))
    retreatNames = dict['Retreats']

    vault = ObsidianVault(root)
    print(vault.folderNotes('2020 Vajra Music/**'))



