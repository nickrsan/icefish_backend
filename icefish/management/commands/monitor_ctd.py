import logging

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from icefish.models import CTD
from icefish_backend import local_settings

import seabird_ctd

log = logging.getLogger("icefish_ctd")

class Command(BaseCommand):
	help = 'Listens for new data on the CTD and inserts into the database'

	def add_arguments(self, parser):
		parser.add_argument('--com_port', nargs='+', type=str, dest="com_port", default=False,)
		parser.add_argument('--baud', nargs='+', type=int, dest="baud", default=False,)
		parser.add_argument('--interval', nargs='+', type=int, dest="interval", default=False,)
		parser.add_argument('--rabbitmq', nargs='+', type=int, dest="rabbitmq", default=False,)

	def handle(self, *args, **options):

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

		ctd = seabird_ctd.CTD(port, baud=baud, timeout=5,)
		if not ctd.is_sampling:  # if it's not sampling, set the datetime, otherwise, we can't
			ctd.set_datetime()
		else:
			log.info("CTD already logging. Listening in")

		log.debug("Setting up interrupt handler")
		# ctd.setup_interrupt(server, local_settings.RABBITMQ_USERNAME, local_settings.RABBITMQ_PASSWORD, local_settings.RABBITMQ_VHOST)  # set it up to receive commands from rabbitmq once autosampling starts
		log.info("Starting automatic logger")
		ctd.start_autosample(interval, realtime="Y", handler=handle_records, no_stop=True)


def handle_records(records):
	log.info("Sample received. Inserting records.")
	for record in records:
		new_model = CTD()
		new_model.temp = record["temperature"]
		new_model.conductivity = record["conductivity"]
		new_model.pressure = record["pressure"]
		new_model.datetime = record["datetime"]
		new_model.server_datetime = timezone.now()

		new_model.save()
		log.debug("Record saved")

	log.error("Test")