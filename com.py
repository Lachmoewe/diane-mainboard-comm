import serial
import io
import time

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
            print hex(byte)
            if byte == 0xCC:
                if previous_byte == 0xCC:
                    break

        packagenumber = self.rs232.read(2)
        packagelength = self.rs232.read(1)
        data = self.rs232.read(int(packagelength))
        print "#" + packagenumber + ": " + data
        stop = self.rs232.read(2)

        if (stop is not 0x1F1F):
            print "ERROR: Package number " + packagenumber + " is broken!\n"
        

if __name__ == '__main__':
    mb = Mainboard()
    while True:
        mb.read_package()
