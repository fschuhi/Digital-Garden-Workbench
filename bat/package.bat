@echo off
echo.
set /p doit=do it?
if not "%doit%"=="do it" (
   echo aborted
   goto :EOF
)
echo.

python transcripts.py reindex
echo.

python talks.py update
echo.

python talks.py updateParagraphsLists
echo.

python index.py topTalks
echo.

python index.py topParagraphs
echo.

python HAFScripts.py transferFilesToPublish
echo.

echo.
echo INTENTION: "publish" from the publish vault
goto :EOF

:EOF
echo.
set uname=doit