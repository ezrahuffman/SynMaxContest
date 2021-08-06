import csv

import pandas as pd
import math

# sort by ship

numberOfPorts = 802000
R = 6373.0
Epsilon = 10  # kilometers
minSpeed = .3 # knots


# determine what ports the ship visits

# use ml to predict future points using past points and use points given for testing

def ConvertToMinutes(date):
    arr = date.split(" ");
    date = arr[0].split("/")
    months = int(date[0])
    days = int(date[1])
    year = date[2]  # not used because every year is 2019

    time = arr[1].split(":")
    hours = int(time[0])
    mins = int(time[1])

    return [(((((months * 30) + days) * 24) + hours) * 60) + mins, mins, hours, days, months]


def ConvertFromMinutesToDateStr(dateArr):
    retArr = ["", ""]

    mins = dateArr[1]
    hrs = dateArr[2]
    days = dateArr[3]
    months = dateArr[4]
    months_days_year = [str(months), str(days), '2019']
    retArr[0] = "/".join(months_days_year)
    hrs_mins = [str(hrs), str(mins)]
    retArr[1] = ":".join(hrs_mins)

    return " ".join(retArr)

# vessel,datetime,lat,long,heading,speed,draft
class Lat_Long:

    def __init__(self, lat, long):
        self.lat = float(lat)
        self.long = float(long)

    def __eq__(self, other):
        return self.lat == other.lat and self.long == other.long

    # def __hash__(self):
    # p1 = 73856093
    # p2 = 19349663
    # val = int(self.lat * p1) ^ int(self.long * p2) % numberOfPorts
    # return val


class TrackingPoint:
    def __init__(self, shipNumber, date, lat, long, heading, speed, draft):
        self.shipNumber = shipNumber
        if type(date) is type([1,2]):
            self.date = date
        else:
            self.date = ConvertToMinutes(date)
        self.latLong = Lat_Long(lat, long)
        self.heading = heading
        self.speed = speed
        self.draft = draft


def TimeStamp(currPoint):
    return currPoint.date[0]


class Boat:
    def __init__(self, voyageNumber):
        self.voyageNumber = voyageNumber
        self.points = sorted([])
        self.ports = sorted([], key=TimeStamp)
        self.portNames = []
        self.lastPort = Lat_Long(-1, -1)

    def Add(self, currPoint):
        self.points.append(currPoint)

        shipPort = GetPort(currPoint)
        # need to add sorting by time
        if shipPort != Lat_Long(-1, -1) and shipPort != self.lastPort:
            self.ports.append(TrackingPoint(self.voyageNumber, currPoint.date, shipPort.lat, shipPort.long, currPoint.heading, currPoint.speed, currPoint.draft))
            self.portNames.append("{" + str(shipPort.lat) + ", " + str(shipPort.long) + "}")

        self.lastPort = port


# Get the port if it exists else return -1
def GetPort(currPoint):
    lat1 = math.radians(currPoint.latLong.lat)
    long1 = math.radians(currPoint.latLong.long);

    for shipPort in portList:
        lat2 = math.radians(shipPort.lat)
        long2 = math.radians(shipPort.long)

        dlong = long2 - long1
        dlat = lat2 - lat1

        # Haversine formula
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlong / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        dist = R * c

        # print(dist)
        if dist < Epsilon:
            return shipPort
    return Lat_Long(-1, -1)


def FindAllVoyages(allPorts):

    p1 = None
    p2 = None

    stopped = False

    returnArr = []
    lastTimeInPort = None

    for shipPort in allPorts:
        if stopped:
            if shipPort.speed > minSpeed:
                # starting to move again
                # ship has to leave from last port it arrived at
                if shipPort.latLong != p2.latLong:
                    p1 = lastTimeInPort
                else:
                    p1 = p2
                stopped = False
            elif shipPort.latLong == p2.latLong:
                # still in last port
                lastTimeInPort = shipPort
        else:
            if shipPort.speed <=minSpeed:
                # arriving at first port
                if p1 == None:
                    p2 = shipPort
                    stopped = True
                #arriving at next port (not the same as port that was last departed from)
                elif shipPort.latLong != p1.latLong:
                    p2 = shipPort
                    returnArr.append([p1, p2])
                    stopped = True
                # still in the same port (don't log as stopped)
                else:
                    stopped = False

    return returnArr




#def YMD_To_Sec(ymd):
    #ymd.par


# dictionary of boats
boats = {}
ports = {}

portList = []

rowcount = 0

# import contents from file
with open('ports.csv', newline='') as portsfile:
    reader = csv.reader(portsfile, delimiter=' ', quotechar='}')
    for row in reader:
        row = row[0].split(",")
        # create LatLong point with given row
        port = Lat_Long(row[1], row[2])

        ##create dictionary of ports
        if port.lat not in ports:
            ports[port.lat] = row[0]
        portList.append(port)

with open('tracking.csv', newline='') as trackingfile:
    reader = csv.reader(trackingfile, quotechar='}')
    for row in reader:
        rowcount+=1
        # create tracking point with given row

        # find a better way to deal with null values
        if (row[4] == 'NULL'):
            row[4] = 1
        if (row[5] == 'NULL'):
            row[5] = 1
        if (row[6] == 'NULL'):
            row[6] = 1
        point = TrackingPoint(row[0], row[1], row[2], row[3], float(row[4]), float(row[5]), float(row[6]))

        # create dictionary of boats
        if row[0] not in boats:
            newBoat = Boat(row[0])
            boats[row[0]] = newBoat
        boats[row[0]].Add(point)

# sort by ship

# sort ship points by time

# determine what ports the ship visits
with open('voyages.csv', 'w', newline='') as voyagefile:
    voyageWriter = csv.writer(voyagefile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    voyageWriter.writerow(['vessel', 'begin_date', 'end_date', 'begin_port_id', 'end_port_id'])
    for key in boats:
        boat = boats[key]
        boat.ports.sort(key=TimeStamp)
        startingPort = boat.ports[0]
        startingPortID = ports[startingPort.latLong.lat]
        endingPort = boat.ports[len(boat.ports) - 1]
        endingPortID = ports[endingPort.latLong.lat]
        # determine when arriving at ending port (first recorded time getting to port)
        voyagePorts = FindAllVoyages(boat.ports)

        string = ""
        endingPortSet = False
        for portSet in voyagePorts:
            startingPort = portSet[0]
            startingPortID = ports[startingPort.latLong.lat]
            endingPort = portSet[1]
            endingPortID = ports[endingPort.latLong.lat]

            finalStartDate = ConvertFromMinutesToDateStr(startingPort.date)
            finalEndDate = ConvertFromMinutesToDateStr(endingPort.date)

            voyageWriter.writerow([key, finalStartDate, finalEndDate, startingPortID, endingPortID])

with open('predict.csv', 'w', newline='') as predictfile:
    predictWriter = csv.writer(predictfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    predictWriter.writerow(['vessel', 'begin_port_id', 'end_port_id', 'voyage'])
    for key in boats:
        boat = boats[key]
        boat.ports.sort(key=TimeStamp)
        startingPort = boat.ports[0]
        startingPortID = ports[startingPort.latLong.lat]
        endingPort = boat.ports[len(boat.ports) - 1]
        endingPortID = ports[endingPort.latLong.lat]
        # determine when arriving at ending port (first recorded time getting to port)

        string = ""
        endingPortSet = False
        for port in boat.ports:
            # determine when leaving starting port (last recorded time leaving port)
            if port.latLong == startingPort.latLong:
                startingPort = port

            # determine when arriving at ending port (first recorded time getting to port)
            if port.latLong == endingPort.latLong and not endingPortSet:
                endingPort = port
                endingPortSet = True
            #string += "{" + str(port.latLong.lat) +", " + str(port.latLong.long) + ", " + str(port.date) + "}, "
        #startstring = "{" + str(startingPort.latLong.lat) + ", " + str(startingPort.latLong.long) + "}(" + startingPortID + ")"
        #endstring = "{" + str(endingPort.latLong.lat) + ", " + str(endingPort.latLong.long) + "}(" + endingPortID + ")"
        #print(str(boat.voyageNumber) + ": " + "starting port " + startstring + "  endingPort " + endstring + "   ports: " + string)

        finalStartDate = ConvertFromMinutesToDateStr(startingPort.date)
        finalEndDate = ConvertFromMinutesToDateStr(endingPort.date)

        testToPandas = pd.to_datetime(finalStartDate)
        testToPandas = pd.to_datetime(finalEndDate)
        for voyageID in range(1, 4):
            predictWriter.writerow([key, startingPortID, endingPortID, str(voyageID)])

# use ml to predict future points using past points and use points given for testing
