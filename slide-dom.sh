#!/bin/bash
# feh --slideshow-delay 5 --fullscreen --auto-zoom --randomize /mnt/pixelparty/Photos_fête_Valou/

#mpv --fullscreen \
#    --image-display-duration=5 \
#    --vo=gpu \
#    --gpu-context=wayland \
#    --osd-level=0 \
#    --shuffle \
#    --loop-playlist=inf \
#    --blend-subtitles \
#    --interpolation \
#    /mnt/pixelparty/Photos_fête_Valou/*


imv-wayland -f -t 5 /mnt/pixelparty/Photos_fête_Valou/*
# imv-wayland -f -t 5 $(ls /mnt/pixelparty/Photos_fête_Valou/* | shuf)
