import csv
import os
import django

os.environ["DJANGO_SETTINGS_MODULE"] = "icefish_backend.settings"
django.setup()

from icefish import models

with open(r"C:\Users\dsx\Desktop\icefish_ctd.csv", 'r') as csvfile:
	import_file = csv.DictReader(csvfile)
	for row in import_file:
		print("Loading")
		ctd = models.CTD()
		ctd.salinity = row["salinity"]
		ctd.pressure = row["pressure"]
		ctd.conductivity = row["conductivity"]
		ctd.temp = row["temp"]
		ctd.dt = row["dt"]
		ctd.server_dt = row["server_dt"]
		ctd.instrument = models.CTDInstrument.objects.first()
		ctd.measured = True
		ctd.save()
