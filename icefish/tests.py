# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.core import mail

from icefish_backend import local_settings
from icefish.models import Weather
from icefish.data_management import ncdc
from icefish.management.commands import monitor_ctd
import datetime
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
