#!/bin/bash

# This needs to run as root.
# The script assumes your OS is Raspberry Pi OS and that the following hardware is installed
# on your Raspberry Pi Zero:
# Breakout Garden Mini (I2C + SPI) - https://shop.pimoroni.com/products/breakout-garden-mini-i2c-spi?variant=29495178362963
# BME680 Breakout - https://shop.pimoroni.com/products/bme680-breakout?variant=12491552129107
# 1.3" SPI Colour Square LCD (240x240) Breakout - https://shop.pimoroni.com/products/1-3-spi-colour-lcd-240x240-breakout?variant=30250963632211
# Note: I'm not affiliated with Pimoroni. It's just where I happened to buy these things.

if [ ! -f /usr/share/fonts/truetype/RobotoMono/RobotoMono-Medium.ttf ]; then
    echo 'Font not found!'
    echo "1. Download the font archive from https://fonts.google.com/specimen/Roboto+Mono"
    echo "2. Unzip and copy RobotoMono-Medium.ttf into /usr/share/fonts/truetype/RobotoMono/"
    echo "3. Rerun this script"
    exit 1
fi
raspi-config nonint do_i2c 0
python3 -m pip install -r ./requirements.txt
