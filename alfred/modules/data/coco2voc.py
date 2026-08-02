# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 JinTian.
#
# This file is part of alfred
# (see http://jinfagang.github.io).
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
"""
Convert COCO format annotations to VOC format.

This module provides functionality to convert COCO format dataset
annotations to PASCAL VOC format.
"""
import os
import json
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement
from collections import defaultdict
import shutil
from typing import Dict, List, Any, Optional


def coco2voc(
    coco_dir: str,
    json_file: str,
    output_dir: Optional[str] = None,
    img_dir: Optional[str] = None,
) -> str:
    """
    Convert COCO format annotations to VOC format.

    Args:
        coco_dir: Path to COCO dataset directory (contains images and annotations)
        json_file: Path to COCO annotations JSON file
        output_dir: Output directory for VOC format (default: coco_voc)
        img_dir: Path to COCO images directory (default: coco_dir/images)

    Returns:
        Path to the output VOC directory
    """
    # Load COCO annotations
    with open(json_file, "r") as f:
        coco_data = json.load(f)

    # Set default paths
    if img_dir is None:
        img_dir = os.path.join(coco_dir, "images")
    if output_dir is None:
        output_dir = os.path.join(coco_dir, "VOCdevkit", "VOC2007")

    # Create VOC directory structure
    voc_dir = output_dir
    os.makedirs(os.path.join(voc_dir, "JPEGImages"), exist_ok=True)
    os.makedirs(os.path.join(voc_dir, "Annotations"), exist_ok=True)
    os.makedirs(os.path.join(voc_dir, "ImageSets", "Main"), exist_ok=True)

    # Build category mapping
    categories = {cat["id"]: cat["name"] for cat in coco_data.get("categories", [])}
    cat_id_to_voc_id = {cat_id: idx + 1 for idx, cat_id in enumerate(categories.keys())}

    # Process images and annotations
    images = coco_data.get("images", [])
    annotations = coco_data.get("annotations", [])
    groups = defaultdict(list)

    # Group annotations by image_id
    for ann in annotations:
        groups[ann["image_id"]].append(ann)

    # Create VOC annotations
    for img in images:
        img_id = img["id"]
        file_name = os.path.basename(img["file_name"])
        width = img["width"]
        height = img["height"]

        # Create XML annotation
        annotation = Element("annotation")
        SubElement(annotation, "folder").text = "JPEGImages"
        SubElement(annotation, "filename").text = file_name
        SubElement(annotation, "path").text = os.path.join("JPEGImages", file_name)

        size = SubElement(annotation, "size")
        SubElement(size, "width").text = str(width)
        SubElement(size, "height").text = str(height)
        SubElement(size, "depth").text = "3"

        SubElement(annotation, "segmented").text = "0"

        # Add objects
        if img_id in groups:
            for ann in groups[img_id]:
                obj = SubElement(annotation, "object")
                cat_name = categories.get(ann["category_id"], "unknown")
                cat_id = cat_id_to_voc_id.get(ann["category_id"], 0)

                SubElement(obj, "name").text = cat_name
                SubElement(obj, "pose").text = "Unspecified"
                SubElement(obj, "truncated").text = "0"
                SubElement(obj, "difficult").text = "0"

                bbox = SubElement(obj, "bndbox")
                bbox_data = ann["bbox"]
                SubElement(bbox, "xmin").text = str(int(bbox_data[0]))
                SubElement(bbox, "ymin").text = str(int(bbox_data[1]))
                SubElement(bbox, "xmax").text = str(int(bbox_data[0] + bbox_data[2]))
                SubElement(bbox, "ymax").text = str(int(bbox_data[1] + bbox_data[3]))

        # Write XML file
        xml_path = os.path.join(voc_dir, "Annotations", f"{os.path.splitext(file_name)[0]}.xml")
        tree = ET.ElementTree(annotation)
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)

    # Copy images
    src_img_dir = os.path.join(coco_dir, "images")
    dst_img_dir = os.path.join(voc_dir, "JPEGImages")
    if os.path.exists(src_img_dir):
        for file_name in os.listdir(src_img_dir):
            src_file = os.path.join(src_img_dir, file_name)
            if os.path.isfile(src_file):
                shutil.copy2(src_file, dst_img_dir)

    # Create image sets
    trainval_images = [os.path.splitext(img["file_name"])[0] for img in images]
    with open(os.path.join(voc_dir, "ImageSets", "Main", "trainval.txt"), "w") as f:
        f.write("\n".join(trainval_images))

    return voc_dir


def main():
    """Main entry point for COCO to VOC conversion CLI."""
    import argparse

    parser = argparse.ArgumentParser(description="Convert COCO format to VOC format")
    parser.add_argument("--coco_dir", "-c", required=True, help="Path to COCO dataset directory")
    parser.add_argument("--json_file", "-j", required=True, help="Path to COCO annotations JSON file")
    parser.add_argument("--output_dir", "-o", default=None, help="Output directory for VOC format")
    parser.add_argument("--img_dir", "-i", default=None, help="Path to COCO images directory")

    args = parser.parse_args()

    output_dir = coco2voc(
        coco_dir=args.coco_dir,
        json_file=args.json_file,
        output_dir=args.output_dir,
        img_dir=args.img_dir,
    )

    print(f"Conversion completed! VOC format saved to: {output_dir}")


if __name__ == "__main__":
    main()
