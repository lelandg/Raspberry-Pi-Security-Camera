# Raspberry-Pi-Security-Camera
This product is called JamPi. The name JamPi is
Copyright (C) 2016 Leland Green... All rights reserved. 
(On the name and graphic, only. You are free to use those in a non-commercial setting, only. For commercial purposes, you must remove them and state that your project was derived from the JamPi.)

This script requires custom hardware, which is included as a Fritzing/PNG files. Uses ePIR to detect motion. Emails a list of people when detected. Also is a Linphone server, so you can simultaneously connect to the camera for a live picture! (Right now is one-way on the Pi.)

You will need to run the script with:

sudo python security_camera.py

Because it uses an I/O device you need elevated permissions to run it. 

This project also represents my first (serious) attempt at using GitHub as it was intended. You may see me open issues and then close them after a commit/merge. I hope that these comments prove useful to you.
