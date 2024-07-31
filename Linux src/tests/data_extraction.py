
import os
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from PIL import Image
import tempfile
from datetime import datetime, timedelta
import numpy as np
from scipy.optimize import curve_fit
import re




def get_detailed_metadata(image_path):
    """Use ExifTool to extract image metadata.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: The metadata as a string.

    Raises:
        FileNotFoundError: If ExifTool is not installed or not found in PATH.
    """
    # Run the 'exiftool' command and capture the output
    try:
        result = subprocess.run(['exiftool', image_path], stdout=subprocess.PIPE, text=True)
        return result.stdout
    except FileNotFoundError:
        return "ExifTool is not installed or not found in PATH."

def parse_metadata_to_dict(metadata):
    metadata_dict = {}
    for line in metadata.strip().split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            metadata_dict[key] = value
    return metadata_dict


def extract_data(folder_path):
    data_list = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')):
            file_path = os.path.join(folder_path, filename)
            try:
                metadata = get_detailed_metadata(file_path)
                data_dict = parse_metadata_to_dict(metadata)
                if all(key in data_dict for key in ['Relative height', 'Flight Roll Degree', 'Flight Yaw Degree', 'Flight Pitch Degree', 'Flight X speed', 'Flight Y speed', 'Flight Z speed', 'File Modification Date/Time']):
                    data_dict['Relative height'] = float(data_dict['Relative height'].split(' ')[0])
                    data_dict['Flight Roll Degree'] = float(data_dict['Flight Roll Degree'].replace('+', '').strip())
                    data_dict['Flight Yaw Degree'] = float(data_dict['Flight Yaw Degree'].replace('+', '').strip())
                    data_dict['Flight Pitch Degree'] = float(data_dict['Flight Pitch Degree'].replace('+', '').strip())
                    data_dict['Flight X speed'] = float(data_dict['Flight X speed'].split(' ')[0])
                    data_dict['Flight Y speed'] = float(data_dict['Flight Y speed'].split(' ')[0])
                    data_dict['Flight Z speed'] = float(data_dict['Flight Z speed'].split(' ')[0])
                    data_dict['File Name'] = filename
                    file_modification_date = data_dict.get('File Modification Date/Time', 'Unknown')
                    if file_modification_date != 'Unknown':
                        data_dict['File Modification Date/Time'] = datetime.strptime(file_modification_date, "%Y:%m:%d %H:%M:%S%z")
                    
                    data_list.append(data_dict)
            except Exception as e:
                print(f"Failed to process {filename}: {e}")

    data_list.sort(key=lambda x: x['File Modification Date/Time'])
    return data_list