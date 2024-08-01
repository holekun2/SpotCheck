import os
import subprocess
import multiprocessing
import re
from datetime import datetime
from tqdm import tqdm
import pickle
from multiprocessing import Pool, Value
import pandas as pd
from geopy.distance import geodesic
import math
from typing import List, Dict, Any, Tuple
import logging
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

PHOTO_BASE_PATH = r'Shared\photos\cable anchor'


class DataImportAndPreprocessing:
    def __init__(self):
        pass

    def write_data_to_file(self, data: Any, filename: str) -> None:
        with open(filename, 'wb') as f:
            pickle.dump(data, f)

class DJIDroneDataImport(DataImportAndPreprocessing):
    def __init__(self):
        super().__init__()
        self.keys_to_extract = ['File Name', 'Create Date', 'Exposure Time', 'F Number', 'Exposure Program', 'ISO', 'Sensitivity Type', 'Components Configuration', 'Shutter Speed Value', 'Aperture Value',
                                'Exposure Compensation', 'Max Aperture Value', 'Light Source', 'Focal Length', 'Custom Rendered', 'Exposure Mode', 'White Balance', 'Digital Zoom Ratio', 'Focal Length In 35mm Format', 'Scene Capture Type',
                                'Gain Control', 'Contrast', 'Saturation', 'Sharpness', 'GPS Version ID', 'Relative Altitude', 'Gimbal Pitch Degree', 'Gimbal Yaw Degree', 'Flight Yaw Degree', 'Flight X Speed', 'Flight Y Speed', 'GPS Latitude', 'GPS Longitude',
                                'Preview Image', 'Circle Of Confusion', 'Field Of View', 'GPS Position', 'Hyperfocal Distance', 'Light Value', 'Image Width', 'Image Height']
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler('dji_data_extraction.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)

    def dms_to_dd(self, dms: str) -> float:
        try:
            direction = dms[-1]
            dms = dms.strip('NSWE ')
            parts = dms.replace('deg', '').replace('\'', '').replace('\"', '').split()
            degrees = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            decimal_degrees = degrees + (minutes / 60) + (seconds / 3600)
            if direction in ['S', 'W']:
                decimal_degrees *= -1
            return decimal_degrees
        except Exception as e:
            self.logger.error(f"Error converting DMS to decimal degrees: {e}")
            self.logger.error(f"Input DMS: {dms}")
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(subprocess.CalledProcessError))
    def get_detailed_metadata(self, file_path: str, keys_to_extract: List[str]) -> Dict[str, str]:
        try:
            command = ['exiftool'] + [file_path]
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            lines = result.stdout.split('\n')
            metadata = {}
            for line in lines:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    if key in keys_to_extract:
                        metadata[key] = value
            return metadata
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Exiftool error for {file_path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error processing {file_path}: {e}")
            raise

    def process_file(self, file_path: str, keys_to_extract: List[str]) -> Dict[str, Any]:
        try:
            metadata = self.get_detailed_metadata(file_path, keys_to_extract)

            if keys_to_extract is None or all(key in metadata for key in keys_to_extract):
                for key in ['Gimbal Pitch Degree', 'Relative Altitude', 'Flight Yaw Degree']:
                    if key in metadata and isinstance(metadata[key], str):
                        metadata[key] = re.sub(r'[^\d.-]', '', metadata[key])

                gps_latitude_dms = metadata.get('GPS Latitude', None)
                gps_longitude_dms = metadata.get('GPS Longitude', None)

                if gps_latitude_dms and gps_longitude_dms:
                    gps_latitude_dd = self.dms_to_dd(gps_latitude_dms)
                    gps_longitude_dd = self.dms_to_dd(gps_longitude_dms)
                    metadata['GPS Latitude'] = gps_latitude_dd
                    metadata['GPS Longitude'] = gps_longitude_dd

                file_modification_date_time_str = metadata.get('Create Date', None)
                if file_modification_date_time_str:
                    try:
                        file_modification_date_time_dt = datetime.strptime(file_modification_date_time_str, '%Y:%m:%d %H:%M:%S%z')
                        file_modification_date_time_dt = file_modification_date_time_dt.replace(tzinfo=None)
                        metadata['Create Date'] = file_modification_date_time_dt
                    except ValueError:
                        try:
                            file_modification_date_time_dt = datetime.strptime(file_modification_date_time_str, '%Y:%m:%d %H:%M:%S')
                            metadata['Create Date'] = file_modification_date_time_dt
                        except ValueError:
                            self.logger.error(f"Failed to parse 'Create Date' for {metadata.get('File Name', 'unknown file')}: {file_modification_date_time_str}")
                            metadata['Create Date'] = None

                return metadata
            else:
                missing_keys = [key for key in keys_to_extract if key not in metadata]
                self.logger.error(f"Missing keys in metadata for {file_path}: {missing_keys}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to process {file_path}: {str(e)}")
            return None

    def process_file_with_progress(self, args: Tuple[str, List[str]]) -> Dict[str, Any]:
        file_path, keys_to_extract = args
        return self.process_file(file_path, keys_to_extract)

    def extract_data(self, folder_path: str) -> List[Dict[str, Any]]:
        files = []
        for root, _, filenames in os.walk(folder_path):
            for filename in filenames:
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')):
                    files.append(os.path.join(root, filename))

        # Sort files by creation time
        files.sort(key=lambda x: os.path.getctime(x))

        progress_counter = multiprocessing.Value('i', 0)

        with multiprocessing.Pool() as pool:
            flight_metadata_list = []
            total_files = len(files)
            with tqdm(total=total_files, desc="Processing files", ncols=100) as progress_bar:
                for metadata in pool.imap_unordered(self.process_file_with_progress, [(file_path, self.keys_to_extract) for file_path in files]):
                    if metadata is not None:
                        # Create a unique identifier using timestamp and original filename
                        create_date = metadata.get('Create Date')
                        if create_date:
                            timestamp = create_date.strftime('%Y%m%d%H%M%S')
                            original_filename = metadata['File Name']
                            unique_identifier = f"{timestamp}_{original_filename}"
                            metadata['Unique Identifier'] = unique_identifier
                        flight_metadata_list.append(metadata)
                    with progress_counter.get_lock():
                        progress_counter.value += 1
                        progress_bar.update(progress_counter.value - progress_bar.n)

        flight_metadata_list = [metadata for metadata in flight_metadata_list if metadata is not None]
        flight_metadata_list.sort(key=lambda x: x['Create Date'])
        return flight_metadata_list


class SalesforceDataImport(DataImportAndPreprocessing):
    def __init__(self):
        super().__init__()

    def import_salesforce_data(self, excel_file_path: str) -> List[Dict[str, Any]]:
        try:
            # Read the Excel file
            df = pd.read_excel(excel_file_path)

            # Convert the DataFrame to a list of dictionaries
            data_list = df.to_dict('records')

            return data_list
        except Exception as e:
            #prinf"Error importing Salesforce data from Excel file: {e}")
            return []

    def extract_and_save_salesforce_data(self, excel_file_path: str, output_file_path: str) -> None:
        try:
            # Import the Salesforce data from the Excel file
            salesforce_data = self.import_salesforce_data(excel_file_path)

            # Write the Salesforce data to a pickle file
            self.write_data_to_file(salesforce_data, output_file_path)

            print(f"Salesforce data has been written to {output_file_path}")
        except Exception as e:
            print(f"Error extracting and saving Salesforce data: {e}")




class SiteLocation(DataImportAndPreprocessing):
    def __init__(self):
        super().__init__()
        self.metadata: List[Dict[str, Any]] = []
        self.inspection_data: List[Dict[str, Any]] = []



    def is_valid_coordinate(self, lat: float, lon: float) -> bool:
        return (lat is not None and lon is not None and 
                isinstance(lat, (int, float)) and isinstance(lon, (int, float)) and
                not math.isnan(lat) and not math.isnan(lon) and
                -90 <= lat <= 90 and -180 <= lon <= 180)

    def find_matching_site(self, photo_data: Dict[str, Any]) -> Dict[str, Any]:
        #print('photo data:', photo_data)
        photo_lat = photo_data.get('GPS Latitude')
        photo_lon = photo_data.get('GPS Longitude')
        


        if not self.is_valid_coordinate(photo_lat, photo_lon):
            print(f"Invalid coordinates: {photo_lat}, {photo_lon}")
            return {'File Name': photo_data.get('File Name', 'Unknown File'),
                    'Site ID': 'Invalid Coordinates',
                    'Latitude': photo_lat,
                    'Longitude': photo_lon,
                    'Pilot Name': 'Unknown Pilot', # Return 'Unknown Pilot' directly
                    'Matched Index': -1}

        nearest_site = None  # Initialize nearest_site here
        nearest_distance = float('inf')
        nearest_index = -1

        for site_index, site in enumerate(self.inspection_data):
            site_lat = site.get('Latitude')
            site_lon = site.get('Longitude')
            if self.is_valid_coordinate(site_lat, site_lon):
                try:
                    distance = geodesic((photo_lat, photo_lon), (site_lat, site_lon)).feet
                    
                    if distance < nearest_distance:
                        nearest_distance = distance
                        nearest_site = site
                        nearest_index = site_index
                        #print(f"Found nearest site: {nearest_site.get('Site ID', 'Unknown Site')} at distance {nearest_distance} feet")
                except ValueError:
                    print(f"Error calculating distance for site {site.get('Site ID', 'Unknown')}")
                    continue

        if nearest_site and nearest_distance <= 500:
            #print(f"Matched to site: {nearest_site.get('Site ID', 'Unknown Site')} at distance {nearest_distance} feet")
            return {'File Name': photo_data.get('File Name', 'Unknown File'),
                    'Site ID': nearest_site.get('Site ID', 'Unknown Site'),
                    'Latitude': photo_lat,
                    'Longitude': photo_lon,
                    'Pilot Name': nearest_site.get('Pilot Name', 'Unknown Pilot'),
                    'Matched Index': nearest_index}
        else:
            #print(f"No match found. Nearest site was {nearest_distance} feet away")
            return {'File Name': photo_data.get('File Name', 'Unknown File'),
                    'Site ID': 'Unknown Site',
                    'Latitude': photo_lat,
                    'Longitude': photo_lon,
                    'Pilot Name': 'Unknown Pilot', # Return 'Unknown Pilot' directly
                    'Matched Index': -1}
            
            
    def process_locations(self) -> None:
        print("Starting process_locations...")
        for photo in tqdm(self.metadata, desc="Processing locations"):
            site_id = self.find_matching_site(photo)
            photo['Site ID'] = site_id
        print(f"Finished processing locations. Processed {len(self.metadata)} entries.")

    def run_analysis(self, metadata_file: str, inspection_data_file: str, output_file: str) -> List[Dict[str, Any]]:
        print("Loading data...")
        self.load_data(metadata_file, inspection_data_file)
        print(f"Loaded {len(self.metadata)} metadata entries and {len(self.inspection_data)} inspection data entries.")
        
        print("Processing locations...")
        self.process_locations()
        

        return self.metadata
        
        







