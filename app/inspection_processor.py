from .database import DatabaseManager
from .flight_processor import FlightProcessor
from .audit_manager import AuditManager
from .flight_models import Inspection, SiteInspection
from .dji_data_extraction import SiteLocation
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
import pytz
from .inspection_data_reader import InspectionDataReader

class InspectionProcessor:
    @staticmethod
    def process_inspection(db, processed_metadata, passfail_list, flight_requirements):
        print("PROCESSING INSPECTION DATA BEGIN...")
        
        current_timestamp = datetime.now(pytz.timezone('US/Central'))
        site_location = SiteLocation()
        try:
            site_location.inspection_data = InspectionDataReader.read_inspection_data()
        except Exception as e:
            print(f"Error reading inspection data: {str(e)}")
            site_location.inspection_data = []

        site_id = next((item.get('Site ID', 'Unknown') for item in processed_metadata), 'Unknown')
        inspection_id = str(next((item.get('Inspection', 'Unknown') for item in site_location.inspection_data if item.get('Site ID') == site_id), 'Unknown'))
        inspection = InspectionProcessor.get_or_create_inspection(db, inspection_id)

        processed_site_ids = set()  # Track processed site IDs

        for site_info in processed_metadata:
            site_id = site_info.get('Site ID', 'Unknown')
            if site_id in processed_site_ids:
                continue  # Skip if already processed

            scope_requirement = next((item.get('Scope Package', 'Unknown') for item in site_location.inspection_data if item.get('Site ID') == site_id), 'Unknown')
            site_inspection = InspectionProcessor.get_or_create_site_inspection(db, inspection, site_id, scope_requirement)
            FlightProcessor.process_flights(db, site_inspection, passfail_list, flight_requirements, current_timestamp)
            processed_site_ids.add(site_id)  # Mark as processed

        
        
        AuditManager.clear_and_add_audit_entries(db, inspection, flight_requirements, current_timestamp)
        print("PROCESSING INSPECTION DATA END...")
        return inspection

    @staticmethod
    def get_or_create_inspection(db, inspection_id):
        existing_inspection = db.query(Inspection).filter_by(inspection_id=inspection_id).first()

        if existing_inspection:
            existing_inspection.status = "Updated"
            return existing_inspection
        else:
            new_inspection = Inspection(inspection_id=inspection_id, status="New")
            db.add(new_inspection)
            db.commit()  
            return new_inspection

    @staticmethod
    def get_or_create_site_inspection(db, inspection, site_id, scope_requirement):
        site_inspection = db.query(SiteInspection).filter_by(site_id=site_id, inspection_id=inspection.inspection_id).first()

        if site_inspection:
            site_inspection.scope_requirement = scope_requirement
        else:
            site_inspection = SiteInspection(site_id=site_id, inspection_id=inspection.inspection_id, scope_requirement=scope_requirement)
            inspection.sites.append(site_inspection)
            db.add(site_inspection)
            db.commit()  
        return site_inspection

