import datetime
import gzip
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
import traceback

from six.moves.urllib import request

import arrow
from django.db.utils import IntegrityError

from icefish.models import Weather, CTD
from icefish_backend import local_settings

log = logging.getLogger("icefish.ncdc")

# MCMURDO_STATION_ISH_ID = 20028971  # this is a separat ID
MCMURDO_USAF_ID = 896640  # IDs to download ISH data - not sure what each ID means yet, but keeping them separate in case we have other uses for them
MCMURDO_WBAN_ID = 87601


class NCDCWeather(object):
	def __init__(self, year):
		self.year = year
		self.gzip_path = None
		self.sanitized_path = None
		self.converted_path = None

	def last_year_complete(self):
		"""
			Checks for data covering last year to see if it's complete. If we have data for Dec 31st, then it stops
			checking for last year.
		:return:
		"""
		last_year = self.year - 1
		dec_31 = datetime.datetime(last_year, 12, 31, 0, 0, 0, tzinfo=datetime.timezone.utc)
		jan_1 = datetime.datetime(self.year, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

		if Weather.objects.filter(dt__gte=dec_31).filter(dt__lt=jan_1).exists():  # exists is a cheap way to check that there's at least one record
			return True
		else:
			return False

	def _download_weather_data_for_year(self):
		data_url = "ftp://ftp.ncdc.noaa.gov/pub/data/noaa/{}/{}-{}-{}.gz".format(self.year, MCMURDO_USAF_ID,
																				 MCMURDO_WBAN_ID, self.year)

		# make temp file path and keep track of it so we can clean it up later
		self.gzip_path = tempfile.mktemp(prefix="mcmurdo_weather",
										 suffix="_{}-{}-{}.gz".format(MCMURDO_USAF_ID,
																	  MCMURDO_WBAN_ID, self.year))
		log.debug("Downloading original file to {}".format(self.gzip_path))

		downloaded = False
		attempts = 0
		while not downloaded and attempts < local_settings.MAX_DOWNLOAD_RETRIES:
			try:
				request.urlretrieve(data_url, self.gzip_path)
				downloaded = True
			except:
				log.warning("Failed to download file. Retrying. Error given was: {}".format(traceback.format_exc()))
				attempts += 1
				if attempts > local_settings.MAX_DOWNLOAD_RETRIES:
					raise
				else:
					time.sleep(local_settings.RETRY_WAIT_TIME)

		# now, extract the gzipped text data straight into a text file
		self.text_path = tempfile.mktemp(prefix="mcmurdo_text", suffix="_{}-{}-{}.txt".format(MCMURDO_USAF_ID,
																							  MCMURDO_WBAN_ID,
																							  self.year))
		log.debug("Extracting gzipped file to {}".format(self.text_path))
		with gzip.open(self.gzip_path, 'rb') as f_in:  # open the gzip file
			with open(self.text_path, 'wb') as f_out:  # open the output path
				shutil.copyfileobj(f_in, f_out)  # copy the file between the two, decompressing in the process

		log.debug("Extraction Complete")

	def _sanitize_weather_file(self):
		"""
			Sanitize it of the stupid shitty records that don't work in the script (anything .*?\s+\d\n) - records that end in a lone digit are bad. Test with original raw download file again
		:return:
		"""
		self.sanitized_path = tempfile.mktemp(prefix="mcmurdo_sanitized",
											  suffix="_{}-{}-{}.txt".format(MCMURDO_USAF_ID,
																			MCMURDO_WBAN_ID, self.year))
		log.debug("Sanitizing data file to {}".format(self.text_path))

		with open(self.text_path, 'rb') as f_in:
			with open(self.sanitized_path, 'wb') as f_out:
				for line in f_in:
					if re.search(".*?\s+\d\n", str(line)):  # skip lines that end with a space, then a single digit - they don't convert well
						continue
					f_out.write(line)

	def _convert_weather_file(self):
		"""
			This uses the perl weather conversion script from NCDC - it needed a few corrections though, so if you plan
			to update it, just do a quick comparison of our stored script to theirs to make sure that the new script seems
			to cover all use cases.
		:return:
		"""

		base_folder = os.path.split(os.path.abspath(__file__))[0]
		isd_display_pl = os.path.join(base_folder, "isd_display.pl")  # get path to perl file in same folder
		os.environ["ISD_FOLDER"] = base_folder  # we need to set this so that the perl file can find its command line argument package
		log.debug("Set ISD_FOLDER environment variable to {}".format(base_folder))

		self.converted_path = tempfile.mktemp(prefix="mcmurdo_converted",
											  suffix="_{}-{}-{}.txt".format(MCMURDO_USAF_ID,
																			MCMURDO_WBAN_ID,
																			self.year))

		log.debug("Converting file to {}".format(self.converted_path))

		self.output = subprocess.check_output([local_settings.PERL_BINARY, isd_display_pl, "cds", "ifn={}".format(self.sanitized_path)])  # the cds argument tells it to only process the section we care about - the others seem broken and cause errors

		# write the data out in case we need to inspect it
		if local_settings.DEBUG:
			with open(self.converted_path, 'wb') as outfile:
				outfile.write(self.output)

	def _transform_and_load_corrected_weather_file(self):
		records = self.output.decode('utf8').split("FILENAME")  # every time the word FILENAME is encountered, we are delimiting a record
		regex_string = "^(?P<variable_name>.+?)\s+(?P<record_id>\d+)\s+=\s+\"(?P<value>.*?)\"\r?$"  # the regex we'll use to find records
		regex = re.compile(regex_string)

		variable_mapping = {"wind_dir": "wind_direction",  # this dict both tells us the Django field names but also which variables to keep
								"wind_dir_flag": "wind_direction_flag",
								"wind_speed": "wind_speed",
								"wind_speed_flag": "wind_speed_flag",
								"air_temp": "air_temp",
								"air_temp_flag": "air_temp_flag",
								"sea_lev_press": "sea_level_pressure",
								"sea_levp_flag": "sea_level_pressure_flag",
							}

		for record in records:  # there are quite a few ways this could be sped up, but not sure it's that important - makes it more complicated
			if record in ("", "\n", "\r\n"):
				continue

			weather_record = Weather()  # make a new model in Django - we can't check for a dupe yet, but we'll store values here and only save if it's not a dupe
			values = record.split("\n")  # now get the individual variables
			datetime_parts = {}

			for value in values:
				match = regex.match(value)
				if not match:  # if there are no groups on this line, then keep going
					continue

				if weather_record.ncdc_id_value is None or weather_record.ncdc_id_value == "":  # we'll see this value many times, only bother to set it once
					weather_record.ncdc_id_value = match.group("record_id")

				if match.group("variable_name") in ("date", "gmt"):
					datetime_parts[match.group("variable_name")] = match.group("value")  # we'll make this an object outside the group
				else:
					if match.group("variable_name") in variable_mapping:
						setattr(weather_record, variable_mapping[match.group("variable_name")], int(match.group("value")))  # set the attribute on the Django model, coercing it to int

			self._check_values(weather_record)
			if weather_record.sea_level_pressure is None:  # if sea level pressure was nulled out, don't bother inserting it. We need it and would rather our CTD records attach to a different value
				continue

			# figure out the datetime of this record
			weather_record.dt = datetime.datetime.strptime("{} {}".format(datetime_parts["date"], datetime_parts["gmt"]), "%Y%m%d %H%M").replace(tzinfo=datetime.timezone.utc)
			if Weather.objects.filter(dt__exact=weather_record.dt).filter(ncdc_id_value__exact=weather_record.ncdc_id_value).exists():
				continue  # we already loaded this a previous time, skip - if we need to optimize, we should check if this is faster than just letting the unique constraint fail
			try:
				weather_record.save()
			except IntegrityError:  # it could fail on duplicate datetimes, or if we didn't have the check about for sea_level_pressure being defined
				log.warning("Failed to insert record with NCDC ID {} and datetime {}".format(weather_record.ncdc_id_value, weather_record.dt))

	def _check_values(self, weather_record):
		"""
			Checks the flags for anything indicating that a value should be Null and changes appropriate values to Null.
			Wondering if this code is surprisingly slow for how simple it is.
		:param weather_record:
		:return:
		"""
		check_attrs = ("wind_speed", "wind_direction", "air_temp", "sea_level_pressure")

		for attr in check_attrs:
			if getattr(weather_record, "{}_flag".format(attr)) == 9:  # if the flag value is 9, then it means the real value is null
				setattr(weather_record, attr, None)

	def get_valid_times(self):
		"""
			Figure out the range of time that each weather record is most relevant for
		:return:
		"""

		log.info("Determining time ranges for weather records")
		year_data = Weather.objects.filter(dt__year=self.year).order_by("dt")

		for index, record in enumerate(year_data):
			if index == 0:
				record.valid_from = datetime.datetime(self.year, 1, 1, 0, 0, 0).replace(tzinfo=datetime.timezone.utc)  # we'll assign it the first of January
			else:
				record.valid_from = year_data[index-1].valid_to

			if index == len(year_data) - 1:  # if it's the last one
				record.valid_to = datetime.datetime(self.year, 12, 31, 23, 59, 59).replace(tzinfo=datetime.timezone.utc)
			else:  # here's where the real calculation is - set it to halfway between this one and the next one
				base_datetime = arrow.get(record.dt)
				future_datetime = arrow.get(year_data[index+1].dt)
				margin = (future_datetime - base_datetime) / 2

				record.valid_to = (base_datetime + margin).datetime

			record.save()

	def update_ctd_records(self):
		"""
			Once we have updated weather data, we need to reassign CTD records to the weather since the ranges have changed.
			Loop through the whole year's CTD data and update. This operation is slower than I would expect - it might
			be worth us optimizing it - only updating the records that don't yet have weather data. The issue would be if
			there are holes in the weather data, making sure to track which records are new so we know which CTD data to update.
			It might be a nonissue, and we may have plenty of processing power to work with to handle this. It's not hitting
			CPU, RAM, or Disk too hard though, so maybe it doesn't matter.
		:return:
		"""

		log.info("Updating CTD records with new weather data")

		ctd_data = CTD.objects.filter(dt__year=self.year)
		for record in ctd_data:
			record.find_weather()
			record.save()

	def load_data(self):
		"""
			Main point of entry - handles the rest of the code
		:return:
		"""

		log.info("Loading weather data for {}".format(self.year))
		try:
			self._download_weather_data_for_year()
			self._sanitize_weather_file()
			self._convert_weather_file()
			self._transform_and_load_corrected_weather_file()
			self.get_valid_times()
			self.update_ctd_records()

		finally:
			if not local_settings.DEBUG:
				self._cleanup()  # only remove the files if we're not debugging - that way can inspect if things go wrong.

	def _cleanup(self):
		"""
			Removes our temporary files
		:return:
		"""
		for path in [self.gzip_path, self.text_path, self.sanitized_path, self.converted_path]:
			if os.path.exists(path):
				os.unlink(path)


def update_weather_data():
	# check to see if weather data for last year is complete
	# if not, download last years, and go through pipeline
	# then do this year's

	year = datetime.datetime.utcnow().year
	weather = NCDCWeather(year)
	if not weather.last_year_complete():  # check if last year is complete - if it's not, then load it. Don't go earlier than 2017
		last_year = NCDCWeather(year - 1)
		last_year.load_data()
	weather.load_data()  # now load this year


