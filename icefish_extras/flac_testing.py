"""
	Tests the original and compressed sizes of flac at multiple compression levels as well as times.
	Reports compression ratio and time/%Saved.

	Also should check decompression.

	Running on the test files, Level 5 seems optimal from a time invested per storage saved standpoint
"""

import os
import datetime
import subprocess

compression_levels = ["-1", "-2", "-3", "-4", "-5", "-6", "-7", "-8"]
base_folder = r"C:\Users\dsx\Dropbox\Antarctica\Audio\Samples"
files = [
	("CzikoTest1_200khz_SBW1713_20170825_145721.wav", 224244328),
	("CzikoTest2_Water_128kS_S_SBW1713_20170922_195000.wav", 23040328)
]
flac_binary = r"C:\Users\dsx\Dropbox\Antarctica\Software\Audio\flac-1.3.2-win\win64\flac.exe"

print("new_name, level, seconds, ratio, seconds_per_percent_saved")
for l_file in files:
	for level in compression_levels:
		prefix = "level{}_".format(level[1:])
		new_name = os.path.join(base_folder, "{}{}.flac".format(prefix, l_file[0][:-4]))
		time_start = datetime.datetime.now()
		subprocess.check_call([flac_binary, "--totally-silent", "-f", "-o", new_name, level, os.path.join(base_folder, l_file[0])])
		time_end = datetime.datetime.now()
		time_elapsed = time_end - time_start  # will include the overhead of subprocess, but I think that'll be small relative to total
		seconds = time_elapsed.total_seconds()  # datetime.timedelta object

		size = os.path.getsize(new_name)
		ratio = size / float(l_file[1])
		seconds_per_percent_saved = seconds / ((1-ratio) * 100)
		print("{}, {}, {}, {}, {}".format(new_name, level[1:], seconds, ratio, seconds_per_percent_saved))