import xbmcgui, xbmcaddon, xbmc, sys, time
import traceback
import urllib
import os
from exceptions import OSError

__id__ = 'script.audio.scplayer'
__addon__ = xbmcaddon.Addon(__id__)
__language__   = __addon__.getLocalizedString
__icon__ = __addon__.getAddonInfo('icon')

__cwd__        = xbmc.translatePath( __addon__.getAddonInfo('path') ).decode("utf-8")

def log(msg, level=xbmc.LOGWARNING):
    xbmc.log((u"### [%s] - %s" % (__baseUrl__,msg,)).encode('utf-8'),level=xbmc.LOGWARNING )
    
__baseUrl__ = sys.argv[0]

BaseWindow = xbmcgui.WindowXMLDialog

class ShufflePlaybackWindow(BaseWindow):  # xbmcgui.WindowXMLDialog
    ALBUM_ART = 801
    ARTIST_LABEL = 802
    TITLE_LABEL = 803
    ALBUM_LABEL = 804
    NEXT_LABEL = 805

    TRACK_POSITION_LABEL = 810
    DURATION_LABEL = 812
    SLIDER_SEEK = 811

    # Button IDs
    BUTTON_PREVIOUS = 600
    BUTTON_PLAY = 601
    BUTTON_PAUSE = 602
    BUTTON_STOP = 603
    BUTTON_NEXT = 604

    BUTTON_NOT_MUTED = 620
    BUTTON_MUTED = 621
    SLIDER_VOLUME = 622

    BUTTON_REPEAT = 605
    BUTTON_REPEAT_ENABLED = 606

    BUTTON_RANDOM = 607
    BUTTON_RANDOM_ENABLED = 608

    BUTTON_CROSSFADE = 609
    BUTTON_CROSSFADE_ENABLED = 610

    def __init__(self, *args, **kwargs):
        self.closeRequested = False
        # Copy off the key-word arguments
        # The non keyword arguments will be the ones passed to the main WindowXML
        self.spotifyIntegration = kwargs.pop('spotifyIntegration')
        self.currentTrack = None
        self.nextTrack = None

        self.delayedRefresh = 0
        # After startup we can always process the action
        self.nextFilteredAction = 0

        # Record if the playlist is random and the loop state
        self.isRandom = False
        self.isLoop = False
        
        self.coverImg = ''

    def setSpotifyIntegration(self, spotifyIntegration):
        self.spotifyIntegration = spotifyIntegration
        
    def isClose(self):
        return self.closeRequested

    # Handle the close action
    def onAction(self, action):
        # actioncodes from https://github.com/xbmc/xbmc/blob/master/xbmc/guilib/Key.h
        ACTION_PREVIOUS_MENU = 10
        ACTION_NAV_BACK = 92

        # For remote control
        ACTION_PAUSE = 12
        ACTION_STOP = 13
        ACTION_NEXT_ITEM = 14
        ACTION_PREV_ITEM = 15
        # The following 4 are active forward and back
        ACTION_FORWARD = 16
        ACTION_REWIND = 17
        ACTION_PLAYER_FORWARD = 77
        ACTION_PLAYER_REWIND = 78

        ACTION_PLAYER_PLAY = 79
        ACTION_VOLUME_UP = 88
        ACTION_VOLUME_DOWN = 89
        ACTION_MUTE = 91

        # Values Used in the custom keymap
        ACTION_FIRST_PAGE = 159  # Next Track
        ACTION_LAST_PAGE = 160  # Previous Track
        ACTION_PAGE_UP = 5  # Increase Volume
        ACTION_PAGE_DOWN = 6  # Decrease Volume
        ACTION_TOGGLE_WATCHED = 200  # Mute volume
        
        #log(action)

        if (action == ACTION_PREVIOUS_MENU) or (action == ACTION_NAV_BACK):
            log("ShufflePlaybackWindow: Close Action received: %s" % str(action.getId()), xbmc.LOGWARNING)
            self.close()
        else:
            # Handle remote control commands
            if((action == ACTION_PLAYER_PLAY) or (action == ACTION_PAUSE)):
                # Get the initial state of the device
                isPlaying = False #bool(self.spotifyDevice.SpPlaybackIsPlaying())
                

                # Play/pause is a toggle, so pause if playing
                if isPlaying:
                    self.onClick(ShufflePlaybackWindow.BUTTON_PAUSE)
                else:
                    self.onClick(ShufflePlaybackWindow.BUTTON_PLAY)
            elif (action == ACTION_STOP):
                self.onClick(ShufflePlaybackWindow.BUTTON_STOP)
            elif (action == ACTION_NEXT_ITEM) or (action == ACTION_FIRST_PAGE):
                self.onClick(ShufflePlaybackWindow.BUTTON_NEXT)
            elif (action == ACTION_PREV_ITEM) or (action == ACTION_LAST_PAGE):
                self.onClick(ShufflePlaybackWindow.BUTTON_PREVIOUS)
            elif (action == ACTION_VOLUME_UP) or (action == ACTION_PAGE_UP):
                # Get the current slider position
                volumeSlider = self.getControl(ShufflePlaybackWindow.SLIDER_VOLUME)
                currentSliderPosition = int(volumeSlider.getPercent())
                if currentSliderPosition < 100:
                    # Bump the volume by double the wait time (otherwise we can't skip forward accurately)
                    volumeSlider.setPercent(currentSliderPosition + 2)
                    self.onClick(ShufflePlaybackWindow.SLIDER_VOLUME)
            elif (action == ACTION_VOLUME_DOWN) or (action == ACTION_PAGE_DOWN):
                # Get the current slider position
                volumeSlider = self.getControl(ShufflePlaybackWindow.SLIDER_VOLUME)
                currentSliderPosition = int(volumeSlider.getPercent())
                if currentSliderPosition > 0:
                    # Bump the volume down by double the wait time (otherwise we can't skip forward accurately)
                    volumeSlider.setPercent(currentSliderPosition - 2)
                    self.onClick(ShufflePlaybackWindow.SLIDER_VOLUME)
            elif((action == ACTION_FORWARD) or (action == ACTION_PLAYER_FORWARD)):
                # Get the current slider position
                seekSlider = self.getControl(ShufflePlaybackWindow.SLIDER_SEEK)
                currentSliderPosition = int(seekSlider.getPercent())
                if currentSliderPosition < 99:
                    # Bump the slider by double the wait time (otherwise we can't skip forward accurately)
                    seekSlider.setPercent(currentSliderPosition + (int(1.5) * 2))
                    self.onClick(ShufflePlaybackWindow.SLIDER_SEEK)
            elif((action == ACTION_REWIND) or (action == ACTION_PLAYER_REWIND)):
                # Get the current slider position
                seekSlider = self.getControl(ShufflePlaybackWindow.SLIDER_SEEK)
                currentSliderPosition = int(seekSlider.getPercent())
                if currentSliderPosition > 0:
                    # Bump the slider down by double the wait time (otherwise we can't skip forward accurately)
                    seekSlider.setPercent(currentSliderPosition - (int(1.5) * 2))
                    self.onClick(ShufflePlaybackWindow.SLIDER_SEEK)

    # Handle the close event - make sure we set the flag so we know it's been closed
    def close(self):
        self.closeRequested = True
        BaseWindow.close(self)

    # Updates the controller display
    def updateDisplay(self, metadata):
        # Get the current track information
        
        log('atualizando tela')

        self.currentTrack = metadata
        
        log(metadata)
        if (metadata is not None):
            titleLabel = self.getControl(ShufflePlaybackWindow.TITLE_LABEL)
            titleLabel.reset()
            titleLabel.addLabel(metadata.get('name'))
            
            artistLabel = self.getControl(ShufflePlaybackWindow.ARTIST_LABEL)
            artistLabel.reset()
            artistLabel.addLabel(metadata.get('artist'))
        
            albumLabel = self.getControl(ShufflePlaybackWindow.ALBUM_LABEL)
            albumLabel.reset()
            albumLabel.addLabel(metadata.get('album'))
            
            self.spotifyIntegration.getAlbumCover()

            '''
            log(utils.get_image_url(metadata['cover_uri']))
            fileToDown = __cwd__ + '/' + self.coverImg
            urllib.urlretrieve(utils.get_image_url(metadata['cover_uri']), fileToDown)
            albumArt.setImage(fileToDown, useCache=False)
            '''
        
        '''
        track = self.spotifyDevice.get_current_track_info()
        # Now merge the track and event information
        track = self.spotifyDevice.mergeTrackInfoAndEvent(track, eventDetails, self.currentTrack)

        # Only update if the track has changed
        if self.spotifyDevice.hasTrackChanged(self.currentTrack, track):
            log("ShufflePlaybackWindow: Track changed, updating screen")
            # Get the album art if it is set (Default to the Sonos icon)
            albumArtImage = __icon__
            if track['album_art'] != "":
                albumArtImage = track['album_art']

            # Need to populate the popup with the artist details
            albumArt = self.getControl(ShufflePlaybackWindow.ALBUM_ART)
            albumArt.setImage(albumArtImage)

            artistLabel = self.getControl(ShufflePlaybackWindow.ARTIST_LABEL)
            artistLabel.reset()
            artistLabel.addLabel(track['artist'])

            titleLabel = self.getControl(ShufflePlaybackWindow.TITLE_LABEL)
            titleLabel.reset()
            titleLabel.addLabel(track['title'])

            albumLabel = self.getControl(ShufflePlaybackWindow.ALBUM_LABEL)
            albumLabel.reset()
            albumLabel.addLabel(track['album'])

            # Display the track duration
            durationLabel = self.getControl(ShufflePlaybackWindow.DURATION_LABEL)
            durationLabel.setLabel(self._stripHoursFromTime(track['duration']))

            # If the duration is 00:00:00 then this normally means that something like radio
            # is steaming so we shouldn't show any timing details
            if track['duration'] == '0:00:00':
                durationLabel.setVisible(False)
            else:
                durationLabel.setVisible(True)

        # Store the duration in seconds - it is used a few times later on
        track['duration_seconds'] = self._getSecondsInTimeString(track['duration'])

        # Set the current position of where the track is playing in the seconds format
        # this makes it easier to use later, instead of always parsing the string format
        track['position_seconds'] = self._getSecondsInTimeString(track['position'])

        # Get the control that currently has focus
        focusControl = -1
        try:
            focusControl = self.getFocusId()
        except:
            pass

        # Get the playing mode, so see if random or repeat has changes
        self.isRandom, self.isLoop = self.spotifyDevice.getPlayMode()

        randomButton = self.getControl(ShufflePlaybackWindow.BUTTON_RANDOM)
        # We can not calculate the next track if it is random
        if self.isRandom:
            log("ShufflePlaybackWindow: Random enabled - Disabling button")
            randomButton.setVisible(False)
            # Set the correct highlighted button
            if focusControl == ShufflePlaybackWindow.BUTTON_RANDOM:
                self.setFocusId(ShufflePlaybackWindow.BUTTON_RANDOM_ENABLED)
        else:
            log("ShufflePlaybackWindow: Random disabled - Enabling Button")
            randomButton.setVisible(True)
            # Set the correct highlighted button
            if focusControl == ShufflePlaybackWindow.BUTTON_RANDOM_ENABLED:
                self.setFocusId(ShufflePlaybackWindow.BUTTON_RANDOM)

        # Set the next track info, needs to be done after we know if
        # random play is enabled
        self._updateNextTrackInfo(track)

        # Set the repeat button status
        repeatButton = self.getControl(ShufflePlaybackWindow.BUTTON_REPEAT)
        if self.isLoop:
            repeatButton.setVisible(False)
            # Set the correct highlighted button
            if focusControl == ShufflePlaybackWindow.BUTTON_REPEAT:
                self.setFocusId(ShufflePlaybackWindow.BUTTON_REPEAT_ENABLED)
        else:
            repeatButton.setVisible(True)
            # Set the correct highlighted button
            if focusControl == ShufflePlaybackWindow.BUTTON_REPEAT_ENABLED:
                self.setFocusId(ShufflePlaybackWindow.BUTTON_REPEAT)

        # Get the current Cross-Fade setting
        crossFade = self.spotifyDevice.cross_fade
        crossFadeButton = self.getControl(ShufflePlaybackWindow.BUTTON_CROSSFADE)
        if crossFade:
            crossFadeButton.setVisible(False)
            # Set the correct highlighted button
            if focusControl == ShufflePlaybackWindow.BUTTON_CROSSFADE:
                self.setFocusId(ShufflePlaybackWindow.BUTTON_CROSSFADE_ENABLED)
        else:
            crossFadeButton.setVisible(True)
            # Set the correct highlighted button
            if focusControl == ShufflePlaybackWindow.BUTTON_CROSSFADE_ENABLED:
                self.setFocusId(ShufflePlaybackWindow.BUTTON_CROSSFADE)

        self.currentTrack = track

        # Display the track position
        trackPositionLabel = self.getControl(ShufflePlaybackWindow.TRACK_POSITION_LABEL)
        trackPositionLabel.setLabel(self._stripHoursFromTime(track['position']))

        # Get the initial state of the device
        playStatus = self.spotifyDevice.get_current_transport_info()

        # Set the play/pause button to the correct value
        playButton = self.getControl(ShufflePlaybackWindow.BUTTON_PLAY)
        if (playStatus is not None) and (playStatus['current_transport_state'] == 'PLAYING'):
            playButton.setVisible(False)
            # Set the correct highlighted button
            if focusControl == ShufflePlaybackWindow.BUTTON_PLAY:
                self.setFocusId(ShufflePlaybackWindow.BUTTON_PAUSE)
        else:
            playButton.setVisible(True)
            # Set the correct highlighted button
            if focusControl == ShufflePlaybackWindow.BUTTON_PAUSE:
                self.setFocusId(ShufflePlaybackWindow.BUTTON_PLAY)

        # Check to see what the current state of the mute button is
        muteButton = self.getControl(ShufflePlaybackWindow.BUTTON_NOT_MUTED)
        if self.spotifyDevice.mute is False:
            muteButton.setVisible(True)
            # Set the correct highlighted button
            if focusControl == ShufflePlaybackWindow.BUTTON_MUTED:
                self.setFocusId(ShufflePlaybackWindow.BUTTON_NOT_MUTED)
        else:
            muteButton.setVisible(False)
            # Set the correct highlighted button
            if focusControl == ShufflePlaybackWindow.BUTTON_NOT_MUTED:
                self.setFocusId(ShufflePlaybackWindow.BUTTON_MUTED)

        # The following controls need a delayed refresh, this is because they
        # are controls like sliders, so we do not want to update them until
        # the slider operation is complete
        if self.delayedRefresh < 1:
            # Get the current volume and set the slider
            # Will return a value between 0 and 100
            currentVolume = self.spotifyDevice.volume
            # Get the slider control
            volumeSlider = self.getControl(ShufflePlaybackWindow.SLIDER_VOLUME)
            # Don't move slider is already in correct position
            currentSliderPosition = int(volumeSlider.getPercent())
            if currentSliderPosition != currentVolume:
                volumeSlider.setPercent(currentVolume)

            # Set the seek slider
            self._setSeekSlider(track['position_seconds'], track['duration_seconds'])
        else:
            self.delayedRefresh = self.delayedRefresh - 1
        '''
    def updateCover(self, coverUrl):
        if self.coverImg != '':
                try:
                    os.remove(__cwd__ + '/' + self.coverImg)
                except OSError:
                    print 'erro ao excluir imagem do cover do album'
                            
        self.coverImg = coverUrl.split('/')[-1]
        albumArt = self.getControl(ShufflePlaybackWindow.ALBUM_ART)
        
        fileToDown = __cwd__ + '/' + self.coverImg
        urllib.urlretrieve(coverUrl, fileToDown)
        albumArt.setImage(fileToDown, useCache=False)
    # Do the initial setup of the dialog
    def onInit(self):
        log('init?')

    # work out if a given action is OK to run
    def _canProcessFilteredAction(self):
        currentTime = time.time()

        # Make sure we are not in a blackout zone
        if currentTime > self.nextFilteredAction:
            # Reset the time, and make sure we do not process any others
            # for another 2 seconds (This will prevent a large build up
            # as we hope that the sonos system can process this within
            # 2 seconds, otherwise there will be a delay)
            self.nextFilteredAction = currentTime + 1.5
            return True
        elif self.nextFilteredAction > 0:
            log("ShufflePlaybackWindow: Ignoring commands until %s" % time.strftime("%H:%M:%S", time.gmtime(self.nextFilteredAction)))

        return False

    # Handle the operations where the user clicks on a button
    def onClick(self, controlID):
        # Play button has been clicked
        if controlID == ShufflePlaybackWindow.BUTTON_PLAY:
            log("ShufflePlaybackWindow: Play Requested")
            # Send the play message to Sonos
            self.spotifyIntegration.play()

        elif controlID == ShufflePlaybackWindow.BUTTON_PAUSE:
            log("ShufflePlaybackWindow: Pause Requested")
            # Send the pause message to Sonos
            self.spotifyIntegration.pause()

        elif controlID == ShufflePlaybackWindow.BUTTON_NEXT:
            log("ShufflePlaybackWindow: Next Track Requested")
            self.spotifyIntegration.next()

        elif controlID == ShufflePlaybackWindow.BUTTON_PREVIOUS:
            log("ShufflePlaybackWindow: Previous Track Requested")
            self.spotifyIntegration.prev()

        elif controlID == ShufflePlaybackWindow.BUTTON_STOP:
            log("ShufflePlaybackWindow: Stop Requested")
            self.spotifyIntegration.pause()

        elif controlID == ShufflePlaybackWindow.BUTTON_REPEAT:
            log("ShufflePlaybackWindow: Repeat On Requested")
            self.isLoop = True
            self.spotifyIntegration.repeat(True)

        elif controlID == ShufflePlaybackWindow.BUTTON_REPEAT_ENABLED:
            log("ShufflePlaybackWindow: Repeat Off Requested")
            self.isLoop = False
            self.spotifyIntegration.repeat(False)

        elif controlID == ShufflePlaybackWindow.BUTTON_RANDOM:
            log("ShufflePlaybackWindow: Randon On Requested")
            self.isRandom = True
            self.spotifyIntegration.shuffle(True)

        elif controlID == ShufflePlaybackWindow.BUTTON_RANDOM_ENABLED:
            log("ShufflePlaybackWindow: Randon On Requested")
            self.isRandom = False
            self.spotifyIntegration.shuffle(False)

        elif controlID == ShufflePlaybackWindow.BUTTON_CROSSFADE:
            log("ShufflePlaybackWindow: Crossfade On Requested")
            log('not implemented')
            #self.spotifyDevice.cross_fade = True

        elif controlID == ShufflePlaybackWindow.BUTTON_CROSSFADE_ENABLED:
            log("ShufflePlaybackWindow: Crossfade Off Requested")
            log('not implemented')
            #self.spotifyDevice.cross_fade = False

        elif controlID == ShufflePlaybackWindow.BUTTON_NOT_MUTED:
            log("ShufflePlaybackWindow: Mute Requested")
            log('not implemented')
            #self.spotifyDevice.mute = True

        elif controlID == ShufflePlaybackWindow.BUTTON_MUTED:
            log("ShufflePlaybackWindow: Mute Requested")
            log('not implemented')
            #self.spotifyDevice.mute = False

        elif controlID == ShufflePlaybackWindow.SLIDER_VOLUME:
            # Only process the operation if we are allowed
            # this is to prevent a buildup of actions
            if self._canProcessFilteredAction():
                # Get the position of the slider
                volumeSlider = self.getControl(ShufflePlaybackWindow.SLIDER_VOLUME)
                currentSliderPosition = int(volumeSlider.getPercent())

                log("ShufflePlaybackWindow: Volume Request to value: %d" % currentSliderPosition)

                # Before we send the volume change request we want to delay any refresh
                # on the gui so we have time to perform the slide operation without
                # the slider being reset
                self._setDelayedRefresh()

                # Now set the volume
                log('TODO implementar volue')
                #self.spotifyDevice.volume = currentSliderPosition

        elif controlID == ShufflePlaybackWindow.SLIDER_SEEK:
            # Only process the operation if we are allowed
            # this is to prevent a buildup of actions
            if self._canProcessFilteredAction():
                # Get the position of the slider
                seekSlider = self.getControl(ShufflePlaybackWindow.SLIDER_SEEK)
                currentSliderPosition = int(seekSlider.getPercent())

                log("ShufflePlaybackWindow: Seek Request to value: %d" % currentSliderPosition)

                # Before we send the seek change request we want to delay any refresh
                # on the gui so we have time to perform the slide operation without
                # the slider being reset
                self._setDelayedRefresh()

                # Now set the seek location
                log('TODO implementar seek')
                self._setSeekPosition(currentSliderPosition)

#        else:
#            xbmcgui.Dialog().ok(__addon__.getLocalizedString(32001), "Control clicked is " + str(controlID))

        # Refresh the screen to show the current state
        #self.updateDisplay()

    # Set a delay time so that the screen does not automatically update
    # and leaves time for a given operation
    def _setDelayedRefresh(self):
        # Convert the refresh interval into seconds
        refreshInterval = 2 / 1000
        if refreshInterval == 0:
            # Make sure we do not divide by zero
            refreshInterval = 1
        self.delayedRefresh = int(4 / float(refreshInterval))
        if self.delayedRefresh == 0:
            self.delayedRefresh = 1

    # Takes a time string (00:00:00) and removes the hour section if it is 0
    def _stripHoursFromTime(self, fullTimeString):
        # Some services do not support duration
        if fullTimeString == 'NOT_IMPLEMENTED':
            return ""

        if (fullTimeString is None) or (fullTimeString == ""):
            return "00:00"
        if fullTimeString.count(':') == 2:
            # Check if the hours section should be stripped
            hours = 0
            try:
                hours = int(fullTimeString.split(':', 1)[0])
            except:
                # Hours section is not numbers
                log("ShufflePlaybackWindow: Exception Details: %s" % traceback.format_exc())
                hours = 0

            # Only strip the hours if there are no hours
            if hours < 1:
                return fullTimeString.split(':', 1)[-1]
        return fullTimeString

    # Set the seek slider to the current position of the track
    def _setSeekSlider(self, currentPositionSeconds, trackDurationSeconds):
        # work out the percentage we are through the track
        currentPercentage = 0
        if trackDurationSeconds > 0:
            currentPercentage = int((float(currentPositionSeconds) / float(trackDurationSeconds)) * 100)

        log("ShufflePlaybackWindow: Setting seek slider to %d" % currentPercentage)

        # Get the slider control
        seekSlider = self.getControl(ShufflePlaybackWindow.SLIDER_SEEK)
        seekSlider.setPercent(currentPercentage)

    # Converts a time string 0:00:00 to the total number of seconds
    def _getSecondsInTimeString(self, fullTimeString):
        # Some services do not support duration
        if fullTimeString == 'NOT_IMPLEMENTED':
            return -1

        # Start by splitting the time into sections
        hours = 0
        minutes = 0
        seconds = 0

        try:
            hours = int(fullTimeString.split(':', 1)[0])
            minutes = int(fullTimeString.split(':')[1])
            seconds = int(fullTimeString.split(':')[2])
        except:
            # time sections are not numbers
            log("ShufflePlaybackWindow: Exception Details: %s" % traceback.format_exc())
            hours = 0
            minutes = 0
            seconds = 0

        totalInSeconds = (((hours * 60) + minutes) * 60) + seconds
        log("ShufflePlaybackWindow: Time %s, splits into hours=%d, minutes=%d, seconds=%d, total=%d" % (fullTimeString, hours, minutes, seconds, totalInSeconds))

        # Return the total time in seconds
        return totalInSeconds

    # Converts a time string 0:00:00 to the total number of seconds
    def _getMillisecondsInTimeString(self, fullTimeString):
        return self._getSecondsInTimeString(fullTimeString) * 1000
        
    # Sets the current seek time, sending it to the sonos speaker
    def _setSeekPosition(self, percentage):
        trackDurationSeconds = self.currentTrack['duration_seconds']

        if trackDurationSeconds > 0:
            # Get the current number of seconds into the track
            newPositionSeconds = int((float(percentage) * float(trackDurationSeconds)) / 100)

            # Convert the seconds into a timestamp
            newPosition = "0:00:00"

            # Convert the duration into a viewable format
            if newPositionSeconds > 0:
                seconds = newPositionSeconds % 60
                minutes = 0
                hours = 0

                if newPositionSeconds > 60:
                    minutes = ((newPositionSeconds - seconds) % 3600) / 60

                if newPositionSeconds > 3600:
                    hours = (newPositionSeconds - (minutes * 60) - seconds) / 3600

                # Build the string up
                newPosition = "%d:%02d:%02d" % (hours, minutes, seconds)

            # Now send the seek message to the sonos speaker
            log('TODO implementar seek')
            #self.spotifyDevice.seek(newPosition)

    # Populates the details of the next track that will be played
    def _updateNextTrackInfo(self, track=None):
        nextTrackLabel = self.getControl(ShufflePlaybackWindow.NEXT_LABEL)
        nextTrackCreator = None
        nextTrackTitle = None

        # Make sure there is a track present, also want to make sure that we
        # are not streaming something - as we do not want to display a next
        # track when we are streaming, this is normally the case if the
        # track duration is zero
        if (track is not None) and (track['title'] != '') and (track['duration'] != '0:00:00'):
            # The code below gives the next track in the playlist
            # not the next track to be played (which is the case if random)
            if self.isRandom is False:
                # Check if there is a next track
                playlistPos = track['playlist_position']
                log("ShufflePlaybackWindow: Current track playlist position is %s" % str(playlistPos))
                if track['playlist_position'] != "" and int(track['playlist_position']) > -1:
                    # Also get the "Next Track" Information
                    # 0 would be the current track
                    nextTrackList = self.spotifyDevice.get_queue(int(track['playlist_position']), 1)

                    if (nextTrackList is not None) and (len(nextTrackList) > 0):
                        nextTrackItem = nextTrackList[0]
                        nextTrackCreator = nextTrackItem.creator
                        nextTrackTitle = nextTrackItem.title
            # If we have random play enabled, then we can not just read the nest
            # track in the playlist, for this case we will need to see if there
            # is an event that tells us what the next track is
            elif track['lastEventDetails'] is not None:
                # Get the track and creator if they both exist, if only one
                # exists, then it's most probably a radio station and Next track
                # title just contains a URI
                if (track['next_artist'] is not None) and (track['next_title'] is not None):
                    nextTrackCreator = track['next_artist']
                    nextTrackTitle = track['next_title']

        # Check to see if both the title and creator of the next track is set
        if (nextTrackCreator is not None) and (nextTrackTitle is not None):
            nextTrackText = "[COLOR=FF0084ff]%s:[/COLOR] %s - %s" % (__addon__.getLocalizedString(32062), nextTrackTitle, nextTrackCreator)
            # If the next track has changed, then set the new value
            # Otherwise we just leave it as it was
            if self.nextTrack != nextTrackText:
                self.nextTrack = nextTrackText
                nextTrackLabel.reset()
                nextTrackLabel.addLabel(nextTrackText)
        else:
            # If there is no next track, then clear the screen
            log("ShufflePlaybackWindow: Clearing next track label")
            nextTrackLabel.reset()
            nextTrackLabel.addLabel("")
