# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import logging
import subprocess
import datetime
import contextlib
import platform
import wave

import arrow  # similar to datetime

from icefish_backend import settings
from django.db import models

log = logging.getLogger("icefish.models")

# Create your models here.

class CTDInstrument(models.Model):
	deployment_start = models.DateTimeField()
	deployment_end = models.DateTimeField(null=True, blank=True)
	model = models.CharField(max_length=20, null=True, blank=True)
	serial = models.CharField(max_length=30, null=True, blank=True)
	depth = models.FloatField(blank=True, null=True)
	coord_x = models.FloatField(null=True, blank=True)
	coord_y = models.FloatField(null=True, blank=True)

class CTD(models.Model):
	temp = models.FloatField(db_index=True)
	pressure = models.FloatField(db_index=True)
	conductivity = models.FloatField(blank=True, null=True, db_index=True)
	salinity = models.FloatField(blank=True, null=True, db_index=True)
	datetime = models.DateTimeField(db_index=True)
	server_datetime = models.DateTimeField()  # the server reading the data's timestamp
	measured = models.BooleanField(default=True)  # used as a flag if we interpolate any values. If measured == True, then it's direct off the CTD
	instrument = models.ForeignKey(CTDInstrument)

class HydrophoneAudio(models.Model):
	wav = models.FilePathField(null=True, blank=True)  # just the original wav location, but if we ever back it out to a wav from flac, could use this - not guaranteed to exist
	flac = models.FilePathField()  # converted flac file
	start_time = models.DateTimeField(db_index=True)
	length = models.PositiveIntegerField()
	spectrogram = models.FilePathField(null=True, blank=True)  # where is
	flags = models.CharField(blank=True, max_length=255)  # we don't have a scheme for flags yet, but we might want to create a set of characters to mean things

	@property
	def end_time(self):
		start_time = arrow.get(self.start_time)
		return start_time.shift(seconds=+self.length).datetime  # use arrow, but return a datetime object

	def time_window_overlaps(self, time_start, time_end):
		"""
			Used to compare another time window (such as one we want to save) to this one to see if they overlap
		:return:
		"""

		if time_start < self.start_time < time_end:
			return True
		if time_start < self.end_time < time_end:
			return True

		return False  # if neither of those are in that window, then it's not overlap

	def make_flac(self, output_path, overwrite=False):
		if os.path.exists(output_path):
			if overwrite is True:
				log.warning("FLAC file already exists and overwrite is on, creating new file")
				os.unlink(output_path)  # remove current version so it can be recreated
			else:
				raise FileExistsError("FLAC file already exists!")

		# Make FLAC file
		flac_params = [settings.FLAC_BINARY, settings.FLAC_COMPRESSION_LEVEL, "--totally-silent", self.wav, "--output-name={}".format(output_path)]
		log.debug(flac_params)
		result = subprocess.check_call(flac_params)
		self.flac = output_path

	def _check_wave(self):
		if not self.wav or not os.path.exists(self.wav):
			raise ValueError("Can't get wave file information - wavefile doesn't exist - it may need to be created from the FLAC file")

	def get_wave_length(self):
		"""
			Gets the length in seconds of a WAV file. Adapted from https://stackoverflow.com/questions/7833807/get-wav-file-length-or-duration#7833963
		:param path: the fully qualified path to a wav file
		:return: time in seconds of duration that the wav file lasts
		"""
		self._check_wave()

		with contextlib.closing(wave.open(self.wav, 'r')) as wav:
			self.length = wav.getnframes() / float(wav.getframerate())  # length = frames / rate

	def get_start_time(self):
		"""
		Try to get the date that a file was created, falling back to when it was
		last modified if that isn't possible. Modification by Nick subtracts out file length to find its start time
		See http://stackoverflow.com/a/39501288/1709587 for explanation.
		:param path_to_file: Fully qualified path to file
		:param file_length: The length of the audio file, in seconds. Only used on unix systems to determine start time from end time
		:return: datetime object representing creation datetime
		"""

		self._check_wave()

		if platform.system() == 'Windows':
			start_time = datetime.datetime.fromtimestamp(os.path.getctime(self.wav))
		else:
			stat = os.stat(self.wav)  # Mac
			try:
				start_time = datetime.datetime.fromtimestamp(stat.st_birthtime)
			except AttributeError:
				# We're probably on Linux. No easy way to get creation dates here, so we'll take the last modified date
				# and subtract the file length, which should be sufficient
				end_time = arrow.get(stat.st_mtime)
				start_time = end_time.shift(seconds=-self.length).datetime  # shift the end time by subtracting the length of the file to get start time as a datetime

		self.start_time = arrow.get(start_time, "UTC").datetime

	def make_spectrogram(self, output_path):
		# Make Spectrogram file
		spectrogram_params = [settings.SOX_BINARY, self.wav, "-n", "spectrogram", "-o", output_path]
		log.debug(spectrogram_params)
		result = subprocess.check_call(spectrogram_params)
		self.spectrogram = output_path
