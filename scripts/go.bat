@echo off

:: Код ниже нужен для смены активной директории на ту, в которой текущий bat находится
:: без этого go.py может не найтись для питона
setlocal
cd /d %~dp0
cd /d ..

set PYTHONPATH=%cd%/src
set JIRA_HOST=https://helpdesk.compassluxe.com
call python -m tool_for_run_project.go %*
