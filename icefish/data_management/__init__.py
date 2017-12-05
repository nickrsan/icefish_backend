import shutil
import logging
import tempfile
import os
import wave
import subprocess

from icefish.models import HydrophoneAudio, FLACIntegrityError, MOOVideo
from icefish_backend import settings

log = logging.getLogger("icefish")

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

		if settings.COPY_WAV_TO_TEMP:
			audio.wav = tempfile.mktemp(prefix="hydrophone")
			shutil.copyfile(full_input, audio.wav)  # we'll delete this and overwrite the path later
		else:
			audio.wav = full_input

		final_flac = os.path.join(outbound_folder, "{}.flac".format(base_name))
		if settings.COPY_FLAC_TO_TEMP:
			full_output = tempfile.mktemp(prefix="hydrophone", suffix="flac")
		else:
			full_output = final_flac

		try:
			try:
				audio.get_wave_length()
			except wave.Error:
				log.warning("Unable to get metadata about wave file {} - skipping".format(full_input))
				continue
			audio.get_start_time()

			try:
				audio.make_flac(full_output, overwrite=reprocess)
			except subprocess.CalledProcessError:
				continue
			except FileExistsError:
				if reprocess is False:
					continue  # it already exists, so we'll just skip adding this file for now - currently, this leaves it to be processed again - should we do that?

			audio.make_spectrogram(os.path.join(spectrogram_folder, "{}.png".format(base_name)))
			audio.save()
		except:
			if settings.COPY_FLAC_TO_TEMP and os.path.exists(full_output):  #  if a temp flac file exists and we hit an exception, delete it
				os.unlink(full_output)
			raise  # raise the exception up no matter what - we just wanted to do some cleanup - it can't go in the finally block though because we don't want this to happen on success
		finally:
			if settings.COPY_WAV_TO_TEMP:
				os.unlink(audio.wav)  # get rid of the temporary wav file assigned to this, then assign audio.wav to match the original again
				audio.wav = full_input

		try:
			if settings.DELETE_WAVS:
				audio.remove_wav()  # automatically checks the integrity of the FLAC file before deleting original WAV file
		except FLACIntegrityError:
			log.warning("Unable to remove wav file {}. FLAC file is invalid. Regenerate the flac file for audio record with ID {}".format(audio.wav, audio.id))

		if settings.COPY_FLAC_TO_TEMP:
			shutil.copyfile(audio.flac, final_flac)
			os.unlink(audio.flac)
			audio.flac = final_flac

		if settings.COPY_WAV_TO_TEMP:
			os.unlink(full_input)  # we already deleted self.wav above, so now we delete the original -
			audio.wav = full_input


def video_pipeline(remove_bottom=True, remove_existing=False):

	log.debug("Searching for new videos")
	for folder in settings.VIDEO_FOLDERS:
		params = settings.VIDEO_FOLDERS[folder]
		log.debug("Searching in {}".format(folder))

		try:
			found_videos = [vid for vid in os.listdir(folder) if os.path.splitext(vid)[1] in params["extensions"]]
		except FileNotFoundError:
			log.warning("Couldn't check for videos in {}. Unable to read folder.".format(folder))
			continue
		log.debug(found_videos)

		for video in found_videos:  # all the videos of the extensions we're looking for
			log.debug("Loading video {}".format(video))
			source_path = os.path.join(folder, video)
			try:
				MOOVideo.objects.get(source_path=source_path)
				continue  ## if it successfully is gotten, skip it
			except MOOVideo.DoesNotExist:
				pass  # only reaches the next portion if we get here anyway

			v = MOOVideo()
			v.source_path = source_path
			v.get_metadata()  # have it load up its own metadata

			if params["transcode"]:
				try:
					v.transcode(params["transcoding_path"], remove_bottom, remove_existing)
				except ValueError:
					pass  # as of right now, it just means it already exists and we didn't tell it to remove it!

			if not params["keep_original"]:
				os.unlink(source_path)

			v.save()


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
