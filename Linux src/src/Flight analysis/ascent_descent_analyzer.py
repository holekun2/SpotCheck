
import re
import numpy as np
from typing import List, Dict, Any, Tuple
from data_export import export_to_excel
from flight_sorting import save_data_to_file
import pandas as pd
from utils import Utilities
import math
import os
from image_analyzer_gemini import ImageAnalyzerGemini
from dji_data_extraction import PHOTO_BASE_PATH
from prompts import TOWER_TOP_SYSTEM_INSTRUCTION, TOWER_TOP_PROMPT

class AscentDescentAnalyzer:
    def __init__(self, passfail_data: List[Dict[str, Any]], flight_data: pd.DataFrame, ascent_descent_criteria: List[Any]):
        self.passfail_data = passfail_data
        self.flight_data = flight_data
        self.ascent_descent_criteria = ascent_descent_criteria
        self.image_analyzer = ImageAnalyzerGemini()
        self.photo_base_path = PHOTO_BASE_PATH

    def analyze(self, categorized_flights):
        ascent_categories = []
        for category in categorized_flights:
            category_name = category['Flight Category']
            if self.is_ascent_descent_category(category_name):
                self.check_ascent_descent_spacing(category)
                self.calculate_vertical_overlap(category)
                
                if 'ascent' in category_name.lower():
                    ascent_categories.append(category)
                elif 'cable run' in category_name.lower():
                    self.height_check(category)

        if ascent_categories:
            self.height_check_ascent(ascent_categories)

    def is_ascent_descent_category(self, category_name: str) -> bool:
        return any(
            category_name == criterion if isinstance(criterion, str) else criterion.search(category_name)
            for criterion in self.ascent_descent_criteria
        )

    def check_ascent_descent_spacing(self, category: Dict[str, Any], closeness_threshold: float = 0.5):
        photo_names = category['Photos']
        flight_data_category = self.flight_data[self.flight_data['Unique Identifier'].isin(photo_names)]
        
        relative_altitudes = flight_data_category['Relative Altitude'].tolist()
        
        # Calculate altitude differences between consecutive pairs
        altitude_diffs = np.abs(np.diff(relative_altitudes))
        
        # Calculate the average spacing
        average_spacing = np.mean(altitude_diffs)
        
        # Compare each pair to the average spacing
        close_pairs = []
        for i, diff in enumerate(altitude_diffs):
            if diff < average_spacing * closeness_threshold:
                close_pairs.append((photo_names[i], photo_names[i+1]))
        
        if close_pairs:
            category['Vertical Spacing'] = ('Fail', None)
            #print(f"Warning: The following photo pairs are too close together vertically: {close_pairs}")
            #print(f"Average spacing: {average_spacing:.2f} feet, Closeness threshold: {average_spacing * closeness_threshold:.2f} feet, actual spacing: {diff:.2f} feet")
        else:
            category['Vertical Spacing'] = ('Pass', None)
            #print("Vertical spacing check passed.")
            #print(f"Average spacing: {average_spacing:.2f} feet")
  
    def calculate_vertical_overlap(self, category: Dict[str, Any]):
        photo_names = category['Photos']
        overlap_failures = []
        weakest_link_overlap = float('inf')

        try:
            flight_data_category = self.flight_data[self.flight_data['Unique Identifier'].isin(photo_names)]
        except KeyError:
            #print(f"Error: 'Unique Identifier' column not found in flight data for category {category['Flight Category']}.")
            return

        if len(flight_data_category) != len(photo_names):
            #print(f"Warning: Missing flight data for some photos in category {category['Flight Category']}.")
            return

        # Calculate average radial distance from orbital flights
        radial_distances = []
        for cat in self.passfail_data:
            if 'Radial Distance Check' in cat:
                if isinstance(cat['Radial Distance Check'], str) and 'Average radius:' in cat['Radial Distance Check']:
                    avg_radius = float(cat['Radial Distance Check'].split(':')[1].split()[0])
                    radial_distances.append(avg_radius)
                elif isinstance(cat['Radial Distance Check'], tuple) and len(cat['Radial Distance Check']) > 2:
                    avg_radius = float(cat['Radial Distance Check'][2].split(':')[1].split()[0])
                    radial_distances.append(avg_radius)

        if not radial_distances:
            #print("Warning: No radial distances found from orbital flights. Using default value of 5 meters.")
            distance_to_subject = 5  # Default value if no radial distances are found
        else:
            distance_to_subject = sum(radial_distances) / len(radial_distances)

        altitudes = flight_data_category['Relative Altitude'].tolist()

        for i in range(len(photo_names) - 1):
            photo1_name, photo2_name = photo_names[i], photo_names[i + 1]
            photo1 = flight_data_category[flight_data_category['Unique Identifier'] == photo1_name]
            photo2 = flight_data_category[flight_data_category['Unique Identifier'] == photo2_name]

            if photo1.empty or photo2.empty:
                #print(f"Warning: Photo metadata not found for {photo1_name} or {photo2_name}")
                continue

            _, vertical_fov_degrees = Utilities.calculate_FOV(photo1.to_dict('records'))
            
            # Calculate the vertical distance covered by the field of view
            vertical_fov_coverage = 2 * distance_to_subject * math.tan(math.radians(vertical_fov_degrees / 2))

            # Calculate the vertical distance between the two photos
            vertical_distance = abs(altitudes[i + 1] - altitudes[i])

            # Calculate the overlap percentage
            overlap_percentage = (1 - (vertical_distance / vertical_fov_coverage)) * 100

            if overlap_percentage < 60:
                overlap_failures.append((photo1_name, photo2_name))

            weakest_link_overlap = min(weakest_link_overlap, overlap_percentage)

        # Update the category with the result
        if weakest_link_overlap >= 60:
            category['Weakest Link Vertical Overlap'] = ('Pass', None)
        else:
            category['Weakest Link Vertical Overlap'] = ('Fail', None)

    def height_check(self, category: Dict[str, Any]) -> Tuple[str, float, str]:
        photos = category['Photos']
        
        if not isinstance(self.flight_data, pd.DataFrame):
            return "Fail", (0, ""), "Flight data is not in the expected format (pandas DataFrame)."
        
        relevant_flight_data = self.flight_data[self.flight_data['Unique Identifier'].isin(photos)]
        
        if relevant_flight_data.empty:
            return "Fail", (0, ""), f"No matching flight data found for '{category['Flight Category']}' photos."
        
        highest_altitude_photo = relevant_flight_data.loc[relevant_flight_data['Relative Altitude'].idxmax()]
        max_altitude = highest_altitude_photo['Relative Altitude']
        highest_photo_filename = highest_altitude_photo['Unique Identifier']
        
        # Construct the full file path for the highest altitude photo
        highest_photo_path = os.path.join(self.photo_base_path, highest_photo_filename)

        analysis_result = self.image_analyzer.analyze_image(
            highest_photo_path, 
            TOWER_TOP_PROMPT, 
            TOWER_TOP_SYSTEM_INSTRUCTION, 
            "tower_top"
        )
        
        if analysis_result == 'PASS':
            category['Height Check'] = ("Pass", None)
            return "Pass", max_altitude, ""
        elif analysis_result == 'FAIL':
            category['Height Check'] = ("Fail", None)
            return "Fail", max_altitude, "The highest altitude photo does not show the top of the tower."
        else:
            category['Height Check'] = ("Indeterminate", None)
            return "Indeterminate", max_altitude, "Unable to determine if the highest altitude photo shows the top of the tower."

    def height_check_ascent(self, ascent_categories: List[Dict[str, Any]]):
        # Find the category with the lowest maximum altitude
        lowest_max_category = min(ascent_categories, key=lambda x: max(self.flight_data[self.flight_data['Unique Identifier'].isin(x['Photos'])]['Relative Altitude']))
        
        # Perform height check on the lowest max altitude category
        result, altitude, message = self.height_check(lowest_max_category)
        
        # Apply the result to all ascent categories
        for category in ascent_categories:
            if result == "Pass":
                category['Height Check'] = ("Pass", None)
            elif result == "Fail":
                category['Height Check'] = ("Fail", None)
            else:
                category['Height Check'] = ("Indeterminate", None)


def main():
    passfail_data_path = r'Shared\Data\Flight Metadata\orbit_passfail_list.pkl'
    flight_data_path = r'Shared\Data\Flight Metadata\sortedflightdata.pkl'

    passfail_data, flight_data = Utilities.load_data_from_pickle(passfail_data_path, flight_data_path)

    ascent_descent_criteria = ['cable run', re.compile(r'ascent', re.IGNORECASE), re.compile(r'descent', re.IGNORECASE)]

    ascent_descent_analyzer = AscentDescentAnalyzer(passfail_data, flight_data, ascent_descent_criteria)
    ascent_descent_analyzer.analyze(passfail_data)

    # Export the updated passfail_data to Excel
    export_to_excel(passfail_data, r'Shared\Data\Flight Metadata\ascent_descent_passfail_list.xlsx')
    save_data_to_file(passfail_data, r'Shared\Data\Flight Metadata\ascent_descent_passfail_list.pkl')
    #print("Updated pass/fail list exported to 'Shared\\Data\\Flight Metadata\\ascent_descent_passfail_list.xlsx'.")

if __name__ == "__main__":
    main()