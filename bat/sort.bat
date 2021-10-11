@echo off
copy RB.yaml RB.yaml.bak
python HAFScripts.py sortRBYaml
rem python HAFScripts.py sortRBYaml --sectionsort
