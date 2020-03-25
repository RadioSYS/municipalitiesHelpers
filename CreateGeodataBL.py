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
osvb = DBF('./data/PLZO_OS.dbf')
osname = DBF('./data/PLZO_OSNAME.dbf', encoding='utf-8')
osnamepos = DBF('./data/PLZO_OSNAMEPOS.dbf', encoding='utf-8')
plz = DBF('./data/PLZO_PLZ.dbf')
print(plz.field_names)
print(osvb.field_names)
print(os.field_names)
print(osname.field_names)
print(osnamepos.field_names)

sHoheitsgebiet = DBF('./data/swissBOUNDARIES3D_1_3_TLM_HOHEITSGEBIET.dbf', encoding='utf-8')
print(sHoheitsgebiet.field_names)

print('Lengths os:%s osname:%s osnamepos:%s plz:%s' % (len(os), len(osname), len(osnamepos), len(plz)))
munFile = open('./data/gemeindeliste.csv', encoding='utf-8')

mun = csv.reader(munFile, delimiter=';')

# Now we create a list of all municipalities of BL
munBL = {}
others = {}

# extract the area for each municipality

# extracting from swissBoundaries DBF
# BL has number 13,
print('Extracting municipalities of BL')
for m in sHoheitsgebiet:
    # print(m['BFS_NUMMER'])
    if m['KANTONSNUM'] == 13 and m['GEM_FLAECH'] != None:
        munBL[m['BFS_NUMMER']] = {'BFS_NR': m['BFS_NUMMER'], 'NAME': m['NAME'], 'OS_UUID': m['UUID'],
                                  'KANTONSNUM': m['KANTONSNUM']}
        # print('BFS: %s Name: %s Type: %s %s' % (m['BFS_NUMMER'], m['NAME'], m['OBJEKTART'], m['GEM_FLAECH']))

print('Extracting other municipalities:')
# extract others by BFS number
othersList = [2471, 2472, 2473, 2474, 2475, 2476, 2477, 2478, 2479, 2480, 2481, 2579, 2611, 2618, 2619, 2621, 2701,
              2702, 2703, 4252, 4254, 4257, 4258, 4263, 2614, 2616, 2613, 2617, 4253, 4262, 2492, 2493, 4181]
othersList.sort()
print(othersList)
for m in sHoheitsgebiet:
    # print(m['BFS_NUMMER'])
    if m['BFS_NUMMER'] in othersList and m['GEM_FLAECH'] is not None:
        others[m['BFS_NUMMER']] = {'BFS_NR': m['BFS_NUMMER'], 'NAME': m['NAME'], 'OS_UUID': m['UUID']}
        # print('BFS: %s Name: %s Type: %s %s' % (m['BFS_NUMMER'], m['NAME'], m['OBJEKTART'], m['GEM_FLAECH']))


def write_areas(list_bfs, filePathOut):
    with open('./data/swissBOUNDARIES3D_1_3_TLM_HOHEITSGEBIET.geojson', encoding='utf-8') as bFile:
        border = json.load(bFile)
        bordersBL = []
        for b in border['features']:
            if b['properties']['BFS_NUMMER'] in list_bfs:
                bordersBL.append(b)

        border['features'] = bordersBL
        with open(filePathOut, 'w', encoding='utf-8') as bOutFile:
            json.dump(border, bOutFile)


print('Writing borders')
write_areas(munBL, './boundaries_BL.geojson')
write_areas(others, './boundaries_Others.geojson')

# we now have a list of ortschaften in BL and some others
# now we have to find where to display the case counter
# this tends to get quite tricky

# generate hashmap
munNames = {}
for m in munBL:
    munNames[munBL[m]['NAME']] = munBL[m]

for m in others:
    munNames[others[m]['NAME']] = others[m]


def set_name_plz(mName, m):
    munNames[mName]['NAME_UUID'] = m['UUID']
    munNames[mName]['PLZ_OS_UUID'] = m['OS_UUID']


# add UUID for position from geodata
i = 0
try:
    for m in osname:
        mName = m['KURZTEXT']
        if mName in munNames:
            set_name_plz(mName, m)
            i = i + 1
            continue
        # special treatment for all municipalities with cantonal suffix ' BL'
        if ' BL' in mName or ' (BL)' in mName:
            i = i + 1
            mName = mName.replace(' BL', ' (BL)')
            if mName in munNames:
                set_name_plz(mName, m)
            else:
                mName = mName.replace(' (BL)', '')
                if mName in munNames:
                    set_name_plz(mName, m)
                else:
                    print('Error writing mun BL: ' + mName)
            continue
        if ' SO' in mName:
            i = i + 1
            mName = mName.replace(' SO', ' (SO)')
            if mName in munNames:
                set_name_plz(mName, m)
            else:
                mName = mName.replace(' (SO)', '')
                if mName in munNames:
                    set_name_plz(mName, m)
                # else:
                # print('Warning writing mun SO: ' + mName)
            continue
        if 'Metzerlen' in mName:
            set_name_plz('Metzerlen-Mariastein', m)
        if 'Nuglar' in mName:
            set_name_plz('Nuglar-St. Pantaleon', m)
        if 'Hofstetten' in mName:
            set_name_plz('Hofstetten-Flüh', m)
        if 'Wahlen b. Laufen' in mName:
            i = i + 1
            set_name_plz('Wahlen', m)

except UnicodeDecodeError:
    print('File ended unexpected')

# add UUID for position from geodata
try:
    for m in osnamepos:
        # OSNAM_UUID # UUID
        # print(m)
        for p in munNames.values():
            if p['NAME_UUID'] == m['OSNAM_UUID']:
                p['POS_UUID'] = m['UUID']

except:
    print("Unexpected error:", sys.exc_info()[0])

# add PLZ from pls dbf
try:
    for m in plz:
        # OSNAM_UUID # UUID
        # print(m)
        for p in munNames.values():
            if p['PLZ_OS_UUID'] == m['OS_UUID']:
                p['PLZ'] = m['PLZ']

except:
    print("Unexpected error:", sys.exc_info()[0])

# now every mun should have a name uuid:
for m in munNames:
    if 'NAME_UUID' not in munNames[m].keys():
        print('Error, mun has no name_uuid: ' + munNames[m]['NAME'])
    if 'POS_UUID' not in munNames[m].keys():
        print('Error, mun has no pos_uuid: ' + munNames[m]['NAME'])


def look_up_by_pos_uuid(munList, uuid):
    for m in munList:
        if munList[m]['POS_UUID'] == uuid:
            return munList[m]
    print('Did not find mun with pos_uuid: %s' % (uuid))


def write_position(munList, filePathOut):
    hashMap = []
    for p in munList:
        hashMap.append(munList[p]['POS_UUID'])

    with open('./data/PLZO_OSNAMEPOS.geojson', encoding='utf-8') as bFile:
        border = json.load(bFile)

    # filter out only BL municipalities:
    positions = []
    for b in border['features']:
        if b['properties']['UUID'] in hashMap:
            positions.append(b)
            # save position to municipality
            mun = look_up_by_pos_uuid(munList, b['properties']['UUID'])
            coords = b['geometry']['coordinates']
            coords.reverse()
            mun['COUNT_COORDS'] = coords

    border['features'] = positions
    with open(filePathOut, 'w', encoding='utf-8') as bOutFile:
        json.dump(border, bOutFile)


write_position(munBL, './position_BL.geojson')
write_position(others, './position_others.geojson')


# #
# print('Wrote out all geodata for BL')
#
# # # write out json file for later processing in webapp:

def write_json(dictMun, out_path):
    munBLasList = []
    for p in dictMun:
        munBLasList.append(dictMun[p])
    munBLasList.sort(key=lambda x: x['BFS_NR'])

    with open(out_path, 'w', encoding='utf-8') as bOutFile:
        json.dump(munBLasList, bOutFile, indent=4)


write_json(munBL, 'mun_BL.json')
write_json(others, 'mun_others.json')


#
# # write out sample csv file
def write_random_csv(dictMun, out_path):
    with open(out_path, 'w', newline='', encoding='utf-8') as sampleFile:
        csvWriter = csv.writer(sampleFile, delimiter=';')
        csvWriter.writerow(['BFS NR', 'NAME', 'Anzahl'])
        for p in dictMun.values():
            csvWriter.writerow([p['BFS_NR'], p['NAME'], int(random.lognormvariate(0, 1) * 100)])


write_random_csv(munBL, './casedata.csv')
write_random_csv(others, './casedata_others.csv')
