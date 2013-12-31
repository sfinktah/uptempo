#!/opt/local/bin/python2.7
import sys, usb.core, hexdump, argparse, struct

# default temperatures

t_nozzle = 225
t_bed = 110

# usb vendorId and productId
# (should be ok for Plus and Mini) 
# Anyone with an Afinia want to let me know?

usbVendorId = 0x4745
usbProductId = 0x0001


# nothing to edit below this line

dev = usb.core.find(idVendor=usbVendorId, idProduct=usbProductId)
if dev is None:
    raise ValueError('Sfinktah! Our device is not connected')

dev.set_configuration(1) 
endpoint = dev[0][(0,0)][1]

def send(s):
    sys.stdout.write("sent: ")
    hexdump.hexdump(s)
    dev.write(1, s, 0);
    return read()

def read():
    sys.stdout.write("read: ")
    test = dev.read(0x81, endpoint.wMaxPacketSize)
    sret = ''.join([chr(x) for x in test])
    hexdump.hexdump(sret)
    return sret;

    # Known commands
    # Command format (hex):  56 mm nn nn 00 00 
    #                         |  |  |  |
    #                         |  |  |  `- high order of argument (will be 0 for anything less than 256)
    #                         |  |  `- low order of argument 
    #                         |  `- command (see list)
    #                         `- command prefix
    #   #   56 - Commands
    #   ##      16 - Preheat
    #   ###                     fmt: 56 16 nn nn 00 00 - Time to preheat bed (in 2 minute units)
    #   ###                     eg:  56 16 08 07 00 00 - preheat bed 1 hour
    #   ###                     eg:  56 16 00 00 00 00 - Preheat off
    #   ##      39 - Set Nozzle Temp
    #   ###                     fmt: 56 39 nn nn 00 00 - Nozzle temp to n degrees
    #   ###                     eg: send('\x56\x3b\x73\x00\x00\x00') # bed 115 degrees (if it can get that high)
    #   ##      3b - Set Bed Temp
    #   ###                     fmt: 56 3b nn nn 00 00 - Bed temp to n degress
    #   ###                     eg: send('\x56\x39\xe1\x00\x00\x00') # extruder temp 240 degrees 

    # guesses

    # 56 94 e7 03 00 00 - print last model?
    # 56 8e ff ff ff ff - stop print?


    # 52 00 - big answer
    # 76 2a 2a
    # 76 2b 2b - maybe ask tmp nozzle - returned c1 00 00 00 06 (193)
    # 76 36 36 - maybe ask tmp tray   - returned 67 00 00 00 06 (103)
    # 76 3e 3e
    # 23 0c 20
    # 23 0f 1c
    # 23 a1 10
    # 23 10 28
    # 23 0b 30
    # 23 0e 23
    # (then issues print last model)

    # movement (used in calibration)

    # 4a 00 00 00 48 42 00 00 02 c3                   J...HB....  -- move X
    # 4a 01 00 00 48 42 00 00 20 41                   J...HB.. A  -- move Y
    #
    # position    4a 00 .....                                                    4a 01 .....
    #    1                left +-- 02 c3                   J...HB....               top   +--  20 41                   J...HB.. A
    #    2                     |   02 c3                   J...HB....                     |    8c 42  --+  center      J...HB...B
    #    3                     +-- 02 c3                   J...HB....          bottom ----|--  02 43    |              J...HB...C
    #    4                mid  +-- 8c c2                   J...HB....                     +--  20 41    |              J...HB.. A
    #    5                     |   8c c2                   J...HB....                     |    8c 42  --+              J...HB...B
    #    6                     +-- 8c c2                   J...HB....                     |    02 43    |              J...HB...C
    #    7              right  +-- 20 c1                   J...HB.. .                     +--  20 41    |              J...HB.. A
    #    8                     |   20 c1                   J...HB.. .                          8c 42  --+              J...HB...B
    #    9                     +-- 20 c1                   J...HB.. .                          02 43                   J...HB...C

    # big big guesses

    # up and down
    # 13 000: 6a 02 00 00 20 41 00 00 80 3f                   j... A...?
    # 11 000: 6a 02 00 00 20 41 00 00 80 bf                   j... A....
    #  4 000: 6a 02 00 00 20 41 cd cc cc 3d                   j... A...=
    # 15 000: 6a 02 00 00 20 41 cd cc cc bd                   j... A....

def stop(): # doesn't work
    send('\x56\x8e\xff\xff\xff\xff') #  - stop print?

def reprint(): # d oesn't work
    # 56 94 e7 03 00 00 - print last model?
    send('\x56\x94\xe7\x03\x00\x00')

def test7610():
    send('\x76\x10\x10') # what does this do anyway

def getlayer():
    send('\x76\x0a\x0a') # works - gets current layer printing

def preheat(): # works
    send('\x56\x16\x08\x07\x00\x00')
#
# Get Bed Temp:
# sent: 0000000000: 76 06 06                                          v..
# read: 0000000000: EC 51 F8 41 06                                    .Q.A.
#	n = 0x41f851ec;
#	memcpy(&f, &n, 4);
#	printf("%f %x\n", n, f);
# sent: 0000000000: 76 07 07                                          v..
# read: 0000000000: F6 28 74 43 06                                    .(tC.
# Get Nozzle Temp:
# sent: 0000000000: 76 08 08                                          v..

def getnozzletemp():
    ret = send('\x76\x08\x08')
    ret = ret[:4]
    
    f = struct.unpack("<f", ret)
    print str.format("Nozzle temperature is {}\n", f)

def getbedtemp():
    ret = send('\x76\x06\x06');
    ret = ret[:4]
    
    f = struct.unpack("<f", ret)
    print str.format("Bed temperature is {}\n", f, ret)

def misc():
    send('\x76\x10\x10')
    send('\x76\x0a\x0a')
    send('\x76\x10\x10')
    send('\x76\x10\x10')
    send('\x76\x00\x00')
    send('\x76\x00\x00')
    send('\x76\x14\x14')
    send('\x76\x15\x15')
    send('\x76\x16\x16')
    send('\x76\x06\x06')
    send('\x76\x07\x07')
    send('\x76\x08\x08')
    send('\x01\x00')


def init(): # initialises printer (not sure how much is required, or does what), but it works
    send('\x56\x10\x00\x00\x00\x00')
    send('\x63')
    send('\x4c\x30')
    send('\x58')


def temp_nozzle(t):
    send('\x56\x39' + chr(t % 255) + chr (t >> 8) + '\x00\x00' ) # extruder temp - max unknown, default 268

def temp_bed(t):
    send('\x56\x3b' + chr(t % 255) + chr (t >> 8) + '\x00\x00' ) # bed temp max 115 (maybe more?) default 110

def temp(nozzle, bed):
    print str.format("Setting temperature of nozzle to {} and bed to {}\n", nozzle, bed) 
    temp_nozzle(nozzle);
    temp_bed(bed);

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Set the temperature on a Delta Micro / PP3DP printer')
    parser.add_argument('-n', '--nozzle', metavar='TEMP', help='nozzle temperature', type=int)
    parser.add_argument('-b', '--bed', metavar='TEMP', help='bed temperature', type=int)
    parser.add_argument("-s", "--stop", action="store_true", help="stop the current print job (todo)")
    parser.add_argument("-v", "--verbose", action="store_true", help="increase output verbosity")
    parser.add_argument("--heat", action="store_true", help="heat the platform for 1 hour")
    # parser.add_argument("--reprint", action="store_true", help="print last model (todo)")
    parser.add_argument("--init", action="store_true", help="init printer")
    parser.add_argument("--misc", action="store_true", help="misc printer commands")
    parser.add_argument("--getlayer", action="store_true", help="getlayer printer")
    parser.add_argument("--nt", action="store_true", help="get nozzle temp")
    parser.add_argument("--bt", action="store_true", help="get bed temp")
    args = parser.parse_args()
    if (args.nozzle):
        t_nozzle = args.nozzle
    if (args.bed):
        t_bed = args.bed

    if (args.heat):
        preheat();
    if (args.stop):
        stop();
    if (args.reprint):
        reprint();
    if (args.init):
        init();
    if (args.misc):
        misc();
    if (args.getlayer):
        getlayer();
    if (args.nozzle):
        temp(t_nozzle, t_bed);
    if (args.bt):
        getbedtemp()
    if (args.nt):
        getnozzletemp()

# vim: set ts=4 sts=0 sw=4 et:
