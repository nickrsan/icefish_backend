import os
import glob
import tempfile
import time
import platform
import logging

from icefish_backend import settings

import arrow
from PIL import Image, ImageFile
import pysftp

from django.core.management.base import BaseCommand, CommandError

from icefish_backend import local_settings

log = logging.getLogger("icefish")

def get_time(file_path):
	if platform.system() == 'Windows':
		return os.path.getmtime(file_path)
	else:
		stat = os.stat(file_path)  # Mac
		try:
			return stat.st_birthtime
		except AttributeError:
			# We're probably on Linux. No easy way to get creation dates here, so we'll take the last modified date
			# and subtract the file length, which should be sufficient
			return stat.st_mtime


def get_newest_image(folder):
	"""
		Inspiration from https://stackoverflow.com/questions/39327032/how-to-get-the-latest-file-in-a-folder-using-python
	:param folder:
	:return:
	"""
	list_of_files = glob.glob(os.path.join(folder, "*.jpg"))  # * means all if need specific format then *.csv
	return max(list_of_files, key=get_time)


class Command(BaseCommand):
	help = 'Uploads the latest image for a waypoint to MOO-CONUS'

	def add_arguments(self, parser):
		parser.add_argument('--waypoint', nargs='+', type=str, dest="waypoint")

	def prep_for_upload(self, image_name, name, params):
		base_name = os.path.basename(image_name).split(".")[0]
		image = Image.open(image_name)
		output_image = tempfile.mktemp("_{}.jpg".format(name), "MOO_{}_".format(base_name))

		resized_image = image.resize((params["resize_x"], params["resize_y"]))
		resized_image.save(output_image, quality=params["resize_quality"])

		return output_image

	def send_image(self, image_path, remote_folder):
		cnopts = pysftp.CnOpts()
		cnopts.hostkeys = None  # disable host key checking
		with pysftp.Connection(settings.REMOTE_SERVER_ADDRESS, port=settings.REMOTE_SERVER_SSH_PORT, username=settings.REMOTE_SERVER_USER, password=settings.REMOTE_SERVER_PASSWORD, cnopts=cnopts) as sftp:
			base_remote_path = "{}/{}".format(settings.REMOTE_SERVER_IMAGE_FOLDER, remote_folder)
			if not sftp.exists(base_remote_path):  # make sure the folder exists
				sftp.mkdir(base_remote_path)

			remote_path = "{}/{}".format(base_remote_path, arrow.utcnow().year)
			if not sftp.exists(remote_path):
				sftp.mkdir(remote_path)

			with sftp.cd(remote_path):  # temporarily chdir to public
				sftp.put(image_path)  # send the image

				base_name = os.path.basename(image_path)
				log.debug("cp \"{}/{}\" {}/current.jpg".format(remote_path, base_name, base_remote_path))
				sftp.execute("cp \"{}/{}\" {}/current.jpg".format(remote_path, base_name, base_remote_path))  # remote copy the file to current.jpg to upload it only once

	def handle(self, *args, **options):

		if options['waypoint']:
			waypoints = [options['waypoint'][0], ]
		else:
			waypoints = [waypoint for waypoint in settings.WAYPOINTS]

		ImageFile.LOAD_TRUNCATED_IMAGES = True  # we have lots of "damaged" images - this lets it read through and use them
		waypoint_last_update = {}

		sleep_time = min([waypoint["update_interval"] for waypoint in waypoints]) # check for new images at the minimum interval specified for all the waypoints

		while True:
			log.debug("Checking for images")
			for waypoint in waypoints:
				current_time = arrow.utcnow()
				waypoint_info = settings.WAYPOINTS[waypoint]
				if waypoint not in waypoint_last_update \
					or (current_time - waypoint_last_update[waypoint]).seconds > waypoint_info["update_interval"]:
					# the timer runs every ten seconds - only if we've gone more than the update interval for this image since the
					# last upload does this actually run

					log.info("Sending new image to remote for waypoint {}".format(waypoint))
					base_folder = os.path.join(settings.WAYPOINT_IMAGE_FOLDER, waypoint_info["base_path"])
					new_image = get_newest_image(base_folder)
					log.debug("Newest image is {}".format(new_image))
					try:
						image_to_upload = self.prep_for_upload(new_image, waypoint, waypoint_info)
						log.info("Sending {}".format(image_to_upload))
						self.send_image(image_to_upload, waypoint_info["remote_path"])

						os.remove(image_to_upload)  # remove the temporary file

						# now, move the image to the uploaded folder
						new_path = os.path.join(base_folder, "uploaded")
						image_name = os.path.basename(new_image)
						os.rename(new_image, os.path.join(new_path, image_name))
						waypoint_last_update[waypoint] = current_time  # set the last update time so we wait the right amount later on
					except OSError:
						log.warning("Failed to read image file")
					except IOError:
						log.warning("Failed to read image file")
						# we want to log these issues, but roll on through them - it seems to have issues with network drive, might need to force a local copy, then read

			time.sleep(sleep_time)
