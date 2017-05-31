import matplotlib
matplotlib.use('TKAgg')

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import scipy.optimize as opt
import requests
import json
import math
import scipy.constants as const
import sys

class Path:
    def __init__(self, array):
        self.vertexes = []
        self.steps = [0.0]
        self.distance = 0;
        i = 0
        while (i < len(array)):
            self.vertexes.append([])
            self.vertexes[i].append(array[i][0])
            self.vertexes[i].append(array[i][1])
            if i >= 1:
                tmp = (array[i][0] - array[i - 1][0]) ** 2
                tmp += (array[i][1] - array[i - 1][1]) ** 2
                tmp = math.sqrt(tmp)
                self.distance += tmp
                self.steps.append(self.distance)
            i += 1

    def get_point(self, ratio):
        d = ratio * self.distance
        i = 0
        while self.steps[i] < d:
            i += 1
    #    print(d - self.steps[i - 1], self.steps[i] - self.steps[i - 1])
        new_ratio = (d - self.steps[i - 1]) * 1.0 / (self.steps[i] - self.steps[i - 1])
    #    print(new_ratio)
        x = self.vertexes[i - 1][0] + new_ratio * (self.vertexes[i][0] - self.vertexes[i - 1][0])
        y = self.vertexes[i - 1][1] + new_ratio * (self.vertexes[i][1] - self.vertexes[i - 1][1])
        return ([x, y])

class Antenna:
    def __init__(self, line):
        arr = line.split(';')
        self.index = int(arr[1])
        self.azimuth = float(arr[4])
        self.erp = float(arr[6])
        self.x = float(arr[7])
        self.y = float(arr[8])
        self.height = float(arr[9])
        self.mec_tilt = float(arr[10])
        self.elec_tilt = float(arr[11])
        self.perimeter = float(arr[12])


    def get_box(self, lon, lat):
        r = 6378137
        south = lat + (self.y - self.perimeter) * 180 / (const.pi * r)
        north = lat + (self.y + self.perimeter) * 180 / (const.pi * r)
        east = lon + (self.x + self.perimeter) * 180 / (const.pi * r * math.cos(lat * const.degree))
        west = lon + (self.x - self.perimeter) * 180 / (const.pi * r * math.cos(lat * const.degree))
        self.box = [south, west, north, east]


google_api_key = "AIzaSyCtlGAe25QoH6XJihq1fljfJMM4IhzCkQM"

diagram_file = "data/antenna/antenna.msi"
horizontal_diagram = []
f = open("data/antenna/horizontal.txt", "r")
for line in f.readlines():
    a = line.split(' ')
    horizontal_diagram.append(float(a[1]))
#print(horizontal_diagram)

vertical_diagram = []
f = open("data/antenna/vertical.txt", "r")
for line in f.readlines():
    a = line.split(' ')
    vertical_diagram.append(float(a[1]))
#print(vertical_diagram)


site_file = "data/Coordinates.csv"

f = open(site_file, "r")
content = f.readlines()
line = content[4]
parse_site = line.split(';')

site = parse_site[0]
print(site)
base_lon = float(parse_site[1])
base_lat = float(parse_site[2])
print(base_lon, base_lat)


antenna_file = "data/" + site +"_Antennes.csv"
f = open(antenna_file, "r")
content = f.readlines()
antennas = []
content.pop(0)
for line in content:
    sys.stdout.write(line)
    new = Antenna(line)
    new.get_box(base_lon, base_lat)
    antennas.append(new)

box = list(antennas[0].box)
for ant in antennas:
    box[0] = min(box[0], ant.box[0])
    box[1] = min(box[1], ant.box[1])
    box[2] = max(box[2], ant.box[2])
    box[3] = max(box[3], ant.box[3])



south = round(box[0] - 5e-5, 4)
west = round(box[1] - 5e-5, 4)
north = round(box[2] + 5e-5, 4)
east = round(box[3] + 5e-5, 4)

print(south, west, north, east)
#api = overpass.API()
if (False):
    print("Fetch from API")
    endpoint = "http://api.openstreetmap.fr/oapi/interpreter"
    query = '[timeout:25][maxsize:1048576][out:json][bbox:'
    query += (str(south) + ',' + str(west) + ',' + str(north) + ',' + str(east) )
    query += '];\n(way[building];relation[building];);\n'
    query += 'out body;>;out skel qt;\n'

    response = requests.post(endpoint, query)
    text = response.text
    print(text)
    string = "data" + site + ".json"
    f = open(string,"w")
    f.write(text.encode('utf-8'))
else:
    print("Fetch from file")
    string = "data" + site + ".json"
    f = open(string,"r")
    text = f.read().decode('utf-8')

#-----------------
#
#-----------------

def compute(point):
    global antennas
    global site_x
    global site_y
    global horizontal_diagram
    global vertical_diagram

    x = point[0]
    y = point[1]
    z = point[2]

    #any(path.contains_point([point[0], point[1]]) for path in paths):
    result = 0
    for ant in antennas:
        diff_x = (x - ant.x)
        diff_y = (y - ant.y)
        diff_z = (z - ant.height)
        d = math.sqrt(diff_x ** 2 + diff_y ** 2 + diff_z ** 2)
        if diff_y == 0:
            h_angle = 180
        else:
            h_angle = math.atan2(diff_y , diff_x) * 180 / const.pi
        #print(round(h_angle))
        h_angle = int(round(h_angle - ant.azimuth))
        if h_angle < 0:
            h_angle = 360 + h_angle
        if (diff_x == 0 and diff_y == 0):
            v_angle = 180
        else:
            v_angle = math.atan2(diff_z , math.sqrt(diff_x ** 2 + diff_y ** 2)) * 180 / const.pi
        if v_angle < 0:
            v_angle = 360 + v_angle
        v_angle = int(round(v_angle - ant.mec_tilt))
        if h_angle < 0:
            h_angle = 360 + h_angle
        if v_angle == 360:
            v_angle = 0
        #print(d, h_angle, v_angle)
        attenuation = 10 ** ((horizontal_diagram[h_angle] + vertical_diagram[v_angle]) / 10)
        if attenuation > 31.62:
            attenuation = 31.62
        #print(h_angle, horizontal_diagram[h_angle], v_angle, vertical_diagram[v_angle], attenuation)
        result += (7 / d * math.sqrt(ant.erp / attenuation) ) ** 2
    result =  round(math.sqrt(result), 2)
    return (result)


#-----------------
#
#-----------------

r = 6371000
meter_degree_lat = 111132.92 - 559.82 * math.cos(2 * south * const.degree) + 1.175 * math.cos(4 * south * const.degree)
meter_degree_lon = 111412.84 * math.cos(south * const.degree) - 93.5 * math.cos(3 * south * const.degree)
#meter_degree_lat = r * const.degree
#meter_degree_lon = r * const.degree

site_x = (base_lon - west) * meter_degree_lon
site_y = (base_lat - south) * meter_degree_lat
endpoint = 'https://maps.googleapis.com/maps/api/elevation/json'
options = {'locations': str(base_lat) + ',' + str(base_lon), 'key': google_api_key}
response = requests.get(endpoint, options)
results = json.loads(response.text)[u'results']
site_z = round(int(results[0][u'elevation']))
print(site_z)

if site == "ZH_0050A":
    site_x += 13.5
    site_y -= 13.5
if site == "GE_0002A":
    site_x += 10
    site_y += 5
get_elevation = True
buildings = []
nodes = []

data = json.loads(text)

a = data[u'elements']
for x in a:
    if u'nodes' in x:
        h = {'id': x[u'id'],'nodes': x[u'nodes']};
        if u'height' in x:
            h['height'] = x[u'height']
        else:
            h['height'] = 20 #default height
        buildings.append(h)
    if x[u'type'] == u'node':
        nodes.append( [x[u'lat'], x[u'lon'], x[u'id']] )

i = 0;
loc = "";
nodes2 = {}
endpoint = 'https://maps.googleapis.com/maps/api/elevation/json'
#print(nodes)
for coord in nodes:
    if (i % 50) == 0:
        if i != 0:
            options = {'locations': loc, 'key': google_api_key}
            if get_elevation:
                response = requests.get(endpoint, options)
            for j in range(50):
                n = nodes[i - 50 + j]
                if get_elevation:
                    elevation = json.loads(response.text)[u'results'][j]
                    nodes2[n[2]] = [n[0], n[1], int(elevation[u'elevation']) - site_z]
                else:
                    elevation = 0
                    nodes2[n[2]] = [n[0], n[1], 0]
        loc = str(coord[0]) + ',' + str(coord[1])
    else:
        loc += ('|' + str(coord[0]) + ',' + str(coord[1]) )
    i += 1
#print(loc);

options = {'locations': loc, 'key': google_api_key}
if get_elevation:
    response = requests.get(endpoint, options)

for j in range(i % 50):
    n = nodes[i - (i % 50) + j]
    if get_elevation:
        elevation = json.loads(response.text)[u'results'][j]
        nodes2[n[2]] = [n[0], n[1], elevation[u'elevation']]
    else:
        elevation = 0
        nodes2[n[2]] = [n[0], n[1], 0]


for index,coord in nodes2.iteritems():
    y = (coord[0] - south) * meter_degree_lat - site_y
    x = (coord[1] - west) * meter_degree_lon - site_x
    nodes2[index][0] = round(x, 2)
    nodes2[index][1] = round(y, 2)


fig1 = plt.figure()
plt.xlim(-100, 100)
plt.ylim(-100, 100)


ax1 = fig1.add_subplot(111)


ax1.plot([0], [0], 'og')
antennas_x = []
antennas_y = []
for ant in antennas:
    ax = ant.x
    ay = ant.y
    antennas_x.append(ax)
    antennas_y.append(ay)
    ax1.plot([ax, ax + math.sin(ant.azimuth * const.degree) * 10], [ay, ay + math.cos(ant.azimuth * const.degree) * 10], 'r')
    #circle = plt.Circle((site_x + ant.x, site_y + ant.y), ant.perimeter, color='r', fill = False)
    #ax1.add_artist(circle)

'''
f = open("data/" + site + "_Omens.csv")
content = f.readlines()
content.pop(0)
omens_x = []
omens_y = []
for line in content:
    arr = line.split(';')
    index =int(arr[0])
    x = float(arr[1])
    y = float(arr[2])
    omens_x.append(x)
    omens_y.append(y)
#    if index == 2:
    z = float(arr[3])
    e = float(arr[4])
    a = compute([x, y, z])
    print(arr[0], a, e)
ax1.plot(omens_x, omens_y, '.g')
'''


#ax.plot([site_x + result.x[0]], [site_y + result.x[1]], '.g' )
ax1.plot(antennas_x, antennas_y, '.r')

paths = []
for b in buildings:
    #print ("--new building " + str(b['id']))
    flag = True
    arr = []
    for node in b['nodes']:
        if flag:
            flag = False
        else:
            arr.append( [nodes2[node][0], nodes2[node][1]])
            #print nodes2[node]

    polygon = np.array(arr)
    arr.append(arr[0])
    path = Path(arr)
    print(path.vertexes)
    b['path'] = path
    ax1.add_patch(
        patches.Polygon(
            polygon,
            True,
            fill = False
        )
    )
    #print '\n'

def to_minimize(arr, path):
    point = path.get_point(arr[0] / 1000.0)
    z = arr[1]
    return - compute([point[0], point[1], z])

result_x = []
result_y = []
final = []
for b in buildings:
    i = 0
    z = 0
    for a in b['nodes']:
        node = nodes2[a]
        z += node[2]
        i += 1
    z /= i
    b['alt'] = z
    #print(x, y)
    bnds = ((0.0, 100.0), (b['alt'], b['height'] + b['alt']))
    result = opt.brute(to_minimize, bnds, args = (b['path'],))
    point = b['path'].get_point(result[0] / 1000.0)
    tmp = [point[0], point[1], result[1]]
    f = compute(tmp)
    if f > 4:
        final.append([tmp[0], tmp[1], tmp[2], f])
    result_x.append(tmp[0])
    result_y.append(tmp[1])
    print(result)
    print (tmp, f)
ax1.plot(result_x , result_y , '.b')

fig1.savefig(site + '_map.png', dpi=90, bbox_inches='tight')

f = open(site + "_Critical_Omens.csv", "w")
string = "OMEN_ID;X;Y;Z;Efield;Approved\n"
f.write(string)
i = 0
for result in final:
    i += 1
    string = str(i) + ';' + str(result[0]) + ';' + str(result[1]) + ';' + str(result[2]) + ';' + str(result[3]) + ';'
    if (result[3] > 5):
        string += 'No\n'
    else:
        string += 'Yes\n'
    f.write(string)
