"""
	SeaBird CTD is meant to handle reading data from a stationary CTD logger. Many packages exist for profile loggers,
	but no options structured for use on a stationary logger or reading
"""

__author__ = "nickrsan"
import seabird_ctd.version as __version__

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
import six

import serial

from seabird_ctd import tasks

class SBE37(object):
	def __init__(self):
		self.max_samples = 3655394  # needs verification. This is just a guess based on SBE39
		self.keys = ("temperature", "pressure", "datetime")

	def set_datetime(self):
		dt = datetime.datetime.now()
		return ["DATETIME={}".format(dt.strftime("%m%d%Y%H%M%S"))]

	def sample_interval(self, interval):
		return "SAMPLEINTERVAL={}".format(interval)

	def retrieve_samples(self, start, end):
		return [
			"OUTPUTFORMAT=1",
			"GetSamples:{},{}".format(start,end)
		]

class SBE39(object):
	def __init__(self):
		self.max_samples = 3655394
		self.keys = ("temperature", "pressure", "datetime")

	def set_datetime(self):
		dt = datetime.datetime.now()
		return ["MMDDYY={}".format(dt.strftime("%m%d%y")), "HHMMSS={}".format(dt.strftime("%H%M%S"))]

	def sample_interval(self, interval):
		return "INTERVAL={}".format(interval)

	def retrieve_samples(self, start, end):
		return [
			"DD{},{}".format(start, end)
		]

	def record_regex(self):
		self.regex = "(?P<temperature>-?\d+\.\d+),\s+(?P<pressure>-?\d+\.\d+),\s+(?P<datetime>\d+\s\w+\s\d{4},\s\d{2}:\d{2}:\d{2})"
		return self.regex

supported_ctds = {
	"SBE 37": "SBE37",
	"SBE 39": "SBE39"
}  # name the instrument will report, then class name. could also do this with 2-tuples.

class CTDConfigurationError(BaseException):
	pass

class CTDOperationError(BaseException):
	pass

class CTDConnectionError(BaseException):
	pass

class CTD(object):
	def __init__(self, COM_port=None, baud=9600, timeout=5, setup_delay=2):
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

		self.last_sample = None

		self.ctd = serial.Serial(COM_port, baud, timeout=timeout)
		time.sleep(setup_delay)  # give it time to init

		self.command_object = None
		self.determine_ctd_model()
		self.status()  # will fill some fields in so we know what sample it's on, etc

	def determine_ctd_model(self):
		ctd_info = self.wake()  # TODO: Is the data returned from wake always junk? What if this is starting up after setting the CTD to autosample, then the server crashes and is reconnecting

		for line in ctd_info:  # it should write out the model when you connect
			if line in supported_ctds.keys():
				logging.log(1, line)
				self.command_object = globals()[supported_ctds[line]]()  # get the object that has the command info for this CTD
				self.model = line

		if not self.command_object:  # if we didn't get it from startup, issue a DS to determine it and peel it off the first part
			self.model = self._send_command("DS")[1][:6]  # it'll be the first 6 characters of the
			self.command_object = globals()[supported_ctds[self.model]]()

		if not self.command_object:
			raise CTDConnectionError("Unable to wake CTD or determine its type. There could be a connection error or this is currently plugged into an unsupported model")

	def _send_command(self, command, length_to_read="ALL"):
		self.ctd.write(six.b('{}\r\n'.format(command)))  # doesn't seem to work unless we pass it a windows line ending. Sends command, but no results

		# reads after sending by default so that we can determine if there was a timeout
		if length_to_read == "ALL":
			data = b""
			new_data = "start"
			while new_data not in (b"", None):
				new_data = self.ctd.read(1000)  # if we're expecting quite a lot, then keep reading until we get nothing
				data += new_data
		else:
			data = self.ctd.read(length_to_read)

		response = self._clean(data)

		if "timeout" in response:  # if we got a timeout the first time, then we should be reconnected. Rerun this function and return the results
			return self._send_command(command, length_to_read)
		else:
			return response

	def _clean(self, response):
		return response.decode("utf-8").split("\r\n")  # first element of list should now be the command, but we'll let the caller filter that

	def set_datetime(self):
		datetime_commands = self.command_object.set_datetime()
		for command in datetime_commands:
			logging.log(1, "Setting datetime: {}".format(command))
			self._send_command(command)

	def take_sample(self):
		self.last_sample = self._send_command("TS", length_to_read=1000)
		return self.last_sample

	def _filter_samples_to_data(self,):
		pass

	def sleep(self):
		self._send_command("QS")

	def wake(self):
		return self._send_command(" ", length_to_read=100)  # Send a single character to wake the device, get the response so that we clear the buffer

	def status(self):
		status = self._send_command("DS")
		self.full_model = status[1].split("   ")[0]
		self.serial_number = status[1].split("   ")[1]
		self.battery_voltage = status[2].split(" = ")[1]
		self.sample_number = status[5].split(", ")[0].split(" = ")[1]
		self.is_sampling = True if status[3] == "logging data" else False

		return status

	def check_interrupt(self):
		"""
			Should return True if we're supposed to stop listening or False if we shouldn't
		:return:
		"""
		return False  # for now, we don't have a way to interrupt it, so we'll just return false

	def start_autosample(self, interval=60, realtime="Y", handler=None, no_stop=False):
		"""
			This should set the sampling interval, then turn on autosampling, then just keep reading the line every interval.
			Before reading the line, it should also check for new commands in a command queue, so it can see if it's
			should be doing something else instead.

			We should do this as an event loop, where we create a celery task to check the line. That way, control can flow
			from here and django can do other work in the meantime. Otherwise, we can have a separate script that does
			the standalone django setup so it can access the models and the DB, or we can just do our own inserts since
			it's relatively simple code here.

		:param interval:  How long, in seconds, should the CTD wait between samples
		:param realtime: Two possible values "Y" and "N" indicating whether the CTD should return results as soon as it collects them
		:param handler: This should be a Python function (the actual object, not the name) that takes a list of dicts as its input.
		 				Each dict represents a sample and has keys for "temperature", "pressure", "conductivity",
		 				and "datetime", as appropriate for the CTD model. It'll skip parameters the CTD doesn't collect.
		 				The handler function will be called whenever new results are available and can do things like database input, etc.
		 				If realtime == "Y" then you must provide a handler function.
		:param no_stop: Allows you to tell it to ignore settings if it's already sampling. If no_stop is True, will just
						start listening to new records coming in (if realtime == "Y"). That way, the CTD won't stop sampling
						for any length of time, but will retain prior settings (ignoring the new interval).
		:return:
		"""
		if self.is_sampling and not no_stop:
			self.stop_autosample()  # stop it so we can set the parameters

		if not self.is_sampling:  # will be updated if we successfully stop sampling
			self._send_command(self.command_object.sample_interval(interval))  # set the interval to sample at
			self._send_command("TXREALTIME={}".format(realtime))  # set the interval to sample at
			self._send_command("STARTNOW")  # start sampling

		if realtime == "Y":
			if not handler:  # if they specified realtime data transmission, but didn't provide a handler, abort.
				raise CTDConfigurationError("When transmitting data in realtime, you must provide a handler function that accepts a list of dicts as its argument. See documentation for start_autosample.")

			self.listen(handler, interval)

	def listen(self, handler, interval=60):
		"""
			Continuously polls for new data on the line at interval. Used when autosampling with realtime transmission to
			receive records.

			See documentation for start_autosample for full documentation of these parameters. This function remains
			part of the public API so you can listen on existing sampling if the autosampler is already configured.

			:param handler: (See start_autosample documentation). A functiion to process new records as they are available.
			:param interval: The sampling interval, in seconds.
		:return:
		"""

		while self.check_interrupt() is False:

			data = self.ctd.read(500)
			records = self.find_and_insert_records(self._clean(data))

			handler(records)  # Call the provided handler function to do whatever the caller wants to do with the data

			time.sleep(interval)

	def find_and_insert_records(self, data):
		records = []
		for element in data:
			matches = re.search(self.command_object.record_regex(), element)
			if matches is None:
				continue

			new_model = {}
			if "temperature" in self.command_object.keys:
				new_model["temperature"] = matches.group("temperature")
			else:
				new_model["temperature"] = None

			if "pressure" in self.command_object.keys:
				new_model["pressure"] = matches.group("pressure")
			else:
				new_model["pressure"] = None

			if "conductivity" in self.command_object.keys:
				new_model["conductivity"] = matches.group("conductivity")
			else:
				new_model["conductivity"] = None

			if "datetime" in self.command_object.keys:
				dt_object = datetime.datetime.strptime(str(matches.group("datetime")), "%d %b %Y, %H:%M:%S")
				new_model["datetime"] = dt_object
			else:
				new_model["datetime"] = None

			records.append(new_model)

		return records

	def stop_autosample(self):
		self._send_command("STOP")
		self.status()

		if self.is_sampling is not False:
			raise CTDOperationError("Unable to stop autosampling. If you are starting autosampling, parameters may not be updated")

	def catch_up(self):
		"""
			Meant to pull in any records that are missing on startup of this script - if the autosampler runs in the
			background, then while the script is offline, new data is being stored in flash on the device. This should
			pull in those records.

			NOTE - this command STOPS autosampling if it's running - it must be restarted on its own.
		:return:
		"""
		self.stop_autosample()

		commands = self.command_object.retrieve_samples(0, self.sample_number)
		for command in commands:
			results = self._send_command(command)  # if we have multiple commands, only the later one will have data

		# we now have all the samples and can parse them so that we can insert them.

	def parse_results(self):
		pass

	def __del__(self):
		"""
			Put the CTD to sleep and close the connection
		:return:
		"""
		self.sleep()
		self.ctd.close()


if __name__ == "__main__":

	ctd = CTD()

	# Stop CTD, check for and load old records
	# ctd.catch_up()

	# Set Datetime
	ctd.set_datetime()

	# Start CTD and begin check/load loops
