from rest_framework import serializers

from icefish import models

class CTDSerializer(serializers.HyperlinkModelSerializer):
	class Meta:
		model = models.CTD
		fields = ('temp', 'pressure', 'conductivity', 'salinity', 'dt', 'measured')