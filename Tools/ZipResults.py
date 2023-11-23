#!/usr/bin/env python3

#============================================================================#
# EVOLIFE  http://evolife.telecom-paris.fr             Jean-Louis Dessalles  #
# Telecom Paris  2023-11-19                                www.dessalles.fr  #
# -------------------------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                                        #
#============================================================================#
# Documentation: https://evolife.telecom-paris.fr/Classes                    #
#============================================================================#


import sys
import os
import shutil

RESULTDIR = '___Results'


if __name__ == "__main__":
	ZipFileName = RESULTDIR.strip('_')
	try:
		shutil.make_archive(ZipFileName, 'zip', RESULTDIR)
		print(f'{ZipFileName}.zip', 'created')
	except Exception as Msg:
		print(Msg)
