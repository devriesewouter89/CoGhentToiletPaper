#! /bin/bash
echo "installing the fonts for the rpi"
mkdir /home/pi/.fonts
cp * /home/pi/.fonts
fc-list | grep "AV"
echo "use the AVHershey or other single line fonts"
