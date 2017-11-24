# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import datetime

from django.test import TestCase
from django.core import mail

from icefish_backend import local_settings, settings
from icefish.models import Weather, HydrophoneAudio, MOOVideo
from icefish.data_management import ncdc
from icefish.management.commands import monitor_ctd
# Create your tests here.

local_settings.DEBUG = True  # for now, always set debug to true for tests

class NCDCTest(TestCase):
	def setUp(self):
		Weather.objects.create(dt=datetime.datetime.now(tz=datetime.timezone.utc), sea_level_pressure=9910)

	def test_last_year_check(self):
		"""
			Makes sure that the check for data completeness at the end of *last* year works
		:return:
		"""

		year = datetime.datetime.utcnow().year
		weather_loader = ncdc.NCDCWeather(year)
		self.assertFalse(weather_loader.last_year_complete())

		Weather.objects.create(dt=datetime.datetime(year-1, 12, 31, 0, 1, 0, tzinfo=datetime.timezone.utc), sea_level_pressure=810)

		self.assertTrue(weather_loader.last_year_complete())


class HydrophoneTest(TestCase):

	def test_integrity_check(self):
		new_audio = HydrophoneAudio()
		new_audio.wav = os.path.join(settings.BASE_DIR, "icefish", "testdata", "short_success.wav")
		new_audio.get_info()
		new_audio.save()

		new_audio.flac = os.path.join(settings.BASE_DIR, "icefish", "testdata", "short_success_24.flac")
		self.assertTrue(new_audio.flac_verifies())

		new_audio.flac = os.path.join(settings.BASE_DIR, "icefish", "testdata", "fail_incomplete.flac")
		self.assertFalse(new_audio.flac_verifies())

		new_audio.flac = os.path.join(settings.BASE_DIR, "icefish", "testdata", "fail_short_corrupt.flac")
		self.assertFalse(new_audio.flac_verifies())


class AlertsTest(TestCase):
	def setUp(self):
		self.data1_supercooled = [
			{
				"temperature": -5,
		 		"pressure": 15,
				"conductivity": 1,
				"salinity": 34,
				"datetime": datetime.datetime.utcnow(),
			}
		]

		self.data2_supercooled = [
			{
				"temperature": -6,
		 		"pressure": 15,
				"conductivity": 2,
				"salinity": 34,
				"datetime": datetime.datetime.utcnow(),
			}
		]

		self.data3_endsupercooled = [
			{
				"temperature": 8,
		 		"pressure": 15,
				"conductivity": 3,
				"salinity": 34,
				"datetime": datetime.datetime.utcnow(),
			}
		]

		self.data4_notsupercooled = [
			{
				"temperature": 5,
		 		"pressure": 15,
				"conductivity": 4,
				"salinity": 34,
				"datetime": datetime.datetime.utcnow(),
			}
		]

	def test_send_start_and_end_alerts(self):

		# no alert - not supercooled
		status = monitor_ctd.handle_records(self.data4_notsupercooled, return_alerts=True)  # should not result in an alert
		self.assertFalse(status["sent"])
		self.assertEqual(status["status"], "normal")
		self.assertEqual(len(mail.outbox), 0)

		# alert - first supercooled observation
		status = monitor_ctd.handle_records(self.data1_supercooled, return_alerts=True)  # should not result in an alert
		self.assertTrue(status["sent"])
		self.assertEqual(status["status"], "supercooled")
		self.assertEqual(len(mail.outbox), 1)

		# repeating supercooled observation - no additional alert should be sent
		status = monitor_ctd.handle_records(self.data2_supercooled, return_alerts=True)  # should not result in an alert
		self.assertFalse(status["sent"])
		self.assertEqual(status["status"], "supercooled")
		self.assertEqual(len(mail.outbox), 1)

		# ok, end the supercooling - an alert should be sent
		status = monitor_ctd.handle_records(self.data4_notsupercooled, return_alerts=True)  # should not result in an alert
		self.assertTrue(status["sent"])
		self.assertEqual(status["status"], "normal")
		self.assertEqual(len(mail.outbox), 2)

		# set it up again, but it shouldn't send because it hasn't been enough time
		status = monitor_ctd.handle_records(self.data1_supercooled, return_alerts=True)  # should not result in an alert
		self.assertFalse(status["sent"])
		self.assertEqual(status["status"], "supercooled")
		self.assertEqual(len(mail.outbox), 2)


class VideoTest(TestCase):
	def setUp(self):
		self.test_video = r"C:\Users\dsx\Dropbox\Antarctica\video\20171117_15-59-38.mp4"
		self.test_video2 = r"C:\Users\dsx\Dropbox\Antarctica\video\PipeInsertion2.asf"

	def test_video_metadata(self):
		for video in (self.test_video, self.test_video2):
			v = MOOVideo()
			v.source_path = video
			v.get_metadata()

			self.assertGreater(v.length, 0)
			self.assertGreater(v.width, 0)
			self.assertGreater(v.height, 0)
			self.assertIsNotNone(v.dt)
			self.assertIsNotNone(v.duration)
			self.assertIsNotNone(v.format)