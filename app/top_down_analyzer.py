import numpy as np
import pandas as pd
import pickle
from typing import List, Dict, Any, Tuple
from data_export import export_to_excel
#from flight_sorting import save_data_to_file

class TopDownAnalyzer:
    def __init__(self):
        self.passfail_data = None
        self.flight_data = None
        self.highest_altitude = None

    def load_data(self, passfail_data_path: str, flight_data_path: str):
        with open(passfail_data_path, 'rb') as f:
            self.passfail_data = pickle.load(f)
        with open(flight_data_path, 'rb') as f:
            self.flight_data = pickle.load(f)
        self.highest_altitude = self.flight_data['Relative Altitude'].max()

    def analyze_top_down(self):
        top_down_category = next((category for category in self.passfail_data if category['Flight Category'] == 'top down'), None)
        
        if top_down_category is None:
            print("No 'top down' category found in passfail data.")
            return

        photo_name = top_down_category['Photos'][0]  # Assuming there's only one top-down photo
        photo_data = self.flight_data[self.flight_data['Unique Identifier'] == photo_name].iloc[0]



        # Check if it's facing north (within 10 degrees)
        yaw = float(photo_data['Flight Yaw Degree'])
        is_facing_north = self.is_facing_north(yaw)

        # Calculate heading relative to north
        heading_relative_to_north = self.calculate_heading_relative_to_north(yaw)

        # Update passfail list
        if is_facing_north:
            top_down_category['North Facing Check'] = ('Pass', heading_relative_to_north) 
        else:
            top_down_category['North Facing Check'] = ('Fail', heading_relative_to_north)


    def is_facing_north(self, yaw: float) -> bool:
        return abs(yaw) <= 10 or abs(yaw - 360) <= 10

    def calculate_heading_relative_to_north(self, yaw: float) -> float:
        if yaw > 180:
            return 360 - yaw
        else:
            return -yaw




    
