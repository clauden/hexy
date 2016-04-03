import time
import Util 

class ServoControl:
    def __init__(self, parent, num, pos, deg=float(0.0), offset=float(0.0), visible=True, active=False, joint=""):
        self.num = int(num)
        self.pos = pos
        self.deg = float(deg)
        self.offset = float(offset)
        self.active = bool(active)
        self.joint = str(joint)
        self.freshlyDriven = False #keeps track if servo was just moved recently
        self.lastDriven = time.clock()

        self.x = 0
        self.y = 0
        self.r = 20
        
        self.InitialMessages()


    def InitialMessages(self):
        if self.active:
            outActive = "active"
        else:
            outActive = "inactive"
        Util.writeAndSendNote("SetServoActive", "%d,%s"%(self.num, outActive), "robot")
        Util.writeAndSendNote("SetServoPos", "%d,%.1f"%(self.num, self.deg), "robot")
        Util.writeAndSendNote("SetServoOffset", "%d,%.1f"%(self.num, self.offset), "robot")
        
    def SetServoControl(self, pt):
        #center of control
        centerX = self.pos[0]+self.width/2
        centerY = self.pos[1]+self.r+3
        
        #these are in regular positive x-y Cartesian
        relativeX = pt[0]-centerX
        relativeX = pt[0]-centerX
        relativeY = centerY-pt[1]
        
        #calculate the degree of the mouse from the center (maxing at +/- 90 deg)
        deg = float(0.0)
        if relativeY <= 0:
            if relativeX >= 0:
                deg = float(90.0)
            else:
                deg = float(-90.0)
        else:
            deg = -math.degrees(math.atan(float(relativeX)/float(relativeY)))
        
        #get degree relative to center
        self.SendDeg(deg)

    def OnDriven(self):
        #run when the servo position or offset was changed. 
        self.freshlyDriven = True
        self.lastDriven = time.clock()

    def CheckDriven(self):
        #function activated by OnDriven after sufficient time has passed 
        if self.freshlyDriven:
            if time.clock() - self.lastDriven > 0.1: #if its been more than 0.1 seconds since the last drive event
                self.freshlyDriven = False
                return True
        return False

    def SendDeg(self, deg):
        #notify the robot module the servo position was changed
        Util.writeAndSendNote("SetServoPos", "%d,%.1f"%(self.num, deg), "robot")
        
    def SetDeg(self, deg):
        self.deg = float(deg)
        self.OnDriven()
        
    def SendOffset(self, offset):
        #notify the robot module the servo position was changed
        Util.writeAndSendNote("SetServoOffset", "%d,%.1f"%(self.num, offset), "robot")

    def SendActive(self, state):
        if state:
            outActive = "active"
        else:
            outActive = "inactive"
        Util.writeAndSendNote("SetServoActive", "%d,%s"%(self.num, outActive), "robot")

    def SetOffset(self, offset):
        self.offset = float(offset)
        self.OnDriven()
        
    def SetActive(self, active):
        self.active = bool(active)
        self.OnDriven()
        

