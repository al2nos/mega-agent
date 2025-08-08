# *****************************************************************************
# * | File        :   epd2in13b_v3.py
# * | Author      :   Waveshare team
# * | Function    :   Electronic paper driver (4-color)
# * | Info        :   Optimized for Orange Pi with 4-color support
# *****************************************************************************

import logging
from PIL import Image, ImageDraw, ImageFont
import RPi.GPIO as GPIO
import spidev
import time

# Pin definition
RST_PIN         = 17
DC_PIN          = 25
CS_PIN          = 8
BUSY_PIN        = 24

# Display resolution
EPD_WIDTH       = 122
EPD_HEIGHT      = 250

logger = logging.getLogger(__name__)

class EPD:
    def __init__(self):
        self.reset_pin = RST_PIN
        self.dc_pin = DC_PIN
        self.cs_pin = CS_PIN
        self.busy_pin = BUSY_PIN
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        
    def digital_write(self, pin, value):
        GPIO.output(pin, value)

    def digital_read(self, pin):
        return GPIO.input(pin)

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.SPI.writebytes(data)

    def module_init(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.reset_pin, GPIO.OUT)
        GPIO.setup(self.dc_pin, GPIO.OUT)
        GPIO.setup(self.cs_pin, GPIO.OUT)
        GPIO.setup(self.busy_pin, GPIO.IN)
        
        self.SPI = spidev.SpiDev(0, 0)
        self.SPI.max_speed_hz = 10000000
        self.SPI.mode = 0b00
        return 0

    def module_exit(self):
        logging.debug("spi end")
        self.SPI.close()
        GPIO.output(self.reset_pin, 0)
        GPIO.cleanup()

    def reset(self):
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(200)
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(2)
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(200)

    def send_command(self, command):
        self.digital_write(self.dc_pin, 0)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([command])
        self.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([data])
        self.digital_write(self.cs_pin, 1)

    def ReadBusy(self):
        logger.debug("e-Paper busy")
        while(self.digital_read(self.busy_pin) == 1):      # 1: busy, 0: idle
            self.delay_ms(10)
        logger.debug("e-Paper busy release")

    def init(self):
        if (self.module_init() < 0):
            return -1
        self.reset()
        
        self.send_command(0x04)  # POWER_ON
        self.ReadBusy()

        self.send_command(0x00)  # PANEL_SETTING
        self.send_data(0x0f)     #KW-BF   KWR-AF  BWROTP 0f
        self.send_data(0x0d)     #VCOM to 0V fast

        self.send_command(0x61)  # RESOLUTION_SETTING
        self.send_data(self.width >> 8)
        self.send_data(self.width & 0xff)
        self.send_data(self.height >> 8)
        self.send_data(self.height & 0xff)

        self.send_command(0X50)  # VCOM AND DATA INTERVAL SETTING
        self.send_data(0xf0)     #WBmode:VBDF 17|D7 VBDW 97 VBDB 57   WBRmode:VBDF F7 VBDW 77 VBDB 37  VBDR B7

        return 0

    def getbuffer(self, image):
        # Create a palette for the image
        buf = [0x00] * int(self.width * self.height / 4)
        image_grays = image.convert('L')
        imwidth, imheight = image_grays.size
        pixels = image_grays.load()
        
        if(imwidth == self.width and imheight == self.height):
            for y in range(imheight):
                for x in range(imwidth):
                    # Convert grayscale to 2-bit color (4 colors)
                    gray = pixels[x, y]
                    if gray < 64:        # Black
                        buf[int((x + y * self.width) / 4)] |= (0xC0 >> ((x % 4) * 2))
                    elif gray < 128:     # Dark gray (simulate red)
                        buf[int((x + y * self.width) / 4)] |= (0x80 >> ((x % 4) * 2))
                    elif gray < 192:     # Light gray (simulate yellow)
                        buf[int((x + y * self.width) / 4)] |= (0x40 >> ((x % 4) * 2))
                    # else white - no bits set
        return buf

    def display(self, black_image, red_image, yellow_image=None):
        """Display 4-color image: black, white, red, yellow"""
        self.send_command(0x10)  # RED RAM
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(0xFF)  # Clear red buffer
            
        self.send_command(0x13)  # BLACK RAM
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(0xFF)  # Clear black buffer
            
        if yellow_image:
            self.send_command(0x11)  # YELLOW RAM (if supported)
            for i in range(0, int(self.width * self.height / 8)):
                self.send_data(0xFF)  # Clear yellow buffer

        # Send black image data
        self.send_command(0x13)  # BLACK RAM
        black_buffer = self.getbuffer(black_image)
        for i in range(len(black_buffer)):
            self.send_data(black_buffer[i])

        # Send red image data
        self.send_command(0x10)  # RED RAM
        red_buffer = self.getbuffer(red_image)
        for i in range(len(red_buffer)):
            self.send_data(red_buffer[i])

        self.TurnOnDisplay()

    def Clear(self):
        self.send_command(0x10)  # RED RAM
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(0xFF)
        self.send_command(0x13)  # BLACK RAM
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(0xFF)
        self.TurnOnDisplay()

    def TurnOnDisplay(self):
        self.send_command(0x22)  # DISPLAY_UPDATE_CONTROL_2
        self.send_data(0xF7)
        self.send_command(0x20)  # MASTER_ACTIVATION
        self.ReadBusy()

    def sleep(self):
        self.send_command(0x10)  # DEEP_SLEEP_MODE
        self.send_data(0x01)
        self.ReadBusy()

# Color display test
def test_color_display():
    logging.basicConfig(level=logging.DEBUG)
    epd = EPD()
    epd.init()
    epd.Clear()
    
    # Create color images
    black_image = Image.new('1', (epd.width, epd.height), 255)  # White background
    red_image = Image.new('1', (epd.width, epd.height), 255)
    draw_black = ImageDraw.Draw(black_image)
    draw_red = ImageDraw.Draw(red_image)
    
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 14)
    except:
        font = ImageFont.load_default()
    
    # Draw text in different colors
    draw_black.text((10, 10), 'Black Text', font=font, fill=0)
    draw_red.text((10, 30), 'Red Text', font=font, fill=0)
    
    # Draw colored rectangles
    draw_black.rectangle((10, 50, 50, 90), outline=0, fill=0)      # Black rectangle
    draw_red.rectangle((60, 50, 100, 90), outline=0, fill=0)       # Red rectangle
    
    # Display the image
    epd.display(black_image, red_image)
    epd.sleep()
    epd.module_exit()
    
    print("✅ 4-color e-Paper display test completed")

if __name__ == "__main__":
    test_color_display()