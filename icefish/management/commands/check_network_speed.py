"""
	Runs an iperf test, checking network speed - requires a computer on the other end hosting an iperf server.
	Fires off an alert if average speed is below a certain threshold.
"""

import subprocess
import re
import logging
import datetime

from django.core.management.base import BaseCommand, CommandError

IPERF_EXE = r"C:\Users\dsx\Downloads\iperf-3.1.3-win64\iperf3.exe"
REMOTE_SERVER = r"157.132.104.177"
MIN_SPEED = 40  # below this, we fire an alert - all speeds in Mbps
DEFAULT_DURATION = "20"  # seconds to run the test for

log = logging.getLogger("icefish.heartbeat")

class Command(BaseCommand):
	help = 'Listens for new data on the CTD and inserts into the database'

	def add_arguments(self, parser):
		pass

	def handle(self, *args, **options):
		run_test()


def run_test(server=REMOTE_SERVER, iperf=IPERF_EXE, alert_threshold=MIN_SPEED, duration=DEFAULT_DURATION):
	"""
		A simple, completely not elegant function that runs an iperf test and fires off a warning (including email) if it's below a threshold
	:param server:
	:param iperf:
	:param alert_threshold:
	:param duration:
	:return:
	"""
	command = [iperf, "-c", server, "-t", duration]
	log.debug("Running Iperf: Command is {}".format(command))
	results = subprocess.run(command, check=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
	lines = results.split("\n")  # get each line
	for index, line in enumerate(lines):   # iterate through to find the main line indicating the results
		if line.startswith("-"):  # that's the only one that starts with a hyphen
			break

	mb_finder = re.match(".*?(\d+.\d+) Mbits/sec.*", lines[index+2])  # two lines below the hyphen line is the line with the results data. Use that and find the rate in Mbps
	speed = float(mb_finder.group(1))
	if speed < alert_threshold:  # compare it to our theshold and fire alerts as necessary
		if speed * 2 < alert_threshold:  # if we're *really* slow
			log.error("ALERT: Very slow connection speed during speedtest! Speed was {} Mbps. Time is {}".format(speed, datetime.datetime.utcnow()))
		else:
			log.warning("ALERT:Slow speed during speedtest. Speed was {} and threshold is {}. Time is {}".format(speed, alert_threshold, datetime.datetime.utcnow()))
	else:
		log.debug("Speed of {} found".format(speed))

