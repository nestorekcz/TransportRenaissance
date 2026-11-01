@echo off
pushd "%~dp0"
openttd.exe -X -x -c openttd.cfg -g save\renaissance-coast.sav 1>stdout.log 2>stderr.log
popd
