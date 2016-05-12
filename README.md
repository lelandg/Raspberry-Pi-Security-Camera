# Raspberry-Pi-Security-Camera
![JamPi Logo](jampi.png)

Copyright (C) 2016 Leland Green... All rights reserved. 
Released under MIT license so you can use for any purpose.
See License.md for the licensing text.

**Definitions**

* **Significant Changes** : Anything that makes the project commercial; non--open-source; or changes the core functionality of the project (i.e., it is no longer a security camera or video doorbell
* **Commercial Software** : If you are *now making money* from the project or there is *any chance* that you will *ever make money* from the project, it is considered commercial software.
* **Educational Setting** : Within the context of teaching. Not necessarily teaching about the Raspberry Pi, but teaching about any subject where this project will be useful. While every institution of formal education would certainly qualify, such an instution is *not* required. E.g., a tutor could certainly claim that they were also using within an *educational setting*.

If you make **significant changes** I require only two things: **the graphic (JamPi Logo)** and **JamPi name** must be removed. You are free to use those (name and graphic) in a **non-commercial** , **or educational** setting, *only*. For a project with significant changes, you must (1) remove them from any place they are shown to the end-user and (2) state that your project was derived from the **JamPi** project in the documentation and/or the comments of the source code. In that case you must also include a link to the original project page. (This will suffice: https://github.com/lelandg/Raspberry-Pi-Security-Camera)

Since the graphic is currently not used, you can just delete it, and then do not show the name **JamPi** to the *end-user* and we will be OK with each other. :-) **Simply search/replace in the file security_camera.py for "JamPi" and replace it with your product name** ; simple... especially since that's only used in the initialization log message. You are allowed to leave that in, until you make **significant changes** , when you must rename it. Fair? Thank you for your cooperation.)

See *Requirements* and then *Installation* below if you want to jump right in!

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
`.startscript.sh`
*or*
`sudo python security_camera.py`.
However, you should *always* use `.startscript.sh`. If you want something different, edit the script once and it will be changed from then on! :)

**TIP** 
 If you want to find programs in your home directory without typing the preceding `./`, whether or not you're running as sudo, you can add to your `.bashrc` with:
  * `nano ~/.bashrc`
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
sudo chmod +x __make_executable
__make_executable
```
* This last command simply runs chmod on the three utility scripts for you. :) It is technically not required--you can run with only "sudo python security_camera.py" if you want to! But that's a mouthful, so I've made it simpler by including three scripts. (See next section.)
* Install Python Linphone
  * Please see <a href="https://wiki.linphone.org/wiki/index.php/Raspberrypi:start" target="new">https://wiki.linphone.org/wiki/index.php/Raspberrypi:start</a> for complete instructions. 

**Optionally**

* Either install python-espeak or set "talkToEm = False" in the script. (Change the existing line, don't add one!)
```
sudo apt-get install python-espeak
```

* If you hit errors, on a Raspberry Pi, especially, please open an issue under this project. I appreciate all reports, even if it's something you do not understand! Please help me to understand what you do not understand, if at all possible. If not, just send me the log file, preferably via your DropBox (or similar service). If you need an invitation to drop box, please let me know and I will send you one.

**Operation** 

Three shell scripts are included to make operation of the Python script a snap. They have very different names to aid you in starting, stopping and showing the process (if any) for the currently running script. 

You do *not* need to prefix these with "sudo". The scripts do that for you! :) These scripts are:
* `.startscript.sh` -- Starts the security_camera.py after some basic "housekeeping".
*This is the recommended way to run your `security_camera.py` script!* This script will: 
  * Stop one previosly running script. (But only one!)
  * Remove the log file. So if you have errors you want to keep, rename `/var/log/security_camera.log` to something unique *before* you restart the script, or it will be overwritten. Or better yet, rename them into your DropBox folder and email me a link! :)
  * Start `security_camera.py` running in the background.
  * `tail -f /var/log/security_camera.log`, so you see all messages on the console. (You could disable the `tail` command if speed is an issue.) Yet they are still saved in the log file, until you restart the script.
* `security_off` -- Kills the currently running script. You can run this multiple times, it won't kill anything else. (Unless the python script has exactly the same name, but then it would be the same script. Ha!)
* `_showproc` -- Shows any currently running security camera Python scripts. Note that if you see only one line, you should also see a "grep" in the command portion of the output, which means that is the _showproc script, itself, *not* the Python script. So if you only see one line in the output, that means you have all instances of the security camera script stopped.

**NOTES**

If you see an error like this: `WARNING: ./share/sounds/linphone/rings/oldphone.wav does not exist`, you can run:
```
sudo find / -iname '*.wav' > /home/pi/soundfiles.txt && less ~/soundfiles.txt
```
to find all sound files on your machine. Once the list is displayed (and stored in `~/soundfiles.txt`, if you see a line with `/usr/local/lib/python2.7/dist-packages/linphone/share/sounds/linphone/ringback.wav`, use the parent directory as input to this command `sudo ln -s /usr/local/lib/python2.7/dist-packages/linphone/share/sounds/linphone `; such that, for this example:
```
sudo ln -s /usr/local/lib/python2.7/dist-packages/linphone/share/sounds/linphone /usr/share/sounds/linphone
```

**IMPORTANT NOTE** In your home directory you will find the file `.linphonerc` ( `~/.linphonerc` should always access it). This file has a line for `contact=`. I recommend opening this file and changing it to contain your current SIP account so that it does not conflict with that given in the script. Depending on how you've used Linphone on RPi, you may have other options that conflict! I cannot hope to document all of those, so you need to look up the documentation for these.

**WARNING** Do *not* run more than one instance of the script! The shell scripts *attempt* to prevent you from doing this by calling `security_off` before it actually "turns it back on". 

**WARNING** Running multiple instances of the script is certainly unsupported and behavior is undefined, at best!
