import os
from dji_data_extraction import DJIDroneDataImport, PHOTO_BASE_PATH, SiteLocation

from flight_sorting import FlightSorter
from orbit_analysis import OrbitAnalyzer
from ascent_descent_analyzer import AscentDescentAnalyzer
from tower_flight_type_1_analyzer import TowerFlightType1Analyzer
from tower_flight_type_2_analyzer import TowerFlightType2Analyzer
from compound_flight_analyzer import CompoundCheckAnalyzer
from top_down_analyzer import TopDownAnalyzer
from cable_anchor_analyzer import CableAnchorAnalyzer
from data_export import export_to_excel
import pandas as pd
import re
from plotter import Plotter
from utils import Utilities
from typing import List, Dict, Any

def process_site(site_id: str, site_metadata: List[Dict[str, Any]]):
    print(f"Processing site: {site_id}")
    
    # 2. Flight Sorting
    flight_sorter = FlightSorter(site_metadata, [])
    flight_data, passfail_list = flight_sorter.process_flight_data()
    
    # Convert flight_data to DataFrame for consistency with other analyzers
    flight_data_df = pd.DataFrame(flight_data)
    print(f"Flight data DataFrame shape: {flight_data_df.shape}")

    # 3. Orbit Analysis
    orbit_criteria = ['downlook', 'center in', 'center out', 'uplook', re.compile(r'Orbit \d+', re.IGNORECASE)]
    orbit_analyzer = OrbitAnalyzer(passfail_list, flight_data_df, orbit_criteria)
    orbit_analyzer.analyze_orbit_flights()

    # 4. Ascent Descent Analysis
    ascent_descent_criteria = ['cable run', re.compile(r'ascent', re.IGNORECASE), re.compile(r'descent', re.IGNORECASE)]
    ascent_descent_analyzer = AscentDescentAnalyzer(passfail_list, flight_data_df, ascent_descent_criteria)
    ascent_descent_analyzer.analyze(passfail_list)

    # 5. Tower Flight Type 1 Analysis (if present)
    if any(category['Flight Category'] == 'tower Flight type 1' for category in passfail_list):
        tf1_analyzer = TowerFlightType1Analyzer(passfail_list, flight_data_df)
        tf1_analyzer.analyze()

    # 6. Tower Flight Type 2 Analysis (if present)
    if any(category['Flight Category'] == 'tower Flight type 2' for category in passfail_list):
        tf2_analyzer = TowerFlightType2Analyzer(passfail_list, flight_data_df)
        tf2_analyzer.analyze()

    # 7. Compound Flight Analysis
    compound_analyzer = CompoundCheckAnalyzer()
    compound_analyzer.passfail_data = passfail_list
    compound_analyzer.flight_data = flight_data_df
    compound_analyzer.analyze_compound_check()

    # 8. Top Down Analysis
    top_down_analyzer = TopDownAnalyzer()
    top_down_analyzer.passfail_data = passfail_list
    top_down_analyzer.flight_data = flight_data_df
    top_down_analyzer.analyze_top_down()

    # Save results for this site
    export_to_excel(passfail_list, f'Shared/Data/Flight Metadata/final_passfail_list_{site_id}.xlsx')
    export_to_excel(flight_data_df, f'Shared/Data/Flight Metadata/final_flight_data_{site_id}.xlsx')

    # Plotting for this site
    plotter = Plotter()
    for category in passfail_list:
        print(f"Processing category: {category['Flight Category']}")
        print(f"Photos in category: {len(category['Photos'])}")
        
        if OrbitAnalyzer.is_orbit_category(category['Flight Category'], orbit_criteria):
            # Plot the results
            matching_files = flight_data_df['Unique Identifier'].isin(category['Photos'])
            print(f"Matching files: {matching_files.sum()}")
            
            filtered_df = flight_data_df[matching_files]
            print(f"Filtered DataFrame shape: {filtered_df.shape}")
            
            filtered_data = filtered_df.to_dict('records')
            if not filtered_data:
                print(f"No data found for category: {category['Flight Category']}")
                continue
            
            x_positions, y_positions = Utilities.calculate_position(filtered_data)
            print(f"Calculated positions: {len(x_positions)}")
            
            estimated_center = Utilities.estimate_center_least_squares(x_positions, y_positions)
            estimated_radius, _ = Utilities.calculate_radius_and_circumference(estimated_center, x_positions, y_positions)
            inner_radius = estimated_radius * 0.8  # You can adjust this factor as needed

            plotter.plot_flight_data(x_positions, y_positions, 
                               filtered_data, 
                               category['Flight Category'], 
                               estimated_center, 
                               estimated_radius, 
                               inner_radius)
    
    # Create the 3D plot for this site
    print(f"Creating 3D plot of flights for site {site_id}...")
    categories_to_plot = [
        ['compound flight upper', 'compound flight lower', 'compound transition'],
        ['cable run'],
        ['tower Flight type 1'],
        ['tower Flight type 2']
    ]
    plotter.plot_3d_flights(passfail_list, flight_data_df, categories_to_plot)

    print(f"Analysis and plotting complete for site {site_id}.")


def main():
    # 1. DJI Data Extraction
    print("1. Extracting DJI data...")
    dji_data_import = DJIDroneDataImport()
    metadata = dji_data_import.extract_data(PHOTO_BASE_PATH)
    
    # 2. Site Location Processing
    print("2. Processing site locations...")
    site_location = SiteLocation()
    site_location.run_analysis(
        'Shared/Data/Flight Metadata/metadata.pkl',
        'Shared/Data/Inspection data/inspection_data.pkl',
        'Shared/Data/Processed flight data/passfail_list.pkl'
    )

    # Get the grouped metadata
    site_grouped_metadata = site_location.get_site_grouped_metadata()

    # 3. Process each site independently
    for site_id, site_metadata in site_grouped_metadata.items():
        process_site(site_id, site_metadata)

    print("All sites have been processed independently.")

if __name__ == "__main__":
    main()