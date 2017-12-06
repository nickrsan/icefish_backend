import os
import logging
import subprocess
import time
import psutil

from django.core.management.base import BaseCommand

from icefish_backend import settings

log = logging.getLogger("icefish.audio")

def start_array_data_manager():
	adm_process = subprocess.Popen([settings.ARRAY_DATA_MANAGER_BINARY])  # run array data manager - don't wait for it to complete
	time.sleep(5)  # wait for the window to open before continuing
	log.info("Starting Array Data Manager - if this is a new installation, change the write-path")
	ahk_result = subprocess.check_call([settings.HYDROPHONE_INITIALIZATION_BINARY, settings.WAV_STORAGE_FOLDER, settings.HYDROPHONE_LOGGING_INTERVAL])  # run the autohotkey script that sets up and starts recording
	time.sleep(2)

def check_recent_hydrophone_data(folder=settings.WAV_STORAGE_FOLDER):
	if "ArrayDataManager.exe" not in {p.name(): p.info for p in psutil.process_iter(attrs=['pid'])}:
		start_array_data_manager()

	data_to_load = [filename for filename in settings.WAV_STORAGE_FOLDER if filename.endswith(".wav")]
	for wav_file in data_to_load:
		pass
		## STILL IN PROGRESS
	# check latest date on files in incoming directory
		# if > 10 minutes ago:
		#	kill ADM process
		#	start ADM process
		#	wait a moment
		#	start autohotkey script to initialize collection


class Command(BaseCommand):
	help = 'Starts Array Data Manager and ensures it stays running'

	def handle(self, *args, **options):
		start_array_data_manager()