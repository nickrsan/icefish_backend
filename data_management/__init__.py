import os
import subprocess
import wave
import contextlib

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

		audio.save()


	# pass it through whatever generates spectrographs
	# send each file to flac,
	# delete original
	#

	# create HydrophoneAudio object for each
	# end by saving it
	pass


def get_wave_length(path):
	with contextlib.closing(wave.open(path,'r')) as wav:
		return wav.getnframes() / float(wav.getframerate())  # length = frames / rate