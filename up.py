#!/opt/local/bin/python2.7
import sys, usb.core, hexdump, argparse

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
    read()

def read():
    sys.stdout.write("read: ")
    test = dev.read(0x81, endpoint.wMaxPacketSize)
    sret = ''.join([chr(x) for x in test])
    hexdump.hexdump(sret)

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


def preheat():
    send('\x56\x16\x08\x07\x00\x00')

def init(): # initialises printer (not sure how much is required, or does what)
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
    args = parser.parse_args()
    if (args.nozzle):
        t_nozzle = args.nozzle
    if (args.bed):
        t_bed = args.bed

    temp(t_nozzle, t_bed)

# vim: set ts=4 sts=0 sw=4 et:
