# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import datetime

import arrow

from django.shortcuts import render, render_to_response
from django.http import Http404, HttpResponse
from django.template.loader import get_template
from rest_framework import viewsets

# Create your views here.

from icefish.serializers import CTDSerializer
from icefish import models
from icefish_backend import settings


class CTDViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows viewing of CTD Data
	"""
	serializer_class = CTDSerializer

	def get_queryset(self):

		queryset = models.CTD.objects.all().order_by('-dt')
		beginning_dt = self.request.query_params.get('since', None)
		end_dt = self.request.query_params.get('before', None)
		if beginning_dt is not None:
			filter_dt = datetime.datetime.strptime(beginning_dt, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
			queryset = queryset.filter(dt__gt=filter_dt)
		elif end_dt is None:  # only do a default beginning filter if there's no end filter. Because if they provide an end before the beginning, then whoops!
			# this block tries to go back one day at a time until it accumulates at least settings.ICEFISH_API_MIN_DEFAULT_RECORDS or until it goes back a max of settings.ICEFISH_API_MAX_DEFAULT_DAYS
			# it can still return no records if there aren't any in that many days. This could be simlified to just be a
			# .order_by("-dt").limit(25) or something like that, but at least early on, it's nice if it includes at
			# least a full day, but sometimes the CTD is down, so we need to go back further. This is a compromise.

			filter_dt = arrow.utcnow().shift(days=-1).datetime
			filtered_queryset = queryset.filter(dt__gt=filter_dt)
			num_days_back = 1

			# this next process is slow and would likely be a problem in public APIs - but for now, it's OK to make it smart - especially for testing while we accumulate data
			while len(filtered_queryset) < settings.ICEFISH_API_MIN_DEFAULT_RECORDS and num_days_back < settings.ICEFISH_API_MAX_DEFAULT_DAYS:
				# basically, this condition checks if we have at least the minimum number of records, or we've tried to go back a certain number of days already
				num_days_back += 1
				filtered_queryset = queryset.filter(dt__gt=arrow.utcnow().shift(days=-num_days_back).datetime)
			queryset = filtered_queryset  # we assign this back at the end so we keep queryset clear for repeated attempts

		if end_dt is not None:
			queryset = queryset.filter(dt__lt=datetime.datetime.strptime(end_dt, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc))

		return queryset

def spectrogram_full(request):
	return render_to_response("icefish/spectrogram.django.html")

def chart_full(request):
	return render_to_response("icefish/data.django.html")


def display_spectrogram(request, hydrophone_audio_id):
	"""
		Used to load hydrophone spectrograms and audio from storage without making them static files. Via:
		http://blog.ekini.net/2010/12/28/django-reading-an-image-outside-the-public-accessible-directory-and-displaying-the-image-through-the-browser/
	:param request:
	:param image_id:
	:return:
	"""

	try:
		audio = models.HydrophoneAudio.objects.get(pk=hydrophone_audio_id)
	except models.HydrophoneAudio.DoesNotExist:
		raise Http404("Audio file with that ID does not exist in database. It may be incorrect, or may not have been loaded yet.")
	file = image_id
	filepath = os.path.join(path, file)

	# Here, you put your code to check whether the user has access to this photo or not

	response = HttpResponse(mimetype=mimetypes.guess_type(filepath))
	response['Content-Disposition'] = 'filename="%s"' % smart_str(file)


	response["X-Sendfile"] = filepath
	response['Content-length'] = os.stat(filepath).st_size

	return response