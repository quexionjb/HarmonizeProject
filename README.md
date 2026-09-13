Harmonize Project *for Philips Hue*
============================
![Pull Requests Welcome](https://img.shields.io/badge/Pull_Requests-welcome-brightgreen) ![Open Source Love](https://badges.frapsoft.com/os/v1/open-source.png?v=103) ![Python 3.12](https://img.shields.io/badge/Python-3.12-brightgreen)

Harmonize Project connects Philips Hue lights and lightstrips to your TV screen content, creating an amazing ambient lighting effect! This application utilizes a low-latency video and color analysis algorithm developed with Python and OpenCV. 

Check out our Reddit thread [here](https://www.reddit.com/r/Hue/comments/i1ngqt/release_harmonize_project_sync_hue_lights_with/) and watch the demo below! Electromaker explains how our application works at a high level in his podcast [here!](https://youtu.be/tYnvYYWedVc?t=1790)

[![Harmonize Project Demo Video](http://img.youtube.com/vi/OkyUntgiYzQ/0.jpg)](http://www.youtube.com/watch?v=OkyUntgiYzQ "Harmonize Project Demo Video")

Harmonize Project (formerly known as Harmonize Hue) has no affiliation with Signify or Philips Hue. Hue and Philips Hue are trademarks of Signify.

# New Features
* v2.4.2: Auto-restart videocapture after specificed number of seconds of missed frames
* v2.4.1: Added videocapture reset command added (useful when switching A/V inputs)
* v2.4:   Added support for Python 3.12 and Ubuntu 24.04 installation
* v2.3:   Added adjustment to maximum brightness
* v2.2:   Added webcam stream input via file/URL
* v2.1:   Support for multiple Hue bridges
* v2.0:   Support for gradient lightstrips is now available!

**Thank you** to all those who have contributed to this project. Please keep your pull requests coming!

# Features
* Light color and intensity follows relative location to the display perimeter
* Video -> Light streaming latency of 80ms
* Approximately 60 color updates per second

# Requirements 

**Lights:**

* Minimum of one compatible Hue light required (obviously). Limited to a maximum of 20 lights for streaming. A gradient lightstrip counts as 7 lights.

**Minimum Hardware:**

* Hue bridge using firmware version 194808600 or greater
* Raspberry Pi 5/4B/3B/Zero or Linux box running at 1.5GHz+ with at least 4 CPU cores (tested on Ubuntu 24.04 64-bit). The RPi 5 and 4B will exhibit optimal performance at 1080p resolution. Good performance can be achieved on the RPi 3B and Zero with minimal tweaking to lower frame rates (~10 FPS for the Zero) and video resolutions. 
* HDMI video capture card or Webcam input device (ex. https://github.com/silvanmelchior/RPi_Cam_Web_Interface)

**Example Hardware configuration (tested successfully unless otherwise noted below):**
* RPi RAM: minimum of 256MB free (512MB free RAM recommended)
* RPi CPU: 1.5GHz+, 4 Cores strongly recommended due to running three concurrent threads
* Rpi power input: use recommended power supply and wattage requirements
* HDMI Splitter capable of outputting 4k and 1080/720p simultaneously, such as the [AVSTAR 4K HDMI 2.0 Splitter 1X2](https://www.amazon.com/dp/B08D9BCX1R?psc=1&ref=ppx_yo2ov_dt_b_product_details). A/V receivers with 2 or more HDMI outputs may also be considered.
* USB3.0 HDMI Capture Card (Capable of capturing 720/1080p; delay should be 50ms or under.) Tested successfully on the [WIIStar](https://www.amazon.com/gp/product/B07Z7RNDBZ/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&psc=1) Also tested successfully on the Elgato Cam Link 4k. The following are untested: [Panoraxy](https://www.amazon.com/Panoraxy-Capture-1080PFHD-Broadcast-Camcorder/dp/B088PYDJ22/ref=sr_1_21?dchild=1&keywords=hdmi+to+usb+3.0+capture&qid=1596386201&refinements=p_36%3A1253504011%2Cp_85%3A2470955011&rnid=2470954011&rps=1&s=electronics&sr=1-21) | [Aliexpress (This shape/style tends to perform well.)](https://www.aliexpress.com/item/4000834496145.html?spm=a2g0o.productlist.0.0.27a14df5Wc5Qoc&algo_pvid=e745d484-c811-4d2e-aebd-1403e862f148&algo_expid=e745d484-c811-4d2e-aebd-1403e862f148-15&btsid=0ab50f4415963867142714634e7e8e&ws_ab_test=searchweb0_0,searchweb201602_,searchweb201603_)

# Setup

**Software Setup:**

**Ubuntu Desktop 24.04 LTS 64-bit with Python v3.12 (most recent version tested)**

* Install the Raspberry Pi Imager software (see https://www.raspberrypi.org/software/) on a separate computer with an available SD card slot/adapter. Insert an SD card with at least 32GB capacity with decent read/write speeds.

* Launch the imager and select the Raspberry Pi device type, Ubuntu Desktop 64-bit OS, and the storage location for the SD card. Click Next.

* After the OS has been installed, insert the SD card into the RPi and boot.

* Install all dependencies via the following commands. **Be sure to watch for errors!** 

* Install pip (will also install gcc and g++ C-compilers as dependencies):
```
sudo apt-get install python3-pip
```
* Install Snap:
```
sudo apt install snapd
```
* Install Avahi (multicast DNS daemon):
```
sudo snap install avahi
```
* Install Screen (SSH multiple window manager):
```
sudo apt install screen
```
* Install pipx [Github reference](https://github.com/pypa/pipx):
```
sudo apt install pipx
pipx ensurepath
```
* Install virtualenv:
```
pipx install virtualenv
```
* Create virtual environment and activate:
```
virtualenv --python=python3.12 ~/harmonize_env
source ~/harmonize_env/bin/activate
```
* Install NumPy, zerconf, requests, and termcolor Python dependencies via pip:
```
pip install numpy=1.26.4 zeroconf requests termcolor
```
* Compile and install OpenCV 4.10.0 from source - [Follow this guide...](https://docs.opencv.org/4.10.0/d7/d9f/tutorial_linux_install.html) Compiling may take a couple of hours depending on the capabilities of your system. Note that if you upgrade Ubuntu to a new release you may need to completely uninstall, recompile, and reinstall OpenCV. Note: As of June 16, 2024, numpy 2.0.0 is available, but this project will plan to use 1.26.4 until a minor upgrade release of numpy 2.1 is available.
```
sudo apt install cmake
sudo apt install python3-dev python3-numpy libpython3-all-dev
sudo apt install libavcodec-dev libavformat-dev libswscale-dev
sudo apt install libgstreamer-plugins-base1.0-dev libgstreamer1.0-dev # to be used for GStreamer support
sudo apt install libgtk-3-dev
sudo apt install wget git
wget -O opencv.zip https://github.com/opencv/opencv/archive/4.10.0.zip
unzip opencv.zip
mv opencv-4.10.0 opencv
mkdir -p build && cd build
cmake -D CMAKE_INSTALL_PREFIX=/usr/local -D BUILD_opencv_java=OFF -D BUILD_opencv_python2=OFF -D BUILD_opencv_python3=ON -D PYTHON_DEFAULT_EXECUTABLE=$(which python3) -D INSTALL_C_EXAMPLES=OFF -D INSTALL_PYTHON_EXAMPLES=OFF -D BUILD_EXAMPLES=OFF -D WITH_CUDA=OFF -D WITH_GSTREAMER=ON -D BUILD_TESTS=OFF -D BUILD_PERF_TESTS=OFF ../opencv
make -j4
sudo make install
cd ..
sudo ln -s /usr/local/lib/python3.12/site-packages/cv2 /home/bdworak/harmonize_env/lib/python3.12/site-packages/cv2
git clone https://github.com/MCPCapital/HarmonizeProject.git
```

**Legacy Software Setup (currently unsupported and not maintained):**

Download the latest scripts and install all dependencies via the following commands. **Be sure to watch for errors!** You will need about 1GB of free space. The script can run for up to an hour.

```
git clone https://github.com/MCPCapital/HarmonizeProject.git
cd HarmonizeProject
sudo ./setup.sh
```

**Hardware Setup Example A:**

* Connect Video Device (PS4, FireStick, etc.) to the splitter input. 
* Connect an HDMI cable from the 4k output to the TV; and from Output 2 (downscaled) to the video capture card connected to your device.
* Ensure your splitter's switches are set to downscale Output 2 to 1080 or 720p!
* ![Connections diagram](https://github.com/bradleydworak/HarmonizeProject/blob/master/connections.png?raw=true)

**Hardware Setup Example B (for A/V receivers with 2 or more HDMI outputs):**

* Connect your video device (PS4, FireStick, etc.) to an available HDMI input on your A/V receiver. 
* Connect an HDMI cable from the HDMI output 1 from A/V receiver to the TV.
* Connect an HDMI cable from HDMI output 2 from the receiver to the HDMI input on the splitter.
* Connect an HDMI cable from the HDMI output 1 of the splitter to the HDMI input on the video capture device.
* Connect the video capture device USB 3.0 output to a USB 3.0 port (not a USB 2.0 port) on the Raspberry Pi. 
* Ensure that the DIP switches on the splitter are set to downscale HDMI Output 1 to 1080 or 720p.

**Entertainment Area Configuration:**

* Hue App -> Settings -> Entertainment Areas
* Harmonize will use the **height** and the **horizontal position** of lights in relation to the TV. **The depth/vertical position are currently ignored.**
* In the example below, the light on the left is to the left of the TV at the bottom of it. The light on the right is on the right side of the TV at the top of it.

**First-Time Run Instructions:**

* Register with the Hue bridge before unattended startup so client.json contains
  a username and client key, then restrict it with chmod 600.
* Copy harmonize.example.toml to harmonize.toml and set the exact default
  Entertainment area. Headless startup does not prompt for bridge or area
  selection.

# Usage

Validate configuration and credentials offline:

    /home/pi/harmonize_env/bin/python tools/validate_config.py \
      --config harmonize.toml \
      --mode unattended \
      --check-credentials

Start the headless foreground runtime:

    /home/pi/harmonize_env/bin/python harmonize.py \
      --config harmonize.toml

The process runs without terminal input. SIGTERM and SIGINT perform bounded
capture, DTLS, and Hue cleanup. The example configuration writes an atomic
non-secret health snapshot to run/harmonize-health.json. A systemd service unit
is planned for a later milestone.

**Command line arguments:**

* --config selects the TOML configuration.
* --check-area performs read-only exact-area validation and exits.
* --run-seconds bounds a diagnostic or soak run and then uses normal cleanup.
* --health-file overrides the configured health snapshot path.
* -v, -g, -b, -i, -s, -w, -f, -l, and -a remain accepted for compatibility.

See docs/milestone-4-headless-reliability.md for recovery policy, health fields,
failure diagnostics, validation evidence, and rollback.

# Troubleshooting

* "Import Error" - Ensure you have all the dependencies installed. Run through the manual dependency install instructions above.
* No video input // lights are all dim gray - Run `python3 ./videotest.py` to see if your device (via OpenCV) can properly read the video input.
* w, h, or rgbframe not defined - Increase the waiting time from the default 0.75 seconds by passing the `-w` argument *This is a known bug (race condition).
* Sanity check: The output of the command `ls -ltrh /dev/video*` should provide a list of results that includes /dev/video0 when the OS properly detects the video capture card.
* Many questions are answered on our Reddit release thread [here.](https://www.reddit.com/r/Hue/comments/i1ngqt/release_harmonize_project_sync_hue_lights_with/) New issues should be raised on Github.

# Contributions & License

Pull requests are encouraged and accepted! Whether you have some code changes or enhancements to the readme, feel free to open a pull request. Harmonize Project is licensed under [The Creative Commons Attribution-NonCommercial 4.0 International Public License.](https://creativecommons.org/licenses/by-nc/4.0/legalcode)

Development credits to Matthew C. Pilsbury (MCP Capital LLC), Ares N. Vlahos, and Brad Dworak.

[![licensebuttons by-nc](https://licensebuttons.net/l/by-nc/3.0/88x31.png)](https://creativecommons.org/licenses/by-nc/4.0/legalcode)
