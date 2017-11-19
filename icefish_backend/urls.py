"""icefish_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

from icefish import views as icefish
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'ctd', icefish.CTDViewSet, base_name="ctd_records")

urlpatterns = [
    url(r'^api/', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^admin/', admin.site.urls),
    url(r'^spectrogram/', icefish.spectrogram_full),
    url(r'^charts/', icefish.chart_full),
    url(r'^archive/audio/', icefish.audio_archive),
    url(r'^retrieve/audio/spectrogram/(?P<hydrophone_audio_id>\d+)/', icefish.display_spectrogram),
    url(r'^retrieve/audio/flac/(?P<hydrophone_audio_id>\d+)/', icefish.send_flac)
]
