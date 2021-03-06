import serial
import io
import time
import struct


class Mainboard():
    
    global signal 
    signal = dict(
        START_byte    =  0xCC ,  #start byte for USART transmission
        STOP_byte     =  0x1F ,  #stop byte for USART transmission

        RXSM_id       =  0x30 ,  #ID for RXSM signal reception answer
        PRS0_id       =  0x31 ,  #ID for data of PRS_sensor_0
        PRS1_id       =  0x32 ,  #ID for data of PRS_sensor_1
        TEMP_id       =  0x33 ,  #ID for data of TEMP_sensor
        CAM0_id       =  0x34 ,  #ID for status of CAM_0
        CAM1_id       =  0x35 ,  #ID for status of CAM_1
        ARM_id        =  0x36 ,  #ID for status of ARM_sensor
        RF_id         =  0x37 ,  #ID for status of RF-Board
        VLV_id        =  0x38 ,  #ID for status of Valve_0
        PRSS_id       =  0x39 ,  #ID for status of Pressure sampling
        CAMS_id       =  0x3A ,  #ID for status of Cams (rec/pwr)
        P5V_id        =  0x3B ,  #ID for status of CubeSat 5V
        FWV_id        =  0x3C ,  #ID for Firmware Version


        GET_prs0      =  0x61 ,  #ID for request of single PRS0 value
        GET_prs1      =  0x62 ,  #ID for request of single PRS1 value
        GET_temp      =  0x63 ,  #ID for request of single TEMP value
        GET_arm       =  0x66 ,  #ID for request of arm state
        OPN_vlv       =  0x67 ,  #ID for command to open Valve_0
        CLS_vlv       =  0x68 ,  #ID for command to close Valve_0
        TON_p5v       =  0x6B ,  #ID for command to turn on 5V in CubeSat 
        REQ_pwr_dwn   =  0x6F ,  #ID for power down request


        PRSS_strt     =  0xA1 ,  #ID for Pressure-Sampling started
        PRSS_stop     =  0xA2 ,  #ID for Pressure-Sampling stopped
        CAM0_ok       =  0xA4 ,  #ID for cam0 status ok
        CAM1_ok       =  0xA5 ,  #ID for cam1 status ok
        ARM_ok        =  0xA6 ,  #ID for ARM sensor ok
        RF_ok         =  0xA7 ,  #ID for RF board ok
        VLV_opnd      =  0xA8 ,  #ID for Valve_0 opened
        VLV_clsd      =  0xA9 ,  #ID for Valve_0 closed
        RF_strt       =  0xAA ,  #ID for RF-Transmission started
        RF_stop       =  0xAB ,  #ID for RF-Transmission stopped
        VR_strt       =  0xAC ,  #ID for Video-Recording started
        VR_stop       =  0xAD ,  #ID for Video-Recording stopped
        CAM_on        =  0xAE ,  #ID for Cams turned on
        CAM_off       =  0xAF ,  #ID for Cams turned off
        ERR_stat      =  0xA0 ,  #ID for error status             

        P5V_on        =  0xE0 ,  #ID for CubeSat 5V turned on
        ARM_success   =  0xE6 ,  #ID for successful CubeSat ejection
        SODS_ok       =  0xE8 ,  #ID for successful SODS reception
        LO_ok         =  0xE9 ,  #ID for successful LO reception
        SOE_ok        =  0xEA ,  #ID for successful SOE reception
    )


    def __init__(self, port="/dev/ttyUSB0"):
        self.baud     = 38400
        self.databits = 8
        self.parity   = "N"
        self.stopbits = 1
        self.timeout  = None
        self.datalogfile = open(str(int(time.time()))+".datalog",'ab')
        self.logfile = open(str(int(time.time()))+".log",'ab')

        self.rs232 = serial.Serial(
                        port, 
                        baudrate = self.baud, 
                        parity   = self.parity,
                        bytesize = self.databits,
                        stopbits = self.stopbits,
                        timeout = self.timeout
                        )

        self.savedata = ''

    def PRS0_to_bar(self,x):
        return round(x * 6.895 * 1.25/512, 3)

    def PRS1_to_bar(self,x):
        return round(x * 17.237 * 1.25/256, 3)

    ### control functions following
    def write_command(self,command):
        w = chr(signal["START_byte"]) + chr(command) + chr(signal["STOP_byte"])
        self.rs232.write(w)
    
    def GET_prs0(self):
        self.write_command(signal["GET_prs0"])

    def GET_prs1(self):
        self.write_command(signal["GET_prs1"])
    
    def GET_temp(self):   
        self.write_command(signal["GET_temp"])

    def GET_arm(self):    
        self.write_command(signal["GET_arm"])
    
    def OPN_vlv(self):   
        self.write_command(signal["OPN_vlv"])
    
    def CLS_vlv(self):    
        self.write_command(signal["CLS_vlv"])

    def TON_p5v(self):
        self.write_command(signal["TON_p5v"])
    
    def REQ_pwr_dwn(self):
        self.write_command(signal["REQ_pwr_dwn"])

    def readdata(self,n):
        dat = self.rs232.read(n)
        self.datalogfile.write(dat)
        return dat


    def read_package(self):
        
        # Find the startbytes
        byte=None
        previous_byte=None
        while True:
            previous_byte = byte
            byte = self.readdata(1)
            if byte == chr(signal["START_byte"]):
                if previous_byte == chr(signal["START_byte"]):
                    break
        
        # Receive the package
        packagenumber = struct.unpack(">H",self.rs232.read(2))[0]
        packagelength = struct.unpack("<B",self.rs232.read(1))[0]
        data = self.readdata(int(packagelength))
        self.savedata += data
        unpackcounter = 0
        datathing = []
        while True:
            try:
                datathing.append(struct.unpack_from("<B",data,offset=unpackcounter)[0])
                unpackcounter=unpackcounter+1
            except:
                break
        
        # Build up returnable list with data in it
        package=[]
        package.append(("PKG_num",packagenumber))
        
        for i in range(packagelength/2):
            signalname = signal.keys()[signal.values().index(datathing[i*2])]
            data = datathing[i*2+1]
            if signalname not in ("PRS0_id","PRS1_id","TEMP_id"):
                try:
                    statename = signal.keys()[signal.values().index(data)]
                except:
                    statename = data
            else:
                if signalname == "PRS0_id":
                    statename = self.PRS0_to_bar(data)
                    #print statename
                elif signalname == "PRS1_id":
                    statename = self.PRS1_to_bar(data)
                else:
                    statename = datathing[i*2+1]
            package.append((signalname,statename))
        
        # Check if stopbytes follow
        stop = self.readdata(2)
        if (stop != 2*chr(signal["STOP_byte"])):
            print "ERROR: Package number " + str(packagenumber) + " is broken!\n"
        
        self.logfile.write(str(time.time()) + " " + str(package) + "\n")
        return package
        

import Tkinter as tk
import threading
import collections
global run
run = True
class App(threading.Thread):
    def __init__(self,mainboard=None):
        threading.Thread.__init__(self)
        self.mb=mainboard

        self.status = collections.OrderedDict()
        # Sensor data
        self.status["PRS0_id"] = None
        self.status["PRS1_id"] = None
        self.status["TEMP_id"] = None

        # Status messages
        self.status["PRSS_id"] = None
        self.status["CAMS_id"] = None
        self.status["RF_id"]   = None
        self.status["VLV_id"]  = None
        self.status["ARM_id"]  = None
        self.status["RXSM_id"] = None

        self.start()

    def callback(self):
        run = False
        self.root.quit()



    def run(self):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.callback)
        self.root.minsize(width=300,height=600)
        self.root.maxsize(width=300,height=600)
        self.root.resizable(width=False,height=False)

        #control buttons for mainboard
        self.GET_prs0_bttn = tk.Button(self.root, text="Get Antenna Pressure",command=self.mb.GET_prs0)
        self.GET_prs1_bttn = tk.Button(self.root, text="Get Tank Pressure",command=self.mb.GET_prs1)
        self.GET_temp_bttn = tk.Button(self.root, text="Get Temperature",command=self.mb.GET_temp)
        self.GET_arm_bttn = tk.Button(self.root, text="Get ARM Status",command=self.mb.GET_arm)
        self.OPN_vlv_bttn = tk.Button(self.root, text="Open Valve",command=self.mb.OPN_vlv)
        self.CLS_vlv_bttn = tk.Button(self.root, text="Close Valve",command=self.mb.CLS_vlv)
        self.t5v_on_bttn = tk.Button(self.root, fg="yellow", text="5V Cubesat ON",command=self.mb.TON_p5v)
        self.REQ_pwr_dwn_bttn = tk.Button(self.root, fg="red", text="!!POWER DOWN!!",command=self.mb.REQ_pwr_dwn)
        
        #text from mainboard
        message = ""
        for i in self.status:
            message += i+": "+str(self.status[i])+"\n"
        self.package_label = tk.Label(self.root, text=message)
        
        #layout
        self.GET_prs0_bttn.grid(row=0)
        self.GET_prs1_bttn.grid(row=1)
        self.GET_temp_bttn.grid(row=2)
        self.GET_arm_bttn.grid(row=0,column=1)
        self.OPN_vlv_bttn.grid(row=1,column=1)
        self.CLS_vlv_bttn.grid(row=2,column=1)
        self.t5v_on_bttn.grid(row=3,column=0)
        self.REQ_pwr_dwn_bttn.grid(row=3,column=1)
        self.package_label.grid(columnspan=3,row=4)
        

        self.root.mainloop()
        self.root.destroy()

    def update_display(self):
        pass

    def update_package(self):
        package = self.mb.read_package()
        #print package
        for signal in package:

            self.status[signal[0]] = signal[1]

        #print self.status
        message = ""
        for i in self.status:
            message += i+": "+str(self.status[i])+"\n"
        self.package_label.configure(text=message)
        #self.package_label.pack()


mb = Mainboard()
app=App(mb)
timecount = 1
while run:
    #time.sleep(0.25)
    #app.update_package((("PKG_num",timecount), ('PRS0_id', 88), ('PRS1_id', 46), ('TEMP_id', 24)))
    #timecount += 1
    app.update_package()

