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

		# figure out which com port to listen on. If it's passed in as an argument, use that, otherwise use the one in the defined environment variable (CTD code will handle that).

		queue = None
		if options['queue']:
			queue = options['queue'][0]
		else:
			queue = os.environ['SEABIRD_CTD_PORT']

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
		connection.close()
