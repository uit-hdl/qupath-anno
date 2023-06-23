#!/usr/bin/env -S python -m IPython
""" Script to convert Domore dataset to QuPath, for setting up a project
"""
import sys
from collections import defaultdict

import configparser
import argparse
from paquo.images import QuPathImageType
from paquo.colors import QuPathColor
from paquo.classes import QuPathPathClass
from paquo.projects import QuPathProject
from shapely.geometry import Polygon, CAP_STYLE, JOIN_STYLE, LineString
from tqdm import tqdm
import glob
import re
import os

interval = 1
kwargs = {"cap_style": CAP_STYLE.square, "join_style": JOIN_STYLE.mitre}

CLASSNAMES = ["Unused", "Border"]
CLASSCOLORS = [0000000, -9408287] # black

parser = argparse.ArgumentParser(description='DoMore dataset to Qupath Converter')
parser.add_argument('-s', '--src-dir', default='./unn_data/Aperio/R46', type=str,
                    metavar='SRC', help='source directory of data', dest='src_dir')
args = parser.parse_args()

if not os.path.exists(args.src_dir):
    print (f"Source directory {args.src_dir} does not exist")
    sys.exit(1)


def add_qupath_classes(classnames: list, colors: list, qp):
    """Add custom classes and corresponding colors to QuPath project"""
    if len(classnames) < len(colors):
        raise ValueError("classnames don't have enough colors, fix code")
    new_classes = []
    for class_name, class_color in zip(classnames, colors):
        new_classes.append(
            QuPathPathClass(name=class_name,
                            color=QuPathColor.from_java_rgba(class_color))
        )
    qp.path_classes = new_classes  # Setting QuPathProject.path_class always replaces all classes
    print("Adding project classes to new QuPath project:")
    for path_class in qp.path_classes:
        print(f"'{path_class.name}'")


def add_annotations(qpout, entry, ann: list, allshapes: list):
    """
    For the original sub-patch ROI with detection, assign a class 

    Parameters
    ----------
    qpout : str
        Project to add annotations to
    entry : something
        image to add annotations to
    ann : list
        annotation with detections from old qpproj
    allshapes : list
        detections from QuPath with added classes

    Returns
    -------
    an empty void
    """
    for classified_shape in allshapes:
        try:
            annotation = entry.hierarchy.add_annotation(roi=classified_shape,
                path_class=qpout.path_classes[classified_shape.class_id] if hasattr(classified_shape, "class_id") else None)
            annotation.name = str(classified_shape.geom_type) # This is the name of annotation that will pop up in QuPath
        except IndexError as ie:
            print(f"Found classification with class id {classified_shape.class_id}, ignoring")
    if ann: # Add the old/original annotations to the new project as they were
        for annotation_shape in ann:
            entry.hierarchy.add_annotation(roi=annotation_shape)


def get_polypons(config_polygon):
    '''
    Return: polygon information, like 
    {
        0:[(x0,y0), (x1,y1),...],
        1:[(x0,y0), (x1,y1),...],
        ...
    }
    '''
    
    poly_points = defaultdict(list)
    l_it = list(((el.split('_')[2:4]) for el in (list(config_polygon))))
    for i in range(0, len(l_it), 2):
        poly, num = l_it[i]
        poly_points[int(poly)].append(
            (float(config_polygon[f"poly_x_{poly}_{num}"]), 
             float(config_polygon[f"poly_y_{poly}_{num}"]))
        )
    return poly_points

if __name__ == "__main__":
    patterning = lambda x: re.sub("([\[\]])", "[\\1]", x)
    polies = defaultdict(list)
    # TODO: consider adding meta key to distinguish other tissue from regular
    # https://paquo.readthedocs.io/en/latest/quickstart.html
    file_list = glob.glob(f"{args.src_dir}/R46*")
    file_list = sorted(file_list)

    for folder in tqdm(file_list, desc="Regular tissue"):
        itn_file = glob.glob(f"{folder}/*.itn")[0]
        svs_file = glob.glob(f"{folder}/*.svs")[0]

        config = configparser.ConfigParser()
        config.read(itn_file)
        polycoords = get_polypons(config['Polygon'])
        for coords in polycoords.values():
            poly = Polygon(coords)
            polies[svs_file].apped(poly)
    file_list = glob.glob(os.path.join(f"{args.src_dir}", "Other_tissue", "*"))
    file_list = sorted(file_list)
    polycoords = defaultdict(list)
    for folder in tqdm(file_list, desc="Other tissue"):
        itn_file = glob.glob(f"{folder}/*.itn")
        if len(itn_file) == 0:
            continue
        itn_file = itn_file[0]
        svs_file = glob.glob(f"{folder}/*.svs")[0]

        config = configparser.ConfigParser()
        config.read(itn_file)
        polycoords = get_polypons(config['Polygon'])
        for coords in polycoords.values():
            poly = Polygon(coords)
            polies[svs_file].append(poly)

    with QuPathProject('domore_qupath', mode='a') as qpout:
        print(f"Created new QuPath project: '{qpout.name}'.")
        add_qupath_classes(CLASSNAMES, CLASSCOLORS, qpout)
        for file_path, polygons in tqdm(polies.items()):
            entry = qpout.add_image(file_path, image_type=QuPathImageType.BRIGHTFIELD_H_E, allow_duplicates=True)
            add_annotations(qpout, entry, [], polygons)
