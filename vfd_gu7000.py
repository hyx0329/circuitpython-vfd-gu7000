import microcontroller
import digitalio
import busio
import time


class ScrollMode:
	Wrapping = 1
	Vertical = 2
	Horizonal = 3


class CompositionMode:
	Normal = 0
	Or = 1
	And = 2
	Xor = 3


class ScreenSaverMode:
	AllOff = 2
	AllOn = 3
	Invert = 4


class VfdBus:
	def __init__(self, **kwargs) -> None:
		pass

	def init(self) -> None:
		pass

	def write(self, buf, **kwargs) -> bool:
		pass

	def is_busy(self) -> bool:
		pass

	def reset(self) -> None:
		pass


class VfdBusUart(VfdBus):
	# TODO: deinit

	def __init__(self, tx: microcontroller.Pin, baudrate: int, busy: microcontroller.Pin, reset: microcontroller.Pin, **kwargs) -> None:
		self.uart = busio.UART(tx=tx, baudrate=baudrate)
		self.busy_pin = digitalio.DigitalInOut(busy)
		self.reset_pin = digitalio.DigitalInOut(reset)
		self.reset_pin.direction = digitalio.Direction.OUTPUT
		self.reset_pin.value = True  # LOW active

	def write(self, buf, **kwargs):
		# must one byte at a time, and check busy signal
		# the display is sloooooow
		# btw the internal buffer size is about 21 bytes
		for i in buf:
			while self.is_busy():
				pass  # change this to asyncio.sleep(0) if adapt to async function
			self.uart.write(bytes([i]))

	def is_busy(self) -> bool:
		return self.busy_pin.value

	def reset(self) -> None:
		self.reset_pin.value = False
		self.reset_pin.value = True


class VfdGu7000:
	def __init__(self, bus: VfdBus, width: int, height: int, model: int = 7000, b_generation:bool = False, **kwargs) -> None:
		self.bus = bus
		self.width = width
		self.height = height
		self.model = model
		self.model_nine = True if (model % 1000) // 100 == 9 else False
		self.b_generation = b_generation

	def _command(self, buf):
		self.bus.write(buf)

	def _command_us(self, buf):
		self._command(b"\x1f\x28")
		self._command(buf)

	def _command_xy(self, x, y):
		xy = bytes((x & 0xFF, x>>8, (y//8) & 0xFF, (y//8)>>8))
		self._command(xy)

	def _command_xy_b_gen(self, x, y):
		# for dot unit functions
		xy = bytes((x & 0xFF, x>>8, y & 0xFF, y>>8))
		self._command(xy)

	def back(self):
		self._command(b"\x08")

	def forward(self):
		self._command(b"\x09")

	def line_feed(self):
		self._command(b"\x0a")

	def home(self):
		self._command(b"\x0b")

	def carriage_return(self):
		self._command(b"\x0d")

	def crlf(self):
		self.carriage_return()
		self.line_feed()

	def set_cursor(self, x, y):
		self._command(b"\x1f$")
		self._command_xy(x, y)

	def clear(self):
		self._command(b"\x0c")

	def cursor_on(self):
		self._command(b"\x1fC\x01")

	def cursor_off(self):
		self._command(b"\x1fC\x00")

	def init_display(self):
		r"""a soft reset"""
		self.bus.init()
		self._command(b"\x1b@"):int
		self.bus.reset()

	def set_scroll_mode(self, mode):
		self._command(bytes((0x1f,mode)))

	def set_horiz_scroll_speed(self, speed):
		self._command(bytes((0x1f, ord("s"), speed)))

	def invert_on(self):
		self._command(b"\x1fr\x01")

	def invert_off(self):
		self._command(b"\x1fr\x00")

	def set_composition_mode(self, mode):
		self._command(bytes((0x1f, ord("w"), mode)))

	def turn_on(self):
		self._command_us(b"a\x40\x01")

	def turn_off(self):
		self._command_us(b"a\x40\x00")

	def set_brightness(self, level):
		level = min(100, max(0, level))
		if level == 0:
			self.turn_off()
		else:
			self.turn_on()
			self._command(bytes((0x1f, ord("X"), (level * 10 + 120) // 125)))

	def wait(self, time):
		r"""Delay time * 0.5 seconds"""
		self._command_us(bytes((ord("a"),0x01,time)))

	def blink(self, on_time=0, off_time=0, times=0, enable=False, reverse=False):
		config = (int(enable) + int(reverse)) if enable else 0
		self._command_us(b"a\x11")
		self._command(bytes([config, on_time, off_time, times]))

	def screensaver(self, mode):
		self._command_us(bytes(("a", 0x40, mode)))

	def set_font_style(self, propotional = False, even_spacing = False):
		self._command_us(bytes((ord("g"), 0x03, (int(int(propotional) << 1) | int(even_spacing)))))

	def set_font_size(self, x: int, y: int, tall=False, **kwargs):
		if x <= 4 and y <= 2:
			self._command_us(bytes((ord("g"), 0x40, x, y)))
			if self.model_nine:
				self._command_us(bytes([ord("g"), 0x01, (int(tall)+1)]))

	def select_window(self, window: int):
		if window <= 4:
			self._command(bytes([0x10 & window]))

	def define_window(self, window, x, y, width, height):
		self._command_us(bytes((ord("w", 0x02, window, 0x01))))
		self._command_xy(x, y)
		self._command_xy(width, height)

	def delete_window(self, window):
		self._command_us(bytes((ord("w"), 0x02, window, 0x00)))
		self._command_xy(0, 0)
		self._command_xy(0, 0)

	def join_screens(self):
		self._command_us(b"w\x10\x01")

	def separate_screens(self):
		self._command_us(b"w\x10\x00")

	def print(self, text: str):
		# NOTE: circuitpython does not support extended ascii, use print_raw if needed
		self._command(bytes(text, "latin-1"))

	def print_dot_unit(self, text: str, x=0, y=0):
		if not self.b_generation:
			raise NotImplementedError("Only for GU7xxxB!")
		self._command_us(b"d\x30")
		self._command_xy_b_gen(x, y)
		self._command(bytes([0x00, len(text)]))
		self.print(text)
	
	def print_raw(self, buf: bytes):
		self._command(buf)

	def scroll(self, x, y, times, speed):
		r"""Speed: smaller is faster, 0-255"""
		pos = (x * self.height // 8) + (y // 8)
		self._command_us(b"a\x10")
		self._command(bytes([pos & 0xFF, pos>>8, times & 0xFF, times>>8, speed]))

	def draw_bitmap(self, width: int, height: int, data: bytes):
		# remember to set the cursor
		r"""draw bitmap using specific data format"""
		self._command_us(b"f\x11")
		self._command_xy(width, height)
		self._command(b"\x01")
		self._command(data)

	def draw_bitmap_dot_unit(self, **kwargs):
		if not self.b_generation:
			raise NotImplementedError("Only for GU7xxxB!")
		raise NotImplementedError

	def draw_bitmap_pos(self, **kwargs):
		if not self.b_generation:
			raise NotImplementedError("Only for GU7xxxB!")
		raise NotImplementedError

	def draw_bitmap_pos_dot_unit(self, **kwargs):
		if not self.b_generation:
			raise NotImplementedError("Only for GU7xxxB!")
		raise NotImplementedError

	def fill_rect(self, x0: int, y0: int, x1: int, y1: int, erase: bool = False):
		# top left point and bottom right point
		x0 = min(x0, self.width - 1)
		y0 = min(y0, self.height - 1)
		x1 = min(x1, self.width - 1)
		y1 = min(y1, self.height - 1)
		if y1 < y0 or x1 < x0:
			raise ValueError("X1 and Y1 should bigger than X0, Y0, respectively")
		# bound region, prepare buffer
		y_top = y0 - y0 % 8
		y_bottom = y1 + (7 - y1 % 8)
		top_row = y_top // 8
		row_count = (y_bottom - y_top + 1) // 8
		col_count = (x1-x0+1)
		buffer = bytearray(row_count * col_count)
		# write data
		if not erase:
			self.set_composition_mode(CompositionMode.Or)
			for i in range(row_count):
				value = 0
				for y in range(8):
					if y0 <= (i+top_row) * 8 + y <= y1:
						value |= 0x80 >> y
				for j in range(col_count):
					buffer[j*row_count+i] = value
		else:
			self.set_composition_mode(CompositionMode.And)
			for i in range(row_count):
				value = 0xFF
				for y in range(8):
					if y0 <= (i+top_row) * 8 + y <= y1:
						value ^= 0x80 >> y
				for j in range(col_count):
					buffer[j*row_count+i] = value
		# draw image
		self.set_cursor(x0, y_top)
		self._command_us(b"f\x11")
		self._command_xy(col_count, row_count * 8)
		self._command(b"\x01")
		self._command(buffer)
		self.set_composition_mode(CompositionMode.Normal)
	
	def fill_line(self, x0: int, y0: int, x1: int, y1: int, erase: bool = False):
		x0 = min(x0, self.width - 1)
		y0 = min(y0, self.height - 1)
		x1 = min(x1, self.width - 1)
		y1 = min(y1, self.height - 1)
		# bound region, prepare buffer
		x_min, x_max = sorted((x0,x1))
		y_min, y_max = sorted((y0,y1))
		if x_min == x_max:  # for y_min == y_max, line is faster
			self.fill_rect(x_min, y_min, x_max, y_max, erase)
		k = (y0 - y1) / (x0 - x1)
		y_top = y_min - y_min % 8
		y_bottom = y_max + (7 - y_max % 8)
		top_row = y_top // 8
		row_count = (y_bottom - y_top + 1) // 8
		col_count = (x_max-x_min+1)
		buffer = None
		# write data
		if not erase:
			buffer = bytearray([0x00]) * (row_count * col_count)
			self.set_composition_mode(CompositionMode.Or)
			for x in range(col_count):
				y = int(k*(x-x0)) + y0
				row = (y - y_top) // 8
				buffer[x*row_count+row] |= 1 << 7 - y % 8
		else:
			buffer = bytearray([0xFF]) * (row_count * col_count)
			self.set_composition_mode(CompositionMode.And)
			for x in range(col_count):
				y = int(k*(x-x0)) + y0
				row = (y - y_top) // 8
				buffer[x*row_count+row] ^= 1 << 7 - y % 8
		# draw image
		self.set_cursor(x_min, y_top)
		self._command_us(b"f\x11")
		self._command_xy(col_count, row_count * 8)
		self._command(b"\x01")
		self._command(buffer)
		self.set_composition_mode(CompositionMode.Normal)

	def set_ascii_variant(self, code: int):
		if code < 0x0d:
			self._command(bytes([0x1b, ord("R"), code]))
	
	def set_charset(self, code: int):
		if code < 0x05 or 0x10 <= code <= 0x13:
			self._command(bytes([0x1b, ord("t"), code]))

	def define_custom_char(self, code, format, data):
		raise NotImplementedError

	def use_custom_char(self, enable: bool):
		self._command(bytes([0x1b, ord('%'), int(enable)]))

	def delete_custom_char(self, code):
		self._command(bytes([0x1b, ord("?"), 0x01, code]))
