import os
import platform
import subprocess
import wave
import contextlib
import datetime

import arrow

from icefish_backend import settings
from icefish.models import HydrophoneAudio

import logging
log = logging.getLogger("icefish.audio")

def hydrophone_pipeline(inbound_folder=settings.WAV_STORAGE_FOLDER, outbound_folder=settings.FLAC_STORAGE_FOLDER):

	new_files = os.listdir(inbound_folder)
	wav_files = [wav for wav in new_files if wav.endswith(".wav")]  # filter to only files ending with the .wav extension

	for wav in wav_files:
		# THIS SHOULD CHECK FOR A FILE WITH THE SAME OUTPUT NAME TO PROTECT AGAINST DUPLICATES - we could also use an index
		full_input = os.path.join(inbound_folder, wav)
		base_name = wav.split(".")[0]  # get just the root filename without directory or extension - directory won't be included here
		full_output = os.path.join(outbound_folder, "{}.flac".format(base_name))

		audio = HydrophoneAudio()
		result = subprocess.check_call([settings.FLAC_BINARY, settings.FLAC_COMPRESSION_LEVEL, "--totally_silent", full_input, full_output])

		audio.wav = full_input
		audio.flac = full_output
		audio.length = get_wave_length(full_input)
		audio.start_time = get_start_time(full_input, audio.length)
		audio.save()

	# pass it through whatever generates spectrographs
	# delete original

def get_wave_length(path):
	"""
		Gets the length in seconds of a WAV file. Adapted from https://stackoverflow.com/questions/7833807/get-wav-file-length-or-duration#7833963
	:param path: the fully qualified path to a wav file
	:return: time in seconds of duration that the wav file lasts
	"""
	with contextlib.closing(wave.open(path,'r')) as wav:
		return wav.getnframes() / float(wav.getframerate())  # length = frames / rate


def get_start_time(path_to_file, file_length):
	"""
	Try to get the date that a file was created, falling back to when it was
	last modified if that isn't possible. Modification by Nick subtracts out file length to find its start time
	See http://stackoverflow.com/a/39501288/1709587 for explanation.
	:param path_to_file: Fully qualified path to file
	:param file_length: The length of the audio file, in seconds. Only used on unix systems to determine start time from end time
	:return: datetime object representing creation datetime
	"""
	if platform.system() == 'Windows':
		return datetime.datetime.fromtimestamp(os.path.getctime(path_to_file))
	else:
		stat = os.stat(path_to_file)  # Mac
		try:
			return datetime.datetime.fromtimestamp(stat.st_birthtime)
		except AttributeError:
			# We're probably on Linux. No easy way to get creation dates here, so we'll take the last modified date
			# and subtract the file length, which should be sufficient
			end_time = arrow.get(stat.st_mtime)
			return end_time.shift(seconds=-file_length).datetime  # shift the end time by subtracting the length of the file to get start time as a datetime

