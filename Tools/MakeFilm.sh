ffmpeg -y -framerate 5 -i ___Field_%06d.png -c:v libx264 -pix_fmt yuv420p -r 30 Field.mov
ffmpeg -y -framerate 5 -i ___Curves_%06d.png -c:v libx264 -pix_fmt yuv420p -r 30 Curves.mov

ffmpeg -y -i Field.mov -vf scale=450:320 -aspect 450:320 -c:v libx264 -r 30 Field.mp4

ffmpeg -y -i Curves.mov -i Field.mp4 -filter_complex "[0:v][1:v]hstack=inputs=2[v]" -map "[v]" Movie.mp4
