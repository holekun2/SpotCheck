import os
import pandas as pd
import pickle
from typing import List, Dict, Any, Tuple
from data_export import export_to_excel
from utils import Utilities


#TODO write conditions for how many ascents or descents are required

class TowerFlightType2Analyzer:
    def __init__(self, passfail_data: List[Dict[str, Any]], flight_data: pd.DataFrame):
        self.passfail_data = passfail_data
        self.flight_data = flight_data
    
    def analyze(self):
        tower_flight_type_2 = next((category for category in self.passfail_data if category['Flight Category'] == 'tower Flight type 2'), None)
        
        if tower_flight_type_2 is None:
            ##print("No 'tower Flight type 2' category found. Analysis skipped.")
            return
        
        orbit_result = self.check_orbital_spacing()
        flight_height_result = self.count_ascents_descents()
        
        tower_flight_type_2['Tower Flight Type 2 Orbit check'] = orbit_result
        tower_flight_type_2['Tower Flight Type 2 ascent/descent count'] = flight_height_result
    
    def check_orbital_spacing(self) -> Tuple[str, str]:
        orbit_categories = [category for category in self.passfail_data if category['Flight Category'].startswith('Orbit')]
        
        if len(orbit_categories) != 2:
            return ('Fail', f'Expected 2 orbits, found {len(orbit_categories)}')
        
        orbit1_altitude = self.flight_data[self.flight_data['Unique Identifier'].isin(orbit_categories[0]['Photos'])]['Relative Altitude'].mean()
        orbit2_altitude = self.flight_data[self.flight_data['Unique Identifier'].isin(orbit_categories[1]['Photos'])]['Relative Altitude'].mean()
        
        if orbit2_altitude < orbit1_altitude:
            return ('Pass', 'Second orbit is lower than the first orbit')
        else:
            return ('Fail', 'Second orbit is not lower than the first orbit')
    
    def count_ascents_descents(self) -> Tuple[str, str]:
        ascent_categories = [category for category in self.passfail_data if category['Flight Category'].startswith('Ascent')]
        descent_categories = [category for category in self.passfail_data if category['Flight Category'].startswith('Descent')]
        
        ascent_count = len(ascent_categories)
        descent_count = len(descent_categories)
        
        if ascent_count == 4 and descent_count == 5:
            return ('Pass', f'Found {ascent_count} ascents and {descent_count} descents')
        else:
            return ('Fail', f'Expected 4 ascents and 5 descents, found {ascent_count} ascents and {descent_count} descents')

def main():
    # Define file paths
    topdown_passfail_path = r'Shared\Data\Flight Metadata\topdown_passfail_list.pkl'
    flight_data_path = r'Shared\Data\Flight Metadata\sortedflightdata.pkl'
    output_pkl_path = r'Shared\Data\Flight Metadata\tf2_passfail_list.pkl'
    output_excel_path = r'Shared\Data\Flight Metadata\tf2_passfail_list.xlsx'

    # Load data
    passfail_data, flight_data = Utilities.load_data_from_pickle(topdown_passfail_path, flight_data_path)

    # Create analyzer and run analysis
    analyzer = TowerFlightType2Analyzer(passfail_data, flight_data)
    analyzer.analyze()

    # Save updated passfail data
    with open(output_pkl_path, 'wb') as f:
        pickle.dump(analyzer.passfail_data, f)

    # Export to Excel
    export_to_excel(analyzer.passfail_data, output_excel_path)

    ##print(f"Analysis complete. Results saved to {output_pkl_path} and {output_excel_path}")

if __name__ == "__main__":
    main()