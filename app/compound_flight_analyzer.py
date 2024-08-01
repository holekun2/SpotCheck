import numpy as np
import pandas as pd
import pickle
from typing import List, Dict, Any, Tuple
from data_export import export_to_excel
from utils import Utilities
import math

class CompoundCheckAnalyzer:
    def __init__(self):
        self.passfail_data = None
        self.flight_data = None

    def load_data(self, passfail_data_path: str, flight_data_path: str):
        with open(passfail_data_path, 'rb') as f:
            self.passfail_data = pickle.load(f)
        self.flight_data = pd.read_pickle(flight_data_path)

    def analyze_compound_check(self):
        upper_flight = self.get_flight_category('compound flight upper')
        lower_flight = self.get_flight_category('compound flight lower')

        if upper_flight and lower_flight:
            upper_coverage = self.calculate_coverage(upper_flight)
            lower_coverage = self.calculate_coverage(lower_flight)

            upper_flight['Coverage'] = upper_coverage
            lower_flight['Coverage'] = lower_coverage

            upper_flight['Compound Check'] = ('Pass',) if upper_coverage >= 350 else ('Fail',)
            lower_flight['Compound Check'] = ('Pass',) if lower_coverage >= 350 else ('Fail',)

            self.calculate_horizontal_overlap(upper_flight, threshold=60)
            self.calculate_horizontal_overlap(lower_flight, threshold=50)

            ###print(f"Upper flight coverage: {upper_coverage:.2f} degrees")
            ##print(f"Lower flight coverage: {lower_coverage:.2f} degrees")
        else:
            print("Compound flight categories not found in the data.")

    def get_flight_category(self, category_name: str) -> Dict[str, Any]:
        return next((category for category in self.passfail_data if category['Flight Category'] == category_name), None)

    def calculate_coverage(self, flight_category: Dict[str, Any]) -> float:
        photo_names = flight_category['Photos']
        flight_data_category = self.flight_data[self.flight_data['Unique Identifier'].isin(photo_names)]
        yaw_degrees = flight_data_category['Flight Yaw Degree'].astype(float).tolist()

        total_rotation = 0
        for i in range(1, len(yaw_degrees)):
            diff = abs(yaw_degrees[i] - yaw_degrees[i-1])
            # Handle the wrap-around case
            if diff > 180:
                diff = 360 - diff
            total_rotation += diff

        return total_rotation

    def calculate_horizontal_overlap(self, category: Dict[str, Any], threshold: float):
        photo_names = category['Photos']
        overlap_failures = []
        weakest_link_overlap = float('inf')

        flight_data_category = self.flight_data[self.flight_data['Unique Identifier'].isin(photo_names)]

        x_positions, y_positions = Utilities.calculate_position(flight_data_category.to_dict('records'))
        estimated_center = Utilities.estimate_center_least_squares(x_positions, y_positions)
        radius, _ = Utilities.calculate_radius_and_circumference(estimated_center, x_positions, y_positions)

        for i in range(len(photo_names) - 1):
            photo1_name, photo2_name = photo_names[i], photo_names[i + 1]
            photo1 = flight_data_category[flight_data_category['Unique Identifier'] == photo1_name]
            photo2 = flight_data_category[flight_data_category['Unique Identifier'] == photo2_name]

            horizontal_fov_degrees, _ = Utilities.calculate_FOV(photo1.to_dict('records'))
            distance = Utilities.sum_distances([x_positions[i], x_positions[i + 1]], [y_positions[i], y_positions[i + 1]])
            overlap_percentage = (1 - (distance / (radius * math.tan(math.radians(horizontal_fov_degrees / 2))))) * 100

            if overlap_percentage < threshold:
                overlap_failures.append((photo1_name, photo2_name))

            weakest_link_overlap = round(min(weakest_link_overlap, overlap_percentage),1)

        # Update the category with the result
        if weakest_link_overlap >= threshold:
            category['Weakest Link Horizontal Overlap'] = ('Pass', round(weakest_link_overlap)) 
        else:
            category['Weakest Link Horizontal Overlap'] = ('Fail', round(weakest_link_overlap), 1)



