from typing import Tuple, List
import numpy as np


def convert_from_raw_to_vfd(image: np.ndarray, invert=True, pad_value=0) -> Tuple[Tuple[int, int], List[bytes]]:
	# just convert binary image to vfd image data
	# no resolution detection
	# but will pad bottom if necessary
	assert len(image.shape) == 2, "Expect a binary or grayscale image!"
	im = image

	# pad y to multiples of 8
	y, x = im.shape
	if y % 8 != 0:
		y = (8 - y % 8) % 8 + y
		im = np.pad(im, ((0, y - im.shape[0]), (0, 0)), mode='constant', constant_values=pad_value)

	# convert to bitmap
	# not good for grayscale images
	if invert:
		im = (im > 0) ^ 1
	else:
		im = (im > 0) & 1
	
	# switch xy(1th d and 2nd d) and reshape to one linear list
	# then group by 8
	im = im.transpose().reshape(-1).ravel().reshape((-1, 8))

	# almost done: encode data
	coefficient = np.array([1 << (7-i) for i in range(8)])
	data = np.einsum('ij,j->i', im, coefficient)

	# convert to bytes and return
	data = bytes([i & 0xFF for i in data])

	# return image size and encoded data
	return ((x,y), data)
