# Raspberry-Pi-Security-Camera
This product is called JamPi. The name JamPi is
Copyright (C) 2016 Leland Green... All rights reserved. 
(On the name and graphic, only. You are free to use those in a non-commercial setting, only. For commercial purposes, you must remove them and state that your project was derived from the JamPi.)

*Features*
* Uses the RaspiCamera as part of an integrated security system.
* Motion detector (PIR/ePIR sensor) triggered events. When motion is detected: 
  * Send a chat message to a list of SIP addresses. This is only done every X seconds. (Configurable; Default=1 minute)
  * Email and image of the intruder to a single person or to several people. Also done only ever X2 seconds. (Separate configuration for time. Default=1 minute.)
  * Start recording video to the SD card (default is for 15 seconds).
  * Flash an LED (optional)
* Log on to the camera, using any Linphone client for live, streaming video from the camera. 
  * No limit to connection time! 
  * While connected to the live camera, the notification features are turned off. (This is to save on resources more than a lack of the Raspberry Pi, which is fully capable of doing everything simultaneously. 
  * Only people configured (in the Python script) are allowed to connect
  

*Requirements*

This script requires custom hardware, which is included as a Fritzing/PNG files. Uses ePIR to detect motion. Emails a list of people when detected. Also is a Linphone server, so you can simultaneously connect to the camera for a live picture! (Right now is one-way on the Pi.)

You will need to run the script with:

sudo python security_camera.py

Because it uses an I/O device you need elevated permissions to run it. 

This project also represents my first (serious) attempt at using GitHub as it was intended. You may see me open issues and then close them after a commit/merge. I hope that these comments prove useful to you.
