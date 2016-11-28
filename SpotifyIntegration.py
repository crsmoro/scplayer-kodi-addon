import json
class SpotifyIntegration:
    def __init__(self, webSocket):
        self.webSocket = webSocket
        
    def initialize(self):
        self.getTrack()
        self.getAlbumCover()
        self.isPlaying()
        self.getRepeat()
        self.getShuffle()
    def play(self):
        self.webSocket.send(json.dumps({'action':'play'}).encode('utf-8'))
    def pause(self):
        self.webSocket.send(json.dumps({'action':'pause'}).encode('utf-8'))
    def next(self):
        self.webSocket.send(json.dumps({'action':'next'}).encode('utf-8'))
    def prev(self):
        self.webSocket.send(json.dumps({'action':'prev'}).encode('utf-8'))
    def repeat(self, enable):
        self.webSocket.send(json.dumps({'action':'repeat', 'data':enable}).encode('utf-8'))
    def shuffe(self, enable):
        self.webSocket.send(json.dumps({'action':'shuffle', 'data':enable}).encode('utf-8'))
    def getAlbumCover(self):
        self.webSocket.send(json.dumps({'action':'getAlbumCover'}).encode('utf-8'))
    def getTrack(self):
        self.webSocket.send(json.dumps({'action':'track'}).encode('utf-8'))
    def isPlaying(self):
        self.webSocket.send(json.dumps({'action':'isPlaying'}).encode('utf-8'))
    def getRepeat(self):
        self.webSocket.send(json.dumps({'action':'getRepeat'}).encode('utf-8'))
    def getShuffle(self):
        self.webSocket.send(json.dumps({'action':'getShuffle'}).encode('utf-8'))
    def isLoggedIn(self):
        self.webSocket.send(json.dumps({'action':'isLoggedIn'}).encode('utf-8'))
    def getPlayerName(self):
        self.webSocket.send(json.dumps({'action':'getPlayerName'}).encode('utf-8'))