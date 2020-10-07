import time
from gc import collect, mem_free
import adafruit_bme280
import board
import busio
from ui import UI

i2c = busio.I2C(board.B6, board.B7)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
bme280.sea_level_pressure = 1011.92
bme280.mode = adafruit_bme280.MODE_NORMAL
bme280.standby_period = adafruit_bme280.STANDBY_TC_500
bme280.iir_filter = adafruit_bme280.IIR_FILTER_X16
bme280.overscan_pressure = adafruit_bme280.OVERSCAN_X16
bme280.overscan_humidity = adafruit_bme280.OVERSCAN_X1
bme280.overscan_temperature = adafruit_bme280.OVERSCAN_X2

ui = UI()
ui.main_screen(0xffbf00, 0x454545)

while KeyboardInterrupt:
    try:
        ui.set_bme_values(bme280.temperature, bme280.humidity, bme280.pressure)
        ui.set_speed_value(bme280.temperature)
    except:
        pass
    ui.set_sys_stat("RAM:" + str(mem_free()) + "B")
    collect()
    time.sleep(1)
