from math import sin, cos, sqrt, atan2, pow, radians, asin

def haversine(lon1, lat1, lon2, lat2, R):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    # 6367 km is the radius of the Earth
    km = R * c
    return km

def m_to_km(m):
    return float(m) * .001

def km_to_m(m):
    return float(m) * 1000

def m_to_mile(m):
    return float(m) * .000621371

def mile_to_m(m):
    return float(m) * 1609.34

def m_to_yd(m):
    return float(m) * 1.09361

def yd_to_m(m):
    return float(m) * .9144
