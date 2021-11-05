@echo off
echo.
set /p doit=do it?
if not "%doit%"=="do it" (
   echo aborted
   goto :EOF
)
echo.

rem before onlyFirst, not allLinks, from 19.10.21 on allLinks
python transcripts.py reindex -allLinks
echo.

python talks.py update
echo.

python talks.py updateParagraphsLists
echo.

python index.py updateAlphabeticalIndex
echo.

python index.py topTalks
echo.

python index.py topParagraphs
echo.

python index.py topCooccurrences
echo.

python index.py allQuotes
echo.

python HAFScripts.py transferFilesToPublish
echo.

echo.
echo INTENTION: "publish" from the publish vault
goto :EOF

:EOF
echo.
set uname=doit