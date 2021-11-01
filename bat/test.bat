@echo off

rem set bla=testing\test_MarkdownLine.py Test_MarkdownSnippet.test_reindexProblem2
set bla=testing\test_TalkSection.py TestTalkSection.test_parseCounts

echo running "%bla%"
set PYTHONPATH=S:\work\python\HAF

python %bla%