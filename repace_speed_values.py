import glob
import re
import os

speedRegex = re.compile(r'<.*Speed>(.*)</.*Speed>')

inputPath = './TCX/*.tcx'
outputPath = './output/'

inputFiles=glob.glob(inputPath)   

for filePath in inputFiles:
    fileHandler = open(filePath, 'r')
    outputFile = open(outputPath + os.path.basename(filePath), 'w+')

    listOfLines = fileHandler.readlines()

    for line in listOfLines:
        regSpeedMatchObject = speedRegex.search(line)

        if regSpeedMatchObject and regSpeedMatchObject.group(1):
            speedValueKmh = regSpeedMatchObject.group(1)
            speedValueMs = str(float(speedValueKmh)/3.6)

            line = line.replace(speedValueKmh, speedValueMs)

        outputFile.write(line)

    fileHandler.close()
