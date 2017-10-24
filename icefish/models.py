# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.

class CTD(models.Model):
	temp = models.FloatField()
	pressure = models.FloatField()
	conductivity = models.FloatField(blank=True, null=True)
	datetime = models.DateTimeField()
	server_datetime = models.DateTimeField()  # the server reading the data's timestamp
	measured = models.BooleanField(default=True)  # used as a flag if we interpolate any values. If measured == True, then it's direct off the CTD
