from typing import Dict, Any
from datetime import datetime
import pandas as pd
from .dji_data_extraction import SiteLocation
from .inspection_reader import InspectionDataReader


class MetadataProcessor:
    @staticmethod
    def parse_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        parsed_metadata: Dict[str, Any] = {}
        key_mapping: Dict[str, str] = {
            'DateTime': 'Create Date',
            'GPSLatitude': 'GPS Latitude',
            'GPSLongitude': 'GPS Longitude',
            'GimbalPitchDegree': 'Gimbal Pitch Degree',
            'FlightYawDegree': 'Flight Yaw Degree',
            'FlightXSpeed': 'Flight X Speed',
            'FlightYSpeed': 'Flight Y Speed',
            'RelativeAltitude': 'Relative Altitude',
            'FileName': 'File Name',
            'ImageWidth': 'Image Width',
            'ImageLength': 'Image Length',
            'DigitalZoomRatio': 'Digital Zoom Ratio'
        }

        for old_key, new_key in key_mapping.items():
            if old_key in metadata:
                value = metadata[old_key]
                
                if new_key == 'Create Date':
                    try:
                        value = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                    except ValueError:
                        pass
                elif new_key in ['File Name', 'GPS Latitude', 'GPS Longitude', 'Gimbal Pitch Degree', 'Flight Yaw Degree', 'Flight X Speed', 'Flight Y Speed', 'Relative Altitude']:
                    try:
                        value = float(value)
                        if new_key == 'GPS Longitude' and value > 0:
                            value = -value
                    except ValueError:
                        pass
                
                parsed_metadata[new_key] = value

        if 'File Name' not in parsed_metadata:
            possible_file_name_keys = ['FileName', 'File Name', 'SourceFile', 'Source File']
            for key in possible_file_name_keys:
                if key in metadata:
                    parsed_metadata['File Name'] = metadata[key]
                    break
            else:
                print("File name not found in metadata")

        if 'Create Date' in parsed_metadata and 'File Name' in parsed_metadata:
            create_date = parsed_metadata['Create Date']
            if isinstance(create_date, datetime):
                timestamp = create_date.strftime('%Y%m%d%H%M%S')
                original_filename = parsed_metadata['File Name']
                unique_identifier = f"{timestamp}_{original_filename}"
                parsed_metadata['Unique Identifier'] = unique_identifier

        return parsed_metadata





    @staticmethod
    def process_and_enrich_metadata(metadata_list, existing_metadata):
        processor = MetadataProcessor()
        site_location = SiteLocation()
        try:
            site_location.inspection_data = InspectionDataReader.read_inspection_data()
        except Exception as e:
            print(f"Error reading inspection data: {str(e)}")
            site_location.inspection_data = []

        processed_metadata = []
        for metadata in metadata_list:
            parsed_metadata = processor.parse_metadata(metadata)
            #print(f"Processing metadata entry: {parsed_metadata}")
            site_info = site_location.find_matching_site(parsed_metadata)
            parsed_metadata.update(site_info)
            processed_metadata.append(parsed_metadata)

        
        print(f"Processed {len(processed_metadata)} metadata entries")

        # Ensure existing_metadata is a list of dictionaries
        print(f"Existing metadata type: {type(existing_metadata)}")
        print(f"Existing metadata content: {existing_metadata}") 

        if existing_metadata and isinstance(existing_metadata[0], dict):
            combined_metadata = existing_metadata + processed_metadata
        else:
            combined_metadata = processed_metadata
            print("Warning: Existing metadata is not in the expected format (list of dictionaries). Using only processed metadata.")

        print(f"Existing {len(existing_metadata)} metadata entries")
        print(f"Combined {len(combined_metadata)} metadata entries")
        return combined_metadata


