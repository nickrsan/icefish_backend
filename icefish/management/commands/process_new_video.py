import logging

from django.core.management.base import BaseCommand

from icefish import data_management
from icefish_backend import local_settings

log = logging.getLogger("icefish.video")

class Command(BaseCommand):
	help = 'Check for new video data, process it to MP4, if desired, and load into database'

	def add_arguments(self, parser):
		parser.add_argument('--remove_bottom', nargs='+', type=str, dest="remove_bottom", default=False,)
		parser.add_argument('--delete_existing', nargs='+', type=str, dest="delete_existing", default=False,)

	def handle(self, *args, **options):
		remove_bottom = None
		if options['remove_bottom']:
			remove_bottom = True if options['remove_bottom'][0] == "True" else False
		else:
			remove_bottom = False

		delete_existing = None
		if options['delete_existing']:
			delete_existing = True if options['delete_existing'][0] == "True" else False
		else:
			delete_existing = False

		data_management.video_pipeline(remove_bottom=remove_bottom, remove_existing=delete_existing)