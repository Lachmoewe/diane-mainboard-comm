import serial
import io
import time
import struct

class Mainboard():
    
    def __init__(self, port="/dev/ttyUSB0"):
        self.baud     = 38400
        self.databits = 8
        self.parity   = "N"
        self.stopbits = 1
        self.timeout  = None

        self.rs232 = serial.Serial(
                        port, 
                        baudrate = self.baud, 
                        parity   = self.parity,
                        bytesize = self.databits,
                        stopbits = self.stopbits,
                        timeout = self.timeout
                        )

    def read_package(self):
        byte=None
        previous_byte=None
        while True:
            previous_byte = byte
            byte = self.rs232.read(1)
#            print ''.join( [ "%02X " % ord( x ) for x in byte ] ).strip()
            if byte == chr(0xCC):
                print "FOUND FIRST START BYTE"
                if previous_byte == chr(0xCC):
                    print "FOUND SECOND START BYTE"
                    break

        packagenumber = struct.unpack("<H",self.rs232.read(2))[0]
        packagelength = struct.unpack("<B",self.rs232.read(1))[0]
        data = self.rs232.read(int(packagelength))
        print "PACKAGELENGTH DETECTED: " + str(packagelength)
        print "#" + str(packagenumber) + ": " + data
        stop = self.rs232.read(2)
        #print stop
        print ''.join( [ "%02X " % ord( x ) for x in stop ] ).strip()
        if (stop is not struct.pack("<H",0x1F1F):
            print "ERROR: Package number " + str(packagenumber) + " is broken!\n"
        

if __name__ == '__main__':
    mb = Mainboard()
    while True:
        mb.read_package()
