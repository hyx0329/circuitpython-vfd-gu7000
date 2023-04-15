# Example on ESP32-S2

from vfd_gu7000 import VfdBusUart, VfdGu7000, ScrollMode, CompositionMode
import board

import time

TX_PIN = board.IO16
BUSY_PIN = board.IO18
RESET_PIN = board.IO35

vfd_bus = VfdBusUart(TX_PIN, 38400, BUSY_PIN, RESET_PIN)
vfd = VfdGu7000(vfd_bus, 140, 32, model=7903, b_generation=True)


while True:

	vfd.reset()
	vfd.init_display()
	print("draw a rectangle and a point")
	vfd.fill_rect(10, 10, 15, 15)
	vfd.fill_rect(50,3,50,3)
	time.sleep(3)

	print("draw 2 lines")
	vfd.fill_line(0,0,139,31)
	vfd.fill_line(139,0,0,31)
	time.sleep(10)

	print("test charset")
	vfd.clear()
	vfd.set_charset(1)
	for j in range(0x80, 0xFF):
		vfd.print_raw(bytes([j]))
	time.sleep(2)

	print("test scroll")
	vfd.scroll(1, 0, 500, 3)
	

	vfd.clear()
	print("test print text")
	vfd.print("The quick brown fox jumps over the lazy dog")
	vfd.blink(50, 10, 1, True, True)
	vfd.blink(50, 10, 1, True, False)
	time.sleep(1)

	print("test brightness")
	vfd.set_brightness(1)
	time.sleep(1)
	vfd.set_brightness(100)
	time.sleep(1)
	vfd.set_brightness(10)

	vfd.clear()

	print("test cursor")
	vfd.cursor_on()
	vfd.set_cursor(99,0)
	time.sleep(2)
	vfd.set_cursor(10,8)
	time.sleep(2)

	print("test font style")
	vfd.clear()
	vfd.set_font_style(False, False)
	vfd.print("Test")
	vfd.crlf()
	vfd.set_font_style(True, False)
	vfd.print("Test")
	vfd.crlf()
	vfd.set_font_style(True, True)
	vfd.print("Test")
	vfd.crlf()
	time.sleep(3)

	print("test font size")
	vfd.clear()
	vfd.set_font_size(4,2)
	vfd.print("A")
	vfd.set_font_size(2,1)
	vfd.print("A")
	vfd.set_font_size(1,1)
	vfd.print("A")
	time.sleep(2)

	print("test dot unit")
	vfd.clear()
	vfd.print_dot_unit("Hello world!", 3, 3)
	time.sleep(2)

	print("test scroll mode")
	vfd.clear()
	vfd.set_scroll_mode(ScrollMode.Horizonal)
	vfd.print("The quick brown fox jumps over the lazy dog.")
	time.sleep(1)
	vfd.set_scroll_mode(ScrollMode.Vertical)
	vfd.print("Another fox jump on to the previous dog.")
	vfd.crlf()
	vfd.print("This is a completely different story. Let's talk about it later.")
	time.sleep(1)

	print("test ascii code")
	vfd.clear()
	print("American")
	vfd.set_ascii_variant(0)
	for i in range(32,128):
		vfd.print(chr(i))
	time.sleep(5)
	vfd.clear()
	print("Japan")
	vfd.set_ascii_variant(8)
	for i in range(32,128):
		vfd.print(chr(i))
	time.sleep(5)

	print("test composition")
	vfd.clear()
	vfd.set_composition_mode(CompositionMode.Or)
	vfd.print("TEST")
	vfd.set_cursor(0,0)
	vfd.print("ABCDE")
	time.sleep(2)
	vfd.set_composition_mode(CompositionMode.Normal)

	print("end of test")
	time.sleep(2)
