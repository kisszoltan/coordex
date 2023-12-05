#!/usr/bin/env python3

'''
    Copyright (c) 2022 Zoltan Kiss

    Permission is hereby granted, free of charge, to any person obtaining a copy of
    this software and associated documentation files (the "Software"), to deal in
    the Software without restriction, including without limitation the rights to
    use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
    of the Software, and to permit persons to whom the Software is furnished to do
    so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
    CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

try:
    import os
    import sys
    from pathlib import Path
    from exif import Image
    from pyproj import Transformer
    import geopandas as gpd
    from shapely.geometry import Point
except ImportError:
    import subprocess
    subprocess.check_call(
        ["python", '-m', 'pip', 'install', 'exif==1.6.0'])
    subprocess.check_call(
        ["python", '-m', 'pip', 'install', 'pyproj==3.6.1'])
    subprocess.check_call(
        ["python", '-m', 'pip', 'install', 'geopandas==0.14.1'])
    subprocess.check_call(
        ["python", '-m', 'pip', 'install', 'shapely==2.0.2'])


def create_shapefile(coords, dir_name: str, file_name: str = '_coordex.shp'):

    geometry = [Point(lon, lat) for lat, lon in coords]
    gdf = gpd.GeoDataFrame(geometry=geometry, crs="EPSG:4326")

    os.makedirs(dir_name, exist_ok=True)
    gdf.to_file(f'{dir_name}/{file_name}')

    print(f'Shapefile saved as {dir_name}/{file_name}')


def wgs84_to_eov(latitude, longitude):
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:23700")
    return transformer.transform(latitude, longitude)


def decimal_coords(coords, ref):
    decimal_degrees = coords[0] + coords[1] / 60 + coords[2] / 3600
    if ref == "S" or ref == 'W':
        decimal_degrees = -decimal_degrees
    return decimal_degrees


def get_creation_time(file_path):
    return os.path.getctime(file_path)


def image_coordinates(image_path):
    with open(image_path, 'rb') as src:
        img = Image(src)
    if img.has_exif:
        try:
            coords = (decimal_coords(img.gps_latitude, img.gps_latitude_ref),
                      decimal_coords(img.gps_longitude, img.gps_longitude_ref))
        except AttributeError:
            print(f'No coordinates in image {image_path}')
            exit(1)
    else:
        print(f'The image ({image_path}) has no EXIF information')
        exit(1)

    eov = wgs84_to_eov(coords[0], coords[1])
    # return ({"imageTakenTime": img.datetime_original,
    #          "geolocation_lat": coords[0], "geolocation_lng": coords[1],
    #          "eov_x": eov[0], "eov_y": eov[1]})
    return (coords[0], coords[1])


def process_images(directory: str):
    contents = [entry for entry in Path(directory).iterdir()]
    sorted_contents = sorted(
        contents, key=lambda x: get_creation_time(x) if os.path.exists(x) else 0)
    sorted_file_names = [entry.name for entry in sorted_contents]

    for f in sorted_file_names:
        yield image_coordinates(f'{directory}/{f}')


if __name__ == '__main__':
    directory_path = sys.argv[1] if len(sys.argv) == 2 else 'samples'
    if not os.path.exists(directory_path):
        print(f'Directory {directory_path} does not exist.')
        exit(1)
    if not os.path.isdir(directory_path):
        print(f'{directory_path} is not a directory.')
        exit(1)

    coordinates = process_images(directory_path)
    create_shapefile(coordinates, 'shapes',
                     f'{os.path.basename(directory_path)}.shp')
