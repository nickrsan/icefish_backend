import logging

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from icefish.models import CTD, CTDInstrument
from icefish_backend import local_settings
from icefish import alerts

import seabird_ctd

try:
	import pika
except ImportError:
	pika = None

log = logging.getLogger("icefish.ctd")

instrument = None

class Command(BaseCommand):
	help = 'Listens for new data on the CTD and inserts into the database'

	def add_arguments(self, parser):
		parser.add_argument('--com_port', nargs='+', type=str, dest="com_port", default=False,)
		parser.add_argument('--baud', nargs='+', type=int, dest="baud", default=False,)
		parser.add_argument('--interval', nargs='+', type=int, dest="interval", default=False,)
		parser.add_argument('--rabbitmq', nargs='+', type=int, dest="rabbitmq", default=False,)

	def handle(self, *args, **options):

		global instrument

		# figure out which com port to listen on. If it's passed in as an argument, use that, otherwise use the one in the defined environment variable (CTD code will handle that).
		port = None
		if options['com_port']:
			port = options['com_port'][0]
		elif hasattr(local_settings, "CTD_DEFAULT_COM_PORT"):  # if the COM port is defined in settings
			port = local_settings.CTD_DEFAULT_COM_PORT
			# if not defined here, the seabird code pulls it from the environment variable SEABIRD_CTD_PORT

		if options['interval']:
			interval = options['interval'][0]
		else:
			interval = local_settings.CTD_LOGGING_INTERVAL

		if options['baud']:
			baud = options['baud'][0]
		else:
			baud = local_settings.CTD_BAUD_RATE  # we're using 4800 baud because the cable is very long

		if options['rabbitmq']:
			server = options['rabbitmq'][0]
		else:
			server = local_settings.RABBITMQ_BASE_URL

		ctd = seabird_ctd.CTD(port, baud=baud)
		if not ctd.is_sampling:  # if it's not sampling, set the datetime, otherwise, we can't
			ctd.set_datetime()
		else:
			log.info("CTD already logging. Listening in")

		if pika and local_settings.CTD_INTERRUPTABLE:  # if pika isn't installed, run anyway, just, do the normal loop
			log.debug("Setting up interrupt handler")
			ctd.setup_interrupt(server, local_settings.RABBITMQ_USERNAME, local_settings.RABBITMQ_PASSWORD, local_settings.RABBITMQ_VHOST)  # set it up to receive commands from rabbitmq once autosampling starts
		log.info("Starting automatic logger")

		instrument = CTDInstrument.objects.get(serial=ctd.serial_number)  # right now, get the *only* object in this table - in the future, when a new instrument goes down, we'd need to update this

		ctd.start_autosample(interval, realtime="Y", handler=handle_records, no_stop=not local_settings.CTD_FORCE_SETTINGS)

def handle_records(records, return_alerts=False):
	"""

	:param records:
	:param return_alerts: a setting for testing - returns the status of the alerts so we can determine behavior
	:return:
	"""
	log.info("Sample received. Inserting records.")
	for record in records:
		new_model = CTD()
		new_model.temp = record["temperature"]
		if "conductivity" in record:
			new_model.conductivity = record["conductivity"]
		new_model.pressure = record["pressure"]
		if "salinity" in record:
			new_model.salinity = record["salinity"]
		new_model.dt = record["datetime"]
		new_model.server_dt = timezone.now()
		new_model.instrument = instrument

		new_model.save()
		log.debug("Record saved")

	try:
		if "salinity" not in record or "pressure" not in record:  # can't do these calculations and alerts without those values
			return

		new_model  # make sure the loop ran
		actions = alerts.supercooling_alerts(new_model)  # only run this for the last record we insert so that it's current
	except NameError:  # just making sure new_model is defined before use
		pass

	if return_alerts:  # mostly used for unit tests
		return actions

