import numpy as np
import pandas as pd
import pickle
from typing import List, Tuple, Dict, Any
from data_export import export_to_excel
from sqlalchemy.orm import joinedload
from flight_models import SiteInspection
import json

class Utilities:
    @staticmethod
    def calculate_position(data: List[Dict[str, Any]]) -> Tuple[List[float], List[float]]:
        positions = []
        initial_position = np.array([0, 0])
        positions.append({'X Position': initial_position[0], 'Y Position': initial_position[1], 'flight_data': data[0]})

        for i in range(1, len(data)):
            speed_x = float(data[i]['Flight X Speed'])
            speed_y = float(data[i]['Flight Y Speed'])

            current_timestamp = data[i]['Create Date']
            previous_timestamp = data[i-1]['Create Date']

            time_diff = (current_timestamp - previous_timestamp).total_seconds()

            dx = speed_x * time_diff
            dy = speed_y * time_diff

            previous_position = np.array([positions[-1]['X Position'], positions[-1]['Y Position']])
            current_position = previous_position + np.array([dx, dy])
            positions.append({'X Position': current_position[0], 'Y Position': current_position[1], 'flight_data': data[i]})

        x_positions = [pos['X Position'] for pos in positions]
        y_positions = [pos['Y Position'] for pos in positions]

        return x_positions, y_positions

    @staticmethod
    def estimate_center_least_squares(x_positions: List[float], y_positions: List[float]) -> np.ndarray:
        x_positions = np.array(x_positions)
        y_positions = np.array(y_positions)
        x_mean = np.mean(x_positions)
        y_mean = np.mean(y_positions)
        u = x_positions - x_mean
        v = y_positions - y_mean
        A = np.column_stack((u, v))
        b = u**2 + v**2
        solution = np.linalg.lstsq(A, b, rcond=None)[0]
        a, b = solution
        center_x = a / 2 + x_mean
        center_y = b / 2 + y_mean
        return np.array([center_x, center_y])

    @staticmethod
    def sum_distances(x_positions: List[float], y_positions: List[float]) -> float:
        x_positions = np.array(x_positions)
        y_positions = np.array(y_positions)
        distances = np.sqrt(np.diff(x_positions)**2 + np.diff(y_positions)**2)
        return np.sum(distances)

    @staticmethod
    def calculate_radius_and_circumference(estimated_center: np.ndarray, x_positions: List[float], y_positions: List[float]) -> Tuple[float, float]:
        x_positions = np.array(x_positions)
        y_positions = np.array(y_positions)
        distances = np.sqrt((x_positions - estimated_center[0])**2 + (y_positions - estimated_center[1])**2)
        estimated_radius = np.mean(distances)
        estimated_circumference = 2 * np.pi * estimated_radius
        return estimated_radius, estimated_circumference

    @staticmethod
    def calculate_drone_heading(x_positions: List[float], y_positions: List[float], yaw_data: List[Any]) -> List[Tuple[float, float]]:
        drone_headings = []
        for i in range(len(x_positions)):
            if not isinstance(yaw_data[i], (int, float)):
                try:
                    yaw_data[i] = float(yaw_data[i])
                except ValueError:
                    print(f"Cannot convert {yaw_data[i]} to a float.")
                    continue
            yaw_radians = np.radians(yaw_data[i])
            adjusted_yaw_radians = yaw_radians
            dy = np.sin(adjusted_yaw_radians)
            dx = np.cos(adjusted_yaw_radians)
            drone_headings.append((dx, dy))
        return drone_headings

    @staticmethod
    def calculate_FOV(data: List[Dict[str, Any]]) -> Tuple[float, float]:
        diagonal_fov_degrees = 84.0
        image_width = None
        image_height = None
        
        for item in data:
            if isinstance(item, dict):
                if 'Image Width' in item:
                    image_width = float(item['Image Width'])
                if 'Image Length' in item:
                    image_height = float(item['Image Length'])
                elif 'Image Height' in item:  # Added this condition
                    image_height = float(item['Image Height'])
        
        if image_width is None or image_height is None:
            raise ValueError("Missing image dimensions metadata in the data list.")
        
        diagonal_fov = np.radians(diagonal_fov_degrees)
        aspect_ratio = image_width / image_height
        horizontal_fov = 2 * np.arctan(np.tan(diagonal_fov / 2) * aspect_ratio / np.sqrt(1 + aspect_ratio**2))
        vertical_fov = 2 * np.arctan(np.tan(diagonal_fov / 2) / (aspect_ratio * np.sqrt(1 + aspect_ratio**2)))
        horizontal_fov_degrees = np.degrees(horizontal_fov)
        vertical_fov_degrees = np.degrees(vertical_fov)
        return horizontal_fov_degrees, vertical_fov_degrees


    @staticmethod
    def load_data_from_pickle(passfail_data_path: str, flight_data_path: str) -> Tuple[List[Dict[str, Any]], pd.DataFrame]:
        with open(passfail_data_path, 'rb') as f:
            passfail_data = pickle.load(f)
        with open(flight_data_path, 'rb') as f:
            flight_data = pickle.load(f)
        return passfail_data, flight_data








def load_flight_requirements():
    with open('Shared/Data/Inspection data/flight_requirements.json', 'r') as f:
        return json.load(f)

def create_inspection_dict(inspection):
    return {
        "inspection_id": inspection.inspection_id,
        "status": inspection.status,
        "created_at": inspection.created_at.isoformat(),
        "sites": [{
            "site_id": site.site_id,
            "scope_requirement": site.scope_requirement,
            "status": site.status.value if site.status else None,
            "scope_status": site.scope_status.value if site.scope_status else None,
            "site_status": site.site_status.value if site.site_status else None,
            "flights": [{
                "flight_id": flight.flight_id,
                "flight_name": flight.flight_name,
                "required": flight.required,
                "status": flight.status.value if flight.status else None,
                "created_at": flight.created_at.isoformat() if flight.created_at else None,
                "is_captured": flight.is_captured,
                "analysis": flight.analysis.to_dict() if flight.analysis else None,
                'unique identifiers in flight': [photo.filename for photo in flight.photos],  # unique identifier
                "photo_count": len(flight.photos)
            } for flight in site.flights] if site.flights else []
        } for site in inspection.sites] if inspection.sites else []
    }

def export_flight_data(flight_data_df, passfail_list):
    export_to_excel(flight_data_df, r'Shared\Data\Processed flight data\updated_metadata.xlsx')

    passfail_df = pd.DataFrame(passfail_list)
    passfail_df.to_excel(r'Shared\Data\Processed flight data\passfail_results.xlsx', index=False)

def print_db_contents(db_session):
    print("\n=== Database Contents ===\n")
    
    site_inspections = db_session.query(SiteInspection).options(
        joinedload(SiteInspection.inspection),
        joinedload(SiteInspection.flights)
    ).all()
    
    for site_inspection in site_inspections:
        print(f"Site ID: {site_inspection.site_id}")
        print(f"Scope Requirement: {site_inspection.scope_requirement}")
        print(f"Status: {site_inspection.status}")
        print(f"Scope Status: {site_inspection.scope_status}")
        
        inspection = site_inspection.inspection
        print(f"\n  Inspection ID: {inspection.inspection_id}")
        print(f"  Inspection Status: {inspection.status}")
        print(f"  Created At: {inspection.created_at}")
        
        for flight in site_inspection.flights:
            print(f"\n    Flight ID: {flight.flight_id}")
            print(f"    Flight Name: {flight.flight_name}")
            print(f"    Required: {flight.required}")
            print(f"    Status: {flight.status}")
            print(f"    Created At: {flight.created_at}")
            
            if flight.analysis:
                print("\n    Analysis:")
                for key, value in flight.analysis.to_dict().items():
                    print(f"      {key}: {value}")
            
            print(f"\n    Photos: {len(flight.photos)}")
        



        print("\n  Audit Trail:")
        sorted_audit_entries = sorted(site_inspection.audit_trail, key=lambda entry: entry.audit_id)
        for entry in sorted_audit_entries:
            status = " "
            if entry.details and 'result' in entry.details:
                result = entry.details['result'].lower()
                if 'pass' in result:
                    status = "Passed"
                elif 'fail' in result:
                    status = "Failed"
                elif 'complete' in result:
                    status = "Completed"
            print(f"    {entry.timestamp}: {entry.action} by {entry.user}  {status}")

    print("\n" + "="*30 + "\n")







