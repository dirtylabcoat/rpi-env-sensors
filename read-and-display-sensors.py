#!/usr/bin/env python3

import time
import bme680
import ST7789
from subprocess import PIPE, Popen
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

cpu_temps = []
factor = 1.0  # Smaller numbers adjust temp down, vice versa
smooth_size = 10

# Set the humidity baseline to 40%, an optimal indoor humidity.
hum_baseline = 40.0

# This sets the balance between humidity and gas reading in the
# calculation of air_quality_score (25:75, humidity:gas)
hum_weighting = 0.25

def get_cpu_temperature():
    process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE)
    output_bytes, _error = process.communicate()
    output = output_bytes.decode("utf-8")
    return float(output[output.index('=') + 1:output.index("'")])

def get_compensated_temperature(cpu_temps):
    cpu_temp = get_cpu_temperature()
    cpu_temps.append(cpu_temp)

    if len(cpu_temps) > smooth_size:
        cpu_temps = cpu_temps[1:]

    smoothed_cpu_temp = sum(cpu_temps) / float(len(cpu_temps))
    raw_temp = sensor.data.temperature
    comp_temp = raw_temp - ((smoothed_cpu_temp - raw_temp) / factor)

    return comp_temp

def get_gas_baseline(burn_in_time=300):
    start_time = time.time()
    curr_time = time.time()
    burn_in_data = []
    while curr_time - start_time < burn_in_time:
        curr_time = time.time()
        if sensor.get_sensor_data() and sensor.data.heat_stable:
            gas = sensor.data.gas_resistance
            burn_in_data.append(gas)
            time.sleep(1)
    gas_baseline = sum(burn_in_data[-50:]) / 50.0
    return gas_baseline

def get_air_quality_score(gas_baseline=-1):
    if gas_baseline < 0:
        gas_baseline = get_gas_baseline()

    gas = sensor.data.gas_resistance
    gas_offset = gas_baseline - gas

    hum = sensor.data.humidity
    hum_offset = hum - hum_baseline

    # Calculate hum_score as the distance from the hum_baseline.
    if hum_offset > 0:
        hum_score = (100 - hum_baseline - hum_offset)
        hum_score /= (100 - hum_baseline)
        hum_score *= (hum_weighting * 100)
    else:
        hum_score = (hum_baseline + hum_offset)
        hum_score /= hum_baseline
        hum_score *= (hum_weighting * 100)

     # Calculate gas_score as the distance from the gas_baseline.
    if gas_offset > 0:
        gas_score = (gas / gas_baseline)
        gas_score *= (100 - (hum_weighting * 100))
    else:
        gas_score = 100 - (hum_weighting * 100)

    # Calculate air_quality_score.
    air_quality_score = hum_score + gas_score

    return air_quality_score

# Init sensors
try:
    sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
except IOError:
    sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

# Oversampling settings
sensor.set_humidity_oversample(bme680.OS_2X)
sensor.set_pressure_oversample(bme680.OS_4X)
sensor.set_temperature_oversample(bme680.OS_8X)
sensor.set_filter(bme680.FILTER_SIZE_3)

sensor.set_gas_heater_temperature(320)
sensor.set_gas_heater_duration(150)
sensor.select_gas_heater_profile(0)

# Create ST7789 LCD display class.
disp = ST7789.ST7789(
    port=0,
    cs=ST7789.BG_SPI_CS_FRONT,  # BG_SPI_CSB_BACK or BG_SPI_CS_FRONT
    dc=9,
    backlight=19,               # 18 for back BG slot, 19 for front BG slot.
    spi_speed_hz=80 * 1000 * 1000
)

# Initialize display.
disp.begin()

# Set constants for width and height of the display.
WIDTH = disp.width
HEIGHT = disp.height
# Font, I'm using Roboto Mono from Google https://fonts.google.com/specimen/Roboto+Mono
FONT_TO_USE = "/usr/share/fonts/truetype/RobotoMono/RobotoMono-Medium.ttf"

img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 0))
draw = ImageDraw.Draw(img)
font = ImageFont.truetype(FONT_TO_USE, 24)
size_x, size_y = draw.textsize("", font)

text_x = 0
text_y = (80 - size_y) // 2

# Display message while getting gas baseline
draw.rectangle((0, 0, disp.width, 80), (0, 0, 0))
draw.text((text_x, text_y), "Collecting data\nfor air quality\nmeasurements.", font=font, fill=(0, 255, 0))
disp.display(img)
gas_baseline = get_gas_baseline(10)

while True:
    if sensor.get_sensor_data() and sensor.data.heat_stable:
        comp_temp = get_compensated_temperature(cpu_temps)
        temperature_str = "Tmp: {:.2f} *C".format(comp_temp)
        humidity_str = "Hum: {:.2f} %RH".format(sensor.data.humidity)
        pressure_str = "Prs: {:.2f} hPa".format(sensor.data.pressure)
        air_quality_score_str = "Air: {:.2f}".format(get_air_quality_score(gas_baseline))
        msg = "{0}\n{1}\n{2}\n{3}".format(temperature_str, humidity_str, pressure_str, air_quality_score_str)
        draw.rectangle((0, 0, WIDTH, HEIGHT), (0, 0, 0))
        draw.text((text_x, text_y), msg, font=font, fill=(0, 255, 0))
        disp.display(img)
        time.sleep(1.0)
