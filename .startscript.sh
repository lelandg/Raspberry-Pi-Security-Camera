#!/bin/bash
#curl wttr.in/SGF
#sleep 5
# You probably want to remove the line with 'sudo rm...', unless you really do 
# want to delete the log file every time.
# The double 'clear' commands are due to a quirk in Putty--it always keeps
# one screenfull in the scrollback buffer unless you do this.
echo 'Stopping any currently running security_camera.py Python script...'
./security_off
sleep 3
# Comment-out the next two lines if you always want to append to the log.
# You should monitor the disk space and move the log file across the network/to a USB.
echo 'Cleaning log...'
sudo rm /var/log/security_camera.log; clear; clear
echo 'Starting security_camera.py, tailing the log.'
sudo python security_camera.py >>security_camera_log 2>&1 &
sleep 3
tail -f /var/log/security_camera.log
cp /var/log/security_camera.log ./
#~/ngrok tcp 22

