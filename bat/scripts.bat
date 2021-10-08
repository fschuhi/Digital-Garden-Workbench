@echo off
cls
set bla=%1
if "%bla%" == "" (
   set bla=HAFScripts
)
echo %bla%
python %bla%.py --scripts