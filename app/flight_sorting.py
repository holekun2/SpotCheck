
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from .utils import Utilities





class FlightSorter:
    def __init__(self, flight_data: List[Dict[str, Any]], passfail_list: List[Dict[str, Any]]):
        print(f"FlightSorter init: {len(flight_data)} items")
        
        
        
        self.flight_data = pd.DataFrame(flight_data)
        #print('dataframe contents:', self.flight_data)
        self.passfail_list = passfail_list
        self.photo_count_requirement = {
            'downlook': 60,
            'uplook': 60,
            'center': 60,
            'cable run': 20,
            'tower Flight type 1': 200,
            'tower Flight type 2': 200,
            'top down': 0,
            'compound flight upper': 0,
            'compound flight lower': 0,
            'compound transition': 0,
            'cable anchor': 0  # Add the new category here
        }
        # Add standard dimensions for DJI Mavic 3
        self.standard_width = 5280  # Update this with the correct width
        
    def segment_flights_by_time(self, category_data: pd.DataFrame, time_threshold: int = 10, height_threshold: float = 5.0, heading_threshold: float = 10.0) -> List[pd.DataFrame]:
        print(f"Segmenting flights for category with {len(category_data)} photos")
        segments = []
        current_segment = [category_data.iloc[0]]
        
        for i in range(1, len(category_data)):
            prev_photo = category_data.iloc[i-1]
            current_photo = category_data.iloc[i]
            
            time_diff = (current_photo['Create Date'] - prev_photo['Create Date']).total_seconds()
            height_diff = abs(float(current_photo['Relative Altitude']) - float(prev_photo['Relative Altitude']))
            heading_diff = abs(float(current_photo['Flight Yaw Degree']) - float(prev_photo['Flight Yaw Degree']))
            heading_diff = min(heading_diff, 360 - heading_diff)  # Account for 0/360 degree wrapping
            
            if time_diff > time_threshold and (height_diff > height_threshold or heading_diff > heading_threshold):
                segments.append(pd.DataFrame(current_segment))
                current_segment = []
            
            current_segment.append(current_photo)
        
        if current_segment:
            segments.append(pd.DataFrame(current_segment))
        print(f"Number of segments created: {len(segments)}")
        return segments

    def determine_center_orientation(self, center_flight_data: pd.DataFrame, estimated_center: np.ndarray, 
                                     outward_tolerance: float = 45, inward_tolerance: float = 30) -> List[Dict[str, Any]]:
        x_positions = center_flight_data['X Position'].values
        y_positions = center_flight_data['Y Position'].values
        yaw_data = center_flight_data['Flight Yaw Degree'].values
        
        drone_headings = Utilities.calculate_drone_heading(x_positions, y_positions, yaw_data)
        
        oriented_photos = []
        for i in range(len(x_positions)):
            # Vector from center to drone position
            center_to_drone = np.array([x_positions[i] - estimated_center[0], y_positions[i] - estimated_center[1]])
            center_to_drone_angle = np.degrees(np.arctan2(center_to_drone[1], center_to_drone[0])) % 360
            
            # Drone heading
            drone_heading_angle = np.degrees(np.arctan2(drone_headings[i][1], drone_headings[i][0])) % 360
            
            # Calculate the difference between angles
            angle_diff = (drone_heading_angle - center_to_drone_angle + 180) % 360 - 180
            
            # Determine orientation based on the angle difference
            if abs(angle_diff) <= outward_tolerance:
                orientation = 'out'
            elif abs(angle_diff) >= (180 - inward_tolerance):
                orientation = 'in'
            else:
                orientation = 'incorrect'
            
            oriented_photos.append({
                'Unique Identifier': center_flight_data['Unique Identifier'].iloc[i],
                'Flight Category': f'center {orientation}',
                'Angle Difference': angle_diff
            })
        
        return oriented_photos


    def detect_partial_orbit(self, photo_sequence, min_rotation=70, max_rotation=350):
        total_rotation = 0
        for i in range(1, len(photo_sequence)):
            prev_yaw = float(photo_sequence[i-1]['Flight Yaw Degree'])
            curr_yaw = float(photo_sequence[i]['Flight Yaw Degree'])
            rotation = abs(curr_yaw - prev_yaw)
            if rotation > 180:
                rotation = 360 - rotation
            total_rotation += rotation
        
        is_partial_orbit = min_rotation <= total_rotation < max_rotation
        return is_partial_orbit, total_rotation


    #TODO: add case where the drone only turns and doesn't change x,y position
    def _process_center_flights(self):
        center_categories = [cat for cat in self.flight_data['Flight Category'].unique() if cat.startswith('center')]
        
        for category in center_categories:
            center_mask = self.flight_data['Flight Category'] == category
            if center_mask.any():
                center_flight_data = self.flight_data[center_mask].copy()
                x_positions, y_positions = Utilities.calculate_position(center_flight_data.to_dict('records'))
                estimated_center = Utilities.estimate_center_least_squares(x_positions, y_positions)
                
                center_flight_data['X Position'] = x_positions
                center_flight_data['Y Position'] = y_positions
                
                oriented_photos = self.determine_center_orientation(center_flight_data, estimated_center)
                
                # Update the flight data with new orientations
                for photo in oriented_photos:
                    new_category = f"{photo['Flight Category']} {category.split(' ')[-1] if ' ' in category else ''}"
                    self.flight_data.loc[self.flight_data['Unique Identifier'] == photo['Unique Identifier'], 'Flight Category'] = new_category.strip()
                
                # Update the passfail_list
                for item in self.passfail_list:
                    if item['Flight Category'] == category:
                        new_photos = [photo for photo in oriented_photos if photo['Unique Identifier'] in item['Photos']]
                        item['Photos'] = tuple(photo['Unique Identifier'] for photo in new_photos if 'incorrect' not in photo['Flight Category'])
                        if len(item['Photos']) > 0:
                            item['Flight Category'] = new_photos[0]['Flight Category']
                        else:
                            item['Flight Category'] = f'center incorrect {category.split(" ")[-1] if " " in category else ""}'.strip()


    def _remove_short_interruptions(self, min_interruption_photos: int = 5) -> None:
        flight_categories = self.flight_data['Flight Category'].tolist()
        new_flight_categories = []

        i = 0
        while i < len(flight_categories):
            current_category = flight_categories[i]
            j = i + 1

            while j < len(flight_categories) and flight_categories[j] == current_category:
                j += 1

            if j < len(flight_categories) and j - i < min_interruption_photos and current_category not in ['compound flight upper', 'compound flight lower', 'compound transition']:
                interruption_category = flight_categories[j]
                k = j + 1

                while k < len(flight_categories) and flight_categories[k] == interruption_category:
                    k += 1

                if k < len(flight_categories) and flight_categories[k] == current_category:
                    new_flight_categories.extend([current_category] * (k - i))
                    i = k
                else:
                    new_flight_categories.extend(flight_categories[i:j])
                    i = j
            else:
                new_flight_categories.extend(flight_categories[i:j])
                i = j

        self.flight_data['Flight Category'] = new_flight_categories


    def _prepare_flight_data(self) -> None:

        self.flight_data = self.flight_data.sort_values(by='Create Date', ascending=True)
        self.flight_data['Create Date'] = pd.to_datetime(self.flight_data['Create Date'], errors='coerce')
        self.flight_data['Relative Altitude'] = pd.to_numeric(self.flight_data['Relative Altitude'], errors='coerce')
        self.flight_data['Gimbal Pitch Degree'] = pd.to_numeric(self.flight_data['Gimbal Pitch Degree'], errors='coerce')
        if 'Flight Component' not in self.flight_data.columns:
            self.flight_data['Flight Component'] = np.nan
        self.flight_data['Flight Yaw Degree'] = pd.to_numeric(self.flight_data['Flight Yaw Degree'], errors='coerce')
        self.flight_data['Image Width'] = pd.to_numeric(self.flight_data['Image Width'], errors='coerce')
    

    def _define_flight_category(self, min_interruption_photos: int = 5) -> None:
        angle_tolerance = 3
        downlook_angle = -35
        uplook_angle = 20
        center_angle = 0
        cable_run_angle = -22
        tower_flight_type_1 = -40
        top_down_angle = -90
        lower_compound_flight_lower_angle = -15
        lower_compound_flight_upper_angle = -30
        upper_compound_flight_angle = -45
        tower_flight_type_2 = -50

        max_relative_altitude = self.flight_data['Relative Altitude'].max()
        conditions = [
            (downlook_angle - angle_tolerance <= self.flight_data['Gimbal Pitch Degree']) & (self.flight_data['Gimbal Pitch Degree'] <= downlook_angle + angle_tolerance),
            (uplook_angle - angle_tolerance <= self.flight_data['Gimbal Pitch Degree']) & (self.flight_data['Gimbal Pitch Degree'] <= uplook_angle + angle_tolerance) & (self.flight_data['Relative Altitude'] < max_relative_altitude),
            (center_angle - angle_tolerance <= self.flight_data['Gimbal Pitch Degree']) & (self.flight_data['Gimbal Pitch Degree'] <= center_angle + angle_tolerance) & (self.flight_data['Relative Altitude'] < max_relative_altitude),
            (self.flight_data['Relative Altitude'] > 20) & (cable_run_angle - angle_tolerance <= self.flight_data['Gimbal Pitch Degree']) & (self.flight_data['Gimbal Pitch Degree'] <= cable_run_angle + angle_tolerance),
            (tower_flight_type_1 - angle_tolerance <= self.flight_data['Gimbal Pitch Degree']) & (self.flight_data['Gimbal Pitch Degree'] <= tower_flight_type_1 + angle_tolerance),
            (tower_flight_type_2 - angle_tolerance <= self.flight_data['Gimbal Pitch Degree']) & (self.flight_data['Gimbal Pitch Degree'] <= tower_flight_type_2 + angle_tolerance),
            (top_down_angle - angle_tolerance <= self.flight_data['Gimbal Pitch Degree']) & (self.flight_data['Gimbal Pitch Degree'] <= top_down_angle + angle_tolerance),
            (upper_compound_flight_angle - angle_tolerance <= self.flight_data['Gimbal Pitch Degree']) & (self.flight_data['Gimbal Pitch Degree'] <= upper_compound_flight_angle + angle_tolerance),
            (self.flight_data['Image Width'].notna()) & (self.flight_data['Image Width'] < self.standard_width)
        ]

        categories = ['downlook', 'uplook', 'center', 'cable run', 'tower Flight type 1', 'tower Flight type 2', 'top down', 'compound flight upper', 'cable anchor']
        self.flight_data['Flight Category'] = np.select(conditions, categories, default='unknown flight category check gimbal angle')

        
        

        # Identify compound flight lower
        compound_upper_mask = self.flight_data['Flight Category'] == 'compound flight upper'
        if compound_upper_mask.any():
            compound_upper_altitude = self.flight_data.loc[compound_upper_mask, 'Relative Altitude'].iloc[0]
            compound_lower_mask = (lower_compound_flight_lower_angle + angle_tolerance >= self.flight_data['Gimbal Pitch Degree']) & \
                                (self.flight_data['Gimbal Pitch Degree'] >= lower_compound_flight_upper_angle - angle_tolerance) & \
                                (self.flight_data['Relative Altitude'] < compound_upper_altitude)
            self.flight_data.loc[compound_lower_mask, 'Flight Category'] = "compound flight lower"

            # Find the last 'compound flight upper' and first 'compound flight lower'
            last_upper_index = self.flight_data[compound_upper_mask].index[-1]
            first_lower_index = self.flight_data[self.flight_data['Flight Category'] == 'compound flight lower'].index[0]

            # Set 'compound transition' for photos between upper and lower
            transition_start = last_upper_index + 1
            transition_end = first_lower_index - 1
            self.flight_data.loc[transition_start:transition_end, 'Flight Category'] = 'compound transition'

        categories_to_segment = ['downlook', 'uplook', 'center', 'top down', 'cable anchor']
        orbit_counts = {category: 0 for category in categories_to_segment}
        segmented_flights = []
        processed_categories = set()

        for category in categories_to_segment:
            mask = self.flight_data['Flight Category'] == category
            if mask.any():
                category_data = self.flight_data[mask].sort_values('Create Date')
                segments = self.segment_flights_by_time(category_data)
                
                for segment in segments:
                    orbit_counts[category] += 1
                    is_partial, rotation = self.detect_partial_orbit(segment.to_dict('records'))
                    orbit_type = "partial" if is_partial else "full"
                    
                    if len(segments) > 1 or orbit_counts[category] > 1:
                        segment_category = f'{category} {orbit_counts[category]}'
                    else:
                        segment_category = category
                    
                    segment['Flight Category'] = segment_category
                    segmented_flights.append(segment)
                    
                    segment_photos = tuple(segment['Unique Identifier'].tolist())
                    passfail_entry = {
                        'Flight Category': segment_category,
                        'Photos': segment_photos,
                        'Orbit Type': orbit_type,
                        'Total Rotation': (f"{rotation:.2f} degrees",) 
                    }
                    self.passfail_list.append(passfail_entry)
                    #print(f"Appending to passfail list: {passfail_entry}")
                processed_categories.add(category)

        # Replace the original flights with the segmented ones
        self.flight_data = pd.concat([self.flight_data[~self.flight_data['Flight Category'].isin(categories_to_segment)]] + segmented_flights)
        self.flight_data = self.flight_data.sort_values('Create Date').reset_index(drop=True)

        self._remove_short_interruptions(min_interruption_photos)

        # Process remaining categories
        for category in self.flight_data['Flight Category'].unique():
            if category not in processed_categories:
                mask = self.flight_data['Flight Category'] == category
                if mask.any():
                    category_data = self.flight_data[mask].sort_values('Create Date')
                    site_ids = category_data['Site ID'].unique().tolist()
                    passfail_entry = {
                        'Flight Category': category,
                        'Photos': tuple(category_data['Unique Identifier'].tolist()),
                        'Orbit Type': ('N/A',),
                        'Total Rotation': ('N/A',),
                        'Site IDs': site_ids  # Add Site IDs to the passfail list
                    }
                    self.passfail_list.append(passfail_entry)
                    #print(f"Appending to passfail list: {passfail_entry}")

        # Add compound flights to passfail_list
        for category in ['compound flight upper', 'compound flight lower', 'compound transition']:
            category_mask = self.flight_data['Flight Category'] == category
            if category_mask.any():
                category_photos = self.flight_data.loc[category_mask, 'Unique Identifier'].tolist()
                site_ids = self.flight_data.loc[category_mask, 'Site ID'].unique().tolist()
                passfail_entry = {
                    'Flight Category': category,
                    'Photos': tuple(category_photos),
                    'Total Rotation': ('N/A',),
                    'Site IDs': site_ids  # Add Site IDs to the passfail list
                }
                self.passfail_list.append(passfail_entry)
                #print(f"Appending to passfail list: {passfail_entry}")


        
    def _remove_short_interruptions(self, min_interruption_photos: int = 5) -> None:
        flight_categories = self.flight_data['Flight Category'].tolist()
        new_flight_categories = []

        i = 0
        while i < len(flight_categories):
            current_category = flight_categories[i]
            j = i + 1

            while j < len(flight_categories) and flight_categories[j] == current_category:
                j += 1

            if j < len(flight_categories) and j - i < min_interruption_photos and current_category not in ['compound flight upper', 'compound flight lower', 'compound transition']:
                interruption_category = flight_categories[j]
                k = j + 1

                while k < len(flight_categories) and flight_categories[k] == interruption_category:
                    k += 1

                if k < len(flight_categories) and flight_categories[k] == current_category:
                    new_flight_categories.extend([current_category] * (k - i))
                    i = k
                else:
                    new_flight_categories.extend(flight_categories[i:j])
                    i = j
            else:
                new_flight_categories.extend(flight_categories[i:j])
                i = j

        self.flight_data['Flight Category'] = new_flight_categories


    def _update_passfail_list(self) -> None:
        photo_counts = self.flight_data.groupby('Flight Category').size()

        for flight_category in self.flight_data['Flight Category'].unique():
            flight_photos = self.flight_data[self.flight_data['Flight Category'] == flight_category]['Unique Identifier'].tolist()
            site_ids = self.flight_data[self.flight_data['Flight Category'] == flight_category]['Site ID'].unique().tolist()

            self.passfail_list.append({
                'Flight Category': flight_category,
                'Photos': tuple(flight_photos),
                'Site IDs': site_ids  # Add Site IDs to the passfail list
            })




    def _disassemble_tower_flights(self, height_change_threshold: float = 0.45, window_size: int = 3, min_orbit_rotation: float = 70) -> None:
        tower_flight_data = self.flight_data[self.flight_data['Flight Category'].isin(['tower Flight type 1', 'tower Flight type 2'])].copy()
        if tower_flight_data.empty:
            return

        # for flight_type in ['tower Flight type 1', 'tower Flight type 2']:
        #     flight_data = tower_flight_data[tower_flight_data['Flight Category'] == flight_type]
        #     if not flight_data.empty:
        #         print(f"Appending to passfail list: flight category = {flight_type}")
        #         self.passfail_list.append({
        #             'Flight Category': flight_type,
        #             'Photos': tuple(flight_data['Unique Identifier'].tolist()),
        #             'Total Rotation': ('N/A',)
        #         })
        
        tower_flight_data['Altitude Change'] = tower_flight_data['Relative Altitude'].diff()
        tower_flight_data['Tower Flight Component'] = ''

        components = []
        current_component = {'label': 'Orbit', 'start': 0, 'end': 0, 'rotation': 0}
        
        for idx in range(len(tower_flight_data)):
            if idx <= len(tower_flight_data) - window_size:
                window_data = tower_flight_data.iloc[idx:idx+window_size]
            else:
                window_data = tower_flight_data.iloc[idx:]

            altitude_changes = abs(window_data['Altitude Change'])
            significant_changes = altitude_changes >= height_change_threshold
            
            if significant_changes.sum() >= min(window_size, len(window_data)):
                new_label = 'Ascent' if window_data['Altitude Change'].mean() > 0 else 'Descent'
            else:
                new_label = 'Orbit'

            if new_label != current_component['label']:
                if current_component['label'] == 'Orbit' and current_component['rotation'] < min_orbit_rotation:
                    current_component['label'] = 'Transition'
                current_component['end'] = idx - 1
                components.append(current_component)
                current_component = {'label': new_label, 'start': idx, 'end': idx, 'rotation': 0}

            if idx > 0 and current_component['label'] == 'Orbit':
                prev_yaw = tower_flight_data['Flight Yaw Degree'].iloc[idx - 1]
                curr_yaw = tower_flight_data['Flight Yaw Degree'].iloc[idx]
                yaw_diff = abs(curr_yaw - prev_yaw)
                if yaw_diff > 180:
                    yaw_diff = 360 - yaw_diff
                current_component['rotation'] += yaw_diff

        current_component['end'] = len(tower_flight_data) - 1
        components.append(current_component)

        consolidated = []
        counters = {'Orbit': 1, 'Ascent': 1, 'Descent': 1, 'Transition': 1}
        for comp in components:
            if consolidated and consolidated[-1]['label'] == comp['label']:
                consolidated[-1]['end'] = comp['end']
                consolidated[-1]['rotation'] += comp['rotation']
            else:
                comp['number'] = counters[comp['label']]
                counters[comp['label']] += 1
                consolidated.append(comp)
        
        tower_flight_data['Tower Flight Component'] = ''

        for comp in consolidated:
            component_name = f"{comp['label']} {comp['number']}"
            tower_flight_data.iloc[comp['start']:comp['end']+1, tower_flight_data.columns.get_loc('Tower Flight Component')] = component_name
            
            flight_photos = tower_flight_data.iloc[comp['start']:comp['end'] + 1]['Unique Identifier'].tolist()
            #print(f"Appending to passfail list: flight category = {component_name}")
            self.passfail_list.append({
                
                'Flight Category': component_name,
                'Photos': tuple(flight_photos),
                'Total Rotation': (f"{comp['rotation']:.2f} degrees",) if comp['label'] == 'Orbit' else ('N/A',)
            })

        self.flight_data.loc[tower_flight_data.index, 'Tower Flight Component'] = tower_flight_data['Tower Flight Component']
        #print("Method completed. Updated flight_data shape:", self.flight_data.shape)




    def process_flight_data(self) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        
        self._prepare_flight_data()
        self._define_flight_category()
        print("define_flight_category completed. found", len(self.flight_data), "flights named", self.flight_data['Flight Category'].value_counts())
        self._remove_short_interruptions()
        self._disassemble_tower_flights()
        print("disassemble_tower_flights completed. found", len(self.flight_data), "flights named", self.flight_data['Flight Category'].value_counts())
        self._process_center_flights()

        return self.flight_data, self.passfail_list









