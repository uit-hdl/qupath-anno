#!/usr/bin/env -S python -m IPython

import itertools
from collections import defaultdict
import os
import configparser
from tqdm import tqdm
import pathlib
import shutil

import numpy as np
import scipy.io as sio
from paquo.projects import QuPathProject
from shapely.geometry import MultiPoint, Polygon, Point

# TODO:

annotation_class_mapping = {
    'Unused': 0,
    'Border': 1,
    }

def read_qupath_annotations(image):
    annotations = image.hierarchy.annotations  
    return [(ann.roi, ann.name) for ann in annotations]

def rm_n_mkdir(dir_paths):
    """Remove and make directory."""
    for dir_path in dir_paths:
        if os.path.isdir(dir_path):
            shutil.rmtree(dir_path)
        os.makedirs(dir_path)


def write_polypons(config_polygon):
    poly_points = defaultdict(list)
    l_it = list(((el.split('_')[2:4]) for el in (list(config_polygon))))
    for i in range(0, len(l_it), 2):
        poly, num = l_it[i]
        poly_points[int(poly)].append(
            (float(config_polygon[f"poly_x_{poly}_{num}"]),
             float(config_polygon[f"poly_y_{poly}_{num}"]))
        )
    return poly_points


def export_annotations(args):
    ''' Export annotations in a format compatible with Hover-Net
    '''

    image_height, image_width, image_name, annotations = args
    config = configparser.ConfigParser()
    config['Polygon'] = {}
    for i,(ann, ann_class) in tqdm(enumerate(annotations)):
        poly = Polygon(ann)
        points = []
        for j, (x,y) in enumerate(zip(*poly.boundary.coords.xy)):
            #points.append((x,y))
            config['Polygon'][f"Poly_X_{i}_{j}"] = f"{x}"
            config['Polygon'][f"Poly_Y_{i}_{j}"] = f"{y}"
    with open(image_name, 'w') as configfile:
        config.write(configfile)

if __name__ == "__main__":
    with QuPathProject('domore_qupath', mode='r') as qp:
        print(f"Opened project ‘{qp.name}’ ")
        print(f"Project has {len(qp.images)} image(s).")
        rm_n_mkdir(["./annotations/"])
        image_args = [()] * len(qp.images)
        for i,image in enumerate(qp.images):
            folder_name = pathlib.Path(image.image_name).stem.split("_")[0]
            image_name = pathlib.Path(image.image_name).stem + ".itn"
            rm_n_mkdir([f"./annotations/{folder_name}"])
            image_args[i] = (image.height, image.width, f"./annotations/{folder_name}/{image_name}", read_qupath_annotations(image))
            export_annotations(image_args[i])
