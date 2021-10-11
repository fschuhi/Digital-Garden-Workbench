@echo off
if "%1" == "" (
   echo param 'old' missing
   goto :EOF
)
if "%2" == "" (
   echo param 'new' missing
   goto :EOF
)
python HAFScripts.py replace --old %1 --new %2

:EOF