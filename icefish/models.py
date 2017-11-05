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

class FLACIntegrityError(BaseException):
	pass

class Weather(models.Model):
	"""
		Data loaded
	"""

class CTDInstrument(models.Model):
	deployment_start = models.DateTimeField()
	deployment_end = models.DateTimeField(null=True, blank=True)
	model = models.CharField(max_length=20, null=True, blank=True)
	serial = models.CharField(max_length=30, null=True, blank=True)
	depth = models.FloatField(blank=True, null=True)
	coord_x = models.FloatField(null=True, blank=True)
	coord_y = models.FloatField(null=True, blank=True)

class CTD(models.Model):
	temp = models.FloatField(db_index=True)  # ITS 90, celsius
	pressure = models.FloatField(db_index=True)  # decibars
	conductivity = models.FloatField(blank=True, null=True, db_index=True)
	salinity = models.FloatField(blank=True, null=True, db_index=True)  # practical salinity units
	dt = models.DateTimeField(db_index=True)  # datetime
	server_dt = models.DateTimeField()  # the server reading the data's timestamp
	measured = models.BooleanField(default=True)  # used as a flag if we interpolate any values. If measured == True, then it's direct off the CTD
	instrument = models.ForeignKey(CTDInstrument)

	def _window_avg(self, var, window=7):
		window_date = arrow.get(self.dt)
		beginning_date = window_date.shift(days=-(window/2)).datetime
		end_date = window_date.shift(seconds=+(window/2)).datetime
		data = CTD.objects.filter(dt__gt=beginning_date).filter(dt__lt=end_date).all()

		values = [getattr(record, var) for record in data]
		return sum(values)/len(values)

	def avg_temp(self, window=7):
		"""
			Gives the average temperature for a window (in days) centered on this observation.
		:param window: number of days the window represents. This observation is the centering point, so a window of
						size 7, the default, will be 3.5 days before and after this measurement.
		:return: float value of average temperature in ITS 90 degrees celsius
		"""
		return self._window_avg("temp", window)

	def avg_pressure(self, window=7):
		"""
			Gives the average pressure for a window (in days) centered on this observation.
			:param window: number of days the window represents. This observation is the centering point, so a window of
							size 7, the default, will be 3.5 days before and after this measurement.
			:return: float value of average pressure in decibars
		"""
		return self._window_avg("pressure", window)

	def avg_conductivity(self, window=7):
		"""
			Gives the average conductivity for a window (in days) centered on this observation.
			:param window: number of days the window represents. This observation is the centering point, so a window of
							size 7, the default, will be 3.5 days before and after this measurement.
			:return: float value of average conductivity
		"""
		return self._window_avg("conductivity", window)

	def avg_salinity(self, window=7):
		"""
			Gives the average salinity for a window (in days) centered on this observation.
			:param window: number of days the window represents. This observation is the centering point, so a window of
							size 7, the default, will be 3.5 days before and after this measurement.
			:return: float value of average salinity in practical salinity units
		"""
		return self._window_avg("salinity", window)

	@property
	def freezing_point(self):
		"""
			This equation is defined in Fofonoff et al 1983 for ITS 78 temperatures, but according to Paul, that is still
			the most current paper on the topic.
		:return:
		"""
		if not self.salinity or self.salinity is None:
			return ValueError("Can't calculate - no salinity measurement for this record")

		return -0.0575*self.salinity + 0.001710523*(self.salinity**1.5) - 0.0002154996*(self.salinity**2) - 0.000753*self.pressure

	@property
	def is_supercooled(self):
		if self.temp < self.freezing_point:
			return True
		else:
			return False

	@property
	def supercooling_amount(self):
		"""
			How much supercooling is occuring at any given moment. If it's supercooled, it returns the number of degrees
			Celsius that the water is supercooled. Otherwise returns 0.
		:return:
		"""
		if self.is_supercooled:
			return self.temp - self.freezing_point
		else:
			return 0

class HydrophoneAudio(models.Model):
	wav = models.FilePathField(null=True, blank=True, unique=True)  # just the original wav location, but if we ever back it out to a wav from flac, could use this - not guaranteed to exist
	flac = models.FilePathField(unique=True)  # converted flac file
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
				raise FileExistsError("FLAC file {} already exists!".format(output_path))

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

	def remove_wav(self):
		"""
			Confirms that the flac file exists and is intact (with flac test), then deletes the wav file if FLAC looks good.
		:return:
		"""
		if self.flac is not None and self.flac != "" and os.path.exists(self.flac):  # check the basics first
			if not self.flac_verifies():
				raise FLACIntegrityError("FLAC file for {} is not valid - it should be regenerated from original WAV. Abandoning WAV deletion".format(self.wav))

			log.debug("Removing wav file at {}".format(self.wav))
			os.unlink(self.wav)  # now remove the wav file

	def flac_verifies(self):
		"""
			Checks that the flac file is a valid flac file - we don't want to delete the wav if it's not (maybe an error
			or a power outage during transcoding, etc).
		:return: True if file is valid, False otherwise
		"""
		try:
			subprocess.check_call([settings.FLAC_BINARY, "-t", self.flac, "--totally-silent"])
		except subprocess.CalledProcessError:
			return False

		return True
