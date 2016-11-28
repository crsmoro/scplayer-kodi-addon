import sys
import urlparse
import xbmc
import xbmcaddon
import urllib
import os
import subprocess
import json


__id__ = 'script.audio.scplayer'
__addon__ = xbmcaddon.Addon(__id__)
__language__   = __addon__.getLocalizedString
__settings__ = __addon__.getSetting

__cwd__        = xbmc.translatePath( __addon__.getAddonInfo('path') ).decode("utf-8")
__resource__   = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) ).decode("utf-8")
sys.path.append (__resource__)

import xbmcgui
from SpotifyIntegration import SpotifyIntegration
from ShufflePlaybackController import ShufflePlaybackController
from ShufflePlaybackWindow import ShufflePlaybackWindow
import traceback

import websocket
import threading

def log(msg, level = xbmc.LOGWARNING):
    xbmc.log((u"### [%s] - %s" % (__baseUrl__,msg,)).encode('utf-8'),level=level )

def buildBaseUrl(query):
    if typeOfCall == 'addon':
        return __baseUrl__ + '?' + urllib.urlencode(query)
    elif typeOfCall == 'service':
        baseUrl = __baseUrl__
        for key in query:
            baseUrl = baseUrl + ',' + query.get(key)
        return baseUrl

typeOfCall = 'addon'
addon_handle = None
args = None

ws = None
attempts = 0
wsconnected = False
wsp = threading.Event()
si = None
playbackController = None
playbackWindow = None
wsthread = None

def stop_screensaver(arg1, stop_event):
    while (not stop_event.is_set()):
        stop_event.wait(60)
        if __settings__('32015') == 'true':
            xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Input.ContextMenu", "id": 1}')

def websocket_ping(arg1, stop_event, ws):
    while (not stop_event.is_set()):
        stop_event.wait(3)
        ws.send(json.dumps({'action':'ping'}).encode('utf-8'))

def websocket_running(arg1, stop_event, ws):
    ws.run_forever();

def on_data(ws, data, type, f):
    global playbackController
    if data is not None:
        jsonData = json.loads(data)
        if jsonData.get('action') <> 'pong':
            print jsonData
            playbackController.playback_notify(jsonData.get('action'), jsonData.get('data'))
        
def on_error(ws, error):
    global wsconnected
    print 'error'
    print error
    wsconnected = False

def on_close(ws):
    global wsconnected
    #print "### closed ###"
    wsconnected = False

def on_open(ws):
    global wsconnected
    global wsp
    global si
    #print 'OPENED'
    wspingthread = threading.Thread(target = websocket_ping, args=(1, wsp, ws))
    wspingthread.start()
    si.initialize()
    wsconnected = True

def initWebSocket():
    global ws
    global wsp
    global si
    global wsthread
    #print 'initWebSocket'
    
    ws = websocket.WebSocketApp('ws://' + __settings__('hostname') + ':' + __settings__('port') + '/', subprotocols=["binary", "base64"]);
    
    wsthread = threading.Thread(target = websocket_running, args=(1, wsp, ws))
    wsthread.start()
    
    si = SpotifyIntegration(ws)
    if playbackWindow is not None:
        playbackWindow.setSpotifyIntegration(si)
    ws.on_data = on_data
    ws.on_error = on_error
    ws.on_close = on_close
    ws.on_open = on_open
    
    return ws

def verifyState(arg1, stop_event):
    global attempts
    global wsconnected
    global ws
    global playbackWindow
    wsi = None
    #print 'verifyState'
    while attempts < 6 and (stop_event is None or not stop_event.is_set()):
        #print 'verifyState WHILE'
        if stop_event is not None:
            stop_event.wait(5)
        else:
            if wsconnected == True:
                break
            else:
                xbmc.sleep(5000)
        #print 'verifyState BEFORE IF CONNECTED'
        if wsconnected == False:
            #print 'verifyState NOT CONNECTED, TRYING TO CONNECT'
            wsi = initWebSocket()
            #print 'verifyState ADD ATTEMPTS'
            attempts = attempts + 1
        else:
            #print 'verifyState ATTEMPTS 0'
            attempts = 0
    #print 'verifyState END WHILE'
    if wsconnected == False:
        xbmcgui.Dialog().ok(__language__(32011), line1=__language__(32012), line2=__language__(32013))
        if stop_event is not None:
            playbackWindow.close()
    return wsi

def intialize_window_data(arg1, stop_event):
    global si
    stop_event.wait(1)
    si.initialize()


__baseUrl__ = sys.argv[0]
if ('plugin://' not in __baseUrl__):
    typeOfCall = 'service'

if __name__ == '__main__':
    if typeOfCall == 'addon':
        addon_handle = int(sys.argv[1])
        args = urlparse.parse_qs(sys.argv[2][1:])
        
    elif typeOfCall == 'service':
        args = sys.argv[1:]
    
        try:

            ar = threading.Event()
            thread = threading.Thread(target = stop_screensaver, args=(1, ar))
            thread.setDaemon(True)
            thread.start()
        
            
            p = None
            try:
                if __settings__('runasservice') == 'false':
                    args = [__cwd__ + '/resources/jdk1.8.0_60/bin/java', '-Xdebug', '-Xrunjdwp:server=y,transport=dt_socket,address=45912,suspend=n']
                    if __settings__('debug') is not None and __settings__('debug') == 'true':
                        args.append('-Ddebug=3')
                    if __settings__('spotifyapppath') is not None and __settings__('spotifyapppath') <> '':
                        args.append('-Dapp.key=' + __settings__('spotifyapppath'))
                    args.append('-Dusername=' + __settings__('username'))
                    args.append('-Dpassword=' + __settings__('password'))
                    args.append('-Dremember.me=' + __settings__('rememberme'))
                    args.append('-Dplayer.name=' + __settings__('playername'))
                    
                    args.append('-jar')
                    args.append(__cwd__ + '/resources/SCPlayer.jar')
                    
                    
                    for arg in args:
                        print arg
                    p = subprocess.Popen(args, cwd=__cwd__ + '/resources/')
                
                    print 'SCPlayer PID : ' + str(p.pid)
                
                pDialog = xbmcgui.DialogProgress()
                pDialog.create('SCPlayer', __language__(32014))
                pDialog.update(percent=50)
                
                ws = verifyState(1, None)
                
                if wsconnected == True:
                    pDialog.close()
                    
                    wsverifythread = threading.Thread(target = verifyState, args=(1, wsp))
                    wsverifythread.setDaemon(True)
                    wsverifythread.start()
                    
                    playbackWindow = ShufflePlaybackWindow("shuffle-playback-window.xml", __cwd__, spotifyIntegration=si)
                    playbackController = ShufflePlaybackController(playbackWindow)
                    
                    wdthread = threading.Thread(target = intialize_window_data, args=(1, wsp))
                    wdthread.start()
                
                    playbackWindow.doModal()
                    ar.set()
                    wsp.set()
                    
                    del playbackWindow
                    del playbackController
                else:
                    pDialog.close()
                    
                if __settings__('runasservice') == 'false':
                    p.terminate()
            except OSError:
                log('Problem loading Core Player', xbmc.LOGFATAL)
                pDialog.close()
                sys.exit(-1)    
            del thread
            
        except:
            log("Exception Details: %s" % traceback.format_exc(), xbmc.LOGERROR)
    
