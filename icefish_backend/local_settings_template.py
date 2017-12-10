import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


STATIC_URL = '/static/'  # actual value should be something like 'b195-moo-router.usap.gov:8005/static/'
SERVE_ADDRESS = "*:8009"
DEVICE_NAME = "CWS-SILVERFORK"  # in a handful of cases, we might not want to clutter local settings with something (a few utilities that may not be used broadly), we'll look up settings by device name that way - we could grab this from the machine, but not going to

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

# Video Settings

FFMPEG_EXECUTABLE = r"C:\Users\dsx\Downloads\ffmpeg-20150401-git-3c91239-win64-static\bin\ffmpeg.exe"
VIDEO_FOLDERS = {
    r'C:\Users\Nick\Documents\Recorded Live Moo Video': {
        "transcode": True,
        "transcoding_path": r'C:\Code\converted',
        "keep_original": True,
        "extensions": [".asf", ".mkv"]
    },
}

# NCDC Weather data
NCDC_V2_API_KEY = ""  # probably not needed
NCDC_LEGACY_API_KEY = ""  # probably not needed
PERL_BINARY = r"C:\StrawberryPerl\perl\bin\perl.exe"
MAX_DOWNLOAD_RETRIES = 10  # how many times should it retry the download if the first one fails
RETRY_WAIT_TIME = 600  # seconds to wait between attempts to retry

# AUDIO PROCESSING
FLAC_STORAGE_FOLDER = r"H:\flac"  # what is the full path to the place we should convert flac files into?
WAV_STORAGE_FOLDER = r"H:\incoming"
COPY_WAV_TO_TEMP = True  # should we copy the wav file to a local temp file before processing? This is useful when it's on the network and prevents multiple network reads of the same file
COPY_FLAC_TO_TEMP = True
DELETE_WAVS = True  # for testing - we don't want to delete them if we're not positive our logic won't result in weird behavior
TEMPORARY_AUDIO_FOLDER = r"C:\Users\dsx\Dropbox\Antarctica\Audio\temp"
SPECTROGRAM_STORAGE_FOLDER = r"H:\spectrographs"  # where should spectrograph images be stored?
FLAC_BINARY = r""  # path to flac.exe for converting files
SOX_BINARY = r""  # path to sox.exe for creating spectrograms for retroactive data visualization
GENERATE_SPECTROGRAM = True  # set this flag to turn spectrogram generation on or off - meant for CPU scheduling
ARRAY_DATA_MANAGER_BINARY = r""
HYDROPHONE_LOGGING_INTERVAL = 10  # minutes

# SECRETS
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''  # make a long string of letters, punctuation, and numbers between the quoteslike asehp987#ohd^yuinOFIUHBSA*(IUsgdshFMSA)IU

# EMAIL AND ALERTS
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587  # the port email should be sent through
EMAIL_HOST_USER = ''  # username for email sending login
EMAIL_HOST_PASSWORD = ''  # the password for the account to send email through
EMAIL_USE_TLS = True  # specify whether to encrypt the traffic to the email server
SERVER_EMAIL = ''  # the email address to send alerts as

# EMAILS
WARN_EMAILS = [('name', 'email@email.com',), ('name2', 'email2@email.com')]  # who should receive warnings emitted by the application - name and email pairs as python tuples in a list
ERROR_EMAILS = [('name', 'email@email.com',),]  # who should receive errors emitted by the application
ADMINS = ERROR_EMAILS
SUPERCOOLING_EMAILS = [('Paul Cziko', '273@pg.mcmurdo.usap.gov',), ('Paul Cziko', 'pcziko@gmail.com',), ('Nick', 'ultraayla@gmail.com',)]  # who should get alerts when the water is supercooled?
SUPERCOOLING_ALERT_INTERVAL = 120  # how often should alerts be resent when water is supercooled?

# CTD Settings
CTD_DEFAULT_SERIAL = 5062  # which CTD should records be considered as coming from by default? Identify it by serial number here. Replace this if the CTD changes, and add a CTDInstrument object to the database that corresponds to it
CTD_LOGGING_INTERVAL = 90  # how often should the CTD take a sample and have the script monitor it - in seconds
CTD_BAUD_RATE = 4800  # The baud rate of the CTD cable. We're running a long cable, so we need to operate at 4800 baud
CTD_DEFAULT_COM_PORT = "COM3"  # What COM port is the CTD running on when it's plugged in?
CTD_INTERRUPTABLE = False  # should the CTD be run in the mode that lets us send commands in through a side channel while it's logging. False is safer, True is helpful when you need it
CTD_FORCE_SETTINGS = False  # should the CTD be stopped to apply the logging interval and update the time (True), or should we just listen in to logging in progress if it's already logging (False)?
CTD_WEB_API_PUBLIC_TOKEN = "b1c583786a501ee2387f8673adfbd225e3d1ba4f"

# Charting URLs - most items in this section should be prefixed with ICEFISH because they'll integrate in the page with other things
ICEFISH_QUERY_ROOT_URL = "/api/ctd/"
ICEFISH_PROXY_BASE_URL = "//b195-moo-proxy.nicksantos.com"
ICEFISH_HYDROPHONE_PORT = 8010
ICEFISH_CONTROL_PORT = 9070
ICEFISH_REALTIME_CTD = True  # Does this device support realtime CTD data in the browser? Should a loaded page request updates? True if so, False if not

ICEFISH_VIDEO_SERVER_URL = "http://157.132.101.162:1935"

# RABBITMQ Settings
# if you're using the advanced version of the CTD logger that lets you send commands while it's autologging, fill these out
RABBITMQ_USERNAME = ""  # username for rabbitmq - this user should have config privileges on the vhost defined below.
RABBITMQ_PASSWORD = ""  # password for rabbitmq
RABBITMQ_BASE_URL = ""  # Just the IP address or base url of the server. The full RabbitMQ address is constructed by the module
RABBITMQ_VHOST = "moo"  # When you create a virtual host in RabbitMQ, you give it a name. Put that name here