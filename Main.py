import threading, os, sys, multiprocessing, Queue
import time
import PoMoCoModule
# import Log
from ControlProxy import ControlProxy

sys.path.append('Robots/Hexy_V1/Moves')
sys.path.append('Robots/Hexy_V1/')
sys.path.append('Comms')
sys.path.append('Controllers')

import robot
import SerialComms
import Servotor32

class ControlProxyProc(PoMoCoModule.Node):
    def __del__():
        if self.ser:
            if self.ser.isOpen():
                self.ser.close()
                
    def __exit__(self, type, value, traceback):
        if self.ser and self.ser.isOpen():
            self.ser.close()
         
    def __init__(self, controlProxy):
        super(ControlProxyProc, self).__init__()
        threading.Thread.__init__(self)
        self.ControlProxy = controlProxy
        self.moduleType = 'GUI'       # this is coupled in the move functions...
        PoMoCoModule.Node.modules[self.moduleType] = self.inNoteQueue
        self.start()

    def run(self):
        while True:
            try:
                message = self.inNoteQueue.get(block=False)
                self.processNote(message)
            except Queue.Empty:
                time.sleep(0) # keeps infinite loop from hogging all the CPU

    def processNote(self, note):
        print self.moduleType,"Received Note:",note.sender,"->",note.receiver,"-",note.type,":",note.message

         # callbacks from onboard controller

        if note.type == "SetServoPos":
            num, pos = note.message.split(',')
            controlProxy.callback( {'type':note.type, 'num':num, 'pos':pos} )
            # wx.CallAfter(self.GUI.UpdateServoPos, int(num), float(pos))
            
        if note.type == "SetServoOffset":
            num, offset = note.message.split(',')
            controlProxy.callback( {'type':note.type, 'num':num, 'pos':offset} )
            # wx.CallAfter(self.GUI.UpdateServoOffset, int(num), float(offset))
            
        if note.type == "SetServoActive":
            num, state = note.message.split(',')
            servoState = False
            if state == "active":
                servoState = True
            if state == "inactive":
                servoState = False
            controlProxy.callback( {'type':note.type, 'num':num, 'state':state} )
            # wx.CallAfter(self.GUI.UpdateServoActive, int(num), servoState)
            
        if note.type == "SetConnectionState":
            connState = False
            if note.message == "active":
                connState = True
            if note.message == "inactive":
                connState = False
            self.connectionState = connState
            controlProxy.callback( {'type':note.type, 'state':note.message} )
            # wx.CallAfter(self.GUI.UpdateConnectionState, connState)
            
        if note.type == "SetPortList":
            portList = note.message.split(',')[:]
            controlProxy.callback( {'type':note.type, 'portlist':portList} )
            # wx.CallAfter(self.GUI.UpdatePortList, portList)

        if note.type == "SetFirmwareV":
            firmwareVersion = note.message
            controlProxy.callback( {'type':note.type, 'version':note.message} )
            # wx.CallAfter(self.GUI.UpdateFirmwareVersion, firmwareVersion)

        if note.type == "UpdateArduinoCode":
            arduinoCode = note.message
            controlProxy.callback( {'type':note.type, 'code':note.message} )
            # wx.CallAfter(self.GUI.UpdateArduinoCode, arduinoCode)


if __name__ == '__main__':
    comms = SerialComms.SerialLink()
    controller = Servotor32.Servotor32()
    robot = robot.robot()
    __builtins__.hexy = robot
    __builtins__.robot = robot
    __builtins__.move = robot.RunMove
    __builtins__.floor = 60

    controlProxy = ControlProxy()
    print controlProxy

    proxyProc = ControlProxyProc(controlProxy)
    print proxyProc

    
    controlProxy.LoadRobot("Robots/Hexy_V1/")
    controlProxy.Main() 

    del controlProxy
    del robot
    del controller
    del comms
    os._exit(0)

    
