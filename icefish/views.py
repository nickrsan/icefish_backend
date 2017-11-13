# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, render_to_response
from django.template.loader import get_template

# Create your views here.

from rest_framework import viewsets
from icefish.serializers import CTDSerializer
from icefish.models import CTD


class CTDViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""
	queryset = CTD.objects.all().order_by('-dt')
	serializer_class = CTDSerializer


def spectrogram_full(request):
	return render_to_response("icefish/spectrogram.django")