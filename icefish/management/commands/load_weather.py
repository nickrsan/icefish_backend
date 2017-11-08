import logging
import datetime

from django.core.management.base import BaseCommand

from icefish.data_management import ncdc
from icefish_backend import local_settings

log = logging.getLogger("icefish.ncdc")

class Command(BaseCommand):
	help = 'Load McMurdo Weather data from NCDC'

	def add_arguments(self, parser):
		pass

	def handle(self, *args, **options):
		log.info("Loading Weather data")
		ncdc.update_weather_data()

