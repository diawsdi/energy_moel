#!/usr/bin/env python3
import math

def deg2num(lat_deg, lon_deg, zoom):
    """Convert latitude and longitude to tile coordinates"""
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)

# Bounding box from our query
min_lon, min_lat = -17.529115456507, 12.3308397547445
max_lon, max_lat = -11.3559746297918, 16.6905772844087

# Try different zoom levels
for zoom in [8, 9, 10, 11, 12]:
    print(f"\nZoom level {zoom}:")
    
    # Calculate tile coordinates for the corners of our bounding box
    nw_tile = deg2num(max_lat, min_lon, zoom)
    ne_tile = deg2num(max_lat, max_lon, zoom)
    sw_tile = deg2num(min_lat, min_lon, zoom)
    se_tile = deg2num(min_lat, max_lon, zoom)
    
    print(f"Northwest corner: x={nw_tile[0]}, y={nw_tile[1]}")
    print(f"Northeast corner: x={ne_tile[0]}, y={ne_tile[1]}")
    print(f"Southwest corner: x={sw_tile[0]}, y={sw_tile[1]}")
    print(f"Southeast corner: x={se_tile[0]}, y={se_tile[1]}")
    
    # Calculate the number of tiles needed to cover the bounding box
    width = ne_tile[0] - nw_tile[0] + 1
    height = sw_tile[1] - nw_tile[1] + 1
    print(f"Tiles needed: {width} x {height} = {width * height} tiles")
    
    # Print a few example tile URLs
    print("Example tile URLs:")
    for x in range(nw_tile[0], ne_tile[0] + 1, max(1, (ne_tile[0] - nw_tile[0]) // 3)):
        for y in range(nw_tile[1], sw_tile[1] + 1, max(1, (sw_tile[1] - nw_tile[1]) // 3)):
            print(f"http://localhost:3000/tiles/buildings_energy/{zoom}/{x}/{y}.pbf")
