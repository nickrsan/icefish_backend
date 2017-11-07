import tempfile

from six.moves.urllib import request

import arrow
import datetime

from icefish.models import Weather

# TODO: Need to test the legacy API again - it likely won't give us data - so, run the pipeline below -

MCMURDO_STATION_ISH_ID = 20028971

class NCDCWeather(object):

	def __init__(self, year):
		self.year = year

	def _last_year_complete(self):
		"""
			Checks for data covering last year to see if it's complete. If we have data for Dec 31st, then it stops
			checking for last year.
		:return:
		"""
		last_year = self.year - 1
		dec_31 = datetime.datetime(last_year, 12, 31, 0, 0, 0, tzinfo=datetime.timezone.utc)
		jan_1 = datetime.datetime(self.year, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

		if len(Weather.objects.filter(dt__gte=dec_31).filter(dt__lte=jan_1)) > 0:
			return True
		else:
			return False

	def _download_weather_data_for_year(self):

		# make temp file path and keep track of it so we can clean it up later
		# download with request.urlretrieve
		pass
		# Download latest file - some sort of logic to determine when to download 2017 vs 2018 - maybe if it's current year and we don't have data for end of last year, download last year's too
		# Extract it

	def _sanitize_weather_file(self):
		pass
		# Sanitize it of the stupid shitty records that don't work in the script (anything .*?\s+\d\n) - records that end in a lone digit are bad. Test with original raw download file again

	def _convert_weather_file(self):
		pass
		# Convert it to be slightly less gibberish

	def _read_corrected_weather_file(self):
		pass
		# Read in new file, transform to list of dicts

	def _insert_weather_data(self):
		pass
		# create datetime object
		# django model will be unique for datetime - we'll just try inserting the whole year each time and let the index reject it, or we can manually check for a record with that datetime

	def load_data(self):
		"""
			Main point of entry - handles the rest of the code
		:return:
		"""
		pass

def update_weather_data(self):
	# check to see if weather data for last year is complete
	# if not, download last years, and go through pipeline
	# then do this year's

	pass
