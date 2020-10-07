import board
import displayio
import busio
import digitalio
import adafruit_bme280
from adafruit_display_text import label
#from adafruit_st7735 import ST7735
#from adafruit_ili9341 import ILI9341
from adafruit_bitmap_font import bitmap_font
from adafruit_display_shapes.roundrect import RoundRect
import adafruit_gps
import time
import gc
from micropython import const, opt_level
from microcontroller import cpu
import terminalio
opt_level(3)
gc.enable( )
gc.collect()
i2c = busio.I2C(board.B6, board.B7)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
bme280.sea_level_pressure = 1011.92
bme280.mode = adafruit_bme280.MODE_NORMAL
bme280.standby_period = adafruit_bme280.STANDBY_TC_500
bme280.iir_filter = adafruit_bme280.IIR_FILTER_X16
bme280.overscan_pressure = adafruit_bme280.OVERSCAN_X16
bme280.overscan_humidity = adafruit_bme280.OVERSCAN_X1
bme280.overscan_temperature = adafruit_bme280.OVERSCAN_X2
uart = busio.UART(board.A2, board.A3, baudrate=9600, timeout=10)
gps = adafruit_gps.GPS(uart, debug=False)
gps.send_command(const(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0"))
gps.send_command(const(b"PMTK220,1000"))

btn = digitalio.DigitalInOut(board.B0)
btn.direction = digitalio.Direction.INPUT
btn.pull = digitalio.Pull.DOWN

# Release any resources currently in use for the displays
displayio.release_displays()
# Display init
spi = busio.SPI(clock=board.B10, MOSI=board.B15, MISO=board.B14)
while not spi.try_lock():
    pass
spi.configure(baudrate=25000000, phase=0, polarity=0)
spi.unlock()

init_sequence = (
    b"\x01\x80\x32"  # _SWRESET and Delay 50ms
    b"\x11\x80\xFF"  # _SLPOUT
    b"\x3A\x81\x05\x0A"  # _COLMOD
    b"\xB1\x83\x00\x06\x03\x0A"  # _FRMCTR1
    b"\x36\x01\x08"  # _MADCTL
    b"\xB6\x02\x15\x02"  # _DISSET5
    # 1 clk cycle nonoverlap, 2 cycle gate, rise, 3 cycle osc equalize, Fix on VTL
    #b"\xB4\x00\x00"  # _INVCTR line inversion
    b"\xC0\x82\x02\x70\x0A"  # _PWCTR1 GVDD = 4.7V, 1.0uA, 10 ms delay
    b"\xC1\x01\x05"  # _PWCTR2 VGH = 14.7V, VGL = -7.35V
    b"\xC2\x02\x01\x02"  # _PWCTR3 Opamp current small, Boost frequency
    b"\xC5\x82\x3C\x38\x0A"  # _VMCTR1
    b"\xFC\x02\x11\x15"  # _PWCTR6
    b"\xE0\x10\x09\x16\x09\x20\x21\x1B\x13\x19\x17\x15\x1E\x2B\x04\x05\x02\x0E"  # _GMCTRP1 Gamma
    b"\xE1\x90\x0B\x14\x08\x1E\x22\x1D\x18\x1E\x1B\x1A\x24\x2B\x06\x06\x02\x0F\x0A"  # _GMCTRN1
    b"\x13\x80\x0a"  # _NORON
    b"\x29\x80\xFF"  # _DISPON
)

display_bus = displayio.FourWire(spi, command=board.B8, chip_select=board.B9, reset=board.B5)
#display = ILI9341(display_bus, width=160, height=128)
display = displayio.Display(display_bus, init_sequence, width=128, height=160)
display.rotation=90

print(const("Initializing UI..."))
# Fonts
font10 = terminalio.FONT
font20 = bitmap_font.load_font("fonts/dseg-10.bdf")
font_spd = bitmap_font.load_font("fonts/dseg-48.bdf")

# UI
print(const("Loading fonts..."))
main_group = displayio.Group(max_size=50)
#background
bg_bitmap = displayio.Bitmap(160, 128, 2)
bg_palette = displayio.Palette(1)
bg_palette[0] = 0xffbf00 # Bright Green
bg_sprite = displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette, x=0, y=0)
main_group.append(bg_sprite)
# Main Screen Round rectangle
roundrect = RoundRect(2, 2, 156, 124, 5, fill=0x454545, outline=0x454545, stroke=2)
main_group.append(roundrect)
# Status Bar Down
status_text = "              "
status = label.Label(font10, text=status_text, color=0xffffff)
status.x = 120
status.y = 25
main_group.append(status)
# Status Bar Time
caption_text = "                           "
caption = label.Label(font10, text=caption_text, color=0xffffff)
caption.x = 78
caption.y = 119
caption.scale = 1
main_group.append(caption)
# SPEED Value
speed_text = "00"
speed_value = label.Label(font_spd, text=speed_text, color=0xffbf00)
speed_value.x = 45
speed_value.y = 32
speed_value.scale = 1
main_group.append(speed_value)
# Speed Unit
speed_unit_text = "km/h"
speed_unit = label.Label(font10, text=speed_unit_text, color=0xffffff)
speed_unit.x = 120
speed_unit.y = 10
speed_unit.scale = 1
main_group.append(speed_unit)
print(str(gc.mem_free()) + const("b of RAM free"))
# Coord
coord_data_text = "                                            "
coord_data = label.Label(font10, text=coord_data_text, color=0xffffff)
coord_data.x = 7
coord_data.y = 106
main_group.append(coord_data)

# Fix_quality
fq_text = "     "
fq = label.Label(font10, text=fq_text, color=0xffffff)
fq.x = 121
fq.y = 37
main_group.append(fq)

# Shapes
frame_1 = RoundRect(3, 3, 42, 33, 5, fill=0xffbf00, outline=0x454545, stroke=2)
main_group.append(frame_1)
frame_2 = RoundRect(3, 35, 42, 33, 5, fill=0xffbf00, outline=0x454545, stroke=2)
main_group.append(frame_2)
frame_3 = RoundRect(3, 67, 42, 33, 5, fill=0xffbf00, outline=0x454545, stroke=2)
main_group.append(frame_3)
# Pressure
press_label_text = "P.mmHg"
press_label = label.Label(font10, text=press_label_text, color=0x454545)
press_label.x = 6
press_label.y = 10
main_group.append(press_label)
# Pressure Value
press_value_text = "   "
press_value = label.Label(font20, text=press_value_text, color=0x454545)
press_value.x = 5
press_value.y = 25
press_value.scale = 1
main_group.append(press_value)
# Altitude
humi_label_text = "HUMI"
humi_label = label.Label(font10, text=humi_label_text, color=0x454545)
humi_label.x = 12
humi_label.y = 41
main_group.append(humi_label)

humi_text = "?        "
humi = label.Label(font20, text=humi_text, color=0x454545)
humi.x = 5
humi.y = 57
humi.scale = 1
main_group.append(humi)
# Temperature BME
bme_temp_label_text = "TEMP"
bme_temp_label = label.Label(font10, text=bme_temp_label_text, color=0x454545)
bme_temp_label.x = 12
bme_temp_label.y = 73
main_group.append(bme_temp_label)

bme_temp_value_text = '?     '
bme_temp_value = label.Label(font20, text=bme_temp_value_text , color=0x454545)
bme_temp_value.x = 6
bme_temp_value.y = 90
bme_temp_value.scale = 1
main_group.append(bme_temp_value)
# COUNTER
# counter label
#counter_label_text = 'DISTANCE'
#counter_label = label.Label(font10, text=counter_label_text, color=0xffbf00)
#counter_label.x = 106
#ounter_label.y = 85
#main_group.append(counter_label)
# counter value
counter_text = '000000     '
counter = label.Label(font20, text=counter_text , color=0xffffff)
counter.x = 76
counter.y = 91
counter.scale = 1
main_group.append(counter)
#Free resources
sys_stat_text = 'Sysytem Status Check            '
sys_stat_label = label.Label(font10, text=sys_stat_text, color=0xffffff)
sys_stat_label.x = 7
sys_stat_label.y = 119
main_group.append(sys_stat_label)

# Time value
timer_text = '00:00'
timer_label = label.Label(font20, text=timer_text, color=0xffffff)
timer_label.x = 97
timer_label.y = 73
main_group.append(timer_label)

#Show display
display.show(main_group)
display.auto_refresh = True
# Main loop
last_print = time.monotonic()
gc.collect()
#main loop
while True:
    # Button
    if btn.value:
        print("press")
    gc.collect()
    try:
        bme_temp_value._update_text("{}".format(round(bme280.temperature)) + chr(0176))
        humi._update_text("{}".format(round(bme280.humidity)) + "%")
        press_value._update_text("{}".format(round(bme280.pressure * 0.75)))
    except:
        pass
    try:
        gps.update()
    except:
        pass
    current = time.monotonic()
    if current - last_print >= 1.0:
        last_print = current
        if not gps.has_fix:
            # Try again if we don't have a fix yet.
            status._update_text("SA:?")
            #print("Waiting for fix...")
            continue
            #print("Fix quality: {}".format(gps.fix_quality))
    if gps.fix_quality is not None:
       fq._update_text("FQ:{}".format(gps.fix_quality))
    # Coordinates
    if gps.latitude is not None:
        coord_data._update_text("LAT:{0:.5f}".format(gps.latitude) + chr(0176) + "LON:{0:.5f}".format(gps.longitude) + chr(0176))
        #print(len(coord_data.text))
    else:
        coord_data._update_text("LAT:0000000" + chr(0176) +  " LON:0000000" + chr(0176))
        #print(len(coord_data.text))
    gc.collect()
    # Speed Value Change
    if gps.speed_knots is not None:
        speed_value._update_text("{:0>2}".format(round(gps.speed_knots * 1.852)))
    # Sattelites Label Change
    if gps.satellites is not None:
		#print("# satellites: {}".format(gps.satellites))
		status._update_text("SA:{}".format(gps.satellites))
    if gps.timestamp_utc is not None:
        caption._update_text("{:02}/{:02}/{}".format(
                gps.timestamp_utc.tm_mday,  # struct_time object that holds
                gps.timestamp_utc.tm_mon,  # Grab parts of the time from the
                gps.timestamp_utc.tm_year,  # the fix time.  Note you might
                #gps.timestamp_utc.tm_hour + 3,  # not get all data like year, day,
                #gps.timestamp_utc.tm_min,  # month!
        ))
        timer_label._update_text("{:0>2}".format(gps.timestamp_utc.tm_hour + 3) + ":{:0>2}".format(gps.timestamp_utc.tm_min))
    sys_stat_label._update_text("RAM:" + str(gc.mem_free()) + "B")
    time.sleep(0.5)

