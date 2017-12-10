from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter('kiosk_url')
def kiosk_url(url, location):
	"""
		When kiosk mode is active (location=="kiosk"), doesn't link URLs because we don't want outbound links. When it's
		not kiosk mode, links URLs because it should be someone on a personal computer.
	:param url: a url to link (or not) to
	:return: template text
	"""

	if location == "kiosk":
		return url
	else:
		if not url.startswith("http"):
			link_url = "http://{}".format(url)
		else:
			link_url = url
		return mark_safe("<a href=\"{}\" target=\"_blank\">{}</a>".format(link_url, url))


