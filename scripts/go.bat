@echo off

:: Код ниже нужен для смены активной директории на ту, в которой текущий bat находится
:: без этого go.py может не найтись для питона
setlocal
cd /d %~dp0
cd /d ..

call python go.py %*
