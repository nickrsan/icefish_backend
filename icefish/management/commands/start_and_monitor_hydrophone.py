import os
import logging
import subprocess
import time
import psutil
import signal

import arrow

from django.core.management.base import BaseCommand

from icefish_backend import settings
from icefish.models import HydrophoneAudio

log = logging.getLogger("icefish.audio")

def start_array_data_manager():
	adm_process = subprocess.Popen([settings.ARRAY_DATA_MANAGER_BINARY])  # run array data manager - don't wait for it to complete
	time.sleep(5)  # wait for the window to open before continuing
	log.info("Starting Array Data Manager - if this is a new installation, change the write-path")
	ahk_result = subprocess.check_call([settings.HYDROPHONE_LOCAL_INITIALIZATION_BINARY, settings.WAV_STORAGE_FOLDER, str(settings.HYDROPHONE_LOGGING_INTERVAL)])  # run the autohotkey script that sets up and starts recording

def check_recent_hydrophone_data(folder=settings.WAV_STORAGE_FOLDER):
	if "ArrayDataManager.exe" not in {p.name(): p.info for p in psutil.process_iter(attrs=['pid'])}:
		start_array_data_manager()

	data_to_load = [filename for filename in folder if filename.endswith(".wav")]
	for wav_file in data_to_load:
		audio = HydrophoneAudio()
		audio.wav = wav_file
		start_time = audio.get_start_time()

		if (arrow.get() - start_time).total_seconds() < 660:  # check for an 11 minute threshold to give it some breathing room
			break  # we have one that's currently being written, or was recently - leave it all alone
	else:
		# ruh roh - no hydrophone data being logged. Kill ADM and reinitialize
		find_and_kill_array_data_manager()
		start_array_data_manager()

def find_and_kill_array_data_manager():
	running_processes = {p.name(): p.info for p in psutil.process_iter(attrs=['pid'])}
	pid = running_processes["ArrayDataMgr.exe"]['pid']
	try:
		kill_process(pid)
	except RuntimeError:
		raise RuntimeError("Failed to kill ArrayDataMgr.exe - please check on the server - it's possible a new copy was still able to start")

def kill_process(pid, sig=signal.SIGTERM, timeout=60):
	"""Kill a process tree (including grandchildren) with signal
	"sig" and return a (gone, still_alive) tuple.
	"on_terminate", if specified, is a callabck function which is
	called as soon as a child terminates.
	"""
	if pid == os.getpid():
		raise RuntimeError("I refuse to kill myself")

	process = psutil.Process(pid)
	process.send_signal(sig)
	gone, alive = psutil.wait_procs([process], timeout=timeout)

	if pid not in gone:
		raise RuntimeError("Failed to kill process!")

class Command(BaseCommand):
	help = 'Starts Array Data Manager and ensures it stays running'

	def handle(self, *args, **options):
		start_array_data_manager()
		while True:
			time.sleep(600)
			check_recent_hydrophone_data()  # if there's nothing recent, this kills the current application and starts it up again