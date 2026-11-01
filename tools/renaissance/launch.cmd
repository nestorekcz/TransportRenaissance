@echo off
pushd "%~dp0"
openttd.exe -X -c openttd.cfg 1>stdout.log 2>stderr.log
popd
