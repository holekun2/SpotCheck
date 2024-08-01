import numpy as np
import pandas as pd
import re
import math
from typing import List, Dict, Any, Tuple

#from flight_sorting import save_data_to_file
from .utils import Utilities
# TODO: Refactor the following method in the OrbitAnalyzer class to integrate database operations:
# Update the method signature to include a db_session parameter.
# Query the FlightAnalysis object using the flight_id from the category dictionary.
# If no FlightAnalysis object exists, create a new one.
# Replace tuple-based results with direct assignments to the corresponding status and value fields in the FlightAnalysis object.
# Convert complex data types to JSON format before storing in value fields.
# Commit changes to the database at the end of the method.
# Maintain the existing logic for updating the passfail_data list.
# Ensure all fields in the FlightAnalysis model are properly handled.
# Provide the refactored code for the method, showing how it interacts with the database while maintaining the existing functionality



class OrbitAnalyzer:
    def __init__(self, passfail_data: List[Dict[str, Any]], flight_data: pd.DataFrame, orbit_criteria: List[Any]):
        self.passfail_data = passfail_data
        self.flight_data = flight_data
        self.orbit_criteria = orbit_criteria


    def analyze_orbit_flights(self):
        for category in self.passfail_data:
            category_name = category['Flight Category']
            photo_names = category['Photos']
            #print(f"Category: {category_name}")

            if self.is_orbit_category(category_name, self.orbit_criteria):
                #print(f"{category_name}: {photo_names}")
                self.calculate_horizontal_overlap(category)
                self.orientation_check(category)
                self.radial_distance_check(category)
                self.calculate_cumulative_rotation(category)
                self.check_photo_closeness(category) 


                horizontal_overlap_percentage = category.get('Weakest Link Overlap Percentage', 'N/A')
                horizontal_overlap_status = category.get('Horizontal Overlap', 'N/A')
                orientation_status = category.get('Orientation', 'N/A')
                radial_distance_status = category.get('Radial Distance Check', 'N/A')
                cumulative_rotation = category.get('Total Rotation', 'N/A')
                #print(f"{category_name}: 'Weakest Link Overlap Percentage': {horizontal_overlap_percentage}, 'Horizontal Overlap': {horizontal_overlap_status}, 'Orientation': {orientation_status}, 'Radial Distance Check': {radial_distance_status}, 'Total Rotation': {cumulative_rotation}")
            else:
                print('skip')            
                
    #TODO: remove failed photos and add new set of photos without failed photos back into the loop
    def check_photo_closeness(self, category: Dict[str, Any], closeness_threshold: float = 0.5, consecutive_limit: int = 3):
        """
        Check if photos in the orbit are too close together relative to the average spacing.
        
        :param category: Dictionary containing flight category information
        :param closeness_threshold: Threshold for considering photos too close, as a fraction of median spacing
        :param consecutive_limit: Number of consecutive close photos allowed before flagging
        """
        photo_names = category['Photos']
        flight_data_category = self.flight_data[self.flight_data['Unique Identifier'].isin(photo_names)]
        
        x_positions, y_positions = Utilities.calculate_position(flight_data_category.to_dict('records'))
        estimated_center = Utilities.estimate_center_least_squares(x_positions, y_positions)
        
        angles = []
        for x, y in zip(x_positions, y_positions):
            angle = np.degrees(np.arctan2(y - estimated_center[1], x - estimated_center[0]))
            angles.append(angle)
        
        # Normalize angles to be between 0 and 360
        angles = [(a + 360) % 360 for a in angles]
        
        # Calculate angle differences and handle wrap-around
        angle_diffs = []
        for i in range(len(angles)):
            diff = (angles[(i + 1) % len(angles)] - angles[i]) % 360
            angle_diffs.append(diff)
        
        median_spacing = np.median(angle_diffs)
        closeness_limit = median_spacing * closeness_threshold
        
        close_photos = []
        consecutive_count = 0
        for i, diff in enumerate(angle_diffs):
            if diff < closeness_limit:
                consecutive_count += 1
                if consecutive_count >= consecutive_limit:
                    close_photos.extend(photo_names[i-consecutive_count+1:i+2])
            else:
                consecutive_count = 0
        
        # Remove duplicates while preserving order
        close_photos = list(dict.fromkeys(close_photos))
        
        if close_photos:
            category['Horizontal Spacing'] = ('Fail', close_photos)
            #print(f"Warning: The following photos are too close together: {close_photos}")
            #print(f"Median spacing: {median_spacing:.2f} degrees, Closeness limit: {closeness_limit:.2f} degrees")
        else:
            category['Horizontal Spacing'] = ('Pass', None)
            #print("Horizontal Spacing check passed.")
            #print(f"Median spacing: {median_spacing:.2f} degrees")
                               
    def calculate_cumulative_rotation(self, category: Dict[str, Any]):
        photo_names = category['Photos']
        flight_data_category = self.flight_data[self.flight_data['Unique Identifier'].isin(photo_names)]
        
        yaw_degrees = flight_data_category['Flight Yaw Degree'].tolist()
        
        total_rotation = 0
        for i in range(1, len(yaw_degrees)):
            diff = abs(yaw_degrees[i] - yaw_degrees[i-1])
            # Handle the wrap-around case
            if diff > 180:
                diff = 360 - diff
            total_rotation += diff
        
        # Apply the pass/fail condition
        if total_rotation < 340:
            category['Total Rotation'] = ('Fail', total_rotation)
        elif 340 <= total_rotation <= 380:
            category['Total Rotation'] = ('Pass', total_rotation)
        else:
            category['Total Rotation'] = ('Fail', total_rotation)  #TODO: add the case where it removes the excess photos

    def orientation_check(self, category: Dict[str, Any]):
        category_name = category['Flight Category'].lower()
        if 'out' in category_name:
            # Skip orientation check for outward-facing orbits
            #print(f"Skipping orientation check for outward-facing orbit: {category['Flight Category']}")
            return

        photo_names = category['Photos']
        flight_data_category = self.flight_data[self.flight_data['Unique Identifier'].isin(photo_names)]

        x_positions, y_positions = Utilities.calculate_position(flight_data_category.to_dict('records'))
        estimated_center = Utilities.estimate_center_least_squares(x_positions, y_positions)

        yaw_data = flight_data_category['Flight Yaw Degree'].tolist()
        drone_headings = Utilities.calculate_drone_heading(x_positions, y_positions, yaw_data)

        failed_photos = []
        for i, photo_name in enumerate(photo_names):
            photo_position = np.array([x_positions[i], y_positions[i]])
            radial_vector = estimated_center - photo_position
            radial_vector_normalized = radial_vector / np.linalg.norm(radial_vector)

            drone_heading_vector = np.array(drone_headings[i])
            drone_heading_normalized = drone_heading_vector / np.linalg.norm(drone_heading_vector)

            dot_product = np.dot(radial_vector_normalized, drone_heading_normalized)
            angle = np.arccos(np.clip(dot_product, -1.0, 1.0))
            angle_degrees = np.degrees(angle)

            #print(f"{photo_name}: {angle_degrees}")

            if angle_degrees > 30:
                failed_photos.append(photo_name)

        if len(failed_photos) == 0:
            category['Orientation'] = ('Pass', None)
        elif len(failed_photos) < 3:
            # Remove failed photos from the category's photo list
            good_photos = [photo for photo in photo_names if photo not in failed_photos]

            # Update the category's photo list
            category['Photos'] = good_photos

            # Set the Orientation status to 'Pass Override' along with the failed photos
            category['Orientation'] = ('Pass Override', None)
        else:
            category['Orientation'] = ('Fail', None)

    def radial_distance_check(self, category: Dict[str, Any]):
        category_name = category['Flight Category']

        if self.is_orbit_category(category_name, self.orbit_criteria) and 'center out' not in category_name.lower():
            photo_names = category['Photos']
            flight_data_category = self.flight_data[self.flight_data['Unique Identifier'].isin(photo_names)]


            x_positions, y_positions = Utilities.calculate_position(flight_data_category.to_dict('records'))

            estimated_center = Utilities.estimate_center_least_squares(x_positions, y_positions)


            failed_photos = []
            radii = []

            for i, photo_name in enumerate(photo_names):
                photo_position = np.array([x_positions[i], y_positions[i]])
                radius = np.linalg.norm(photo_position - estimated_center)
                radii.append(radius)
                # units in meters
                if radius < 3 or radius > 9:
                    failed_photos.append((photo_name, radius))



            average_radius = np.mean(radii)


            if len(failed_photos) < 3:
                print(f"Radial Distance Check result for {category_name}")
                category['Radial Distance Check'] = ('Pass', None)
            else:
                print(f"Radial Distance Check result for {category_name}")
                category['Radial Distance Check'] = ('Fail', None) 
            
            category['Average Radius (m)'] = average_radius

            print(f"Radial Distance Check result for {category_name}: {category['Radial Distance Check']}")
            print(f"Average Radius for {category_name}: {category['Average Radius (m)']}")
            
    @staticmethod
    def is_orbit_category(category_name: str, orbit_criteria: List[Any]) -> bool:
        return any(
            category_name == criterion if isinstance(criterion, str) else criterion.search(category_name)
            for criterion in orbit_criteria
        )

    def calculate_horizontal_overlap(self, category: Dict[str, Any]):
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

        x_positions, y_positions = Utilities.calculate_position(flight_data_category.to_dict('records'))
        estimated_center = Utilities.estimate_center_least_squares(x_positions, y_positions)
        radius, _ = Utilities.calculate_radius_and_circumference(estimated_center, x_positions, y_positions)

        for i in range(len(photo_names) - 1):
            photo1_name, photo2_name = photo_names[i], photo_names[i + 1]
            photo1 = flight_data_category[flight_data_category['Unique Identifier'] == photo1_name]
            photo2 = flight_data_category[flight_data_category['Unique Identifier'] == photo2_name]

            if photo1.empty or photo2.empty:
                #print(f"Warning: Photo metadata not found for {photo1_name} or {photo2_name}")
                continue

            horizontal_fov_degrees, _ = Utilities.calculate_FOV(photo1.to_dict('records'))
            distance = Utilities.sum_distances([x_positions[i], x_positions[i + 1]], [y_positions[i], y_positions[i + 1]])
            overlap_percentage = (1 - (distance / (radius * math.tan(math.radians(horizontal_fov_degrees / 2))))) * 100

            if overlap_percentage < 70:
                overlap_failures.append((photo1_name, photo2_name))

            weakest_link_overlap = round(min(weakest_link_overlap, overlap_percentage), 1)

        # Update the category with the result
        if weakest_link_overlap >= 70:
            category['Weakest Link Horizontal Overlap'] = ('Pass', None)
        else:
            category['Weakest Link Horizontal Overlap'] = ('Fail', None)

