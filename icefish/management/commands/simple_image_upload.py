import os
import tempfile
import time
import platform
import logging
import subprocess
import traceback

from icefish_backend import settings

import arrow
from PIL import Image, ImageFile
import pysftp

from django.core.management.base import BaseCommand, CommandError

from icefish_backend import local_settings

####
#
# NEED TO MAKE IT IGNORE IMAGES THAT START WITH int_19700101 - these happen when the
# camera forgets what time it is (probably a reboot). Either ignore images, or
# overwrite on move. These should be the only files whose names won't be unique. Also
# Don't have it check which is newest if length of images found is 1. Also, don't use
# glob to find images - just use listdir and a comprehension in python to filter to 
# jpgs.
####


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
	list_of_files = os.listdir(os.path.join(folder))  # get all the files in the folder first
	only_jpgs = [filename for filename in list_of_files if filename.endswith("jpg")]  # doing this instead of glob because I think globbing had some performance issues on windows/networks

	# this step does two things - first, it adds back in the full folder path, and it filters out
	# bad images that had date in name from 1970 after camera restarts - causes many problems and network load
	final_candidates = [os.path.join(folder, filename) for filename in only_jpgs if not filename.startswith("int_1970")]

	# return the single image with the latest time, returning None if we have no images for any reason
	if len(final_candidates) is 0:
		return None

	return max(final_candidates, key=get_time)


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

	def send_image(self, image_path, remote_folder, sftp):
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

		# if it's on the network, set it up so the service version can connect to the files
		if settings.WAYPOINT_IMAGE_FOLDER.startswith(r"\\"):
			try:
				connect_command = 'NET USE {} /User:{} "{}"'.format(settings.WAYPOINT_IMAGE_FOLDER, settings.WAYPOINT_IMAGE_USERNAME, settings.WAYPOINT_IMAGE_PASSWORD)
				subprocess.check_call(connect_command, stdout=subprocess.PIPE, shell=True)
			except subprocess.CalledProcessError:
				log.warning("Failed to connect network drive for images. This can be ignored if running interactively and drives are mapped, but should be noted if this crops up from the service")
			
		ImageFile.LOAD_TRUNCATED_IMAGES = True  # we have lots of "damaged" images - this lets it read through and use them
		waypoint_last_update = {}

		sleep_time = min([settings.WAYPOINTS[waypoint]["update_interval"] for waypoint in waypoints]) # check for new images at the minimum interval specified for all the waypoints

		while True:
			log.debug("Checking for images")

			# load the SFTP connection for every update check
			cnopts = pysftp.CnOpts()
			cnopts.hostkeys = None  # disable host key checking
			with pysftp.Connection(settings.REMOTE_SERVER_ADDRESS, port=settings.REMOTE_SERVER_SSH_PORT,
								   username=settings.REMOTE_SERVER_USER, password=settings.REMOTE_SERVER_PASSWORD,
								   cnopts=cnopts) as sftp:
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

						if not os.path.exists(new_image):  # if it returns empty
							log.debug("Skipping upload - no valid image to upload")
							continue
						else:
							log.debug("Newest image is {}".format(new_image))

						try:
							image_to_upload = self.prep_for_upload(new_image, waypoint, waypoint_info)
							log.info("Sending {}".format(image_to_upload))
							try:
								self.send_image(image_to_upload, waypoint_info["remote_path"], sftp)
								
								# now, move the image to the uploaded folder
								new_path = os.path.join(base_folder, "uploaded")
								image_name = os.path.basename(new_image)
								os.rename(new_image, os.path.join(new_path, image_name))
								waypoint_last_update[waypoint] = current_time  # set the last update time so we wait the right amount later on
							finally:  # always remove the temporary file, but it won't catch a failure after it's created, but before this block is entered
								os.remove(image_to_upload)  # remove the temporary file
						except OSError:
							log.warning(traceback.format_exc())
							log.warning("Failed to work with image file - check the permissions on the uploading user's access to the folder this image is uploading into, and check on the images themselves.")
						except IOError:
							log.warning(traceback.format_exc())
							log.warning("Failed to read image file")
							# we want to log these issues, but roll on through them - it seems to have issues with network drive, might need to force a local copy, then read
			
			log.info("Done with sending. Sleeping for {} seconds".format(sleep_time))
			time.sleep(sleep_time)
