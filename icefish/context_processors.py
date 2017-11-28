from icefish_backend import settings

def charting_constants(request):
	return {  # we need to manually have it use the value "null" because these will become Javascript on the page
		'ICEFISH_QUERY_ROOT_URL': "'{}'".format(settings.ICEFISH_QUERY_ROOT_URL) if settings.ICEFISH_QUERY_ROOT_URL is not None else "null",
		'ICEFISH_HYDROPHONE_BASE_URL': "'{}'".format(settings.ICEFISH_HYDROPHONE_BASE_URL) if settings.ICEFISH_HYDROPHONE_BASE_URL is not None else "null",
		'ICEFISH_HYDROPHONE_PORT': settings.ICEFISH_HYDROPHONE_PORT if settings.ICEFISH_HYDROPHONE_PORT is not None else "null",
		'ICEFISH_REALTIME_CTD': "true" if settings.ICEFISH_REALTIME_CTD is True else False,
	}