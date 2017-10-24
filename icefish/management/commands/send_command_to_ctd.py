from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	help = 'Listens for new data on the CTD and inserts into the database'

	def add_arguments(self, parser):
		parser.add_argument('--command', nargs='+', type=str, dest="command", default=False,)

	def handle(self, *args, **options):

		# figure out which com port to listen on. If it's passed in as an argument, use that, otherwise use the one in the defined environment variable (CTD code will handle that).
		port = None
		if options['com_port']:
			port = options['com_port'][0]
