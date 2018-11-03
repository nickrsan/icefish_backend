from icefish_backend import settings

def _js_safe(constant):
	if constant is None:
		return "null"

	return "'{}'".format(constant)


def charting_constants(request):
	return {  # we need to manually have it use the value "null" because these will become Javascript on the page
		'ICEFISH_QUERY_ROOT_URL': _js_safe(settings.ICEFISH_QUERY_ROOT_URL),
		'ICEFISH_PROXY_BASE_URL': _js_safe(settings.ICEFISH_PROXY_BASE_URL),
		'ICEFISH_CONTROL_PORT': _js_safe(settings.ICEFISH_CONTROL_PORT),
		'ICEFISH_HYDROPHONE_PORT': settings.ICEFISH_HYDROPHONE_PORT if settings.ICEFISH_HYDROPHONE_PORT is not None else "null",
		'ICEFISH_REALTIME_CTD': "true" if settings.ICEFISH_REALTIME_CTD is True else False,
		'ICEFISH_CTD_API_TOKEN': "'Token {}'".format(settings.CTD_WEB_API_PUBLIC_TOKEN),
		'DEVICE_NAME': "'{}'".format(settings.DEVICE_NAME),

		# note that this URL is *not* in quotes! meant to be used directly in HTML - if putting it in JS, we need to quote it
		'ICEFISH_VIDEO_SERVER_URL': "{}".format(settings.ICEFISH_VIDEO_SERVER_URL) if settings.ICEFISH_VIDEO_SERVER_URL is not None else "null",
		'ICEFISH_VIDEO_PLAYLIST_URL': "{}".format(settings.ICEFISH_VIDEO_PLAYLIST_URL) if settings.ICEFISH_VIDEO_PLAYLIST_URL is not None else "null",
	}