import re
from orbit_analysis import OrbitAnalyzer
from ascent_descent_analyzer import AscentDescentAnalyzer
from tower_flight_type_1_analyzer import TowerFlightType1Analyzer
from tower_flight_type_2_analyzer import TowerFlightType2Analyzer
from compound_flight_analyzer import CompoundCheckAnalyzer
from top_down_analyzer import TopDownAnalyzer
from database import DatabaseManager, DATABASE_URL
from dji_data_extraction import SiteLocation
import pandas as pd
from flight_processor import FlightProcessor
from flight_models import *
from datetime import datetime
import pytz
from scope_checker import ScopeChecker
from inspection_checker import InspectionChecker
from audit_manager import AuditManager

class FlightAnalyzer:
    def __init__(self, db, flight_data_df, passfail_list):
        self.db = db
        self.flight_data_df = flight_data_df
        self.passfail_list = passfail_list

    def run_analysis(self):
        print("Starting run_analysis method")
        orbit_criteria = ['downlook', 'center in', 'center out', 'uplook', re.compile(r'Orbit \d+', re.IGNORECASE)]
        print(f"Orbit criteria: {orbit_criteria}")

        print("Initializing OrbitAnalyzer")
        orbit_analyzer = OrbitAnalyzer(self.passfail_list, self.flight_data_df, orbit_criteria)
        
        print("Running analyze_orbit_flights")
        orbit_result = orbit_analyzer.analyze_orbit_flights()
        print(f"Orbit analysis result: {orbit_result}")

        if orbit_result:
            print(f"Adding audit entry for orbit analysis: inspection_id={self.inspection_id}, site_id={self.site_id}")
            AuditManager.add_audit_entry(self.db, self.inspection_id, self.site_id, "System", "Orbit Analysis", orbit_result, datetime.now(pytz.timezone('US/Central')))

        # Add similar print statements for other analyzers

        print("Completed run_analysis method")

        ascent_descent_criteria = ['cable run', re.compile(r'ascent', re.IGNORECASE), re.compile(r'descent', re.IGNORECASE)]
        ascent_descent_analyzer = AscentDescentAnalyzer(self.passfail_list, self.flight_data_df, ascent_descent_criteria)
        ascent_descent_result = ascent_descent_analyzer.analyze(self.passfail_list)
        if ascent_descent_result:
            AuditManager.add_audit_entry(self.db, self.inspection_id, self.site_id, "System", "Ascent/Descent Analysis", ascent_descent_result, datetime.now(pytz.timezone('US/Central')))

        compound_analyzer = CompoundCheckAnalyzer()
        compound_analyzer.passfail_data = self.passfail_list
        compound_analyzer.flight_data = self.flight_data_df
        compound_result = compound_analyzer.analyze_compound_check()
        if compound_result:
            AuditManager.add_audit_entry(self.db, self.inspection_id, self.site_id, "System", "Compound Check Analysis", compound_result, datetime.now(pytz.timezone('US/Central')))

        top_down_analyzer = TopDownAnalyzer()
        top_down_analyzer.passfail_data = self.passfail_list
        top_down_analyzer.flight_data = self.flight_data_df
        top_down_result = top_down_analyzer.analyze_top_down()
        if top_down_result:
            AuditManager.add_audit_entry(self.db, self.inspection_id, self.site_id, "System", "Top Down Analysis", top_down_result, datetime.now(pytz.timezone('US/Central')))

        tf1_analyzer = TowerFlightType1Analyzer(self.passfail_list, self.flight_data_df)
        tf1_result = tf1_analyzer.analyze()
        if tf1_result:
            AuditManager.add_audit_entry(self.db, self.inspection_id, self.site_id, "System", "Tower Flight Type 1 Analysis", tf1_result, datetime.now(pytz.timezone('US/Central')))

        tf2_analyzer = TowerFlightType2Analyzer(self.passfail_list, self.flight_data_df)
        tf2_result = tf2_analyzer.analyze()
        if tf2_result:
            AuditManager.add_audit_entry(self.db, self.inspection_id, self.site_id, "System", "Tower Flight Type 2 Analysis", tf2_result, datetime.now(pytz.timezone('US/Central')))


    def populate_flight_analysis_result(self, processed_metadata, passfail_list, flight_requirements):
        with DatabaseManager(DATABASE_URL).get_db() as db:
            site_location = SiteLocation()
            site_location.inspection_data = pd.read_excel(r'app\Inspection data\inspection_data.xlsx').to_dict('records')

            site_id = next((item.get('Site ID', 'Unknown') for item in processed_metadata), 'Unknown')
            scope_requirement = next((item.get('Scope Package', 'Unknown') for item in site_location.inspection_data if item.get('Site ID') == site_id), 'Unknown')
            inspection_id = str(next((item.get('Inspection', 'Unknown') for item in site_location.inspection_data if item.get('Site ID') == site_id), 'Unknown'))

            existing_inspection = db.query(Inspection).filter_by(inspection_id=inspection_id).first()
            if existing_inspection:
                inspection = existing_inspection
                inspection.status = "Updated"
            else:
                inspection = Inspection(inspection_id=inspection_id, status="New")
            
            db.add(inspection)
            db.flush()

            site_inspection = db.query(SiteInspection).filter_by(site_id=site_id, inspection_id=inspection.inspection_id).first()
            if site_inspection:
                site_inspection.scope_requirement = scope_requirement
                #required_flights, captured_flights = ScopeChecker.process_scope(db, site_inspection, flight_requirements)
                
                if site_inspection.scope_status == InspectionStatus.SCOPE_PASSED:
                    site_inspection.status = InspectionStatus.COMPLETED
                    # Add audit entry for scope status change
                    AuditManager.add_audit_entry(
                        db,
                        inspection.inspection_id,
                        site_inspection.site_id,
                        "System",
                        "Scope Status Changed",
                        {"new_status": "PASSED"},
                        datetime.now(pytz.timezone('US/Central'))
                    )
                else:
                    site_inspection.status = InspectionStatus.IN_PROGRESS
            else:
                site_inspection = SiteInspection(site_id=site_id, inspection_id=inspection.inspection_id, scope_requirement=scope_requirement, status=InspectionStatus.IN_PROGRESS)
                db.add(site_inspection)

            db.commit()
            db.refresh(inspection)

            # Check inspection status using InspectionChecker
            inspection_status = InspectionChecker.check_inspection_status(self.db, site_inspection)
            print(f"Inspection Status: {inspection_status}")

            # Placeholder for pass request conditions
            # TODO: Implement the conditions for pass request

            return inspection.inspection_id
