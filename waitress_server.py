"""
	Script to run that serves the project via WSGI using Waitress. This should be set up to run on boot by a Windows
	scheduled task
"""

from waitress import serve
from icefish_backend.wsgi import application
from icefish_backend.local_settings import SERVE_ADDRESS
### Run Python scripts as a service example (ryrobes.com)
### Usage : python aservice.py install (or / then start, stop, remove)

import win32service
import win32serviceutil
import win32api
import win32con
import win32event
import win32evtlogutil
import os, sys, string, time


class aservice(win32serviceutil.ServiceFramework):
	_svc_name_ = "MOOWebServerWaitress"
	_svc_display_name_ = "MOO Web Server Run By Waitress"
	_svc_description_ = "A service for the MOO web server to make sure it can run before login"

	def __init__(self, args):
		win32serviceutil.ServiceFramework.__init__(self, args)
		self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

	def SvcStop(self):
		self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
		win32event.SetEvent(self.hWaitStop)

	def SvcDoRun(self):
		import servicemanager
		servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED,
							  (self._svc_name_, ''))

		self.timeout = 60000
		# This is how long the service will wait to run / refresh itself (see script below)

		while 1:
			# Wait for service stop signal, if I timeout, loop again
			rc = win32event.WaitForSingleObject(self.hWaitStop, self.timeout)
			# Check to see if self.hWaitStop happened
			if rc == win32event.WAIT_OBJECT_0:
				# Stop signal encountered
				servicemanager.LogInfoMsg("SomeShortNameVersion - STOPPED!")  # For Event Log
				break
			else:
				serve(application, SERVE_ADDRESS)  # serve the application! might not respond to termination signals

def ctrlHandler(ctrlType):
	return True


if __name__ == '__main__':
	win32api.SetConsoleCtrlHandler(ctrlHandler, True)
	win32serviceutil.HandleCommandLine(aservice)