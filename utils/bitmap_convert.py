#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Convert a given image to data for GU7000 series VFDs
# This script will read $1 as an image, print code for arduino PROGMEM
# to terminal, and write the converted image data to $1.bin

from PIL import Image
import numpy as np

# 填充至8的整数
def pad_to_eight(data:list):
    data_ = np.array(data)
    ret = (8 - data_ % 8) % 8 + data_
    return ret

# 这是直接将图像转化后输出代码的函数
def convert(filename):
    im = Image.open(filename)

    # 添加白色背景色
    p = Image.new('RGBA', im.size, (255,255,255))
    p.paste(im,(0,0,*im.size), im)
    # 灰度化
    im = p.convert('L')
    # im.show()
    
    # 修正图片大小为8的倍数（其实只要行数是8的倍数即可，这里两个维度都处理了）
    mat = np.zeros(pad_to_eight(im.size))
    
    # 二值化同时反色
    im_mat = np.array(im)
    for i in range(im.size[0]):
        for j in range(im.size[1]):
            mat[i,j] = im_mat[j,i] < 200 
    mat = mat.reshape(-1).ravel()

    # 输出对应C代码
    print('const static uint8_t PROGMEM image[] = {')
    # 记一下图片大小
    print('// image size {:d}x{:d}'.format(*pad_to_eight(im.size)))
    # 8个点一组
    # 搞个数组
    data_ret = []
    coefficient = [128,64,32,16,8,4,2,1]
    linebreak = 0
    for i in range(0,mat.shape[0]-1,8):
        result = 0
        for j in range(8):
            result += int(mat[i+j]) * coefficient[j]
        print('0x{:0>2X},'.format(result), end='')
        data_ret.append(result)
        linebreak += 1
        if not linebreak % 16:
            print()
            linebreak = 0
    print('0x{:0>2X}'.format(result))  # only for progmem
    # data_ret.append(result)
    print('};')
    return data_ret, *pad_to_eight(im.size)

if __name__ == '__main__':
    import sys
    filename = str(sys.argv[1])
    
    # filename = 'bitmap.png'
    data, width, height = convert(filename)
    with open(filename+'.bin', 'wb') as f:
        f.write(bytes([width, height]))
        f.write(bytes(data))
