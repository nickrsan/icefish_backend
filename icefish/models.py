# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import models

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
	intrument = models.ForeignKey(CTDInstrument)

class HydrophoneAudio(models.Model):
	wav = models.FilePathField(null=True, blank=True)  # just the original wav location, but if we ever back it out to a wav from flac, could use this
	flac = models.FilePathField()  # converted flac file
	start_time = models.DateTimeField(db_index=True)
	length = models.PositiveIntegerField()
	spectrograph = models.FilePathField(null=True, blank=True)  # where is
	flags = models.CharField(blank=True, max_length=255)  # we don't have a scheme for flags yet, but we might want to create a set of characters to mean things

	@property
	def end_time(self):
		return datetime.datetime((self.start_time + self.length).total_seconds())  # should test this - not sure if it casts that value to seconds or not - I think it does

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

