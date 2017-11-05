import arrow
import datetime

# TODO: Need to test the legacy API again - it likely won't give us data - so, run the pipeline below -

MCMURDO_STATION_ISH_ID = 20028971

class NCDCWeather(object):

	def __init__(self, year):
		self.year = year

	def _download_weather_data_for_year(self):
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
