# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, render_to_response
from django.template.loader import get_template

# Create your views here.


def spectrogram_full(request):
	return render_to_response("icefish/spectrogram.django")