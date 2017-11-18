import logging

import arrow
from django.core.mail import send_mail

from icefish_backend import local_settings

is_supercooled = None  # track the last item so that we can fire off an alert when it *stops* being supercooled
last_supercooling_alert = None

log = logging.getLogger("icefish.alerts")

def supercooling_alerts(ctd_record):
	"""
		Fires off appropriate alerts for this record, based upon previous status of the water,
		current status of the water, and when the last alert was sent
	:param ctd_record:
	:return:
	"""
	global is_supercooled, last_supercooling_alert

	if local_settings.SUPERCOOLING_DEBUG:
		emails = [person[1] for person in local_settings.SUPERCOOLING_DEBUG_EMAILS]
	else:
		emails = [person[1] for person in local_settings.SUPERCOOLING_EMAILS]

	log.debug("Checking for relevant email alerts to send")

	if ctd_record.is_supercooled:
		log.debug("Water is supercooled")
		current_time = arrow.utcnow()
		if last_supercooling_alert is None or current_time > last_supercooling_alert.shift(minutes=local_settings.SUPERCOOLING_ALERT_INTERVAL):
			log.debug("Emailing {} that supercooling has started".format(emails))
			sent = send_mail('SUPERCOOLING STARTED: Jetty water is supercooled',
					  'Jetty water is supercooled! Here is the information from the most'
					  'recent measurement: \n\nTemperature: {}\nFreezing Point: {}\n'
					  'Pressure: {}\nConductivity: {}\nSalinity: {}\nTime Measured: {}'.format(
						  ctd_record.temp, ctd_record.freezing_point, ctd_record.pressure,
						  ctd_record.conductivity, ctd_record.salinity, ctd_record.dt
					  ),
					  local_settings.EMAIL_HOST_USER,
					  emails,
					  fail_silently=False
					  )
			if sent == 0:
				raise RuntimeError("Emails not sent to notify of supercooling")
			last_supercooling_alert = arrow.utcnow()
			is_supercooled = True  # keep track so we can alert when it stops
			return {"sent": True, "status": "supercooled"}
		return {"sent": False, "status": "supercooled"}
	elif is_supercooled is True:  # so, now it's if the last measurement was supercooled, but this one isn't
		log.debug("Water was supercooled, but isn't anymore. Sending cancellation alert")
		is_supercooled = False
		last_supercooling_alert = None  # null these both out

		log.debug("Emailing {} that supercooling has ended".format(emails))
		sent = send_mail('SUPERCOOLING ENDED: Jetty water is no longer supercooled',
				  'Jetty water is no longer supercooled. The most recent measurement was {}'
				  'and the freezing temperature is {}.'.format(ctd_record.temp, ctd_record.freezing_point),
				  local_settings.EMAIL_HOST_USER,
				  emails,
				  fail_silently=False
				  )
		if sent == 0:
			raise RuntimeError("Emails not sent to notify of end of supercooling")
		return {"sent": True, "status": "normal"}
	return {"sent": False, "status": "normal"}
