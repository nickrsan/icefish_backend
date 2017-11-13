from rest_framework import serializers

from icefish import models


class CTDSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = models.CTD
		fields = ('temp', 'pressure', 'conductivity', 'salinity', 'dt', 'measured', 'is_supercooled', 'freezing_point')