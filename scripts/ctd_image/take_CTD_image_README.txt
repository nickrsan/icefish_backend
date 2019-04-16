CTD image uploader
Implemented 4/16/19 by Cziko and Santos

This code uses NodeJS and a headless chrome browser to load the MOO data web kiosk (headless), and then runs a JS script to
modify some CSS, take an full-screen image capture of the CTD data only and sends it to a folder on an external storage device.

Requirements: One needs NodeJS and Chrome Puppeteer installed in the local code directory (325mb). One will have to run "npn install" to 
build the local dependencies, etc. 

Once node/puppeteer is installed, one needs only call:

C:\Code\icefish_backend\scripts\ctd_image>node take_CTD_image.js

Breifly, the code loads the kiosk (where the video fails a priori, so doesn't load), wait 5 seconds for the page elements
 to load, hide the spectrogram data, resize the CTD panel, and get rid of the toolbar in the data viewer.
 
 The code waits 2 minutes for the CTD data to load, then takes a screen capture and saves it to the NAS.
 
 The headless browser closes completely, then wakes back up in 28-odd minutes to start the process over again for 30-second interval images.
 
 

 The uploader code (not part of this directory, also used for waypoinbt images) checks for recent images and uploads them to Moo-CONUS at full resolution 
 (hosted in the US) at 30-min intervals. 
 
 We sometimes get a 4kb null image, when somthing went wrong in the pipeline (delay in loading page elements or data). The uploader skips any images 
 less than 50kb. 
 
 As a system service, the only call needed is that listed above; the JS loops on its own. This could be modified so that a single instance 
 is called at 30-minute intervals with a Chron task, for example. 
 
 **Modifying the MOO data kiosk webpage may have undesireable effects on this functionality**
 
 
 