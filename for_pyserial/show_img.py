from vfd_gu7000 import VfdBusPySerial, VfdGu7000
from vfd_utils import convert_from_raw_to_vfd
from PIL import Image
import numpy as np


def get_target_shape(original, target):
	ratio = float(max(np.array(original) / np.array(target)))
	shape = [ int(i / ratio) for i in original ]
	return shape

# load and reize image
im = Image.open("archlinux-logo-dark-test.jpg")
target_shape = get_target_shape(im.size, (140, 32))

im = im.convert('L')
im = im.resize(target_shape, Image.Resampling.BILINEAR)

# convert to binary image
im = np.asarray(im)
im = (im > 200) & 1

# encode image data
shape, data = convert_from_raw_to_vfd(im)
x, y = shape

# open device
vfd_bus = VfdBusPySerial("/dev/ttyCH343USB0", 38400)
vfd = VfdGu7000(vfd_bus, 140, 32, model=7903)

# init and write data
vfd_bus.reset()
vfd.init_display()
vfd.set_cursor(0,0)
vfd.draw_bitmap(x, y, data)
