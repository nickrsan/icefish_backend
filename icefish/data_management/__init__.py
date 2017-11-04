import contextlib
import datetime
import logging
import os
import platform
import subprocess
import wave

import arrow

from icefish.models import HydrophoneAudio, FLACIntegrityError
from icefish_backend import settings

log = logging.getLogger("icefish.audio")

def hydrophone_pipeline(inbound_folder=settings.WAV_STORAGE_FOLDER, outbound_folder=settings.FLAC_STORAGE_FOLDER, spectrogram_folder=settings.SPECTROGRAM_STORAGE_FOLDER, reprocess=False):
	"""
		Handles incoming data from the high quality hydrophone - makes a spectroraph, converts to flac, gets metadata
		and loads it into the database, removing original wav file
	:param inbound_folder:
	:param outbound_folder:
	:return:
	"""

	new_files = os.listdir(inbound_folder)
	wav_files = [wav for wav in new_files if wav.endswith(".wav")]  # filter to only files ending with the .wav extension

	for wav in wav_files:
		log.debug("Loading {}".format(wav))
		# THIS SHOULD CHECK FOR A FILE WITH THE SAME OUTPUT NAME TO PROTECT AGAINST DUPLICATES - we could also use an index

		full_input = os.path.join(inbound_folder, wav)
		if already_loaded(full_input):  # check if that wav file path is already in the database. If so, skip it
			log.debug("Skipping already loaded file at {}".format(full_input))
			continue

		audio = HydrophoneAudio()
		base_name = os.path.basename(wav).split(".")[0]  # get just the root filename without directory or extension - directory won't be included here
		audio.wav = full_input
		full_output = os.path.join(outbound_folder, "{}.flac".format(base_name))

		audio.get_wave_length()
		audio.get_start_time()

		try:
			audio.make_flac(full_output, overwrite=reprocess)
		except FileExistsError:
			if reprocess is False:
				continue  # it already exists, so we'll just skip adding this file for now - currently, this leaves it to be processed again - should we do that?

		audio.make_spectrogram(os.path.join(spectrogram_folder, "{}.png".format(base_name)))
		audio.save()

		try:
			audio.remove_wav()  # automatically checks the integrity of the FLAC file before deleting WAV file
		except FLACIntegrityError:
			log.warning("Unable to remove wav file {}. FLAC file is invalid. Regenerate the flac file for audio record with ID {}".format(audio.wav, audio.id))

def already_loaded(wave_path):
	"""
		Checks if the wave named at wave_path has already been loaded
	:param wave_path:
	:return:
	"""
	try:
		HydrophoneAudio.objects.get(wav=wave_path)
	except HydrophoneAudio.DoesNotExist:
		return False

	# If succeeds without error, then it's loaded. return True to skip it
	return True