import celery

def insert_CTD_records(records):
	"""
		This function should take the raw records described here, parse them, create django objects, and write them out
		to the DB. It will do this as a celery task so that the main thread can continue.
	:param records:
	:return:
	"""