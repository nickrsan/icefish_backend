import os

from django.core.management.base import BaseCommand, CommandError

from icefish_backend import local_settings

class Command(BaseCommand):
	help = 'Uploads the latest image for a waypoint to MOO-CONUS'

	def add_arguments(self, parser):
		parser.add_argument('--waypoint', nargs='+', type=str, dest="waypoint", default=True,)