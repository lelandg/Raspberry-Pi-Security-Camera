# Raspberry-Pi-Security-Camera
![](jampi.png)

**Copyright**

This product is called JamPi. The name JamPi is
Copyright (C) 2016 Leland Green... All rights reserved. 
(On the name and graphic, only. You are free to use those in a non-commercial setting, only. For commercial purposes, you must remove them and state that your project was derived from the JamPi. Since the graphic is currently not used, just don't use the name JamPi and we'll be OK. Simple... especially since that's only used in the initialization log message. You are allowed to leave that in, until you change the code, when you must rename it. Fair? Thank you for your cooperation.)

**Notice**

I plan to have major updates for this project very soon. (Probably this week--the week of 2016.03.20.)
_See "Installation" below if you want to jump right in!

**Features**
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
  * Works with a Raspberry Pi camera module (AKA "RaspiCam") *OR* a USB webcam! Preferably one that has hardware H2.64 compression.
* Optionally use as a "video doorbell". Put the button and camera (and optional motion sensor) outside the door and record a picture of everyone who rings your doorbell, plus, it rings through to your SIP videophone (Linphone is a good one), so you can see video of the person! Right now you can talk to them, but they can't talk to you (sound is only working one way... maybe just my system?)
  

**Requirements**

This script requires custom hardware, which is included as a Fritzing/PNG files. Uses ePIR to detect motion. Emails a list of people when detected. Also is a Linphone server, so you can simultaneously connect to the camera for a live picture! (Right now is one-way on the Pi.)

You will need to run the script with:
./.startscript
*or*
sudo python security_camera.py

If you want to find programs in your home directory without typing the preceding "./", whether or not you're running as sudo, you can add to your .bashrc with:
* nano .bashrc
*  Scroll to the end of the file and add the line:
*   export PATH=$PATH:/home/pi
* After this change you can simply type ".startscript.sh". (And *actually* just type ".sta" and press the <<tab>>. It will probably type the rest of the command for you. Same thing with the other shell scripts! Save your typing for Github! :)

Because it uses an I/O device you need elevated permissions to run it. 

This project also represents my first (serious) attempt at using GitHub as it was intended. You may see me open issues and then close them after a commit/merge. I hope that these comments prove useful to you.

**Installation**
* If you do not have git installed, run:
    sudo apt-get install git
* Then always run this to start with (or else download & unzip all files to your home directory, or whichever one you want to run from). Only the program files will be installed to this directory. In keeping with Linux standards the log will alwas be /var/log/security_camera.log
*  This file is owned by root so you may need to chown on it if you can't access it. I just copy to Windows and use my favorite GUI editor.
* run:
   sudo chmod +x ./__make_executable
   ./__make_executable
* This last command simply runs chmod on the three utility scripts for you. :) It is technically not required--you can run with only "sudo python security_camera.py" if you want to! But that's a mouthful, so I've made it simpler. The three scripts have very different names to aid you in starting, stopping and showing the process (if any) for the currently running script. You do *not* need to prefix these with "sudo". The scripts do that for you! :) These scripts are:
* .startscript.sh -- Starts the security_camer.py Python script, waits 3 seconds, then starts a "tail -f /var/log/security_camera.log" (The script is ran in the background and will print very little, if anything directly to the console. Everything's in the log, now! :)
* security_off -- Kills the currently running script. You can run this multiple times, it won't kill anything else (unless the python script has exactly the same name, but then it would be the same script. Ha!)
* _showproc -- Shows any currently running security camera Python scripts. Note that if you see only one line, you should also see a "grep" in the command portion of the output, which means that is the _showproc script, itself, *not* the Python script. So if you only see one line in the output, you have all instances of the security camera script stopped.
* **WARNING** Do *not* run more than one instance of the script! The shell scripts *attempt* to prevent you from doing this by calling 'security_off' before it actually "turns it back on".
