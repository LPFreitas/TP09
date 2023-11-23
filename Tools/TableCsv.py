#!/usr/bin/env python3

""" @brief  Input and Output using CSV files (as the standard 'csv' module does not seem to be reliable) """


#============================================================================#
# EVOLIFE  http://evolife.telecom-paris.fr             Jean-Louis Dessalles  #
# Telecom Paris  2023-11-19                                www.dessalles.fr  #
# -------------------------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                                        #
#============================================================================#
# Documentation: https://evolife.telecom-paris.fr/Classes                    #
#============================================================================#

import os
import re
#	compatibility with python 2
import sys
Python3 = (sys.version_info >= (3,0))

pyCrypt = None
try:	import pyCrypt
except ImportError:	pass

# MaxRead = 4*4096	# max chars read from a file to get an idea of its structure
MaxRead = 100	# max chars read from a file to get an idea of its structure
PrologPredicate = 'record_'	# for prolog output
ENCODING = 'utf-8'

try:
	from TableUtils import trace
except ImportError:
	def trace(TraceLevel, Msg):	print(Msg)


# ________________________________ #
#                                  #
# csv file format                  #
# ________________________________ #
class Dialect:
	"""	sets delimiter and escape char - Partially mimics standard csv module
	"""
	def __init__(self, delimiter=',', escapechar='\\', quotechar='"', initial='', final='', entete='', fullQuote=False):
		self.delimiter = delimiter
		self.escapechar = escapechar
		self.quotechar = quotechar
		self.initial = initial
		self.final = final
		self.entete = entete
		self.QUOTE_MINIMAL = not fullQuote
		self.fullQuote = fullQuote

	def mostRepresented(self, Chars, Sample):
		Poll = [Sample.count(Char) for Char in Chars]
		Candidate = Poll.index(max(Poll))
		# print(Sample[:100])
		# print Chars, Poll, Candidate
		Poll1 = sorted(Poll)
		if Poll1[-1] > 1.3 * Poll1[-2]: return Chars[Candidate]
		return None
		
	def sniff(self, fileName=None, sample='', verbose=True):
		" Returns another dialect after detecting delimiter and quote char "
		D = Dialect(delimiter=self.delimiter, quotechar=self.quotechar)
		if fileName and os.path.exists(fileName):
			Input = openFile(fileName, verbose=verbose)
			Sample = ''
			try:
				for nroLine in range(MaxRead):	Sample += next(Input)
			except StopIteration:	pass
		elif sample:	Sample = sample
		else:
			if verbose:	trace(1, 'ERROR:	Unable to open %s for sniffing' % fileName)
			return D

		delimiter = self.mostRepresented([',', ';', '\t'], Sample)
		if verbose and delimiter != self.delimiter:	trace(5, 'candidate delimiter: %s' % delimiter)
		if delimiter is not None:
			# and len(set([Line.count(delimiter) for Line in Sample.split('\n')])) == 1:
			if delimiter != self.delimiter:
				# further test: same number of delimiters per line
				# suppressing dots
				Sample1 = re.sub(r'\\.', '', Sample)	# Note the 'r' which is necessary here
				# suppressing quoted fields
				Sample1 = re.sub('%s.*?%s' % (self.quotechar, self.quotechar), '', Sample1).split('\n')[:-1]
				P = set([Line.count(delimiter) for Line in Sample1])
				D.delimiter = delimiter
				if verbose:	trace(4, "Delimiter set to '%s'" % delimiter)
				if len(P) != 1:
					if verbose:	trace(2, 'warning: candidate delimiter %s seems to fail %s' % (delimiter, str(P)))
					# trying to find faulty lines
					P = list(P)
					LineCounts = [(l[0], l[1].count(delimiter)) for l in enumerate(Sample1)]
					Occurrences = [[l[1] for l in LineCounts].count(n) for n in P]
					trace(2, Occurrences)
					trace(2, P)
					Faultyline = LineCounts[[l[1] for l in LineCounts].index(P[Occurrences.index(min(Occurrences))])]
					Msg = '\n********* line %d has %d occurrences of "%c" *********\n' % (Faultyline + (delimiter,))
					Msg += Sample1[Faultyline[0]]
					# raise Exception, Msg
					if verbose:	trace(2, Msg)
		return D
			
			# quotechar = self.mostRepresented(['"', "'"], Sample)
			# if quotechar is not None:
				# self.quotechar = quotechar
				# print("Quotechar set to '%s'" % quotechar)

	def extension(self):
		if self.initial.startswith(PrologPredicate):	return '.pl'
		if self.delimiter in [',', ';']:	return '.csv'
		if self.delimiter in ['\t']:	return '.csv'
		return '.txt'

	def __str__(self):	return 'Delimiter: >%s<' % self.delimiter
		
class Sniffer(Dialect):
	" compatibility with csv "
	pass


def openFile(csvFileName, CryptKey=None, Ecoding=ENCODING, verbose=True):
	"	Opens a csv file and returns content line by line "
	if CryptKey is not None:
		# # try:
		csvString = pyCrypt.p3_decrypt(open(csvFileName, 'rb').read(), CryptKey)
		try:
			if verbose:	trace(2, 'splitting')
			csvList = csvString.decode(ENCODING).split('\n')
		except UnicodeDecodeError:
			if verbose:	trace(4, '*****  mmm...  %s: Not a %s file. *****' % (csvFileName, ENCODING))
			csvList = csvString.decode('latin-1').split('\n')
			# print(len(csvList))
		# # except (TypeError, pyCrypt.CryptError) as E:
			# # trace(3, E)
			# # # Python 2 compatibility
			# # if verbose:	trace(3, '*************** Python2 COMPATIBILITY ****************')
			# # os.system('cmd /C decrypte -d %s tmpfile000.csv' % csvFileName)
			# # csvList = open('tmpfile000.csv', 'r').readlines()
			# # os.system('cmd /C del tmpfile000.csv')
		for L in csvList:	yield L.strip()	# because of trailing \r
	else:	# no crypting
		Line = ''
		nroLine = 0
		if Python3:
			try:
				# read one line at a time
				for Line in open(csvFileName, 'r', encoding=ENCODING, buffering=1, newline='\n'):	
					nroLine += 1
					if Line.endswith('\r'):	yield Line.strip('\r')
					else:	yield Line
			except UnicodeDecodeError:
				if verbose:
					trace(2, '*****  well...  %s: Not a %s file. *****' % (csvFileName, ENCODING))
					trace(2, "Line %d: %s" % (nroLine, Line))
				for Line in open(csvFileName, 'r', encoding='latin-1', buffering=1, newline='\n'):	
					if Line.endswith('\r'):	yield Line.strip('\r')
					yield Line
		else:
			# read one line at a time
			for Line in open(csvFileName, 'r', buffering=1):	yield Line
	# if CryptKey is None:	csvFile.close()
	
	
def DictReader(csvFileId, dialect=None):
	" compatibility with csv "
	T = list(reader(csvLines=iter(csvFileId.readlines()), dialect=dialect))
	if T:
		# return [dict(zip(T[0], R)) for R in T[1:]]
		for R in T[1:]:	yield dict(zip(T[0], R)) 
	return []
	
def reader(csvFileName=None, csvLines=None, dialect=None, CryptKey=None, verbose=True, permissive=False):
	"	Opens a csv file and returns a record generator "
	if dialect is None:	dialect = Dialect()
	# print(dialect)
	FieldNr = 0
	Nroline = 1
	literal = False		# true between quote chars
	Fields = []			# list of fields for the current record (usually read from a single line)
	currentField = ''	# receives current field as string
	# if csvFileName.endswith('struct'):	print('hello')
	if csvFileName:	
		csvLines = openFile(csvFileName, CryptKey=CryptKey, verbose=verbose)
	for Line in csvLines:
		# try:	print(Line)
		# except Exception as E: print(E)
		# if CryptKey is not None:	print(Line)
		# this loop should be an automaton
		# if csvFileName.endswith('struct'):	print(line)
		if not Line or Line[-1] != '\n':	Line += '\n'
		# Ignore empty lines
		if re.match(r'\s*$', Line) and not literal:	continue
		if not literal:	Fields = []			# list of fields for the current record (usually read from a single line)
		if dialect.initial and Line.startswith(dialect.initial):
			Line = Line[len(dialect.initial):]
		if dialect.final and Line.endswith(dialect.final):
			Line = Line[:-len(dialect.final)]
		skip = False	# to record char next to escape char
		for c in Line:
			if skip:	
				currentField += c
				skip = False
			else:
				# print(c, literal)
				if c == dialect.escapechar: skip = True
				elif c == '\r' and not literal:	continue
				elif c == dialect.quotechar:	literal = not literal
				elif c in [dialect.delimiter, '\n'] and not literal and not skip:	
					Fields.append(currentField)
					currentField = ''
				else:	currentField += c
		if FieldNr > 0 and FieldNr != len(Fields) and not literal:
			# Discrepancy between expected and observed lengths
			if permissive:
				if verbose:	print('repairing', Fields, FieldNr, len(Fields))
				Fields += [''] * max(0, FieldNr - len(Fields))	# missing fields
				# impossible to do the converse when too many fields - saving attempt: merge last fields
				Fields = Fields[:FieldNr-1] + [dialect.delimiter.join(Fields[FieldNr-1:])]
			else:
				ErrorMsg = f'\nUnbalanced line:\nline {Nroline} in {csvFileName} has {len(Fields)} fields instead of {FieldNr}:\n{Line}\n' + "\n>>>>\n".join(Fields)
				# if Python3:	input(ErrorMsg) 	# provoque un plantage dans QT
				# else:	raw_input(ErrorMsg)
				raise Exception(ErrorMsg)
		if not literal:
			FieldNr = len(Fields)
			Nroline += 1
			yield Fields
	return
	
class writer:
	" Writes records to an opened csv file "
	def __init__(self, csvFile, dialect=None):
		self.dialect = dialect
		if self.dialect is None:	self.dialect = Dialect()
		self.csvFile = csvFile

	def field2Str(self, Field):
		Field = str(Field).replace(self.dialect.escapechar, '%s%s' % (self.dialect.escapechar, self.dialect.escapechar))	
		Field = Field.replace(self.dialect.quotechar, '%s%s' % (self.dialect.escapechar, self.dialect.quotechar))
		if not self.dialect.fullQuote:
			Field = Field.replace(self.dialect.delimiter, '%s%s' % (self.dialect.escapechar, self.dialect.delimiter))
		if Field.find('\n') >= 0 or Field.find('\r') >= 0 or self.dialect.fullQuote: 
			Field = '%s%s%s' % (self.dialect.quotechar, Field, self.dialect.quotechar)
		return Field
		
	def writerow(self, Fields):
		" Saves tuple into csv file "
		Line = self.dialect.initial + (self.dialect.delimiter).join(map(self.field2Str, Fields)) + self.dialect.final + '\n'
		if self.csvFile:	self.csvFile.write(Line)
		return Line

def load(csvFileName, dialect=None, sniff=False, CryptKey=None, verbose=True, permissive=False):
	" Loads data from a csv file "
	if dialect is None:	dialect = Dialect()
	if sniff:	dialect = dialect.sniff(csvFileName, verbose=False)
	return reader(csvFileName, dialect=dialect, CryptKey=CryptKey, verbose=verbose, permissive=permissive)
	# return [R for R in Reader]
	
def loadTable(csvFileName, dialect=None, sniff=True, CryptKey=None, verbose=True, permissive=False):
	" Loads table from a csv file (first line expected to be header) and returns list of dicts "
	T = list(load(csvFileName, dialect=dialect, sniff=sniff, CryptKey=CryptKey, verbose=verbose, permissive=permissive))
	if T:
		return [dict(zip(T[0], R)) for R in T[1:]]
	return []


def save(Data, csvFileName, dialect=None, CryptKey=None, verbose=False, Encoding=None):
	" Saves data (list or generator of tuples) to a csv file "
	if dialect is None:	dialect = Dialect()
	# Determining file extension
	if os.path.splitext(csvFileName)[1] == '':	csvFileName += dialect.extension()
	try:
		if CryptKey is not None:
			CryptingOK = True
			csvFile = open(csvFileName, 'wb')
			try:
				if dialect.entete:	
					csvFile.write(pyCrypt.p3_encrypt(dialect.entete + '\n', CryptKey))
				W = writer(None, dialect)
				csvStr = ''
				# Compatibility:	provisoire
				Data1 = [d for d in Data]
				for D in Data1:	csvStr += W.writerow(D)
				csvFile.write(pyCrypt.p3_encrypt(csvStr.encode(ENCODING), CryptKey))
			except (TypeError, pyCrypt.CryptError) as E:	
				####### Provisoire
				if verbose:	trace(2, E)
				if verbose:	trace(2, '*************** Python2 COMPATIBILITY ****************')
				CryptingOK = False
				tmpFile = open('tmpfile000.csv', 'w')
				if dialect.entete:	tmpFile.write(dialect.entete + '\n')
				W = writer(tmpFile, dialect)
				for D in Data1:	W.writerow(D)
				tmpFile.close()
			csvFile.close()	
		else:	# no crypting
			# print(csvFileName, Encoding)
			if Encoding is None: Encoding = ENCODING
			if Python3:	csvFile = open(csvFileName, 'w', encoding=Encoding, errors='replace', newline='\r\n')
			else:	csvFile = open(csvFileName, 'w')
			if dialect.entete:	csvFile.write(dialect.entete + '\n')
			W = writer(csvFile, dialect)
			for D in Data:	W.writerow(D)
			csvFile.close()
		if CryptKey and not CryptingOK:
			####### Provisoire
			os.system('cmd /C decrypte -e tmpfile000.csv %s' % csvFileName)
			os.system('cmd /C del tmpfile000.csv')
			
		if verbose:	trace(2, '%s created' % csvFileName)
	except IOError:
			if verbose:	trace(2, '*************** ERROR *******************')
			if verbose:	trace(2, '* Unable to open %s for writing' % csvFileName)
			if verbose:	trace(2, '*****************************************')
	return csvFileName

def repair(csvFileName, dialect=None, verbose=True):
	" attempt to repair csv file with inconsistent record lengths "
	T = load(csvFileName, dialect=dialect, sniff=True, verbose=verbose, permissive = True)
	F, E = os.path.splitext(csvFileName)
	RepairedFileName = '%s_repaired%s' % (F, E)
	save(T, RepairedFileName, dialect=dialect, verbose=verbose)
	if verbose:	print('%s created' % RepairedFileName)
	

if __name__ == "__main__":
	print(__doc__)


__author__ = 'Dessalles'
