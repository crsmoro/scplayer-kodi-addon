from ShufflePlaybackWindow import ShufflePlaybackWindow

class ShufflePlaybackController:

    def __init__(self, playbackWindow):
        self.playbackWindow = playbackWindow
    
    def playback_notify(self, action, data):
        print 'playback_notify : ' + action
        if action == 'play':
            print "ShufflePlaybackWindow kSpPlaybackNotifyPlay"
            self.playbackWindow.getControl(ShufflePlaybackWindow.BUTTON_PLAY).setVisible(False)
            self.playbackWindow.getControl(ShufflePlaybackWindow.BUTTON_PAUSE).setVisible(True)
            self.playbackWindow.setFocusId(ShufflePlaybackWindow.BUTTON_PAUSE)
        elif action == 'pause':
            print "ShufflePlaybackWindow kSpPlaybackNotifyPause"
            self.playbackWindow.getControl(ShufflePlaybackWindow.BUTTON_PAUSE).setVisible(False)
            self.playbackWindow.getControl(ShufflePlaybackWindow.BUTTON_PLAY).setVisible(True)
            self.playbackWindow.setFocusId(ShufflePlaybackWindow.BUTTON_PLAY)
        elif action == 'trackChanged' or action == 'track':
            print "ShufflePlaybackWindow kSpPlaybackNotifyTrackChanged"
            self.playbackWindow.updateDisplay(data)
        elif action == 'trackNext':
            print "ShufflePlaybackWindow kSpPlaybackNotifyNext"
            self.playbackWindow.updateDisplay(data)
        elif action == 'trackPrev':
            print "ShufflePlaybackWindow kSpPlaybackNotifyPrev"
            self.playbackWindow.updateDisplay(data)
        elif action == 'shuffle':
            self.playbackWindow.isRandom = data
            if data == True:
                print "ShufflePlaybackWindow kSpPlaybackNotifyShuffleEnabled"
            else:
                print "ShufflePlaybackWindow kSpPlaybackNotifyShuffleDisabled"
                
            try:
                focusControl = self.playbackWindow.getFocusId()
            except:
                pass
                
            repeatButton = self.getControl(ShufflePlaybackWindow.BUTTON_RANDOM)
            if self.playbackWindow.isRandom:
                repeatButton.setVisible(False)
                # Set the correct highlighted button
                if focusControl == ShufflePlaybackWindow.BUTTON_RANDOM:
                    self.playbackWindow.setFocusId(ShufflePlaybackWindow.BUTTON_RANDOM_ENABLED)
            else:
                repeatButton.setVisible(True)
                # Set the correct highlighted button
                if focusControl == ShufflePlaybackWindow.BUTTON_RANDOM_ENABLED:
                    self.playbackWindow.setFocusId(ShufflePlaybackWindow.BUTTON_RANDOM)

        elif action == 'repeat':
            self.playbackWindow.isLoop = data
            if data == True:
                print "ShufflePlaybackWindow kSpPlaybackNotifyRepeatEnabled"
            else:
                print "ShufflePlaybackWindow kSpPlaybackNotifyRepeatDisabled"
            
            try:
                focusControl = self.playbackWindow.getFocusId()
            except:
                pass
                
            repeatButton = self.getControl(ShufflePlaybackWindow.BUTTON_REPEAT)
            if self.playbackWindow.isLoop:
                repeatButton.setVisible(False)
                # Set the correct highlighted button
                if focusControl == ShufflePlaybackWindow.BUTTON_REPEAT:
                    self.playbackWindow.setFocusId(ShufflePlaybackWindow.BUTTON_REPEAT_ENABLED)
            else:
                repeatButton.setVisible(True)
                # Set the correct highlighted button
                if focusControl == ShufflePlaybackWindow.BUTTON_REPEAT_ENABLED:
                    self.playbackWindow.setFocusId(ShufflePlaybackWindow.BUTTON_REPEAT)
                    
        elif action == 'albumcover':
            print "albumcover"
            self.playbackWindow.updateCover(data)
        elif action == 'seek':
            print "seek"
            self.playbackWindow.updateSeek(data)
        else:
            print "ShufflePlaybackWindow UNKNOWN PlaybackNotify {}".format(action)
    
    
    def playback_seek(self, millis):
        print "playback_seek: {}".format(millis)
    
    def playback_volume(self, volume):
        print "playback_volume: {}".format(volume)
    