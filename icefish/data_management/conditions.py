import arrow

from icefish import models

def _check_temperature_in_window(start_date, base_temperature=-1.900, max_start_deviation=0.5):
	"""
		Checks if temperatures in a 7 day window are above a certain threshold
		:param start_date: datetime object representing the start date
		:param base_temperature: what's the 7 day temperature threshold for summer conditions? Set to be close to the correct value now - but verify
		:param max_start_deviation: How far away, in days, can the first observation found be - if it can't find a record within this time range, raises icefish.models.DataQuantityError
		:return: bool. Returns True if the window indicates summer conditions or False if it doesn't
	"""
	start_ctd_obs = models.CTD.objects.filter(dt__lt=start_date).order_by("-dt").first()  # get the first most recent datetime
	if arrow.get(start_date).shift(days=-max_start_deviation).datetime > start_ctd_obs.dt:  # if the object we retrieved is further than half a day away from our requested starting time
		raise models.DataQuantityError("Couldn't find a starting value within half a day of requested starting datetime. Not enough data to proceed")

	if start_ctd_obs.avg_temp(window_centering="BEFORE") > base_temperature:  # check if the seven day average prior to our starting date is above the base temperature required for summer conditions
		return True
	else:
		return False

def is_summer_conditions(start_date, base_temperature=-1.900, max_start_deviation=0.5):
	"""
		Given a starting datetime, checks if it's currently summer, as defined by 7 day average above a specified temperature.
		The window it uses could be off by as much as max_start_deviation because it has to find the closest previous record to the starting point to use.

		This function provides a close estimate because the real calculation is whether or not the temperature is above
		the freezing point - since we calculate that per record, we'd need to write some new code to calculate that on
		average and it could be a bit wonky.

	:param start_date: datetime object representing the start date
	:param base_temperature: what's the 7 day temperature threshold for summer conditions? Set to be close to the correct value now - but verify
	:param max_start_deviation: How far away, in days, can the first observation found be - if it can't find a record within this time range, raises icefish.models.DataQuantityError
	:return: bool. Returns True if the window indicates summer conditions or False if it doesn't
	"""

	_check_temperature_in_window(start_date, base_temperature, max_start_deviation)

def is_fish_melting(start_date, base_temperature=-1.00, max_start_deviation=0.5):
	"""
		Fish melting temperature is similar calculation to the summer conditions temp, but with a different temp. Checks
		whether the average temperature is high enough for ice in fish to melt out
	:param start_date: datetime object representing the start date
	:param base_temperature: what's the 7 day temperature threshold for summer conditions? Set to be close to the correct value now - but verify
	:param max_start_deviation: How far away, in days, can the first observation found be - if it can't find a record within this time range, raises icefish.models.DataQuantityError
	:return: bool. Returns True if the window indicates summer conditions or False if it doesn't
	"""
	return _check_temperature_in_window(start_date, base_temperature, max_start_deviation)