#!/usr/bin/env python
import argparse
import gdspy
from PIL import Image

def parse_args():
    parser = argparse.ArgumentParser(description='convert images (catgirls) to gds')
    parser.add_argument('img', help='image to convert')
    parser.add_argument('gds', nargs='?', help='gds to export, default to image filename with gds extension')
    parser.add_argument('cell_name', nargs='?', help='name of the cell, default to image filename')
    parser.add_argument('--rects', action='store_const', const=True, default=False, help='try to use filling rects (vv slow)')
    return parser.parse_args()

def is_set(p):
    return p == 255

def rectangles(img_data, img_width, img_height):
    rects = []

    while True:
        left = [0] * img_width
        right = [img_width] * img_width
        height = [0] * img_width

        rect = ((0, 0, 0, 0), 0)
        for y in range(img_height):
            cur_left, cur_right = 0, img_width
            for x in range(img_width):
                if is_set(img_data[x, y]):
                    height[x] += 1
                else:
                    height[x] = 0
            for x in range(img_width):
                if is_set(img_data[x, y]):
                    left[x] = max(left[x], cur_left)
                else:
                    left[x] = 0
                    cur_left = x + 1
            for x in range(img_width - 1, -1, -1):
                if is_set(img_data[x, y]):
                    right[x] = min(right[x], cur_right)
                else:
                    right[x] = img_width
                    cur_right = x
            for x in range(img_width):
                rect2 = ((left[x], y - height[x] + 1, right[x], y + 1), height[x] * (right[x] - left[x]))
                rect = max(rect, rect2, key=lambda p: p[1])
        if rect[1] == 0:
            return rects
        else:
            rects.append(rect[0])

            x1, y1, x2, y2 = rect[0]
            w, h = x2 - x1, y2 - y1
            
            if w <= 5 and h <= 5:
                for y in range(img_height):
                    for x in range(img_width):
                        if is_set(img_data[x, y]):
                            rects.append((x, y, x + 1, y + 1))
                return rects

            for dy in range(h):
                for dx in range(w):
                    img_data[x1 + dx, y1 + dy] = 0

def main():
    args = parse_args()

    img_path = args.img
    img_filename = img_path.split('.')[0]
    gds_path = args.gds if args.gds is not None else f'{img_filename}.gds'
    cell_name = args.cell_name if args.cell_name is not None else f'{img_filename}'
    rects = args.rects

    img = Image.open(img_path)
    width, height = img.size

    channels = img.split()[:3]
    channels = [channel.convert('1') for channel in channels]

    lib = gdspy.GdsLibrary()
    cell = lib.new_cell(cell_name)

    for i, img in enumerate(channels):
        img_data = img.load()
        if rects:
            for x1, y1, x2, y2 in rectangles(img_data, width, height):
                cell.add(gdspy.Rectangle((x1, height - y1 - 1), (x2, height - y2 - 1), layer=i))
        else:
            for y in range(height):
                for x in range(width):
                    if is_set(img_data[x, y]):
                        cell.add(gdspy.Rectangle((x, height - y - 1), (x + 1, height - y), layer=i))

    lib.write_gds(gds_path)

if __name__ == '__main__':
    main()
