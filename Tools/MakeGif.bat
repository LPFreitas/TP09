REM @for /F "tokens=2-4 delims==\" %%A in ('ftype Magick.MVGFile') do @set MagickPath=%%A\%%B\%%C
REM %MagickPath%\convert.exe" -delay 3 ___CF_0*.png -loop 1 EvolifeMovie.mpg

@ffmpeg -y -framerate 5 -i ___Field_%%06d.png -c:v libx264 -pix_fmt yuv420p -r 30 Field.mov
@ffmpeg -y -i Field.mov -pix_fmt rgb24 -loop 0 Field.gif
@echo ******************
@echo Field.gif created