@echo off

:: Код ниже нужен для смены активной директории на ту, в которой текущий bat находится
:: без этого файл *.py может не найтись для питона
setlocal
cd /d %~dp0
cd /d ..

set PYTHONPATH=%cd%
set JIRA_HOST=https://helpdesk.compassluxe.com
call python core/jira.py %*
