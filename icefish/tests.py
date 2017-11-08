# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

from icefish.models import Weather
from icefish.data_management import ncdc

import datetime
# Create your tests here.

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