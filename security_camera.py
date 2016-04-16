#!/usr/bin/python
# Based on the "security camera" example Python script found on Linphone.org here:
# https://wiki.linphone.org/wiki/index.php/Raspberrypi:start
# Heavily modified to add motion detector features for Zilog ePIR SBC with ZDots. This is an advanced
# version and I cannot find this exact model, so I think it's discontinued.
#
# Now supports PIR sensor (newer style, lower power) by simply setting PIRPIN > 0.
# The default is to use pin 4 (in BCM mode = GPIO4 = physical pin = 7 = BOARD mode pin 7).
#
# On the off-chance that you DO have an ePIR, simply set PIRPIN = 0 and MDPIN = pin 5 on the ePIR. You'll
# actually want to refer to the Fritzing/PNG file for the schematic in that case, too. In order to support
# all features (at a future date), I wired up all of the ePIR pins. So it's GPIO-hungry. But I can add things
# like ambient light level (which I plan to do, BTW--even if I AM the only one with the module! :) ).
#
# Tip: If you want to disable the LED on the camera completely, add "disable_camera_led=1" (with no quotes) to
# the end of the line in /boot/cmdline.txt. *However* this is not working with Raspbian Jessie.
#
# Please let me know if you have questions. I will do my best to help you. (Please be patient. I am on disability.)
# All modifications written by: Leland Green - aboogieman - a t - gmail.com
__version__ = "0.2.1"

import os
import traceback
import datetime
import picamera
import linphone  # From python
import pygame  # pygame is only used to play sound files (in OGG format). You could easily remove all of this if needed.
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
import RPi.GPIO as GPIO
import io
import logging
# import stun
import serial
import signal
import time
import smtplib
import sys

# Global variables:

# This is only for additional trace messages, logging some info for the outgoing call, attempting external IP, etc.
DEBUG = False

# Constants
thisDeviceName = "rpi01"  # This is used for the email subject line. This should be unique per-device!
# While this is *not* required, it will let you know at a glance which camera triggered
# the email! :)

PRODUCTNAME = 'JamPi'  # You *must* change this in any commercial setting.

# WAITSECONDS also controls the shortest amount of time between printing "Motion detected".
WAITSECONDS = 60  # Set to zero to send a chat message every time motion is detected. (Not advised!)

# How long to wait between sending emails. Independent of WAITSECONDS. I recommend 60 or more, but use what you want.
WAITEMAILSECONDS = 60

RECORDVIDEO = True  # If you think you want a time lapse, please try a video first. Video is *less resource intensive*!
# If True, a video of length (WAITEMAILSECONDS / 2) seconds will be recorded.

# Set 'disableCameraLED = True' to turn off camera LED while recording
disableCameraLED = not DEBUG  # This leaves the camera LED *on* when DEBUG == True. Check it out! :-)
# disableCameraLED = True

# Video length: default = record for 3/4 the time up until next email-event.
VIDEOLENTGH = ((WAITEMAILSECONDS / 4) * 3)

RECORDTIMELAPSE = False

camera = 'V4L2: /dev/video0'  # This *should* pick up either the RaspiCam *or* a USB web cam. :)
RESOLUTION = (1296, 972)  # For high-latency networks, you probably want more like this. Max is (2592, 1944)
VIDEORESOLUTION = (1920, 1080)  # This is not transmitted, only stored on SD card/disk.

# Possible values are:
# 1080p=1920x1080, uxga=1600x1200, sxga=1280x960, 720p=1280x720, xga=1024x768,
# svga=800x600, 4cif=704x576, vga=640x480, cif=352x288, qvga=320x240, qcif=176x144

resolutions = \
    {
        '1080p': (1920, 1080),
        'uxga': (1600, 1200),
        'sxga': (1280, 960),
        '720p': (1280, 720),
        'xga': (1024, 768),
        'svga': (800, 600),
        '4cif': (704, 576),
        'vga': (640, 480),
        'cif': (352, 288),
        'qvga': (320, 240),
        'qcif': (176, 144)
    }
# TODO: Implement resolution by VIDEOPHONE_RESOLUTION_BY_NAME
VIDEOPHONE_RESOLUTION_BY_NAME = 'cif'  # 'cif' is the default resolution. See above fore other possible choices.

# Note that if you are NOT running as root, you should change this to '~/security_camera.log', or similar.
LOGFILENAME = '/var/log/security_camera.log'
SIPSERVER = 'sip:sip.linphone.org;transport=tls'
AUTHORIZATIONDOMAN = 'sip.linphone.org'

# Whether or not to save all images that are emailed to disk. (Or SD card, depending on the path you give.)
SAVEEMAILEDIMAGES = True
# Specify a unique mount-point here to save images to external/USB/network, etc.
SAVEIMAGEDIR = '/home/pi/'  # Leave this blank for current directory, else end with '/' char.

# sipUserName = 'yourSipUsername'
# sipPassword = 'yourSipPassword'
sipUserName = 'yourEmailAddressFrom(UserNameOnly)'
sipPassword = 'yoursippassword'
# doorbellToAddress is the SIP (or URL) address that will be called when the "doorbell" is pressed.
doorbellToAddress = 'sip:yourSipUsername@sip.linphone.org'  # Who to "ring". SIP address format
doorBellSoundWav = 'doorbell2.wav'  # Sound for local "doorbell ring". Person pushing button hears this.
doorBellSoundOgg = 'doorbell2.ogg'  # Sound for local "doorbell ring". Person pushing button hears this.

# sndCapture = 'ALSA: C-Media USB Headphone Set'
sndCapture = 'ALSA: default device'

# sndPlayback = 'snd_rpi_hifiberry_dac'
sndPlayback = 'ALSA: default device'
# Stuff that did NOT work for me:
# 'sndrpihifiberry' # 'snd_rpi_hifiber' # 'snd_soc_hifiberry_dac' # alsa.driver_name from 'pacmd'
# 'snd_rpi_hifiberry_dac'  # = 'HifiBerry DAC HiFi pcm5102a-hifi-0' = 'snd_rpi_hifiberry_dac'

# Now a set, not a list, which is mutable.
whiteList = ('sip:yourSipUsername@sip.linphone.org',
             'sip:aSecondSIPAccount@sip.linphone.org')

emailFromAddress = 'yourEmailAddressFrom(UserNameOnly)'
emailServer = 'smtp.gmail.com'
emailPort = 587

# Specify multiple destination email addresses by using this format:
# emailAddressTo = ['youremail@example.com', 'anotheremail@example.com'] # Do it like this for several,

# Specify a single destination email address like this:
emailAddressTo = 'youremail@example.com'  # or like this for just one recipient.

emailAccount = 'emailaddressfrom@example.com'  # Account to use for emailing
emailPassword = 'youremailpassword'  # Password for that account
emailSubject = 'Motion detected'  # Whatever you'd like in the subject line
# Alternate text (which *you* may not see, but others will!):
emailTextAlternate = 'Motion was detected. An image is included in the alternate MIME of this email.'

# Note: This can be overridden! See a few lines down.
detectMotion = True  # Whether or not we have the motion detector SBC connected. True = connected.
FLIPVERTICAL = False
ACK = 6  # "Acknowledge" character
NACK = 21  # "Non-Acknowledge" character

# *** WARNING *** Do not change these unless you are SURE what you are doing!  ***
# *** Specifying an incorrect value for LEDPIN can *DAMAGE YOUR RASPBERRY PI*! ***
# These pin numbers refer to the GPIO.BCM numbers.
# The first two (LEDPIN and BUTTONPIN) can be set to zero to disable.
LEDPIN = 17  # Motion-detected status - Blinking = motion detected. 0 = disable.
BUTTONPIN = 18  # Button to trigger start outgoing call. 0 = disable. (E.g., for use as a "video doorbell". Thanks Toshi!)

# You can--and it is recommended that YOU DO--add an additional LED by simply changing this:
LEDPINDOORBELL = LEDPIN  # If <> 0, this will stay on at all times, except blink when doorbell is rang.
# If you use two LED's, then LEDPIN will be exclusively for motion-detection status.
LEDDOORBELLBLINK = 2  # Time in seconds to blink. Blink will be ~4Hz, so at least 2 seconds is recommended.

# Setting the next two to 0 (or False) will disable the motion sensor. *THIS OVERRIDES ABOVE SETTING*
# MDPIN = 22  # Motion Detected pin (on ePIR). This can be any valid GPIO pin value, in BCM numbering scheme.
MDPIN = 0  # Set this *AND* PIRPIN = 0 to use as a "video doorbell", only. You can do both, too, if you'd like.
PIRPIN = 4  # Set this to zero to always use the MDPIN. That's for legacy ePIR devices, which you probably don't need.

# Changes expected below this line. Careful changes. :)
# Set GPIO for camera LED. Use 5 for Model A/B and 32 for Model B+.
CAMLEDPIN = 32  # This is sporadic across models so I discourage using it.

blinkCamLed = False

talkToEm = True
if talkToEm:
    from espeak import espeak


# These can be changed, but beware of setting them too low because camera IO takes place during both
# motion detection and sending email phases:
# WARNING: THIS FUNCTION IS DEPRECATED
# noinspection PyPep8Naming
def readLineCR(port):
    s = ''
    while True:
        try:
            ch = port.read(1)
            s += ch
            if ch == '\r' or ch == '':
                break
        except:  # TODO: Add specific exceptions here.
            # if traceback.print_exc() # Will be a "ready to read, but no data", in my experience.
            pass
    return s


def setup_log_colors():
    logging.addLevelName(logging.DEBUG, '\033[1;37m%s\033[1;0m' % logging.getLevelName(logging.DEBUG))
    logging.addLevelName(logging.INFO, '\033[1;36m%s\033[1;0m' % logging.getLevelName(logging.INFO))
    logging.addLevelName(logging.WARNING, '\033[1;31m%s\033[1;0m' % logging.getLevelName(logging.WARNING))
    logging.addLevelName(logging.ERROR, '\033[1;41m%s\033[1;0m' % logging.getLevelName(logging.ERROR))


def setup_log(log, trace):
    # if log is None:
    setup_log_colors()
    fmt = "%(asctime)s.%(msecs)03d %(levelname)s: %(message)s"
    datefmt = "%H:%M:%S"
    if trace:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(filename=log, level=level, format=fmt, datefmt=datefmt)


def log_handler(level, msg):
    method = getattr(logging, level)
    method(msg)


class SecurityCamera:
    def __init__(self, username='', password='', whitelist=(), camera='', snd_capture='', snd_playback=''):
        # type: (string, string, list, string, string, string) -> object
        """
    Main class, params are what you'd expect based on the names.
    :param username:
    :param password:
    :param whitelist:
    :param camera:
    :param snd_capture:
    :param snd_playback:
    """
        logging.debug("__init__")
        logging.info(
            "Initializaing {product} System version {version}...".format(product=PRODUCTNAME, version=__version__))
        # logging.debug("setting audio_dscp")
        # Pulling my values from "Commonly used DSCP Values" table in this article:
        # https://en.wikipedia.org/wiki/Differentiated_services
        # self.core.audio_dscp = 26
        # self.core.video_dscp = 46 # 46 = High Priority Expedited Forwarding (EF) - TODO: Can this be lowered???

        self.lastMessageTicks = time.time()  # Wait one "cycle" so everything gets initialized
        self.lastEmailTicks = time.time()  # via the TCP/IP (UDP/TLS/DTLS).

        self.dirname = '/var/log/jampi'
        if not os.path.exists(self.dirname):
            os.makedirs(self.dirname)

        # Initialize email
        self.smtp = smtplib.SMTP()

        # Initialize the motion detector. This is for the Zilog ePIR ZDot SBC. It has more features via serial mode,
        # so that's what we'll use here.
        GPIO.setwarnings(False)  # Disable "this channel already in use", etc.
        GPIO.setmode(GPIO.BCM)
        # GPIO.setup(CAMLEDPIN, GPIO.OUT, initial=False)

        self.port = serial.Serial("/dev/ttyAMA0", baudrate=9600, timeout=2)

        s = "Waiting for motion sensor to come online...."
        print s
        logging.debug(s)
        # time.sleep(10) # Arduino example says need delays between commands for proper operation. (I suspect for 9600 bps it needs time.)
        time.sleep(5)

        self.imageDir = os.getcwd()
        # self.imageDir = os.path.join(os.getcwd(), 'security-images')
        if not os.path.exists(self.imageDir):
            os.makedirs(self.imageDir)

        self.videoDir = os.getcwd()
        # self.videoDir = os.path.join(os.getcwd(), 'security-videos')
        if not os.path.exists(self.videoDir):
            os.makedirs(self.videoDir)

        if 0 != PIRPIN:
            # Assume newer PIR device, signal hooked to PIRPIN
            logging.info("Sensor online... Turning on motion sensor...")
            logging.debug('calling GPIO.setup(PIRPIN, ...)')
            GPIO.setup(PIRPIN, GPIO.IN, GPIO.PUD_DOWN)
            # GPIO.add_event_detect(PIRPIN, GPIO.RISING, self.motion_detected, bouncetime=2000)  # add rising edge detection on a channel
            print "Waiting for it to stabilize..."
            time.sleep(5)
            # while GPIO.input(PIRPIN)==1:
            #    Current_State  = 0
            logging.info("PIR sensor is ready.")
        elif 0 != MDPIN:
            # let the ePIR sensor wake up.
            # time.sleep(10) # Arduino example says need delays between commands for proper operation. (I suspect for 9600 bps it needs time.)
            ch = 'U'
            while ch == 'U':  # Repeat loop if not stablized. (ePIR replies with the character 'U' until the device becomes stable)
                # time.sleep(1)
                ch = self.port.read(
                    1)  # Sends status command to ePIR and assigns reply from ePIR to variable ch. (READ ONLY function)
                logging.debug('ch = %s' % (ch,))

            ch = readLineCR(self.port)
            s = "ePIR"
            if PIRPIN:
                s = "PIR"
            time.sleep(1)
            # print "%s sensor device online..." % (s, )

            self.port.write('CM')

            # If we don't do this, the next readLineCR() will get garbage and will take an undetermined amount of time!
            time.sleep(1)
            result = readLineCR(self.port)

            if len(result) > 1: result = result[-1]

            if result == 'R':
                print 'ePIR reset!'
            elif result == 'M' or result == 'N':
                print 'Motion detection mode confirmed.'
            else:
                logging.debug('Result = "%s"' % (result,))

            logging.debug("ch = '%s'\r\nDevice Ready" % (ch,))
            logging.info("\nePIR sensor ready.")

        if 0 != LEDPIN:
            GPIO.setup(LEDPIN, GPIO.OUT)  # This light blinks when motion detected. Connect with long wires to monitor!
            # If the video and chat are not enough notifications. :)
        if 0 != LEDPINDOORBELL:
            GPIO.setup(LEDPINDOORBELL, GPIO.OUT)
            GPIO.output(LEDPINDOORBELL, 1)  # Keep this LED ON.

        if 0 != MDPIN:
            GPIO.setup(MDPIN, GPIO.IN)

        self.doorbell_sound = None
        if 0 != BUTTONPIN:
            GPIO.setup(BUTTONPIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            # try:  # Background music is loaded here.
            #     #pygame.mixer.pre_init(48000, -16, 2, 4096)
            #     pygame.init()
            #     pygame.mixer.init(44100, -16, 2, 2048)
            #     self.doorbell_sound = pygame.mixer.Sound(doorBellSoundOgg)
            # except pygame.error, message:
            #     logging.error("Cannot load doorbell sound: {doorbellsound}\r\n{exception}".format(
            #         doorbellsound=doorBellSoundOgg, exception=traceback.format_exc()))

        global blinkCamLed
        val1 = blinkCamLed  # Only time we force a blinking LED is during initialization, so you know it's ready.
        blinkCamLed = True
        if LEDPINDOORBELL:
            self.flash_led(ledpin=LEDPINDOORBELL)
        else:
            self.flash_led()
        blinkCamLed = val1

        # Other member variables:
        self.imgStream = io.BytesIO()
        # time.sleep(2) #Allow time for ePIR warming-up

        self.quit = False
        self.username = ""
        self.current_call = None
        self.whitelist = whitelist
        callbacks = {
            'call_state_changed': self.call_state_changed,
        }

        # Initialize & Configure the linphone core
        logging.basicConfig(level=logging.INFO)
        signal.signal(signal.SIGINT, self.signal_handler)
        linphone.set_log_handler(log_handler)
        self.core = linphone.Core.new(callbacks, None, None)
        self.core.max_calls = 3
        self.core.video_adaptive_jittcomp_enabled = False
        self.core.adaptive_rate_control_enabled = False
        # self.core.quality_reporting_enabled = False # This fails straight away.
        self.core.echo_cancellation_enabled = False
        self.core.video_capture_enabled = True
        self.core.video_display_enabled = False  # This will only show up on a composite/HDMI monitor.
        self.core.keep_alive_enabled = True  # This is the default at time of writing.

        self.core.mic_enabled = True
        self.core.ringback = doorBellSoundWav  # This causes terrible distortion on my system
        # self.core.ring = doorBellSoundWav      # TODO: Use a separate sound for this.

        tr = self.core.sip_transports
        # assert_equals(tr.udp_port, 5060) # default config
        # assert_equals(tr.tcp_port, 5060) # default config
        tr.udp_port = 5063
        tr.tcp_port = 5067
        tr.tls_port = 32737
        tr.dtls_port = 32738
        self.core.sip_transports = tr
        tr = self.core.sip_transports
        logging.debug('Transports = UDP: %s, TCP %s, TLS %s, DTLS %s' % \
                      (tr.udp_port, tr.tcp_port, tr.tls_port, tr.dtls_port))

        # tr = self.core.sip_transports
        # tr.dtls_port = 5060
        # tr.tcp_port = 5061
        # tr.udp_port = 5062
        # tr.tls_port = 5063
        # self.core.sip_transports = tr
        self.core.stun_server = 'stun.linphone.org'
        self.core.firewall_policy = linphone.FirewallPolicy.PolicyUseIce
        if len(camera):
            self.core.video_device = camera
        if len(snd_capture):
            self.core.capture_device = snd_capture
        if len(snd_playback):
            self.core.playback_device = snd_playback

        # Only enable PCMU, PCMA and speex audio codecs
        for codec in self.core.audio_codecs:
            if codec.mime_type in ["PCMA",
                                   "PCMU"]:  # [, "speex", "opus", "VP8", "H264", "opus", "VP8", "H264"]: # Overkill! , "SILK"
                self.core.enable_payload_type(codec, True)
                logging.info("Adding codec %s..." % (codec.mime_type,))
            else:
                self.core.enable_payload_type(codec, False)

        # Only enable VP8 video codecs
        for codec in self.core.video_codecs:
            if codec.mime_type in ["VP8"]:
                logging.info("Adding codec %s..." % (codec.mime_type,))
                self.core.enable_payload_type(codec, True)
            else:
                self.core.enable_payload_type(codec, False)

        logging.debug("Configuring SIP account...")
        self.configure_sip_account(username, password)

        if talkToEm:
            espeak.synth('Security system is now on line.')
            time.sleep(3)
        self.configured = False

    def captureImage(self):
        # Create an in-memory stream
        with picamera.PiCamera(sensor_mode=4) as camera:  # A hack! Pin 0 causes it to not light at all.
            camera.led = False
            if FLIPVERTICAL:
                camera.vflip = True
                camera.hflip = True  # No separate option, just flip both directions.
            # Native mode: 2592 x 1944
            camera.resolution = RESOLUTION
            camera.start_preview()
            # camera.framerate = 30
            # camera.annotate_text = "You are SO BUSTED! This image has ALREADY been emailed to security!" # Fun! :-)
            time.sleep(2) # Wait for the automatic gain control to settle
            # Now fix the values
            camera.shutter_speed = camera.exposure_speed
            camera.exposure_mode = 'off'
            g = camera.awb_gains
            camera.awb_mode = 'off'
            camera.awb_gains = g
            # Finally, take several photos with the fixed settings

            # Camera warm-up time
            # fname = '%s' + str(datetime.datetime.now())
            self.imgStream.seek(0)
            camera.capture(self.imgStream, 'jpeg', use_video_port=True)
            try:
                outname = 'security_camera_image-{timestamp}.jpg'.format(timestamp=datetime.datetime.now().isoformat())
                outf = file(outname, 'wb')
                self.imgStream.seek(0)
                outf.write(self.imgStream.read())
            except:
                logging.error(traceback.format_exc())
            camera.stop_preview()
        return self.imgStream

    def emailImage(self):
        logging.debug("emailImage() called")
        self.captureImage()

        # if RECORDVIDEO or RECORDTIMELAPSE:
        #  return

        # Create the root message and fill in the from, to, and subject headers
        msgRoot = MIMEMultipart('related')
        msgRoot['Subject'] = 'Motion detected'
        msgRoot['From'] = emailFromAddress
        msgRoot['To'] = 'Security Team for camera ' + thisDeviceName  # emailAddressTo
        msgRoot.preamble = 'This is a multi-part message in MIME format.'

        # Encapsulate the plain and HTML versions of the message body in an
        # 'alternative' part, so message agents can decide which they want to display.
        msgAlternative = MIMEMultipart('alternative')
        msgRoot.attach(msgAlternative)

        msgText = MIMEText(emailTextAlternate)
        msgAlternative.attach(msgText)

        # We reference the image in the IMG SRC attribute by the ID we give it below
        msgText = MIMEText(
            '<b>Alert <i>motion detected</i> on camera %s</b> and here is a picture of what/whomever triggered this alert! <br><img src="cid:image1"><br>^^^ The Culprit ^^^' % (
                thisDeviceName), 'html')
        msgAlternative.attach(msgText)

        self.imgStream.seek(0L)
        msgImage = MIMEImage(self.imgStream.read())

        # Define the image's ID as referenced above
        msgImage.add_header('Content-ID', '<image1>')
        msgRoot.attach(msgImage)

        # Send the email (this example assumes SMTP authentication is required)
        self.smtp.connect(emailServer, emailPort)
        self.smtp.starttls()  # TODO: Can this be moved out of the iteration? Is it expensive?
        self.smtp.login(emailAccount, emailPassword)
        self.smtp.sendmail(emailFromAddress, emailAddressTo, msgRoot.as_string())
        self.smtp.quit()  # TODO: Determine if this can be elsewhere, or if we can leave this open.
        self.lastEmailTicks = time.time()
        if SAVEEMAILEDIMAGES:
            fname = '{saveimagedir}emailedSecurityCameraImage-{date}.jpg'.format(
                saveimagedir=SAVEIMAGEDIR,
                date=datetime.datetime.now().isoformat()
            )
            outf = file(fname, 'wb')
            self.imgStream.seek(0L)
            outf.write(self.imgStream.read())
            outf.close()
            logging.info('Emailed and saved image to "{fname}"'.format(fname=fname))
        else:
            logging.info('Emailed image at {currenttime}'.format(currenttime=datetime.datetime.now().isoformat()))

    def signal_handler(self, signal, frame):
        self.core.terminate_all_calls()
        self.quit = True

    def call_state_changed(self, core, call, state, message):
        body = "State: {state}".format(state=linphone.CallState.string(state))
        if state == linphone.CallState.IncomingReceived:
            if call.remote_address.as_string_uri_only() in self.whitelist:
                params = core.create_call_params(call)
                params.audio_enabled = True
                params.audio_multicast_enabled = False
                params.video_multicast_enabled = False
                logging.debug("Call params:\r\n" "%s" % (str(params),))
                core.accept_call_with_params(call, params)
                # call.microphone_volume_gain = 0.98 # Maximum value, I believe....
                self.current_call = call
                logging.debug('sip_transports: dtls = %d, tcp = %d, udp = %d, tls = %d' % \
                              (self.core.sip_transports.dtls_port, self.core.sip_transports.tcp_port,
                               self.core.sip_transports.udp_port, self.core.sip_transports.tls_port))
                logging.debug('sip_transports_used: dtls = %d, tcp = %d, udp = %d, tls = %d' % \
                              (self.core.sip_transports_used.dtls_port, self.core.sip_transports_used.tcp_port,
                               self.core.sip_transports_used.udp_port, self.core.sip_transports_used.tls_port))
                if talkToEm:
                    espeak.synth('Incoming call answered. You are being watched!')
                    time.sleep(2)
            else:
                core.decline_call(call, linphone.Reason.Declined)
                for contact in self.whitelist:
                    chat_room = core.get_chat_room_from_uri(contact)
                    if not chat_room:
                        continue
                    msg = chat_room.create_message(call.remote_address_as_string + ' tried to call')
                    chat_room.send_chat_message(msg)
        elif state == linphone.CallState.CallOutgoingInit \
                or state == linphone.CallState.CallOutgoingProgress \
                or state == linphone.CallState.CallOutgoingRinging:
            logging.info("\nCall remote: {address}".format(address=call.remote_address.as_string()))
            body += "\nFrom: {address}".format(address=call.remote_address.as_string())

        elif state == linphone.CallState.End:
            logging.info("Call ended normally.")
            self.current_call = None
        elif state == linphone.CallState.Error:
            logging.error("Error ... ending call!")
            # core.end_call(call)
            self.current_call = None
        else:
            logging.debug("call_state_changed() state = %s" % (linphone.CallState.string(state),))
        logging.info(body)

    def configure_sip_account(self, username, password):
        # Configure the SIP account
        proxy_cfg = self.core.create_proxy_config()
        proxy_cfg.identity_address = self.core.create_address(
            # 'sip:{username}@{authdomain}:5061'.format(username=username, authdomain=AUTHORIZATIONDOMAN))
            'sip:{username}@{authdomain}:5061'.format(username=username, authdomain=AUTHORIZATIONDOMAN))
        # proxy_cfg.server_addr = SIPSERVER
        proxy_cfg.server_addr = 'sip:' + AUTHORIZATIONDOMAN
        proxy_cfg.register_enabled = True
        self.core.add_proxy_config(proxy_cfg)
        self.core.default_proxy_config = proxy_cfg
        # auth_info = self.core.create_auth_info(username, None, password, None, None, 'sip.linphone.org')
        auth_info = self.core.create_auth_info(username, None, password, None, None, None)
        self.core.add_auth_info(auth_info)
        logging.info('auth_info.username = {username}, '.format(username=username, authdomain=AUTHORIZATIONDOMAN))
        self.username = username

    def run(self):
        while not self.quit:
            button_pressed = False
            if 0 != BUTTONPIN:
                button_pressed = not GPIO.input(BUTTONPIN)
            if button_pressed and self.core.current_call is None:
                # We do not check the time here. They can keep "ringing" the doorbell if they want
                # but it won't matter once a call is initiated.
                if self.doorbell_sound:
                    self.doorbell_sound.play()
                try:
                    if time.time() - self.lastMessageTicks > WAITSECONDS:
                        self.notify_chat_contacts(message_template="Doorbell ring on %s at %s")
                    params = self.core.create_call_params(None)
                    params.audio_enabled = True
                    params.video_enabled = True
                    params.audio_multicast_enabled = False  # Set these = True if you want multiple
                    params.video_multicast_enabled = False  # people to connect at once.
                    address = linphone.Address.new(doorbellToAddress)
                    logging.info('address = {address}, used_video_codec = {codec}'.format(
                        address=address,
                        codec=params.used_video_codec))
                    self.current_call = self.core.invite_address_with_params(address, params)
                    if None is self.current_call:
                        logging.error("Error creating call and inviting with params... outgoing call aborted.")
                    if time.time() - self.lastEmailTicks >= WAITEMAILSECONDS:
                        if LEDPINDOORBELL:
                            self.flash_led(ledpin=LEDPINDOORBELL, stay_on=True,
                                           blink_cam_led=False, delay=0.25, blink_count=8)
                        else:
                            self.flash_led()
                        self.notify_email_contacts()
                except KeyboardInterrupt:
                    self.quit = True
                    break
            elif detectMotion and self.core.current_call is None:
                motion_detected = False
                # Incoming calls have been handled, so check the motion detector:
                if 0 != PIRPIN:
                    # motion_detected = GPIO.wait_for_edge(PIRPIN,GPIO.RISING)
                    # motion_detected = GPIO.event_detected(PIRPIN)
                    motion_detected = GPIO.input(PIRPIN)
                    logging.debug("\rmotion_detected = %s, GPIO.input(PIRPIN) = %s" % (
                        str(motion_detected), str(GPIO.input(PIRPIN))))
                elif 0 != MDPIN:
                    motion_detected = GPIO.input(MDPIN) == 0

                if motion_detected:
                    self.motion_detected()
            # else:
            #  time.sleep(0.01) #
            self.core.iterate()

    def motion_detected(self):
        t = time.time()
        # logging.info('*Motion detected!*') # This may be useful when adjusting potentiometers on PIR sensor.
        if t - self.lastMessageTicks < WAITSECONDS and t - self.lastEmailTicks < WAITEMAILSECONDS:
            return
        logging.info('*Motion detected!*')
        if DEBUG:
            logging.debug('sip_transports: dtls = %d, tcp = %d, udp = %d, tls = %d' % \
                          (self.core.sip_transports.dtls_port, self.core.sip_transports.tcp_port, \
                           self.core.sip_transports.udp_port, self.core.sip_transports.tls_port))
            logging.debug('sip_transports_used: dtls = %d, tcp = %d, udp = %d, tls = %d' % \
                          (self.core.sip_transports_used.dtls_port, self.core.sip_transports_used.tcp_port, \
                           self.core.sip_transports_used.udp_port, self.core.sip_transports_used.tls_port))
            logging.debug('self.core.upnp_external_ipaddress = %s' % (self.core.upnp_external_ipaddress,))
            logging.debug('self.core.nat_address = %s' % (self.core.nat_address,))
            tr = self.core.sip_transports_used
            logging.debug(
                'self.core.linphone_core_get_sip_transports_used = dtls = %d, tcp = %d, udp = %d, tls = %d' % \
                (tr.dtls_port, tr.tcp_port, tr.udp_port, tr.tls_port))

        if time.time() - self.lastMessageTicks > WAITSECONDS:
            self.notify_chat_contacts()  # Note that times for message and email are independent.
        if time.time() - self.lastEmailTicks >= WAITEMAILSECONDS:
            try:
                self.notify_email_contacts()
                self.record_video_event()
            except KeyboardInterrupt:
                self.quit = True
        self.flash_led()

    def record_video_event(self):
        if RECORDVIDEO:
            with picamera.PiCamera(sensor_mode=1) as camera:
                if disableCameraLED:
                    camera.led = False  # The LED will still blink
                # What resolution for video is best??? This is full 1080p
                # On the Pi, the full resolution of the sensor is (2592 x 1944), and there's a 1080p video mode (1920 x 1080).
                # (1296, 972) # Had this
                camera.resolution = VIDEORESOLUTION
                camera.start_recording(os.path.join(self.videoDir, 'security_camera-%s.h264' % (
                    datetime.datetime.now().isoformat(' ')), ))
                camera.wait_recording(VIDEOLENTGH)
                camera.stop_recording()
        elif RECORDTIMELAPSE:
            with picamera.PiCamera(sensor_mode=4) as camera:  # 1296 x 972, 4:3
                if disableCameraLED:
                    camera.led = False
                camera.resolution = (1296, 972)
                logging.debug(('\rtime.time() - self.lastEmailTicks = %s, WAITEMAILSECONDS/2 = %d' % \
                               (time.time() - self.lastEmailTicks, WAITEMAILSECONDS / 2)))
                while time.time() - self.lastEmailTicks <= WAITEMAILSECONDS / 2:
                    for filename in camera.capture_continuous(os.path.join(self.imageDir,
                                                                           'img-%s{counter:03d}.jpg' % (
                                                                                   datetime.datetime.now().isoformat(
                                                                                       ' '),))):
                        self.core.iterate()
                        logging.info('Captured %s' % filename)
                        time.sleep(0.2)  # wait 5 minutes

    def notify_email_contacts(self):
        self.lastEmailTicks = time.time()
        self.emailImage()
        if talkToEm:
            # Note we *tell them* we're going to record a video, even if we're not. Sneaky! :)
            espeak.synth('An image has just been emailed to security.')
            time.sleep(2)
            espeak.synth('A video is being recorded of you, even as we speak.')
            time.sleep(2)

    def notify_chat_contacts(self, message_template="'Motion detected on %s at %s'"):
        logging.info("Notifying contacts...")
        for contact in self.whitelist:
            logging.info("Notifying %s" % (contact,))
            chat_room = self.core.get_chat_room_from_uri(contact)
            if not chat_room:
                continue
            dt = datetime.datetime.now()
            c = self.core.primary_contact_parsed
            ip = self.core.upnp_external_ipaddress
            ea = c.as_string()
            un = c.username
            cl = c.clean()
            # po = c.port
            logging.debug("c.port = {p}".format(p=c.port))
            po = 5061
            logging.debug("dir(c) = {d}".format(d=dir(c)))
            logging.info("c.display_name = {cdn}, c.username = {cun}, c.port = {cp}".format(
                cdn=c.display_name, cun=c.username, cp=c.port))
            logging.info("po = {po}, cl = {cl}, c = {c}, ip = {ip}, ea = {ea}, un = {un}".format(
                po=po, cl=cl, c=c, ip=ip, ea=ea, un=un))
            # nattype, external_ip, external_port = stun.get_ip_info('0.0.0.0', 54320, self.core.stun_server, 3478)
            # logging.debug('nattype = %s, external_ip = %s, external_port = %s' % (nattype, external_ip, external_port))
            # sipaddress = 'sip:yourSipUsername@%s:%s' %(external_ip, external_port)
            # logging.debug('sipaddress = %s' % (sipaddress, ))
            msg = chat_room.create_message(message_template % (ea, dt.isoformat(' ')))
            chat_room.send_chat_message(msg)
            self.lastMessageTicks = time.time()
            self.core.iterate()

    def flash_led(self, ledpin=LEDPIN, stay_on=False, blink_cam_led=blinkCamLed, delay=0.05, blink_count=10):
        if ledpin == LEDPINDOORBELL and not stay_on:  # Goof-proof? :)
            logging.debug('Recursion for flash_led()...')
            return self.flash_led(ledpin=LEDPINDOORBELL, stay_on=True, blink_cam_led=False, delay=0.125,
                                  blink_count=int(1 / delay) * LEDDOORBELLBLINK)
        for j in range(0, blink_count):
            if ledpin:
                GPIO.output(ledpin, True)
                if blink_cam_led:
                    GPIO.output(CAMLEDPIN, True)
                time.sleep(delay)
            if ledpin:
                GPIO.output(ledpin, False)
                if blink_cam_led:
                    GPIO.output(CAMLEDPIN, False)
                time.sleep(delay)
        if stay_on and ledpin:
            GPIO.output(ledpin, True)


def main(argc, argv):
    error = None
    try:
        setup_log(LOGFILENAME, trace=DEBUG)
        # These are your SIP username and password and system devices
        cam = SecurityCamera(username=sipUserName, password=sipPassword, whitelist=whiteList, camera=camera,
                             snd_capture=sndCapture, snd_playback=sndPlayback)
        cam.run()
    except:
        traceback.print_exc()  # Print the error
        error = traceback.format_exc()  # and format to log it (if possible)
    finally:
        GPIO.cleanup()
        if error:
            logging.error(error)


if __name__ == '__main__':
    main(len(sys.argv), sys.argv)
