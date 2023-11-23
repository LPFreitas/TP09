#!/usr/bin/env python3

#============================================================================#
# EVOLIFE  http://evolife.telecom-paris.fr             Jean-Louis Dessalles  #
# Telecom Paris  2023-11-19                                www.dessalles.fr  #
# -------------------------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                                        #
#============================================================================#
# Documentation: https://evolife.telecom-paris.fr/Classes                    #
#============================================================================#



" Checks whether running version is up to date "

import sys
import os
import datetime as dt
#	compatibility with python 2
Python3 = (sys.version_info >= (3,0))
if Python3:
	from urllib.request import urlopen, urlretrieve
	Input = input
else:
	from urllib import urlopen, urlretrieve
	Input = raw_input

EVOLIFEURL = 'http://evolife.telecom-paristech.fr'
EVOLIFEFILE = 'Evolife.zip'
EVOLIFECHECKFILE = 'Main.py'	# used to determine local version date

def CheckUpToDate(RemoteUrl, LocalCheckFile):
	if RemoteUrl.startswith('http'):
		try:	
			if Python3:	f = urlopen(RemoteUrl, timeout=1)
			else:	f = urlopen(RemoteUrl)
		except Exception as E:	
			# print(E)
			return False	# no connexion, don't care about updates
		last_modified = f.headers['last-modified']
		Remote_date = dt.datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S %Z')
	else:	# assuming local file
		Remote_date = dt.datetime.fromtimestamp(os.path.getmtime(RemoteUrl))
	# Now = dt.datetime.now()
	Local_date = dt.datetime.fromtimestamp(os.path.getmtime(LocalCheckFile))
	# print(Remote_date); print(Local_date)
	return (Remote_date > Local_date)

def Reload(Url, RemoteFile, LocalFile):
	try:	urlretrieve(Url+RemoteFile, LocalFile)
	except Exception as E:
		print(E)
		print("**** Error downloading %s \nfrom \n%s" % (RemoteFile, Url))
	
def CheckVersion(Url, RemoteFile, LocalCheckFile, LocalVersion=None):
	if LocalVersion is None: LocalVersion = os.path.join('..', os.path.basename(RemoteFile))
	if not Url.endswith('/'):	Url += '/'
	if CheckUpToDate(Url, LocalCheckFile):
		print('New version of %s available' % os.path.splitext(os.path.basename(LocalVersion))[0])
		if os.path.exists(LocalVersion) and not CheckUpToDate(Url, LocalVersion):
			print('\nYour local download: %s  \nis ready to be installed' % LocalVersion)
			print("You should now unzip it and run 'starter' again.")
			print('Be careful, as all modified files will be lost \nif you unzip %s at the same location.' % EVOLIFEFILE)
			R = Input('\n[Return],  or "s" + [Return] to suppress this warning.\n')
			if R.lower().startswith('s'):
				if os.path.exists(EVOLIFECHECKFILE):	
					os.utime(EVOLIFECHECKFILE, None)		# file is given current time
		else:
			R = Input('download (d), not now (n), or ignore (i) this new version (d/n/i)? ').lower()
			if R.startswith('d'):	
				print('Downloading...')
				Reload(Url, RemoteFile, LocalVersion)
				print('\nNew version saved to', os.path.abspath(LocalVersion))
				print("\nYou should now unzip it and run 'starter' again.")
				print('Be careful, as all modified files will be lost \nif you unzip %s at the same location.' % EVOLIFEFILE)
				Input('[Return]')
			elif R.startswith('i'):
				if os.path.exists(EVOLIFECHECKFILE):	
					os.utime(EVOLIFECHECKFILE, None)		# file is given current time
	else:	
		# print('Your version is probably up to date')
		pass

if __name__ == "__main__":
	CheckVersion(EVOLIFEURL, EVOLIFEFILE, EVOLIFECHECKFILE)
