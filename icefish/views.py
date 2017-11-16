# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import arrow

from django.shortcuts import render, render_to_response
from django.template.loader import get_template

# Create your views here.

from rest_framework import viewsets
from icefish.serializers import CTDSerializer
from icefish.models import CTD


class CTDViewSet(viewsets.ReadOnlyModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""
	serializer_class = CTDSerializer

	def get_queryset(self):
		"""
		Optionally restricts the returned purchases to a given user,
		by filtering against a `username` query parameter in the URL.
		"""
		queryset = CTD.objects.all().order_by('-dt')
		beginning_dt = self.request.query_params.get('since', None)
		end_dt = self.request.query_params.get('before', None)
		if beginning_dt is not None:
			filter_dt = datetime.datetime.strptime(beginning_dt, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
		else:
			filter_dt = arrow.utcnow().shift(days=-1).datetime
		queryset = queryset.filter(dt__gt=filter_dt)

		if end_dt is not None:
			queryset = queryset.filter(dt__lt=datetime.datetime.strptime(end_dt, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc))

		return queryset


def spectrogram_full(request):
	return render_to_response("icefish/spectrogram.django.html")

def chart_full(request):
	return render_to_response("icefish/data.django.html")