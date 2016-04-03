import PoMoCoModule

def sendNote(note):
    PoMoCoModule.Node.modules[note.receiver].put(note)

def writeAndSendNote(type, message, receiver):
    toSend = PoMoCoModule.Note()
    toSend.sender = "MyController"
    toSend.type = type
    toSend.message = message
    toSend.receiver = receiver
    sendNote(toSend)


