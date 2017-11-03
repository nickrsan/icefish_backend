import logging

from django.core.management.base import BaseCommand

from icefish import data_management
from icefish_backend import local_settings

log = logging.getLogger("icefish.audio")

class Command(BaseCommand):
	help = 'Check for new hydrophone data, process it to FLAC and make a spectrograph'

	def add_arguments(self, parser):
		parser.add_argument('--incoming_folder', nargs='+', type=str, dest="incoming_folder", default=False,)
		parser.add_argument('--output_folder', nargs='+', type=str, dest="output_folder", default=False,)

	def handle(self, *args, **options):
		incoming_folder = None
		if options['incoming_folder']:
			incoming_folder = options['incoming_folder'][0]
		elif hasattr(local_settings, "WAV_STORAGE_FOLDER"):  # if the COM port is defined in settings
			incoming_folder = local_settings.WAV_STORAGE_FOLDER
		else:
			raise ValueError("The folder to check for data is not defined either via argument or via local_settings.py")

		output_folder = None
		if options['output_folder']:
			incoming_folder = options['output_folder'][0]
		elif hasattr(local_settings, "FLAC_STORAGE_FOLDER"):  # if the COM port is defined in settings
			output_folder = local_settings.FLAC_STORAGE_FOLDER
		else:
			raise ValueError("The folder to save audio data out to is not defined either via argument or via local_settings.py")

		data_management.hydrophone_pipeline(inbound_folder=incoming_folder, outbound_folder=output_folder)