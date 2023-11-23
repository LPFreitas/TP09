@echo off
for /L %%f in (1,1,9) do (
if EXIST Classes%%f.dot (
call dot -Tgif -Gdpi=300 -o Images\Classes%%f.gif Classes%%f.dot 
echo Classes%%f.gif
))

set fmt=svg
for %%f in (Ecology Scenario Observer Graphics Window) do (
REM call dot -T%fmt% -Gdpi=300 -o Images\Evolife_%%f.%fmt% Evolife_%%f.dot 
call dot -T%fmt% -o Images\Evolife_%%f.%fmt% Evolife_%%f.dot 
echo Evolife_%%f.%fmt%
)

rem dot -Tgif -o Evolife_schema1.gif Evolife_schema1.dot
rem echo Evolife_schema1.gif
