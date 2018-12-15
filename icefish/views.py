# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import datetime
import mimetypes
import logging

import arrow

from django.shortcuts import render, render_to_response
from django.http import Http404, HttpResponse
from django.utils.encoding import smart_str
from django.template.loader import get_template
from rest_framework import viewsets
from wsgiref.util import FileWrapper

# Create your views here.

from icefish.serializers import CTDSerializer
from icefish import models
from icefish_backend import settings

log=logging.getLogger("icefish.views")

class CTDViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows viewing of CTD Data
	"""
	serializer_class = CTDSerializer

	def make_datetime(self, time_string):
		"""
			Takes the time passed to the API and tries a few supported format strings against it until it gets one that works
			or runs out of format strings to try, in which case it raises ValueError. Returns a datetime object matching the
			string value if successful.
		:param time_string: a string time value to parse to a datetime object
		:return: datetime.datetime matching the passed in string
		"""
		date_formats = ["%Y-%m-%dT%H:%M:%SZ",
						"%Y-%m-%dT%H:%M:%S.%fZ"]  # tries these in order - some of our times may have microseconds, and I don't see a way to make it optional

		for format_string in date_formats:
			try:
				dt_object = datetime.datetime.strptime(time_string, format_string).replace(tzinfo=datetime.timezone.utc)
			except ValueError:
				continue
			break
		else:
			raise ValueError("Couldn't find a matching format string for the supplied datetime. Allowed formats are {}".format(date_formats))

		return dt_object

	def get_queryset(self):
		"""
			Primary function that determines API results. By default returns the last day or so, but takes parameters
			"since" and "before" that allow specification of datetime values (in formats supported by self.make_datetime
			- see that method for supported formats. Returns a queryset with the records to pass to the API.
			
			Excludes any CTD records with a BoundFail flag - in the future, we *might* want to make this configurable, but
			for now, it's fine to just leave them out
		:return:
		"""

		queryset = models.CTD.objects.exclude(flags__flag="BoundFail").order_by('-dt')  # NOTE - this excludes any records that have a BoundFail flag associated with them!
		beginning_dt = self.request.query_params.get('since', None)
		end_dt = self.request.query_params.get('before', None)
		if beginning_dt is not None:
			filter_dt = self.make_datetime(beginning_dt)
			queryset = queryset.filter(dt__gt=filter_dt)
		elif end_dt is None:  # only do a default beginning filter if there's no end filter. Because if they provide an end before the beginning, then whoops!
			# this block tries to go back one day at a time until it accumulates at least settings.ICEFISH_API_MIN_DEFAULT_RECORDS or until it goes back a max of settings.ICEFISH_API_MAX_DEFAULT_DAYS
			# it can still return no records if there aren't any in that many days. This could be simlified to just be a
			# .order_by("-dt").limit(25) or something like that, but at least early on, it's nice if it includes at
			# least a full day, but sometimes the CTD is down, so we need to go back further. This is a compromise.

			filter_dt = arrow.utcnow().shift(days=-settings.ICEFISH_API_NUM_DAYS_DATA_DEFAULT).datetime  # shift today back by API_NUM_DAYS_DATA_DEFAULT days to get the beginning date
			filtered_queryset = queryset.filter(dt__gt=filter_dt)
			num_days_back = settings.ICEFISH_API_MIN_DEFAULT_RECORDS

			# this next process is slow and would likely be a problem in public APIs - but for now, it's OK to make it smart - especially for testing while we accumulate data
			while len(filtered_queryset) < settings.ICEFISH_API_MIN_DEFAULT_RECORDS and num_days_back < settings.ICEFISH_API_MAX_DEFAULT_DAYS:
				# basically, this condition checks if we have at least the minimum number of records, or we've tried to go back a certain number of days already
				num_days_back += 1
				filtered_queryset = queryset.filter(dt__gt=arrow.utcnow().shift(days=-num_days_back).datetime)
			queryset = filtered_queryset  # we assign this back at the end so we keep queryset clear for repeated attempts

		if end_dt is not None:
			queryset = queryset.filter(dt__lt=self.make_datetime(end_dt))

		return queryset

def spectrogram_full(request):
	return render_to_response(request, "icefish/spectrogram.django.html", {'title': "McMurdo Ocean Observatory: Spectrogram"})

def chart_full(request, location=None):
	return render(request, "icefish/data.django.html", {'title': "McMurdo Ocean Observatory", "location": location})


def audio_archive(request):
	audio_files = models.HydrophoneAudio.objects.all().order_by('-start_time')[:20]
	log.debug("{} audio files".format(len(audio_files)))

	return render_to_response("icefish/audio_archive.django.html", context={"audio_files": audio_files, "title": "McMurdo Ocean Observatory: Audio"})

def display_spectrogram(request, hydrophone_audio_id):
	"""

	:param request:
	:param image_id:
	:return:
	"""

	return _hydrophone_attribute_stream(hydrophone_audio_id=hydrophone_audio_id, attribute="spectrogram")

def send_flac(request, hydrophone_audio_id):
	"""

	:param request:
	:param image_id:
	:return:
	"""

	return _hydrophone_attribute_stream(hydrophone_audio_id=hydrophone_audio_id, attribute="flac")

def _hydrophone_attribute_stream(hydrophone_audio_id, attribute):
	"""
	Used to load hydrophone spectrograms and audio from storage without making them static files. Not great for a high
	volume server, but fine for us - don't want staticfiles moving them around. If we have a server that supports
	X-SendFile, but Waitress doesn't support it, so we're doing this for now.

	Via: http://blog.ekini.net/2010/10/15/file-streaming-in-django-sending-large-files-through-django/
	:param hydrophone_audio_id:
	:param attribute:
	:return:
	"""
	try:
		audio = models.HydrophoneAudio.objects.get(pk=hydrophone_audio_id)
	except models.HydrophoneAudio.DoesNotExist:
		raise Http404("Audio file with that ID does not exist in database. It may be incorrect, or may not have been loaded yet.")

	filepath = getattr(audio, attribute)
	if not os.path.exists(filepath):
		raise Http404("Audio file is defined, but actual file was not found!")

	wrapper = FileWrapper(open(filepath, 'rb'),)
	response = HttpResponse(wrapper, content_type=mimetypes.guess_type(filepath))
	response['Content-Length'] = os.path.getsize(filepath)
	return response

