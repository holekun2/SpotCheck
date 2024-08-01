
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from .utils import Utilities
from .image_analyzer_gemini import ImageAnalyzerGemini
from .dji_data_extraction import PHOTO_BASE_PATH
from .ascent_descent_analyzer import AscentDescentAnalyzer

class TowerFlightType1Analyzer:
    def __init__(self, passfail_data: List[Dict[str, Any]], flight_data: pd.DataFrame):
        self.passfail_data = passfail_data
        self.flight_data = flight_data
        self.image_analyzer = ImageAnalyzerGemini()
        self.photo_base_path = PHOTO_BASE_PATH
        self.ascent_descent_analyzer = AscentDescentAnalyzer(passfail_data, flight_data, [])


    def analyze(self):
        tower_flight_type_1 = next((category for category in self.passfail_data if category['Flight Category'] == 'tower Flight type 1'), None)
        
        if tower_flight_type_1 is None:
            #print("No 'tower Flight type 1' category found. Analysis passed by default.")
            return
        
        self.calculate_tower_coverage()

    def calculate_tower_coverage(self):
        orbit_categories = [category for category in self.passfail_data if category['Flight Category'].startswith('Orbit')]
        
        # Sort orbit categories by altitude in ascending order (lowest to highest)
        orbit_categories.sort(key=lambda x: self.flight_data[self.flight_data['Unique Identifier'] == x['Photos'][0]]['Relative Altitude'].values[0])
        
        coverage_areas = []
        total_tower_height = 0
        
        for i, category in enumerate(orbit_categories):
            photo_names = category['Photos']
            flight_data_category = self.flight_data[self.flight_data['Unique Identifier'].isin(photo_names)]
            
            # Calculate average radius
            x_positions, y_positions = Utilities.calculate_position(flight_data_category.to_dict('records'))
            estimated_center = Utilities.estimate_center_least_squares(x_positions, y_positions)
            radii = np.sqrt((x_positions - estimated_center[0])**2 + (y_positions - estimated_center[1])**2)
            average_radius = np.mean(radii)
            
            # Calculate vertical field of view
            first_photo_data = flight_data_category.iloc[0].to_dict()
            _, vertical_fov_degrees = Utilities.calculate_FOV([first_photo_data])
            vertical_fov_radians = np.radians(vertical_fov_degrees)
            
            # Calculate the vertical distance covered by this orbit
            altitude = flight_data_category['Relative Altitude'].values[0]
            vertical_coverage = 2 * altitude * np.tan(vertical_fov_radians / 2)
            
            # Calculate the bottom and top of the coverage area
            bottom = altitude - vertical_coverage / 2
            top = altitude + vertical_coverage / 2
            
            coverage_areas.append((bottom, top))
            
            # Update total tower height
            if i == 0:  # Lowest orbit
                total_tower_height += vertical_coverage / 2  # Assume the bottom half of the FOV covers below the tower
            elif i == len(orbit_categories) - 1:  # Highest orbit
                total_tower_height += vertical_coverage / 2  # Assume the top half of the FOV covers above the tower
            else:
                total_tower_height += vertical_coverage
        
        # Calculate the actual coverage by merging overlapping areas
        coverage_areas.sort()  # Sort by bottom altitude
        merged_areas = []
        for area in coverage_areas:
            if not merged_areas or area[0] > merged_areas[-1][1]:
                merged_areas.append(area)
            else:
                merged_areas[-1] = (merged_areas[-1][0], max(merged_areas[-1][1], area[1]))
        
        actual_coverage = sum(top - bottom for bottom, top in merged_areas)
        coverage_percentage = (actual_coverage / total_tower_height) * 100
        
        # Find Tower Flight Type 1 category and append results
        for category in self.passfail_data:
            if category['Flight Category'] == 'tower Flight type 1':
                category['Tower Coverage Check'] = ('Pass' if coverage_percentage >= 60 else 'Fail', coverage_percentage)
                break



