@echo off
del Evolife*.xjl Evolife*.html Classes.xjl Classes.html
DocGenerate.py
for %%f in (*.xjl); do; %%f
echo .
echo Transporter les fichiers .html sur Evolife.Classes