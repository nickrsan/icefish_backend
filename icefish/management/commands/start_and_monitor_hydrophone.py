import logging
import time

from django.core.management.base import BaseCommand

from icefish.data_management.hydrophone import start_array_data_manager, check_recent_hydrophone_data

log = logging.getLogger("icefish.audio")


class Command(BaseCommand):
	help = 'Starts Array Data Manager and ensures it stays running'

	def handle(self, *args, **options):
		start_array_data_manager()
		while True:
			time.sleep(600)
			check_recent_hydrophone_data()  # if there's nothing recent, this kills the current application and starts it up again