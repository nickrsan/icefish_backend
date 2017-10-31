import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

#Paths and databases
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # leave this line alone
DB_NAME = "icefishdb"  # replace with the name of your database on the server.
DB_SCHEMA = "icefish_backend"  # replace with the name of the schema you created, if using postgres
DATABASES = {
	'default': {  # these database settings assume you're connecting to a Postgres database. If you'll use something else, consult the Django documentation
		'ENGINE': 'django.db.backends.postgresql',  # this is for Postgres - if you'll use something else like MySQL, consult Django documentation
		'HOST': '127.0.0.1',  # the IP address or publicly accessible base URL of the database. If you're running the database server on the same computer as the web server, this value is correct already
		'PORT': '5432',  # the port the database runs on. This value is the default for Postgres
		'NAME': DB_NAME,  # no need to change, defined above
		'USER': 'mydatabaseuser',  # replace with the username for your database
		'PASSWORD': 'mypassword',  # replace with the password for your database
		'OPTIONS': {  # you don't need to modify this line or the next one *if* you're using PostgreSQL
			'options': '-c search_path={}'.format(DB_SCHEMA)
		},
	}
}

# FLAC
FLAC_STORAGE_FOLDER = r"H:\flac"  # what is the full path to the place we should convert flac files into?
FLAC_EXECUTABLE_PATH = r""  # Where is the flac utlity executable located (full path)

# SECRETS
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''  # make a long string of letters, punctuation, and numbers between the quoteslike asehp987#ohd^yuinOFIUHBSA*(IUsgdshFMSA)IU

# EMAIL AND ALERTS
EMAIL_HOST = 'mail.google.com'  # the server to send email through - using gmail as a default, change it for other mail providers
EMAIL_PORT = 587  # the port email should be sent through
EMAIL_HOST_USER = ''  # username for email sending login
EMAIL_HOST_PASSWORD = ''  # the password for the account to send email through
EMAIL_USE_TLS = True  # specify whether to encrypt the traffic to the email server
SERVER_EMAIL = ''  # the email address to send alerts as

# EMAILS
WARN_EMAILS = [('name', 'email@email.com',), ('name2', 'email2@email.com')]  # who should receive warnings emitted by the application - name and email pairs as python tuples in a list
ERROR_EMAILS = [('name', 'email@email.com',),]  # who should receive errors emitted by the application
ADMINS = ERROR_EMAILS

# CTD Settings
CTD_LOGGING_INTERVAL = 90  # how often should the CTD take a sample and have the script monitor it - in seconds
CTD_BAUD_RATE = 4800  # The baud rate of the CTD cable. We're running a long cable, so we need to operate at 4800 baud
CTD_DEFAULT_COM_PORT = "COM6"  # What COM port is the CTD running on when it's plugged in?

# FLAC settings
FLAC_BINARY = ""  # path to flac.exe for converting files

# RABBITMQ Settings
# if you're using the advanced version of the CTD logger that lets you send commands while it's autologging, fill these out
RABBITMQ_USERNAME = ""  # username for rabbitmq - this user should have config privileges on the vhost defined below.
RABBITMQ_PASSWORD = ""  # password for rabbitmq
RABBITMQ_BASE_URL = ""  # Just the IP address or base url of the server. The full RabbitMQ address is constructed by the module
RABBITMQ_VHOST = "moo"  # When you create a virtual host in RabbitMQ, you give it a name. Put that name here