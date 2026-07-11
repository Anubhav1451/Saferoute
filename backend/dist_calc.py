#!/usr/bin/env python
import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# Coordinates
lat1, lon1 = 28.6315, 77.2167
lat2, lon2 = 29.9660, 77.5540

dist = haversine(lat1, lon1, lat2, lon2)
print(f"Distance: {dist} meters")
print(f"Distance: {dist/1000} km")

# Max segment length for map matching
max_seg = 10000  # meters
num_chunks = math.ceil(dist / max_seg)
print(f"Number of chunks: {num_chunks}")
print(f"Number of waypoints: {num_chunks + 1}")
print(f"Expected route points (ifwe start with first point and add waypoints[1:]): {1 + (num_chunks + 1 - 1)}")  # which is num_chunks + 1
# Actually, we start with the first point, then add waypoints[1:] which has (num_chunks+1 - 1) = num_chunks points
# So total = 1 + num_chunks = num_chunks + 1
print(f"Total points in route: {num_chunks + 1}")