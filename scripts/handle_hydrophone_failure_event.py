import logging
import os

import django
from django.core.mail import send_mail

os.environ["DJANGO_SETTINGS_MODULE"] = "icefish_backend.settings"
django.setup()

from icefish_backend import local_settings
from icefish.data_management.hydrophone import start_array_data_manager, find_and_kill_array_data_manager

log = logging.getLogger("icefish.audio")

if __name__ == "__main__":
	log.warning("Hydrophone failure detected. Attempting restart")
	sent = send_mail('ADM Failed', 'Attempting to restart',
					 local_settings.EMAIL_HOST_USER,
					 ["pcziko@gmail.com",],
					 fail_silently=False
					 )
	if sent == 0:
		log.warning("Emails not sent to notify Paul of ADM failure")
		
	try:
		find_and_kill_array_data_manager()
	except:
		log.warning("Array data manager kill was unsuccessful")

	try:
		start_array_data_manager()
	except:
		log.warning("Array data manager start was unsuccessful")