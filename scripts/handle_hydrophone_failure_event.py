import logging

from icefish.data_management.hydrophone import start_array_data_manager, find_and_kill_array_data_manager

log = logging.getLogger("icefish.audio")

if __name__ == "__main__":
	log.warning("Hydrophone failure detected. Attempting restart")
	find_and_kill_array_data_manager()
	start_array_data_manager()