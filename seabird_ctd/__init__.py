"""
	SeaBird CTD is meant to handle reading data from a stationary CTD logger. Many packages exist for profile loggers,
	but no options structured for use on a stationary logger or reading
"""

__author__ = "nickrsan"


"""
	Plan is to have this return either a pandas dataframe or a Python dictionary with the new records. Should filter
	out any noise in the serial transmission (commands, status information, etc).
	
	I believe the CTD will be constantly outputting a file that we'll be reading via USB/serial. Not sure how often we
	can clear/rotate the file, but we should assume:
		1. The file will be open for writing while we read it
		2. It will have duplicate records in it that we'll need to avoid (DB integrity will help, but would be good
			to filter out most, if not all, so that we don't have a bunch of failed inserts
		3. Some records won't be records because they'll be commands, errors, or status messages. We'll want to do data
			cleaning to confirm the record is what we think it is (RegEx, probably - CSV parsing might not work if we're
			trying to read only specific lines - we could potentially dump the lines we know we want to a new file for
			CSV reading, but that seems silly because we would already need to know what's new to do that. File offset
			reading? Parsing the whole file, loading the dates and jumping to the record with the correct dates?
"""

import time
import datetime
import os
import re
import logging

import serial

class CTDConnectionError(BaseException):
	pass

class Element(object):
	def __init__(self, name, value, db_field, regex=None,):
		"""

		:param name:
		:param regex:
		:param db_field: matching field on the django postgres object
		"""
		self.name = name
		self.value = value
		self.db_field = db_field

	def filter_values(self):
		"""
			Runs the regex on the value and stores the new value
		:return:
		"""

		pass

class CTD(object):
	def __init__(self, COM_port=None, baud=9600, timeout=8, setup_delay=2, date_format=""):
		"""
		If COM_port is not provided, checks for an environment variable named SEABIRD_CTD_PORT. Otherwise raises
		CTDConnectionError
		"""
		if COM_port is None:
			if "SEABIRD_CTD_PORT" in os.environ:
				COM_port = os.environ["SEABIRD_CTD_PORT"]
			else:
				raise CTDConnectionError("SEABIRD_CTD_PORT environment variable is not defined. Don't know what COM port"
										 "to connect to for CTD data. Can't collect CTD data.")

		self.ctd = serial.Serial(COM_port, baud, timeout=timeout)
		time.sleep(setup_delay)  # give it time to init
		self.ctd.write(b"")  # sometimes needs a write and a read to fully connect
		junk = self.ctd.read(100)  # should hit timeout waiting for the read, but then be ready to do work
			# TODO: Is this always junk? What if this is starting up after setting the CTD to autosample, then the server crashes and is reconnecting

	def _send_command(self, command, get_response=True, length_to_read=1000):
		self.ctd.write(serial.to_bytes('{}\r\n'.format(command)))  # doesn't seem to work unless we pass it a windows line ending. Sends command, but no results

		if get_response:
			if length_to_read == "LINE":
				data = self.ctd.readline()
			else:
				data = self.ctd.read(length_to_read)

		return data.split("\r\n")  # first element of list should now be the command, but we'll let the caller filter that

	def set_datetime(self):
		dt = datetime.datetime.now()
		self._send_command("DATETIME={}".format(dt.strftime("%m%d%Y%H%M%S")),get_response=False)

	def take_sample(self):
		data = self._send_command("TS")


	def _filter_samples_to_data(self,):
		pass