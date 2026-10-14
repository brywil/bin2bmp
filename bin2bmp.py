#!/usr/bin/env python3
#"Copyright 2009-2026 Bryan Harris"
#
#This file is part of bin2bmp.py.
#
#    bin2bmp.py is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    bin2bmp.py is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with bin2bmp.py; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""Make an image of any file, and get the file back out of the image.

Run as `bin2bmp` to encode and as `bmp2bin` (or `bin2bmp -d`) to decode.

Every image starts with a small header, so decoding needs no flags and recovers the exact bytes:

    b"B2B2" | flags (1 byte, bit 0 = signed) | length (8 bytes, big-endian) | [sha256 (32 bytes)]

The rest of the last row is padding, and the header's length is what tells the decoder where the
file ends. Images from 0.1.x (no header; `-s` wrote a "<sha256>SIZE<n>SIZE" trailer) still decode.

PNG (the default), BMP and GIF are lossless, so the round trip is exact. JPEG is lossy -- it changes
several percent of the bytes even at quality 100 -- so it is for looking at a file, not storing one.
"""

import getopt
import hashlib
import os
import struct
import sys

from PIL import Image

version = '0.2.0'

MAGIC = b'B2B2'
FLAG_SIGNED = 1

# output type -> (extension, PIL mode, bytes per pixel, fill byte, lossless)
FORMATS = {
    'PNG':  ('png', 'RGB', 3, 0xff, True),
    'BMP':  ('bmp', 'RGB', 3, 0xff, True),
    'GIF':  ('gif', '1', None, 0x00, True),    # one bit per pixel; a 0 bit is a white pixel
    'JPEG': ('jpg', 'CMYK', 4, 0x00, False),
}


def warn(msg):
    print('bin2bmp: warning: ' + msg, file=sys.stderr)


def pack(data, sign=False):
    """Header + data: the exact byte stream that the image's pixels carry."""
    flags = FLAG_SIGNED if sign else 0
    header = MAGIC + struct.pack('>BQ', flags, len(data))
    if sign:
        header += hashlib.sha256(data).digest()
    return header + data


def unpack(stream):
    """Inverse of pack(). Returns (data, signature_ok), signature_ok None when unsigned."""
    if stream[:4] != MAGIC:
        return unpack_legacy(stream)
    flags, length = struct.unpack('>BQ', stream[4:13])
    body = 13
    digest = None
    if flags & FLAG_SIGNED:
        digest, body = stream[13:45], 45
    if body + length > len(stream):
        raise ValueError('image is truncated: header says %d bytes, image holds %d' % (length, len(stream) - body))
    data = stream[body:body + length]
    if digest is None:
        return data, None
    return data, hashlib.sha256(data).digest() == digest


def unpack_legacy(stream):
    """Images written by 0.1.x. Unsigned ones never stored a length, so their trailing padding cannot be
    told apart from data and is returned with it. Signed ones end in "<64 hex>SIZE<n>SIZE": search from the
    END, since the file itself may contain "SIZE"."""
    end = stream.rfind(b'SIZE')
    start = stream.rfind(b'SIZE', 0, end) if end != -1 else -1
    size = stream[start + 4:end] if start != -1 else b''
    if start < 64 or not size.isdigit():
        warn('no bin2bmp header (an image from 0.1.x without -s?): output may carry trailing padding')
        return stream, None
    length = int(size)
    data, digest = stream[:length], stream[start - 64:start]
    return data, hashlib.sha256(data).hexdigest().encode() == digest


MAX_SIDE = {'GIF': 65535, 'JPEG': 65535}   # 16-bit dimensions in the file format itself


def fit_width(units, width, output_type):
    """`width`, widened if the image would be taller than the format allows."""
    limit = MAX_SIDE.get(output_type)
    if limit and -(-units // width) > limit:
        new = -(-units // limit)
        if new > limit:
            raise ValueError('file too large for a %s image (at most %d x %d pixels)' % (output_type, limit, limit))
        warn('%s images are at most %d pixels tall: widening to %d pixels' % (output_type, limit, new))
        return new
    return width


def encode(data, output_type='PNG', width=128, sign=False, quality=100):
    """The image for `data`, filled row by row from the top left."""
    ext, mode, bpp_bytes, fill, lossless = FORMATS[output_type]
    stream = pack(data, sign)
    if output_type == 'GIF':
        bits = len(stream) * 8
        width = fit_width(bits, width, output_type)
        height = -(-bits // width)
        # unpack every bit, MSB first, into an 8-bit grey pixel (1 -> black, 0 -> white)
        grey = bytes(0 if (byte >> (7 - k)) & 1 else 255 for byte in stream for k in range(8))
        grey += b'\xff' * (width * height - bits)
        return Image.frombytes('L', (width, height), grey).convert('1', dither=Image.Dither.NONE)
    pixels = -(-len(stream) // bpp_bytes)
    width = fit_width(pixels, width, output_type)
    height = -(-pixels // width)
    stream += bytes([fill]) * (width * height * bpp_bytes - len(stream))
    return Image.frombytes(mode, (width, height), stream)


def decode_image(im):
    """The byte stream an image carries, whichever format wrote it."""
    if im.mode in ('RGB', 'CMYK'):
        return im.tobytes()
    if im.mode in ('1', 'L', 'P', 'LA', 'PA'):
        # GIF comes back palettised; read each pixel's brightness and repack 8 pixels per byte, MSB first.
        # (Not tobytes() on mode '1': that pads every row to a whole byte, which breaks widths not divisible by 8.)
        grey = im.convert('L').tobytes()
        out = bytearray()
        for i in range(0, len(grey) - len(grey) % 8, 8):
            byte = 0
            for g in grey[i:i + 8]:
                byte = (byte << 1) | (g < 128)
            out.append(byte)
        return bytes(out)
    return im.convert('RGB').tobytes()


def usage(prog):
    print('usage: %s <options> ... <filename>' % prog)
    print('-i, --input       \tfile to visualize (or the image to decode)')
    print('-o, --output      \toutput filename')
    print('-d, --decode      \tget the file back out of an image (what bmp2bin does)')
    print('-w, --width       \twidth of output image (default 128)')
    print('-p, --png         \tPNG output (the default; lossless)')
    print('-b, --bmp         \tBMP output (lossless)')
    print('-m, --monochrome  \tone bit per pixel, as a GIF (lossless)')
    print('-j, --jpeg        \tJPEG output -- LOSSY: for looking at, cannot be decoded exactly')
    print('-c, --compress    \thighly compressed JPEG -- LOSSY, as -j but much worse')
    print('-s, --sign        \tstore a SHA256 of the file, checked when decoding')
    print('-V, --verbose     \tprint lots of extra stuff')
    print('-v, --version     \tprint the version')


def main(argv):
    prog = os.path.basename(argv[0])
    decode_mode = prog.startswith('bmp2bin')
    verbose, sign, quality = False, False, 100
    output_file, input_file, output_type, width = None, None, 'PNG', 128
    try:
        opts, args = getopt.getopt(argv[1:], 'w:ho:i:Vjbmvcpsd',
                                   ['width=', 'help', 'output=', 'input=', 'verbose', 'jpeg', 'bmp',
                                    'monochrome', 'version', 'compress', 'png', 'sign', 'decode'])
    except getopt.GetoptError as err:
        print(str(err))
        usage(prog)
        return 2
    for o, a in opts:
        if o in ('-V', '--verbose'):
            verbose = True
        elif o in ('-v', '--version'):
            print(prog + ' ' + version)
            return 0
        elif o in ('-w', '--width'):
            try:
                width = int(a)
                if width < 1:
                    raise ValueError
            except ValueError:
                print(a + ' does not appear to be a positive integer!')
                return 2
        elif o in ('-h', '--help'):
            usage(prog)
            return 1
        elif o in ('-o', '--output'):
            output_file = a
        elif o in ('-i', '--input'):
            input_file = a
        elif o in ('-d', '--decode'):
            decode_mode = True
        elif o in ('-b', '--bmp'):
            output_type = 'BMP'
        elif o in ('-m', '--monochrome'):
            output_type = 'GIF'
        elif o in ('-p', '--png'):
            output_type = 'PNG'
        elif o in ('-j', '--jpeg'):
            output_type = 'JPEG'
        elif o in ('-c', '--compress'):
            output_type, quality = 'JPEG', 10
        elif o in ('-s', '--sign'):
            sign = True

    if input_file is None:
        if not args:
            print('**Error. No input filename specified.**')
            usage(prog)
            return 2
        input_file = args[0]

    if decode_mode:
        return decode_file(input_file, output_file, verbose)
    return encode_file(input_file, output_file, output_type, width, sign, quality, verbose)


def encode_file(input_file, output_file, output_type, width, sign, quality, verbose):
    ext, _, _, _, lossless = FORMATS[output_type]
    try:
        with open(input_file, 'rb') as f:
            data = f.read()
    except OSError as err:
        print("Can't open %s: %s" % (input_file, err.strerror))
        return 1
    if not lossless:
        warn('JPEG is lossy: the image cannot be decoded back to the exact file (use PNG, BMP or -m for that)')
    if output_file is None:
        output_file = os.path.basename(input_file) + '.' + ext
    try:
        im = encode(data, output_type, width, sign)
    except ValueError as err:
        print('**Error. %s**' % err)
        return 1
    if output_type == 'JPEG':
        im.save(output_file, 'JPEG', quality=quality)
    else:
        im.save(output_file, output_type)
    if sign:
        print(hashlib.sha256(data).hexdigest() + ' *' + input_file)
    print('%s: %d bytes -> %s (%dx%d)' % (os.path.basename(input_file), len(data), output_file, im.size[0], im.size[1]))
    return 0


def decode_file(input_file, output_file, verbose):
    try:
        im = Image.open(input_file)
    except OSError as err:
        print("Can't open %s as an image: %s" % (input_file, err))
        return 1
    if im.format == 'JPEG':
        warn('JPEG is lossy: the decoded bytes are very likely not the original file')
    try:
        data, ok = unpack(decode_image(im))
    except ValueError as err:
        print('**Error. %s**' % err)
        return 1
    if output_file is None:
        output_file = os.path.splitext(input_file)[0]
        # 0.1.x did this silently. The original is usually what you want back, but say so.
        if os.path.exists(output_file):
            warn('overwriting existing file %s (use -o to write somewhere else)' % output_file)
    with open(output_file, 'wb') as f:
        f.write(data)
    if ok is None:
        print('We cannot guarantee file integrity without a signature (encode with -s)')
    elif ok:
        print('OK: SHA256 matches')
    else:
        print("Hashes don't match.  File has changed")
    print('%s: %d bytes -> %s' % (input_file, len(data), output_file))
    return 0 if ok is not False else 3


if __name__ == '__main__':
    sys.exit(main(sys.argv))
