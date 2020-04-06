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
        newLine = line
        regSpeedMatchObject = speedRegex.search(line)

        if regSpeedMatchObject and regSpeedMatchObject.group(1):
            speedValueKmh = regSpeedMatchObject.group(1)
            speedValueMs = str(float(speedValueKmh)/3.6)

            staticPartStart = line[0:regSpeedMatchObject.start(1)]
            staticPartEnd = line[regSpeedMatchObject.end(1)::]

            newLine = staticPartStart + speedValueMs + staticPartEnd

        outputFile.write(newLine)

    fileHandler.close()
