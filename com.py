import serial
import io
import time
import struct


class Mainboard():
    
    global signal 
    signal = dict(
       START_byte    =  0xCC ,  #start byte for USART transmission
       STOP_byte     =  0x1F ,  #stop byte for USART transmission

       PRS0_id       =  0x31 ,  #ID for data of PRS_sensor_0
       PRS1_id       =  0x32 ,  #ID for data of PRS_sensor_1
       TEMP_id       =  0x33 ,  #ID for data of TEMP_sensor
       CAM0_id       =  0x34 ,  #ID for status of CAM_0
       CAM1_id       =  0x35 ,  #ID for status of CAM_1
       ARM_id        =  0x36 ,  #ID for status of ARM_sensor
       RF_id         =  0x37 ,  #ID for status of RF-Board
       VLV_id        =  0x38 ,  #ID for status of Valve_0
       RXSM_id       =  0x30 ,  #ID for RXSM signal reception answer

       GET_prs0      =  0x61 ,  #ID for request of single PRS0 value
       GET_prs1      =  0x62 ,  #ID for request of single PRS1 value
       GET_temp      =  0x63 ,  #ID for request of single TEMP value
       GET_arm       =  0x66 ,  #ID for request of arm state
       OPN_vlv       =  0x67 ,  #ID for command to open Valve_0
       CLS_vlv       =  0x68 ,  #ID for command to close Valve_0
       REQ_pwr_dwn   =  0x6F ,  #ID for power down request

       CAM0_ok       =  0xA4 ,  #ID for cam0 status ok
       CAM1_ok       =  0xA5 ,  #ID for cam1 status ok
       ARM_ok        =  0xA6 ,  #ID for ARM sensor ok
       RF_ok         =  0xA7 ,  #ID for RF board ok
       VLV_opnd      =  0xA8 ,  #ID for Valve_0 opened
       VLV_clsd      =  0xA9 ,  #ID for Valve_0 closed
       ERR_stat      =  0xA0 ,  #ID for error status
       
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
        return x * 6.895 * 1.25/512

    def PRS1_to_bar(self,x):
        return x * 17,237 * 1,25/256

    ### control functions following
    def write_command(self,command):
        w = chr(signal["START_byte"]) + chr(command) + chr(signal["START_byte"])
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
    
    def REQ_pwr_dwn(self):
        self.write_command(signal["REQ_pwr_dwn"])





    def read_package(self):
        
        # Find the startbytes
        byte=None
        previous_byte=None
        while True:
            previous_byte = byte
            byte = self.rs232.read(1)
            if byte == chr(signal["START_byte"]):
                if previous_byte == chr(signal["START_byte"]):
                    break
        
        # Receive the package
        packagenumber = struct.unpack(">H",self.rs232.read(2))[0]
        packagelength = struct.unpack("<B",self.rs232.read(1))[0]
        data = self.rs232.read(int(packagelength))
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
            if signalname not in ("PRS0_id","PRS1_id","TEMP_id"):
                try:
                    statename = signal.keys()[signal.values().index(datathing[i*2+1])]
                except:
                    statename = datathing[i*2+1]
            else:
                if signalname == "PRS0_id":
                    statename = self.PRS0_to_bar(datathing[i*2+1])
                elif signalname == "PRS1_id":
                    statename = self.PRS0_to_bar(datathing[i*2+1])
                else:
                    statename = datathing[i*2+1]
            package.append((signalname,statename))
        
        # Check if stopbytes follow
        stop = self.rs232.read(2)
        if (stop != 2*chr(signal["STOP_byte"])):
            print "ERROR: Package number " + str(packagenumber) + " is broken!\n"
        
        return package
        

import Tkinter as tk
import threading
global run
run = True
class App(threading.Thread):
    def __init__(self,mainboard=None):
        threading.Thread.__init__(self)
        self.mb=mainboard

        self.status = dict()
        self.status["PRS0_id"] = None
        self.status["PRS1_id"] = None
        self.status["TEMP_id"] = None
        self.status["CAM0_id"] = None
        self.status["CAM1_id"] = None
        self.status["ARM_id"]  = None
        self.status["RF_id"]   = None
        self.status["VLV_id"]  = None
        self.status["RXSM_id"] = None

        self.start()

    def callback(self):
        run = False
        self.root.quit()



    def run(self):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.callback)

        #control buttons for mainboard
        self.GET_prs0_bttn = tk.Button(self.root, text="GET_prs0",command=self.mb.GET_prs0)
        self.GET_prs1_bttn = tk.Button(self.root, text="GET_prs1",command=self.mb.GET_prs1)
        self.GET_temp_bttn = tk.Button(self.root, text="GET_temp",command=self.mb.GET_temp)
        self.GET_arm_bttn = tk.Button(self.root, text="GET_arm",command=self.mb.GET_arm)
        self.OPN_vlv_bttn = tk.Button(self.root, text="OPN_vlv",command=self.mb.OPN_vlv)
        self.CLS_vlv_bttn = tk.Button(self.root, text="CLS_vlv",command=self.mb.CLS_vlv)
        self.REQ_pwr_dwn_bttn = tk.Button(self.root, fg="red", text="REQ_pwr_dwn",command=self.mb.REQ_pwr_dwn)
        
        #text from mainboard
        self.package_label = tk.Label(self.root, text="Nothing yet.")
        
        #layout
        self.GET_prs0_bttn.grid(row=0)
        self.GET_prs1_bttn.grid(row=1)
        self.GET_temp_bttn.grid(row=2)
        self.GET_arm_bttn.grid(row=0,column=1)
        self.OPN_vlv_bttn.grid(row=1,column=1)
        self.CLS_vlv_bttn.grid(row=2,column=1)
        self.REQ_pwr_dwn_bttn.grid(columnspan=2,row=3)
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

