@echo off
cd  ..
"c:\Program Files\doxygen\bin\doxygen.exe" Docs\Evolife_Doxyfile.txt
echo Doc generated in %cd%\Docs\Classes
REM cd /D %cd%\Docs\html
REM cd /D %cd%\Docs