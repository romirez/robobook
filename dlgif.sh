#!/bin/sh

wget $1 -O temp.gif
#convert temp.gif -background black -coalesce -scale 64x64 -remap temp.gif[0] temp.gif
convert temp.gif -background black -coalesce -scale 64x64 temp.gif
num1=`ls -1 gifs/ | wc -l`
num2=`expr $num1 + 1`
mv temp.gif gifs/$num2.gif
echo $num2.gif done!
read -p "test? " yn 
echo    # (optional) move to a new line
case yn in 
	[Yy]* ) sudo /home/pi/led-image-viewer --led-rows=64 --led-cols=64 --led-brightness=50 --led-rgb-sequence=RBG gifs/$num2.gif; break;;
esac
