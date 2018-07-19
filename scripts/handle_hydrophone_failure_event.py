import logging
import os

import django

os.environ["DJANGO_SETTINGS_MODULE"] = "icefish_backend.settings"
django.setup()

from icefish.data_management.hydrophone import start_array_data_manager, find_and_kill_array_data_manager

log = logging.getLogger("icefish.audio")

if __name__ == "__main__":
	log.warning("Hydrophone failure detected. Attempting restart")
	try:
		find_and_kill_array_data_manager()
	except:
		log.warning("Array data manager kill was unsuccessful")

	try:
		start_array_data_manager()
	except:
		log.warning("Array data manager start was unsuccessful")