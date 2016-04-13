#!/bin/bash
wget https://linphone.org/releases/linphone-python-raspberry/linphone4raspberry-3.9.0-cp27-none-any.whl
sudo apt-get install python-setuptools
sudo easy_install pip
sudo pip install wheel
sudo pip install --upgrade pip
sudo pip install linphone4raspberry-3.9.0-cp27-none-any.whl

