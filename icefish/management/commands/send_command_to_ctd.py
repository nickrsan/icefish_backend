import os

from django.core.management.base import BaseCommand, CommandError

from icefish_backend import local_settings

import pika
from pika import PlainCredentials

class Command(BaseCommand):
	help = 'Sends commands to the CTD while autosampling'

	def add_arguments(self, parser):
		parser.add_argument('--server', nargs='+', type=str, dest="server", default=False,)
		parser.add_argument('--queue', nargs='+', type=str, dest="queue", default=False,)
		parser.add_argument('--command', nargs='+', type=str, dest="command", default=True,)

	def handle(self, *args, **options):

		# Figure out what COM port the CTD runs on - it'll be the name of the queue in RabbitMQ
		queue = None
		if options['queue']:
			queue = options['queue'][0]
		elif hasattr(local_settings, "CTD_DEFAULT_COM_PORT") and local_settings.CTD_DEFAULT_COM_PORT not in (None, ""):  # if the COM port is defined in settings, use that
			queue = local_settings.CTD_DEFAULT_COM_PORT  # often times, it's defined as blank in the template, so we'll exclude that in the conditional above. Only use this if it's truly defined
		elif 'SEABIRD_CTD_PORT' in os.environ:  # otherwise, try the environment variable
			queue = os.environ['SEABIRD_CTD_PORT']
		else:
			raise ValueError("Can't find COM port for CTD. It should be passed either for the --queue variable here, be defined in local_settings.py, or set as an environment variable")

		server = None
		if options['server']:
			server = options['server'][0]
		else:
			server = local_settings.RABBITMQ_BASE_URL

		command = options['command'][0]

		connection = pika.BlockingConnection(pika.ConnectionParameters(host=server,
																	   virtual_host=local_settings.RABBITMQ_VHOST,
																	   credentials=PlainCredentials(local_settings.RABBITMQ_USERNAME, local_settings.RABBITMQ_PASSWORD)))
		channel = connection.channel()

		channel.queue_declare(queue=queue)

		channel.basic_publish(exchange='seabird',
							  routing_key='seabird',
							  body=command)
		print("Sent {}".format(command))
		print("For results of the command, if any, see the console of the CTD reader script.")
		connection.close()
