#!/usr/bin/python
# Based on the "security camera" example Python script found on Linphone.org here:
# https://wiki.linphone.org/wiki/index.php/Raspberrypi:start
# Heavily modified to add motion detector features for Zilog ePIR SBC with ZDots. This is an advanced
# version and I cannot find this exact model, so I think it's discontinued. Should work with minor
# modifications (and removal of features?) on other motion detectors.
#
# Please let me know if you have questions!
# Modifications by: Leland Green - yourEmailToAddress
__version__ = "0.1.3"

import datetime
import picamera
import linphone
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
global debug # This is only for printing some account info for the outgoing call, attempting external IP....
debug = True

# Constants
global thisDeviceName
thisDeviceName = "rpi01"

emailFromAddress = 'yourSipUserNamelabs'
#emailAddressTo = ['yourEmailToAddress', 'yourAdditionalEmail(Add more here)'] # Do it like this for several,
emailAddressTo = 'yourEmailToAddress'                          # or like this for just one recipient.
emailSubject = 'Motion detected'
emailTextAlternate = 'Motion was detected. An image is included in the alternate MIME of this email.'

detectMotion = True  # Whether or not we have the motion detector SBC connected. True = connected.
FLIPVERTICAL = False
ACK =  6 # "Acknowledge" character
NACK = 21 # "Non-Acknowledge" character

# *** WARNING *** Do not change these unless you are SURE what you are doing! ***
# These pin numbers refer to the GPIO.BCM numbers.
LEDPIN = 17  # Status - could do without
MDPIN = 22  # Motion Detected pin (on ePIR)
PIRPIN = 0  # Set this to zero to always use the MDPIN. That's for legacy ePIR devices, which you probably don't need.

# These can be changed, but beware of setting them too low because camera IO takes place during both
# motion detection and sending email phases:
WAITSECONDS = 30  # Set to zero to send a message every time motion is detected.
#WAITSECONDS = 20  # Set to zero to send a message every time motion is detected. Not recommended! :-)
# WAITSECONDS also controls the shortest amount of time between printing "Motion detected".

WAITEMAILSECONDS = 30  # How long to wait between sending emails. Independent of WAITSECONDS. I recommend 90 or more, but use what you want.
#WAITEMAILSECONDS = 60  # How long to wait between sending emails. Independent of WAITSECONDS. I recommend 60 or more, but use what you want.

def readLineCR(port):
  s = ''
  while  True:
    try:
      ch = port.read(1)
      s += ch
      if ch == '\r' or ch == '':
        break
    except: # TODO: Add specific exceptions here.
      pass # Will be a "ready to read, but no data", in my experience.
  return s

class SecurityCamera:
  def __init__(self, username='', password='', whitelist=[], camera='', snd_capture='', snd_playback=''):
    if debug: print "__init__"
    print "Initializaing...."
    #if debug:
    #print "setting audio_dscp"
    # Pulling my values from "Commonly used DSCP Values" table in this article:
    # https://en.wikipedia.org/wiki/Differentiated_services
    #self.core.audio_dscp = 26
    #self.core.video_dscp = 46 # 46 = High Priority Expedited Forwarding (EF) - TODO: Can this be lowered???

    self.lastMessageTicks = time.time() # Wait one "cycle" so everything gets initialized
    self.lastEmailTicks = time.time()   # via the TCP/IP (UDP/TLS/DTLS).

    # Initialize email
    self.smtp = smtplib.SMTP()

    # Initialize the motion detector. This is for the Zilog ePIR ZDot SBC. It has more features via serial mode,
    # so that's what we'll use here.
    GPIO.setwarnings(False) # Disable "this channel already in use", etc.
    GPIO.setmode(GPIO.BCM)

    self.port = serial.Serial("/dev/ttyAMA0", baudrate = 9600, timeout = 2)

    if PIRPIN <> 0:
      # Assume newer PIR device, signal hooked to PIRPIN
      print "Turning on motion sensor..."
      if debug: print 'calling GPIO.setup(PIRPIN, ...)'
      if PIRPIN <> 0:
        GPIO.setup(PIRPIN, GPIO.IN, GPIO.PUD_DOWN)
      #GPIO.setup(PIRPIN, GPIO.IN)
      GPIO.add_event_detect(PIRPIN, GPIO.RISING)  # add rising edge detection on a channel
      if debug: print "calling setmode()"
      # Loop until PIR indicates nothing is happening
      print "Waiting for it to stabilize..."
      while GPIO.input(PIRPIN) == 1:
        time.sleep(0.01)
      #while GPIO.input(PIRPIN)==1:
      #    Current_State  = 0
      print "PIR sensor is ready."
    else:
      # let the ePIR sensor wake up.
      #time.sleep(10) # Arduino example says need delays between commands for proper operation. (I suspect for 9600 bps it needs time.)
      time.sleep(5)
      ch = 'U'
      while ch == 'U': # Repeat loop if not stablized. (ePIR replies with the character 'U' until the device becomes stable)
        time.sleep(1)
        ch = self.port.read(1) # Sends status command to ePIR and assigns reply from ePIR to variable ch. (READ ONLY function)
        if debug: print 'ch = %s' % (ch, )

      self.port.write('CM')
      time.sleep(3) # If we don't do this, the next line will get garbage and will take an indermined amount of time!
      result = readLineCR(self.port)

      #if debug:
      if result == 'R':
        print 'ePIR reset!'
      elif result == 'M':
        print 'Motion detection mode confirmed.'
      else:
        print 'Result = "%s"' % (result, )

      if debug:
        print "ch = '%s'\r\nDevice Ready" % (ch, )
      else:
        print "\nePIR sensor ready."

    GPIO.setup(LEDPIN, GPIO.OUT) # Light (blink?) when motion detected
    GPIO.setup(MDPIN, GPIO.IN)
    self.flash_led()

    # Other member variables:
    self.imgStream = io.BytesIO()
    #time.sleep(2) #Allow time for ePIR warming-up

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
    linphone.set_log_handler(self.log_handler)
    self.core = linphone.Core.new(callbacks, None, None)
    self.core.max_calls = 2
    self.core.video_adaptive_jittcomp_enabled = False
    self.core.adaptive_rate_control_enabled = False
    #self.core.quality_reporting_enabled = False # This fails straight away.
    self.core.echo_cancellation_enabled = False
    self.core.video_capture_enabled = True
    self.core.video_display_enabled = False

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

    # Only enable PCMU and PCMA audio codecs
    for codec in self.core.audio_codecs:
      if codec.mime_type == "PCMA" or codec.mime_type == "PCMU":
        self.core.enable_payload_type(codec, True)
      else:
        self.core.enable_payload_type(codec, False)

    # Only enable VP8 video codec
    for codec in self.core.video_codecs:
      if codec.mime_type == "VP8":
        self.core.enable_payload_type(codec, True)
      else:
        self.core.enable_payload_type(codec, False)

    self.configure_sip_account(username, password)

    self.configured = False

  def captureImage(self):
    # Create an in-memory stream
    with picamera.PiCamera() as camera:
      if FLIPVERTICAL:
        camera.vflip = True
        camera.hflip = True # No separate option, just flip both directions.
      camera.start_preview()
      # Native mode: 2592 x 1944
      camera.resolution = (1920, 1080)
      #camera.framerate = 30
      # Wait for the automatic gain control to settle
      #camera.annotate_text = "You are SO BUSTED! This image has ALREADY been emailed to security!" # Fun! :-)
      time.sleep(2)
      # Now fix the values
      camera.shutter_speed = camera.exposure_speed
      camera.exposure_mode = 'off'
      g = camera.awb_gains
      camera.awb_mode = 'off'
      camera.awb_gains = g
      # Finally, take several photos with the fixed settings

      # Camera warm-up time
      #fname = '%s' + str(datetime.datetime.now())
      self.imgStream.seek(0)
      camera.capture(self.imgStream, 'jpeg', use_video_port=True)
      camera.stop_preview()
    return self.imgStream

  global shownDebugInfo
  shownDebugInfo = False
  def emailImage(self):


    if debug:
      print "emailImage() called"
    self.captureImage()
    #return

    # Create the root message and fill in the from, to, and subject headers
    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = 'Motion detected'
    msgRoot['From'] = emailFromAddress
    msgRoot['To'] = 'Security Team for camera ' + thisDeviceName #emailAddressTo
    msgRoot.preamble = 'This is a multi-part message in MIME format.'

    # Encapsulate the plain and HTML versions of the message body in an
    # 'alternative' part, so message agents can decide which they want to display.
    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)

    msgText = MIMEText(emailTextAlternate)
    msgAlternative.attach(msgText)

    # We reference the image in the IMG SRC attribute by the ID we give it below
    msgText = MIMEText('<b>Alert <i>motion detected</i> on camera %s</b> and here is a picture of what/whomever triggered this alert! <br><img src="cid:image1"><br>Nifty!' % (thisDeviceName), 'html')
    msgAlternative.attach(msgText)

    self.imgStream.seek(0)
    msgImage = MIMEImage(self.imgStream.read())

    # Define the image's ID as referenced above
    msgImage.add_header('Content-ID', '<image1>')
    msgRoot.attach(msgImage)

    # Send the email (this example assumes SMTP authentication is required)
    self.smtp.connect('smtp.gmail.com', 587)
    self.smtp.starttls() # TODO: Can this be moved out of the iteration? Is it expensive?
    self.smtp.login('yourEmailFromAddress', 'yourEmailFromPassword')
    self.smtp.sendmail(emailFromAddress, emailAddressTo, msgRoot.as_string())
    self.smtp.quit() # TODO: Determine if this can be elsewhere, or if we can leave this open.
    self.lastEmailTicks = time.time()

  def signal_handler(self, signal, frame):
    self.core.terminate_all_calls()
    self.quit = True

  def log_handler(self, level, msg):
    method = getattr(logging, level)
    method(msg)

  def call_state_changed(self, core, call, state, message):
    if state == linphone.CallState.IncomingReceived:
      if call.remote_address.as_string_uri_only() in self.whitelist:
        params = core.create_call_params(call)
        core.accept_call_with_params(call, params)
        self.current_call = call
        if debug:
            print 'sip_transports: dtls = %d, tcp = %d, udp = %d, tls = %d' % \
                  (self.core.sip_transports.dtls_port, self.core.sip_transports.tcp_port, self.core.sip_transports.udp_port, self.core.sip_transports.tls_port)
            print 'sip_transports_used: dtls = %d, tcp = %d, udp = %d, tls = %d' % \
                  (self.core.sip_transports_used.dtls_port, self.core.sip_transports_used.tcp_port, self.core.sip_transports_used.udp_port, self.core.sip_transports_used.tls_port)
      else:
        core.decline_call(call, linphone.Reason.Declined)
        for contact in self.whitelist:
          chat_room = core.get_chat_room_from_uri(contact)
          if not chat_room:
            continue
          msg = chat_room.create_message(call.remote_address_as_string + ' tried to call')
          chat_room.send_chat_message(msg)
    elif state == linphone.CallState.End:
      print "Call ended normally."
      self.current_call = None
    elif state == linphone.CallState.Error:
      print "Error ... ending call!"
      self.current_call = None
      core.end_call(call)

  def configure_sip_account(self, username, password):
    # Configure the SIP account
    proxy_cfg = self.core.create_proxy_config()
    proxy_cfg.identity_address = self.core.create_address('sip:{username}@sip.linphone.org:5060'.format(username=username))
    proxy_cfg.server_addr = 'sip:sip.linphone.org;transport=tls'
    proxy_cfg.register_enabled = True
    self.core.add_proxy_config(proxy_cfg)
    auth_info = self.core.create_auth_info(username, None, password, None, None, 'sip.linphone.org')
    self.core.add_auth_info(auth_info)
    self.username = username

  def run(self):
    while not self.quit:
      if detectMotion and self.core.current_call == None:
        # Incoming calls have been handled, so check the motion detector:
        motionDetected = False
        if PIRPIN <> 0:
          #motionDetected = GPIO.wait_for_edge(PIRPIN,GPIO.RISING)
          #if debug: print "\rvalue = %s" % (value, ) ,
          motionDetected = GPIO.event_detected(PIRPIN)
          if debug:
            print "motionDetected = %s" % (str(motionDetected))
            print "GPIO.input(PIRPIN) = " % (str(GPIO.input(PIRPIN)), )
          #motionDetected = GPIO.input(PIRPIN) # This will be 1 for detected, 0 otherwise.
        else:
          motionDetected = GPIO.input(MDPIN)
          if motionDetected == 0:
            motionDetected = True
          else:
            motionDetected = False
        if motionDetected:

          print '\n\a*Motion detected!*\n'
          if debug:
            print 'sip_transports: dtls = %d, tcp = %d, udp = %d, tls = %d' % \
                  (self.core.sip_transports.dtls_port, self.core.sip_transports.tcp_port, \
                   self.core.sip_transports.udp_port, self.core.sip_transports.tls_port)
            print 'sip_transports_used: dtls = %d, tcp = %d, udp = %d, tls = %d' % \
                  (self.core.sip_transports_used.dtls_port, self.core.sip_transports_used.tcp_port, \
                   self.core.sip_transports_used.udp_port, self.core.sip_transports_used.tls_port)
            print 'self.core.upnp_external_ipaddress = %s' % (self.core.upnp_external_ipaddress, )
            print 'self.core.nat_address = %s' % (self.core.nat_address, )
            tr = self.core.sip_transports_used
            print 'self.core.linphone_core_get_sip_transports_used = dtls = %d, tcp = %d, udp = %d, tls = %d' % \
                  (tr.dtls_port, tr.tcp_port, tr.udp_port, tr.tls_port)
          self.flash_led()
          flashed = True
          # GPIO.output(LEDPIN, True)
          # GPIO.output(LEDPIN, False)
          if time.time() - self.lastMessageTicks > WAITSECONDS:
            if debug: print "notifying contacts..."
            for contact in self.whitelist:
              if debug: print "notifying %s" % (contact, )
              chat_room = self.core.get_chat_room_from_uri(contact)
              if not chat_room:
                continue
              dt = datetime.datetime.now()
              c = self.core.primary_contact_parsed
              ip = self.core.upnp_external_ipaddress
              ea = c.as_string()
              un = c.username
              cl = c.clean()
              po = c.port
              if debug:
                print "dir(c) = %s" % (dir(c), )
                print "DEBUG: po = %s, cl = %s, c = %s, ip = %s, ea = %s, un = %s" % (po, cl, c, ip, ea, un)
              # nattype, external_ip, external_port = stun.get_ip_info('0.0.0.0', 54320, self.core.stun_server, 3478)
              # if debug:
              #   print 'nattype = %s, external_ip = %s, external_port = %s' % (nattype, external_ip, external_port)
              # sipaddress = 'sip:yourSipUserName@%s:%s' %(external_ip, external_port)
              # if debug:
              #   print 'sipaddress = %s' % (sipaddress, )
              msg = chat_room.create_message('Motion detected on %s at %s' % (ea, dt.isoformat(' ')))
              chat_room.send_chat_message(msg)
              self.lastMessageTicks = time.time()

          # Note that times for message and email are independent.
          if time.time() - self.lastEmailTicks >= WAITEMAILSECONDS:
            if not flashed:
              self.flash_led()
            self.lastEmailTicks = time.time()
            self.emailImage()
      #else:
      #  time.sleep(0.01) #
      self.core.iterate()


  def flash_led(self):
    for j in range(0, 10):
      GPIO.output(LEDPIN, True)
      time.sleep(0.05)
      GPIO.output(LEDPIN, False)
      time.sleep(0.05)


def main(argc, argv):
  try:
    # These are your SIP username and password
    cam = SecurityCamera(username='yourSipUserName', password='yourSipPassword', \
                         whitelist=['sip:yourAccount@sip.linphone.org',
                                    'sip:yourAdditionalSIPAddressesHere@sip.linphone.org'], \
                         camera='V4L2: /dev/video0', \
                         snd_capture='ALSA: Set [C-Media USB Headphone Set]', \
                         snd_playback='ALSA: USB Audio [USB Audio]')
    cam.run()
  except:
    GPIO.cleanup()
  finally:
    GPIO.cleanup()

if __name__ == '__main__':
	main(len(sys.argv), sys.argv)