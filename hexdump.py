#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
Dump binary data to the following text format:

0000000000: 00 00 00 5B 68 65 78 64  75 6D 70 5D 00 00 00 00  ...[hexdump]....
0000000010: 00 11 22 33 44 55 66 77  88 99 AA BB CC DD EE FF  .."3DUfw........

It is similar to the one used by:
Scapy
00 00 00 5B 68 65 78 64 75 6D 70 5D 00 00 00 00  ...[hexdump]....
00 11 22 33 44 55 66 77 88 99 AA BB CC DD EE FF  .."3DUfw........

Far Manager
000000000: 00 00 00 5B 68 65 78 64 ¦ 75 6D 70 5D 00 00 00 00     [hexdump]
000000010: 00 11 22 33 44 55 66 77 ¦ 88 99 AA BB CC DD EE FF   ?"3DUfwˆ™ª»ÌÝîÿ

"""

__version__ = '0.6dev'
__author__  = 'anatoly techtonik <techtonik@gmail.com>'
__license__ = 'Public Domain'

__history__ = \
"""
0.5 (2013-06-10)
 * hexdump is now also a command line utility (no
   restore yet)

0.4 (2013-06-09)
 * fix installation with Python 3 for non English
   versions of Windows, thanks to George Schizas

0.3 (2013-04-29)
 * fully Python 3 compatible

0.2 (2013-04-28)
 * restore() to recover binary data from a hex dump in
   native, Far Manager and Scapy text formats (others
   might work as well)
 * restore() is Python 3 compatible

0.1 (2013-04-28)
 * working hexdump() function for Python 2
"""

import binascii  # binascii is required for Python 3
import sys

# --- constants
PY3K = sys.version_info >= (3, 0)

# --- helpers
def int2byte(i):
  '''convert int [0..255] to binary byte'''
  if PY3K:
    return i.to_bytes(1, 'little')
  else:
    return chr(i)

# --- - chunking helpers
def chunks(seq, size): 
  '''Generator that cuts sequence (bytes, memoryview, etc.)
     into chunks of given size. If `seq` length is not multiply
     of `size`, the lengh of the last chunk returned will be
     less than requested.

     >>> list( chunks([1,2,3,4,5,6,7], 3) ) 
     [[1, 2, 3], [4, 5, 6], [7]] 
  ''' 
  d, m = divmod(len(seq), size)
  for i in range(d):
    yield seq[i*size:(i+1)*size]
  if m: 
    yield seq[d*size:]

def chunkread(f, size):
  '''Generator that reads from file like object. May return less
     data than requested on the last read.'''
  c = f.read(size)
  while len(c):
    yield c
    c = f.read(size)

def genchunks(mixed, size):
  '''Generator to chunk binary sequences or file like objects.
     The size of the last chunk returned may be less than
     requested.'''
  if hasattr(mixed, 'read'):
    return chunkread(mixed, size)
  else:
    return chunks(mixed, size)
# --- - /chunking helpers

# --- hex stuff
def dump(binary):
  '''
  Convert `binary` bytes (Python 3) or str (Python 2) to
  hex string:

  00 00 00 00 00 00 00 00 00 00 00 ...
  '''
  hexstr = binascii.hexlify(binary).decode('ascii').upper()
  return ' '.join(chunks(hexstr, 2))

def dumpgen(data):
  '''
  Generator that produces strings:

  '0000000000: 00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  ................'
  '''
  generator = genchunks(data, 16)
  for addr, d in enumerate(generator):
    # 0000000000:
    line = '%010X: ' % (addr*16)
    # 00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00 
    dumpstr = dump(d)
    line += dumpstr[:8*3]
    if len(d) > 8:  # insert separator if needed
      line += ' ' + dumpstr[8*3:]
    # ................
    # calculate indentation, which may be different for the last line
    pad = 2
    if len(d) < 16:
      pad += 3*(16 - len(d))
    if len(d) <= 8:
      pad += 1
    line += ' '*pad

    for byte in d:
      # printable ASCII range 0x20 to 0x7E
      if not PY3K:
        byte = ord(byte)
      if 0x20 <= byte <= 0x7E:
        line += chr(byte)
      else:
        line += '.'
    yield line
  
def hexdump(data, result='print'):
  '''
  Transform binary data to the hex dump text format:

  0000000000: 00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  ................

    [x] data argument as a binary string
    [x] data argument as a file like object

  Returns result depending on the `result` argument:
    'print'     - prints line by line
    'return'    - returns single string
    'generator' - returns generator that produces lines
  '''
  if PY3K and type(data) == str:
    raise TypeError('Abstract unicode data (expected bytes sequence)')

  gen = dumpgen(data)
  if result == 'generator':
    return gen
  elif result == 'return':
    return '\n'.join(gen)
  elif result == 'print':
    for line in gen:
      print(line)
  else:
    raise ValueError('Unknown value of `result` argument')

def restore(dump):
  '''
  Restore binary data from a hex dump.
    [x] dump argument as a string
    [ ] dump argument as a line iterator

  Supported formats:
    [x] hexdump.hexdump
    [x] Scapy
    [x] Far Manager
  '''
  minhexwidth = 2*16    # minimal width of the hex part - 00000... style
  bytehexwidth = 3*16-1 # min width for a bytewise dump - 00 00 ... style

  result = bytes() if PY3K else ''
  if type(dump) == str:
    text = dump.strip()  # ignore surrounding empty lines
    for line in text.split('\n'):
      # strip address part
      addrend = line.find(':')
      if 0 < addrend < minhexwidth:  # : is not in ascii part
        line = line[addrend+1:]
      line = line.lstrip()
      # check dump type
      if line[2] == ' ':  # 00 00 00 ...  type of dump
        # check separator
        sepstart = (2+1)*7+2  # ('00'+' ')*7+'00'
        sep = line[sepstart:sepstart+3]
        if sep[:2] == '  ' and sep[2:] != ' ':  # ...00 00  00 00...
          hexdata = line[:bytehexwidth+1]
        elif sep[2:] == ' ':  # ...00 00 | 00 00...  - Far Manager
          hexdata = line[:sepstart] + line[sepstart+3:bytehexwidth+2]
        else:                 # ...00 00 00 00... - Scapy, no separator
          hexdata = line[:bytehexwidth]

        # remove spaces and convert
        if PY3K:
          result += bytes.fromhex(hexdata)
        else:
          result += hexdata.replace(' ', '').decode('hex')
      else:
        raise TypeError('Unknown hexdump format')
  return result


def runtest():
  '''Run hexdump tests. Requires hexfile.bin to be in the same
     directory as hexdump.py itself'''
  import os.path as osp
  hexfile = osp.dirname(osp.abspath(__file__)) + '/hexfile.bin' 

  # varios length of input data
  hexdump(b'zzzz'*12)
  hexdump(b'o'*17)
  hexdump(b'p'*24)
  hexdump(b'q'*26)
  # allowable character set filter
  hexdump(b'line\nfeed\r\ntest')
  hexdump(b'\x00\x00\x00\x5B\x68\x65\x78\x64\x75\x6D\x70\x5D\x00\x00\x00\x00'
          b'\x00\x11\x22\x33\x44\x55\x66\x77\x88\x99\xAA\xBB\xCC\xDD\xEE\xFF')
  print('---')
  bin = open(hexfile, 'rb').read()
  # dumping file-like binary object to screen (default behavior)
  hexdump(bin)
  print('-- returned output')
  hexout = hexdump(bin, result='return')
  print(hexout)
  print('-- returned generator')
  hexgen = hexdump(bin, result='generator')
  print(next(hexgen))
  print(next(hexgen))

  # binary restore test
  bindata = restore(
'''
0000000000: 00 00 00 5B 68 65 78 64  75 6D 70 5D 00 00 00 00  ...[hexdump]....
0000000010: 00 11 22 33 44 55 66 77  88 99 AA BB CC DD EE FF  .."3DUfw........
''')
  if bin == bindata:
    print('restore check passed')
  else:
    raise
  far = \
'''
000000000: 00 00 00 5B 68 65 78 64 ¦ 75 6D 70 5D 00 00 00 00     [hexdump]
000000010: 00 11 22 33 44 55 66 77 ¦ 88 99 AA BB CC DD EE FF   ?"3DUfwˆ™ª»ÌÝîÿ
'''
  if bin == restore(far):
    print('restore far format check passed')
  else:
    raise
  scapy = '''\
00 00 00 5B 68 65 78 64 75 6D 70 5D 00 00 00 00  ...[hexdump]....
00 11 22 33 44 55 66 77 88 99 AA BB CC DD EE FF  .."3DUfw........
'''
  if bin == restore(scapy):
    print('restore scapy format check passed')
  else:
    raise
  print('---')
  hexdump(open(hexfile, 'rb'))


if __name__ == '__main__':
  from optparse import OptionParser
  parser = OptionParser(usage='%prog [binfile]')
  parser.add_option('--test', action='store_true', help='run hexdump sanity checks')

  options, args = parser.parse_args()

  if args:
    if options.test:
      parser.print_help()
      sys.exit(-1)

  if options.test:
    runtest()
  elif not args:
    parser.print_help()
    sys.exit(-1)
  else:
    # [x] memory effective dump 
    hexdump(open(args[0], 'rb'))

# [ ] file restore from command line utility
# [ ] encoding param for hexdump()ing Python 3 str if anybody requests that
