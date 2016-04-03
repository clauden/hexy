import math, ConfigParser, ast, os, re, time, sys
import PoMoCoModule
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

if os.name == 'nt': #sys.platform == 'win32':
    from serial.tools.list_ports_windows import *
elif os.name == 'posix':
    from serial.tools.list_ports_posix import *
else:
    raise ImportError("Sorry: no implementation for your platform ('%s') available" % (os.name,))
#naughty magic constants
ROBOTS_FOLDER_PATH = "Robots/"
ROBOT_FOLDER_PATH = "Robots/Hexy V1/"
#----------------------------------------------------------------------

def sendNote(note):
    PoMoCoModule.Node.modules[note.receiver].put(note)

def writeAndSendNote(type, message, receiver):
    toSend = PoMoCoModule.Note()
    toSend.sender = "MyController"
    toSend.type = type
    toSend.message = message
    toSend.receiver = receiver
    sendNote(toSend)

class MyController():
    def __init__(self):
        pass 
        
    def initController(self):
        # load controller mapping from file
        # establish connection to framework
        # initialize locals
        self.servos = []
        pass

    def LoadRobot(self, folderPath):
        Config = ConfigParser.ConfigParser()
        Config.read(folderPath+"robot.inf")
        
        self.robotName          = Config.get('robot', 'name')
        self.robotVersion       = Config.get('robot', 'version')
        self.controllerName     = Config.get('robot', 'controller')
        robotMovesFolder        = Config.get('robot', 'movesfolder')
        mainFileName            = Config.get('robot', 'mainfile')
        servoFileName           = Config.get('robot', 'servofile')
        imageFileName           = Config.get('robot', 'imagefile')
        
        # build the list of available moves
        self.moveFolderPath = folderPath + robotMovesFolder

        # self.loadButtons()
        self.moves = []   

        if not self.moveFolderPath:
            print "empty folder path"
            exit(2)

        for fileName in os.listdir(self.moveFolderPath):
            if os.path.splitext(fileName)[1] == '.py':
                fileName = os.path.splitext(fileName)[0]
                s1 = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', fileName)
                self.moves.append(s1)
        self.moves.sort()

        # show the moves we found
        for move in self.moves:
            print move 

        # servo offsets and mappings
        self.LoadServoConfig(folderPath + servoFileName)

    def OnMoveButton(self, evt):
        moveName = evt.GetEventObject().moveName
        writeAndSendNote("RunMove", "%s"%(moveName), "robot")
                       
        
    def LoadServoConfig(self, filePath):
        Config = ConfigParser.ConfigParser()
        Config.read(filePath)
        self.servos.servos = []
        for servo in Config.sections():
            num = int(Config.get(servo, 'num'))
            posX = int(Config.get(servo, 'posX'))
            posY = int(Config.get(servo, 'posY'))
            pos = (posX, posY)
            deg = float(Config.get(servo, 'deg'))
            offset = float(Config.get(servo, 'offset'))
            visible = ast.literal_eval(Config.get(servo, 'visible'))
            active = ast.literal_eval(Config.get(servo, 'active'))
            joint = str(Config.get(servo, 'joint'))
            self.servos.append(ServoControl(self, num, pos, deg, offset, visible, active, joint))
        
    def onDisableAll(self, evt):
        for servo in self.servos:
            servo.SetActive(False)
        writeAndSendNote("RequestDisableAll", "", "robot")

    def onEnableAll(self, evt):
        for servo in self.servos:
            servo.SetActive(True)
        writeAndSendNote("RequestEnableAll", "", "robot")

    def onCenterAll(self, evt):
        for servo in self.servos:
            servo.SetDeg(0)
        writeAndSendNote("RequestCenterAll", "", "robot")

    def requestConnection(self, evt):
        writeAndSendNote("RequestConnectPort",self.serialPortSelect.GetValue(),"controller")

    def SetConnectionStatus(self, status):
        if status:
            self.statusImage.SetBitmap(self.greenButton)
        else:
            self.statusImage.SetBitmap(self.redButton)

    def scanSerialPorts(self):
        writeAndSendNote("RequestPortList","","controller")

    def SetPortList(self, portList):
        self.portList = portList


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
        writeAndSendNote("SetServoActive", "%d,%s"%(self.num, outActive), "robot")
        writeAndSendNote("SetServoPos", "%d,%.1f"%(self.num, self.deg), "robot")
        writeAndSendNote("SetServoOffset", "%d,%.1f"%(self.num, self.offset), "robot")
        
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
        writeAndSendNote("SetServoPos", "%d,%.1f"%(self.num, deg), "robot")
        
    def SetDeg(self, deg):
        self.deg = float(deg)
        self.OnDriven()
        
    def SendOffset(self, offset):
        #notify the robot module the servo position was changed
        writeAndSendNote("SetServoOffset", "%d,%.1f"%(self.num, offset), "robot")

    def SendActive(self, state):
        if state:
            outActive = "active"
        else:
            outActive = "inactive"
        writeAndSendNote("SetServoActive", "%d,%s"%(self.num, outActive), "robot")

    def SetOffset(self, offset):
        self.offset = float(offset)
        self.OnDriven()
        
    def SetActive(self, active):
        self.active = bool(active)
        self.OnDriven()
        
     
class httpHandler(BaseHTTPRequestHandler):

    # do the move invocations here
    def do_GET(self):
        print "got path " + self.path
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(self.path)


if __name__ == '__main__':
    try:
        httpd = HTTPServer(('127.0.0.1', 8000), httpHandler)
        httpd.serve_forever()
    except KeyboardInterrupt:
        print 'bye\n'
        httpd.socket.close()

