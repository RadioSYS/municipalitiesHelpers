from dbfread import DBF
import csv
import sys
import json
from random import randrange
import random

# Script to generate a geoJSON with all municipalities of BL
# Datenquellen:
# Gemeindeliste: https://www.bfs.admin.ch/bfs/de/home/grundlagen/agvch.assetdetail.11467406.html
# Geodaten: SwissBoundaries3D

# not the best code ;) but it works
# (c) 2020, RadioSYS GmbH, Oliver Wisler

os = DBF('./data/PLZO_OS.dbf')
osname = DBF('./data/PLZO_OSNAME.dbf', encoding='utf-8')
osnamepos = DBF('./data/PLZO_OSNAMEPOS.dbf', encoding='utf-8')
plz = DBF('./data/PLZO_PLZ.dbf')

print('Lengths os:%s osname:%s osnamepos:%s plz:%s' % (len(os), len(osname), len(osnamepos), len(plz)))
munFile = open('./data/gemeindeliste.csv', encoding='utf-8')

mun = csv.reader(munFile, delimiter=';')

# Now we create a list of all municipalities of BL
munBL = {}
hashList = []
for row in mun:
    if row[0] == 'BL':
        # print("KT:%s, BFS_NR:%s, Name:%s" % (row[0], row[2], row[3]))
        sanitizedName = row[3].replace(' (BL)', '')
        munBL[sanitizedName] = {'BFS_NR': int(row[2]), 'NAME': sanitizedName}

print('Added %s municipalities for BL' % len(munBL))

# add OS and Name UUID from the geodata
try:
    for m in osname:
        mName = m['LANGTEXT']
        if mName in munBL:
            munBL[mName]['OS_UUID'] = m['OS_UUID']
            munBL[mName]['NAME_UUID'] = m['UUID']
        # special treatment for all municipalities with cantonal suffix ' BL'
        if ' BL' in mName:
            mName = mName.replace(' BL', '')
            munBL[mName]['OS_UUID'] = m['OS_UUID']
            munBL[mName]['NAME_UUID'] = m['UUID']
        if 'Wahlen b. Laufen' in mName:
            munBL['Wahlen']['OS_UUID'] = m['OS_UUID']
            munBL['Wahlen']['NAME_UUID'] = m['UUID']

except:
    print('File ended unexpected')

# add UUID for position from geodata
try:
    for m in osnamepos:
        # OSNAM_UUID # UUID
        # print(m)
        for p in munBL:
            if munBL[p]['NAME_UUID'] == m['OSNAM_UUID']:
                munBL[p]['POS_UUID'] = m['UUID']

except:
    print("Unexpected error:", sys.exc_info()[0])

print('Loading Geojson for Borders')

# Generate GEOJSON files with content only for BL
hashOSUUID = []
hashPOSUUID = []
for p in munBL:
    hashOSUUID.append(munBL[p]['OS_UUID'])
    hashPOSUUID.append(munBL[p]['POS_UUID'])

with open('./data/PLZO_OS.geojson', encoding='utf-8') as bFile:
    border = json.load(bFile)

    # filter out only BL municipalities:
    bordersBL = []
    for b in border['features']:
        if (b['properties']['UUID'] in hashOSUUID):
            bordersBL.append(b)

    border['features'] = bordersBL
    with open('./PLZO_OS_BL.geojson', 'w', encoding='utf-8') as bOutFile:
        json.dump(border, bOutFile)

with open('./data/PLZO_OSNAMEPOS.geojson', encoding='utf-8') as bFile:
    border = json.load(bFile)

    # filter out only BL municipalities:
    bordersBL = []
    for b in border['features']:
        if (b['properties']['UUID'] in hashPOSUUID):
            bordersBL.append(b)

    border['features'] = bordersBL
    with open('./PLZO_OSNAMEPOS_BL.geojson', 'w', encoding='utf-8') as bOutFile:
        json.dump(border, bOutFile)

print('Wrote out all geodata for BL')

# write out json file for later processing in webapp:
munBLasList = []
for p in munBL:
    munBLasList.append(munBL[p])
with open('./municipalities.json', 'w', encoding='utf-8') as bOutFile:
    json.dump(munBLasList, bOutFile)

# write out sample csv file
with open('SampleFile.csv', 'w', newline='', encoding='utf-8') as sampleFile:
    csvWriter = csv.writer(sampleFile, delimiter=';')
    csvWriter.writerow(['BFS NR', 'NAME', 'Anzahl'])
    for p in munBL:
        csvWriter.writerow([munBL[p]['BFS_NR'], munBL[p]['NAME'], int(random.lognormvariate(0, 1) * 100)])
