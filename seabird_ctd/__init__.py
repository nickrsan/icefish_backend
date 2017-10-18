"""
	SeaBird CTD is meant to handle reading data from a stationary CTD logger. Many packages exist for profile loggers,
	but no options structured for use on a stationary logger or reading
"""

__author__ = "nickrsan"


"""
	Plan is to have this return either a pandas dataframe or a Python dictionary with the new records. Should filter
	out any noise in the serial transmission (commands, status information, etc).
	
	I believe the CTD will be constantly outputting a file that we'll be reading via USB/serial. Not sure how often we
	can clear/rotate the file, but we should assume:
		1. The file will be open for writing while we read it
		2. It will have duplicate records in it that we'll need to avoid (DB integrity will help, but would be good
			to filter out most, if not all, so that we don't have a bunch of failed inserts
		3. Some records won't be records because they'll be commands, errors, or status messages. We'll want to do data
			cleaning to confirm the record is what we think it is (RegEx, probably - CSV parsing might not work if we're
			trying to read only specific lines - we could potentially dump the lines we know we want to a new file for
			CSV reading, but that seems silly because we would already need to know what's new to do that. File offset
			reading? Parsing the whole file, loading the dates and jumping to the record with the correct dates?
"""

