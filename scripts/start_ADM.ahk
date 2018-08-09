
hydrophone_data_directory = %1%
logging_interval = %2%	
IfWinNotExist, ahk_exe ArrayDataMgr.exe
{
	Exit 1
}

SetKeyDelay 75							; Make it type a little slower
WinActivate ahk_exe ArrayDataMgr.exe   	; Switch to Array Data Manager's windows
Click 94, 54  							; Click in the box to put in the hydrophone ID
Send ^a            						; Select all text in the box
Send 1713  								; Hydrophone is ID 1713 - that's the one we want to find
Click 148, 55 							; click the button to find Hydrophone 1713 on the network
Sleep 5000  							; wait for it to find the IP - it should be far less than this, but as a buffer

; Normally, I'd use a conditional here to get the text from the IP address box, but it doesn't seem to have a way to
; retrieve text from the selection (that I can find) and the window's controls aren't named, so we can't use those.
; We're going to assume it's fine, and if it breaks, we'll get alerts

Click 60, 166
Send ^a
Send %hydrophone_data_directory%		; Output directory
Click 156, 241
Send ^a
Send MOO200_24							; Filename prefix
Click 137, 266
Send ^a
Send %logging_interval%					; How many minutes each file should be

PixelSearch, Px, Py, 0, 0, 2000, 2000, 0xff0000, 5, Fast RGB       ; find the start button - it moves if the window resizes
if ErrorLevel
	Exit 1								; Couldn't find the pixel to click to start logging
else
	Click %Px%, %Py%

;Click 502, 474							; Start Logging

Sleep 20000								; Give it some time for an error to occur, if it's going to

If WinExist("Error"){
	Exit 1								; Notify the calling script that we failed
}

