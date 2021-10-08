@echo off
copy RB.yaml RB.yaml.bak
python HAFScripts.py --script sortRBYaml

rem python HAFScripts.py --script sortRBYaml --sectionsort
