import math, ast, os, re, time, sys, inspect, urlparse
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import ConfigParser
import PoMoCoModule
import Util 
from ServoControl import ServoControl

if os.name == 'nt': #sys.platform == 'win32':
    from serial.tools.list_ports_windows import *
elif os.name == 'posix':
    from serial.tools.list_ports_posix import *
else:
    raise ImportError("Sorry: no implementation for your platform ('%s') available" % (os.name,))

#naughty magic constants
ROBOTS_FOLDER_PATH = "Robots/"
ROBOT_FOLDER_PATH = "Robots/Hexy_V1/"


# def sendNote(note):
#     PoMoCoModule.Node.modules[note.receiver].put(note)
# 
# def Util.writeAndSendNote(type, message, receiver):
#     toSend = PoMoCoModule.Note()
#     toSend.sender = "MyController"
#     toSend.type = type
#     toSend.message = message
#     toSend.receiver = receiver
#     sendNote(toSend)
# 

class ControlProxy(object):
    def __init__(self):
        print "ControlProxy init"
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


    def Main(self):
      try:
          httpd = HTTPServer(('127.0.0.1', 8000), makeHandlerClass(self))
          httpd.serve_forever()
      except KeyboardInterrupt:
          print 'bye\n'
          httpd.socket.close()

       
    def getInstance():
      return self;

    def LoadServoConfig(self, filePath):
        Config = ConfigParser.ConfigParser()
        Config.read(filePath)
        self.servos = []
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
        
    def callback(self, params = {}): 
      if 'type' in params:
        if params['type'].find('Servo'):
          print '.',
        else:
          print 'callback type = ', params['type']
          print params
      else:
        print "Unknown"


    # 
    # invocable methods (from external request)
    #

    def move(self, params):
        moveName = params['name'][0] if 'name' in params else 'Unknown'
        Util.writeAndSendNote("RunMove", "%s"%(moveName), "robot")
                       
    def disable(self, params=None):
        for servo in self.servos:
            servo.SetActive(False)
        Util.writeAndSendNote("RequestDisableAll", "", "robot")

    def enable(self, params=None):
        for servo in self.servos:
            servo.SetActive(True)
        Util.writeAndSendNote("RequestEnableAll", "", "robot")

    def center(self, params=None):
        for servo in self.servos:
            servo.SetDeg(0)
        Util.writeAndSendNote("RequestCenterAll", "", "robot")

    def connect(self, params):
        print "attempting connect to '" + params['port'][0] + "'..."
        Util.writeAndSendNote("RequestConnectPort", params['port'][0],"controller")

    def connect_direct(self, port):
        print "attempting connect to '" + port
        Util.writeAndSendNote("RequestConnectPort", port,"controller")

    def ports(self, params=None):
        Util.writeAndSendNote("RequestPortList","","controller")


def makeHandlerClass(something):

    class MyHttpHandler(BaseHTTPRequestHandler, object):
        def __init__(self,  *args, **kwargs):
          self.proxy = something
          super(MyHttpHandler, self).__init__(*args, **kwargs)
          # BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

        # do the move invocations here
        def do_GET(self):
            print "got path " + self.path
            try:
              # pick off the verb and arguments
              parsed = urlparse.urlparse(self.path)
              print parsed

              action = parsed.path[1:]
              print "action: " + action
  
              params = urlparse.parse_qs(parsed.query)
              print params

              getattr(self.proxy, action)(params)

            except AttributeError as ae:
              print ae
              self.send_response(500)
              self.send_header('Content-type','text/html')
              self.end_headers()
              self.wfile.write(ae)
              return
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write(self.path)
    return MyHttpHandler



#class httpHandler(BaseHTTPRequestHandler):
#
#    def __init__(self,  *args, **kwargs):
#      # super(httpHandler, self).__init__(self, *args)
#      print inspect.getmembers(self)
#      self.proxy = self.server
#      BaseHTTPRequestHandler.__init__(self, *args, **kwargs)
#
#    # do the move invocations here
#    def do_GET(self):
#        print "got path " + self.path
#        try:
#          getattr(self.proxy, self.path)()
#        except AttributeError as ae:
#          print ae
#          self.send_response(500)
#          self.send_header('Content-type','text/html')
#          self.end_headers()
#          self.wfile.write(ae)
#          return
#        self.send_response(200)
#        self.send_header('Content-type','text/html')
#        self.end_headers()
#        self.wfile.write(self.path)
#
#

if __name__ == '__main__':
  proxy = ControlProxy()
  proxy.Main()

