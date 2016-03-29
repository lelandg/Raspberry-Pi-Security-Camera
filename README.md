# Raspberry-Pi-Security-Camera
![JamPi Logo](jampi.png)

Copyright (C) 2016 Leland Green... All rights reserved. 
Released under MIT license so you can use for any purpose.
See License.md for the licensing text.

**Definitions**

* **Significant changes** : Anything that makes the project commercial; non--open-source; or changes the core functionality of the project (i.e., it is no longer a security camera or video doorbell

If you makek **significant changes** I require only two changes: **the graphic** and **JamPi** name must be removed. You are free to use those (name and graphic) in a **non-commercial** , **or educational** setting, *only*. For a project with significant changes, you must remove them and state that your project was derived from the JamPi in the comments of the source code. Since the graphic is currently not used simply delete it, and just do not use the name **JamPi** and we'll be OK. **Simply search/replace in the file security_camera.py for "JamPi" and replace it with your product name** ; simple... especially since that's only used in the initialization log message. You are allowed to leave that in, until you make **significant changes** , when you must rename it. Fair? Thank you for your cooperation.)

See *Installation* below if you want to jump right in!

**Features**

* This is an active project! New features are planned (no matter *when* you read this! :D ). So I hope you'll check back once-in-a-while, or follow me on Google+ or Facebook. (Everything I do is 100% visible to the public.)
* Works with a Raspberry Pi camera module (AKA "RaspiCam") *OR* a USB webcam! Preferably one that has hardware H2.64 compression.
* Motion detector (PIR/ePIR sensor) triggered events. When motion is detected: 
  * Send a chat message to a list of SIP addresses. This is only done every X seconds. (Configurable; Default=1 minute)
  * Email and image of the intruder to a single person or to several people. Also done only ever X2 seconds. (Separate configuration for time. Default=1 minute.)
  * Start recording video to the SD card (default is for 15 seconds).
  * Flash an LED (optional)
* Log on to the camera, using any Linphone client for live, streaming video from the camera. 
  * No limit to connection time! 
  * While connected to the live camera, the notification features are turned off. (This is to save on resources more than a lack of the Raspberry Pi, which is fully capable of doing everything simultaneously. 
  * Only people configured (in the Python script) are allowed to connect
* Optionally use as a "video doorbell". Put the button and camera (and optional motion sensor) outside the door and record a picture of everyone who rings your doorbell, plus, it rings through to your SIP videophone (Linphone is a good one), so you can see video of the person! Right now you can talk to them, but they can't talk to you. (Sound is only working one way... maybe just my system?) This is true of both the doorbell and when you make a call to this device.

**Requirements**

* This script requires custom hardware, which is included as a Fritzing/PNG files. Uses a PIR/ePIR sensor to detect motion. 
* It is recommended that you have two SIP accounts, one for the security camera device and one for you. This greatly simplifies connecting to the camera via Linphone. Simply use the "address" that is the SIP account running on the device.

Sending video is resource-intensive so you should boot to Console mode (probably with auto-login if this is to be a remote deployment). To be clear, I could never get video to work when I booted my Pi to X desktop. So that is unsupported at this time. (This may be a misunderstanding of something on my part so please speak-up if you have info that may help me.)

First, change to the directory with:
`cd Raspberry-Pi-Security-Camera`

Because it uses an I/O device you need elevated permissions to run it. So you will need to run the script with:
`./.startscript.sh`
*or*
`sudo python security_camera.py`

  TIP: If you want to find programs in your home directory without typing the preceding "./", whether or not you're running as sudo, you can add to your .bashrc with:
  * `nano .bashrc`
  *  Scroll to the end of the file and add the line:
     `export PATH=$PATH:/home/pi`
  * After this change you can simply type `.startscript.sh`. (And *actually* just type ".sta" and press the [tab]. It will probably type the rest of the command for you. Same thing with the other shell scripts! Save your typing for Github! :)

This project also represents my first (serious) attempt at using GitHub as it was intended. You may see me open issues and then close them after a commit/merge. I hope that these comments prove useful to you.

**Installation**
* If you do not have git installed, run:
```
sudo apt-get install git
```
Then everyone should run:
```
git clone https://github.com/lelandg/Raspberry-Pi-Security-Camera
cd Raspberry-Pi-Security-Camera
```
* After that, when updating, always run that same command to start with (or else download & unzip all files to your home directory, or whichever one you want to run from). Only the program files will be installed to this directory. In keeping with Linux standards the log will alwas be /var/log/security_camera.log
*  This file is owned by root so you may need to chown on it if you can't access it. I just copy to Windows and use my favorite GUI editor.
* run:
```
sudo chmod +x ./__make_executable
./__make_executable
```
* This last command simply runs chmod on the three utility scripts for you. :) It is technically not required--you can run with only "sudo python security_camera.py" if you want to! But that's a mouthful, so I've made it simpler by including three scripts. (See next section.)
* Install python-espeak
```
sudo apt-get install python-espeak
```
* Install Python Linphone
  * Please see https://wiki.linphone.org/wiki/index.php/Raspberrypi:start for complete instructions. 

* If you hit errors, on a Raspberry Pi, especially, please open an issue under this project. I appreciate all reports, even if it's something you do not understand!

**Operation** 

Three shell scripts are included to make operation of the Python script a snap. They have very different names to aid you in starting, stopping and showing the process (if any) for the currently running script. 

You do *not* need to prefix these with "sudo". The scripts do that for you! :) These scripts are:
* `.startscript.sh` -- Starts the security_camera.py Python script, waits 3 seconds, then starts a `tail -f /var/log/security_camera.log` (The script is run in the background and will print very little, if anything directly to the console. Everything's in the log, now! :)
* `security_off` -- Kills the currently running script. You can run this multiple times, it won't kill anything else. (Unless the python script has exactly the same name, but then it would be the same script. Ha!)
* `_showproc` -- Shows any currently running security camera Python scripts. Note that if you see only one line, you should also see a "grep" in the command portion of the output, which means that is the _showproc script, itself, *not* the Python script. So if you only see one line in the output, that means you have all instances of the security camera script stopped.

**WARNING** Do *not* run more than one instance of the script! The shell scripts *attempt* to prevent you from doing this by calling `security_off` before it actually "turns it back on". 

**WARNING** Running multiple instances of the script is certainly unsupported and behavior is undefined, at best!
