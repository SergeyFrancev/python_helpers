import os
import sys
import re

def get_old_rxjs(line):
	result = re.search(r'\{ ([a-zA-Z]+) \}.*\'rxjs\/(internal|Observable|Subject|ReplaySubject|Subscription|BehaviorSubject).?', line)
	if result:
		r = result.group(1)
		if r == 'fromPromise':
			return 'from as fromPromise'
		return r
	result = re.search(r'\{ ([_a-zA-Z]+) \}.*\'rxjs-compat\/', line)
	if result:
		r = result.group(1)
		if r == 'fromPromise':
			return 'from as fromPromise'
		if r == '_throw':
			return 'throwError'
		if r == 'IntervalObservable':
			return 'interval'
	return None	

def get_operators(file):
	lines = file.readlines()
	operators = []
	lineNumber = 0;
	for line in lines:
		lineNumber += 1
		operator = get_old_rxjs(line)
		if operator != None and operator not in operators:
			operators.append([lineNumber, operator])
	return operators	

def update_file(pathToFile, operators):
	removeLineInx = []
	for operator in operators:
		removeLineInx.append(operator[0])

	operatorNames = []
	for operator in operators:
		operatorNames.append(operator[1])

	operatorsInserted = 0
	lastImportLine = 1

	with open(pathToFile, 'r') as readFile:
		newFile = open(pathToFile + '_tmp', 'x')	
		lineNumber = 0
		for line in readFile.readlines():
			lineNumber += 1
			if re.match(r'import', line):
				lastImportLine = lineNumber
			if lineNumber in removeLineInx:
				continue
			result = re.search(r'\{ ([a-zA-Z,\s]*) \}.*\'rxjs\'', line)
			if result:
				newFile.write('import { ' + result.group(1) + ', ' + ', '.join(operatorNames) + ' } from \'rxjs\';\r\n')
				operatorsInserted = 1
				continue
			if 'throwError' in operatorNames:
				line = re.sub(r'_throw', 'throwError', line)
			if 'interval' in operatorNames:
				line = re.sub(r'IntervalObservable\.create', 'interval', line)
			newFile.write(line)

		readFile.close()
		newFile.close()
		os.remove(pathToFile)
		os.rename(pathToFile + '_tmp', pathToFile)

	if (operatorsInserted == 0):
		lastImportLine -= len(operators) - 1
		with open(pathToFile, 'r') as readFile:
			newFile = open(pathToFile + '_tmp', 'x')	
			lineNumber = 0
			for line in readFile.readlines():
				lineNumber += 1
				if lastImportLine == lineNumber:
					newFile.write('import { ' + ', '.join(operatorNames) + ' } from \'rxjs\';\r\n')
				newFile.write(line)
			readFile.close()
			newFile.close()
			os.remove(pathToFile)
			os.rename(pathToFile + '_tmp', pathToFile)

	return 1;		

def check_file(pathToFile):
	with open(pathToFile, "r+") as file:
		operators = get_operators(file)
		file.close();
		if len(operators) > 0:
			update_file(pathToFile, operators)
			print('# Updated: ' + pathToFile)
			return 1
	return 0
	

def run(path):
	count = 0;
	for root, dirs, files in os.walk(path):
		for file in files:
			if re.search(r'ts$', file):
				count += check_file(root + '/' + file)

	print('*** UPDATED ' + str(count) + ' FILES ***')

if __name__ == '__main__':
    run(sys.argv[1])
