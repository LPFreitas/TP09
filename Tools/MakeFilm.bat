ffmpeg -y -framerate 5 -i ___Field_%%06d.png -c:v libx264 -vf scale=450:320 -pix_fmt yuv420p -r 30 Field.mov
ffmpeg -y -framerate 5 -i ___Curves_%%06d.png -c:v libx264 -vf scale=450:320 -pix_fmt yuv420p -r 30 Curves.mov
REM ffmpeg -i Field.mov -vf scale=512:364 -aspect 512:364 -c:v libx264 -r 30 Field.mp4
REM ffmpeg -i Curves.mov -vf scale=512:512 -aspect 1:1 -c:v libx264 -r 30 Curves.mp4
REM ffmpeg -i Curves.mp4 -i Field.mp4 -filter_complex "[0:v][1:v]vstack=inputs=2[v]" -map "[v]" Movie.mp4
ffmpeg -y -i Field.mov -vf scale=450:320 -aspect 450:320 -c:v libx264 -r 30 Field.mp4
ffmpeg -y -i Curves.mov -i Field.mp4 -filter_complex "[0:v][1:v]hstack=inputs=2[v]" -map "[v]" Movie.mp4
@echo ******************
@echo Movie.mp4 created
@ffmpeg -y -i Movie.mp4 -pix_fmt rgb24 -loop 0 Movie.gif
