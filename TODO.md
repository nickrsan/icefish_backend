# To Do List
Quick Note: this is here, rather than in issues because the list is quite
long right now and many of these are small and fast to check off - when it
decreases, or some of these look like they'll be here for longer and require
more individual planning and attention, they'll be moved to Issues.

## Interface
 * Panels need an X in the top right so people know they can close them - clicking same button isn't always intuitive

## Kiosk
 * Come up with plan for how we know which browser is the kiosk
 * Add URL to page
 * Pages should have correct permalinks (including #ctd or #info, etc)
 * Put a reload button on the page so that when it stalls out, they can refresh - kiosk won't have that in browser

## Stability
 * Set Caddy to run as local service - use its own account - is this already happening though?
 * Automate deployments to specific branches
 * Move secrets out of local_settings to local_secrets - those items would require logging in to update - others come from either copying local_settings_template or from a kiosk_specific template and a cloud specific template
 * Double check disk array security, maintenance, and alert settings
 * Upgrade Django to 2.0 - test in new Venv first
 * Set up WOL from one system to the rest - maybe a scheduled task to wake the server

### Wowza
 * Close down remaining unnecessary ports to wowza from camera
 * Confirm running as local wowza account
[ ] Test bitrate vs. stability of stream in browser on public kiosk
[ ] Configure to use password + PTZ to access camera
[ ] Issue of HTTP timing and sychronization with hydrophone (https://www.wowza.com/forums/content.php?88-How-to-configure-Apple-HLS-packetization-%28cupertinostreaming%29#mgrlive)
[ ] Wowza error recovery: we can track if the person pressed stop (maybe) by if the events trigger for play and stop - not sure if they trigger when wowza stops it because it's broken. Maybe we can autorecover by detecting if the player is stopped for a long time and then sending a stop command then waiting, then a play command. Maybe have a setting for this behavior that's automatically true for McMurdo IPs and otherwise is false? Then, we can detect if it's a failing stream that hasn't yet stopped (still shows state of playing) by using the onStats events that will tell us, hopefully, that we're not getting any data.
 * Set up VOD again for kiosk

### Hydrophone data ingestion
[ ] Broken - need to fix the part that deletes the source file - trying to delete tempfile only, not original
[ ] Autostart ingestion service? Or just run as scheduled task? What about recovery when it fails?
[ ] Run ingestion as low priority
[ ] Report of number of uningested files if it's over 24*6 or something (since that would mean it has files that didn't process)
[ ] Crash recovery for OceanSonics Array Data Manager
[ ] Autostart macro for Array Data Manager - does running it as high priority avoid crashes? Seems to crash when CPU load is heavy

### Video
[ ] Move transcoded videos to VideoVariant class
[ ] Do we want to transcode automated surveys?
[ ] Ingestion service for video, even if we don't transcode, so Paul can have listing of what we're getting
[ ] How are we going to get the image off continent every two minutes? Separate from Wowza? Do we have a script that connects, reads, dumps the first frame it finds, and uploads?
[ ] Alternatively, script constantly dumps a frame every __ seconds - server stores these frames anyway, and we have a web service that loads last frame. Cloud server hits that service

### Monitoring
[ ] Logging Server?
[ ] Django sentry or similar
[ ] Some sort of heartbeat check for crucial systems - logging in the web page so I know if the kiosk is open, etc, as well as all services are up.

#### Things to Monitor
 * High CPU, RAM, and low disk on MOO-SERVER, MOO-Proxy, RaspPI kiosk, and MOO-Cloud
 * Crashes of ADM
 * All warnings from Django, application errors, etc
 * Kiosk load failures and warnings - should it email, or just make a post to a URL that loading failed with a specific message?
 * CTD API is producing new values
 * New images coming out of MOO Server to MOO-Cloud
 * Hydrophone audio is being logged
 * CTD data is being logged
 * New surveys are being saved
 * Pages load from the proxy with 200 OK status
 * Daily (at least at first) "all is well" email - that way if that stops coming, I know email is broken
 * Core Temp of MOO Server

## Enhancements
[ ] Dump daily Postgres backups - rotate backups so that we keep one from 6 months ago, 3 months, 1 month, 2 weeks, 1 week, and last 7 days, or something similar that covers all use cases without destroying disk
[ ] Backups - do we want to dump some critical data to externals in addition to array?
[ ] Set up and secure cloud server - autoupdates, fail2ban, move ssh port, ban root from SSH, the works
 * Schedule light turn on/off sequences to go with surveys
 * Schedule automatic surveys for timelapse
 * Some sort of system for archiving data by timelapsing it

### Admin enhancements
[ ] Can we initiate recording to the disk array from the web application? Logged in user?
[ ] Tool for adding flags to visible time range when logged in as admin?
[ ] Cycle passwords on core devices

## Bugfixes and enhancements
[ ] When hovering over an item in a chart, highlight items on the other charts
[ ] Pull occasional thumbnails from video on ingestion?
[ ] Schedule full panorama recording on camera
[ ] Fill interface panels with appropriate items
[ ] Load older data from TDs. Include other sites so API is a sort of McMurdo sound data repo
[ ] Why isn't Paul receiving pager messages?
[ ] Stronger staticfiles planning in deployment - if we ever had another application (even the admin console) it wouldn't get its staticfiles because we're just serving out of our app's directory. Should have update run collectstatic, then serve from that folder.
[ ] Hydrophone and video history browser

### Spectrogram
[ ] Fix times on spectrogram display
[ ] Can we tweak colors or dB scaling on SoX spectrograms?
[ ] What will we put in place of the spectrogram on the web? Most recent one generated by SoX? Do we have bandwidth for this? These should compress well.

### Charting and CTD
[ ] Autoscale breaks when zoomed in and auto-update happens - other graphs lose correct window
[ ] CTD lookup by serial will fail if there are multiple deployments. It should load by serial and where end_date is null since it should only log to an open deployment. It should then complain if multiple records are returned (use .get())
[ ] Allow users to select time range to view data for
[ ] Manual refresh button - or some other way to make it clear that the charts autoupdate
[ ] Public documentation of CTD API - some sort of way to obtain a token?
[ ] Need to somehow move data off the left side of the viewing window - maybe leave it loaded, but not showing

### Tides
 * Need to scale all values to an appropriate depth
 * Delete downloaded weather data from temp when complete - it was sitting there on the server

### Interface
[ ] Changing panels by class toggling fails in weird ways when switching from an open panel of one size to another, then trying to close it. Use addClass and removClass insteads and we'll need to track the current_active class so we can remove it.
[ ] Better error reporting and console, esp for Jquery AJAX/CTD loads

## Documentation
[ ] Network diagram showing the various firewalls and services that would need to be configured when network changes happen

## One-offs
[ ] Add flags for temperature during dive
[ ] Confirm corrected CTD logging device after SBE19 went in
[ ] Fix bad salinity records - move to null values, or compute them as an average of others and add flag (null preferred)
