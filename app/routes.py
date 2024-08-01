from flask import request, jsonify, render_template
from metadata_processor import MetadataProcessor
from flight_analyzer import FlightAnalyzer
from utils import load_flight_requirements, create_inspection_dict, export_flight_data, print_db_contents
from flight_models import Inspection, SiteInspection, Flight
import json
from sqlalchemy.orm import joinedload
from flight_sorting import FlightSorter
from inspection_processor import InspectionProcessor  # Add this import
from database_loader import *
from flask import send_file
import io
from PIL import Image
import os
from plotter import Plotter


def setup_routes(app, db_manager):
    @app.route('/')
    def index() -> str:
        return render_template('index.html')

    @app.route('/process', methods=['POST'])
    def process_metadata():
        metadata_list = request.json
        print(f"Received {len(metadata_list)} metadata items")
        print(f"First item: {metadata_list[0]}")
        with db_manager.get_db() as db:
            db_loader = DatabaseLoader(db)
            
            # Get unique identifiers from the incoming metadata
            unique_identifiers = [item.get('Unique Identifier', item.get('unique_identifier')) for item in metadata_list] 
            print(f"Found {len(unique_identifiers)} unique identifiers")

            # Fetch existing metadata from the database
        
            existing_photos = db_loader.get_existing_photos(unique_identifiers)
            print(f"Found {len(existing_photos)} existing photos")
            
            
            # Merge existing metadata with incoming metadata
            processor = MetadataProcessor()
            merged_metadata = processor.process_and_enrich_metadata(metadata_list, existing_photos)
            
            # --- Moved db_loader.load_metadata call ---

        # Process the MERGED metadata
        sorter = FlightSorter(merged_metadata, [])
        flight_data_df, passfail_list = sorter.process_flight_data()
        
        with db_manager.get_db() as db:
            analyzer = FlightAnalyzer(db, flight_data_df, passfail_list)
            print(f"Running flight analysis")
            analyzer.run_analysis()

            flight_requirements = load_flight_requirements()
    
            inspection_id = analyzer.populate_flight_analysis_result(merged_metadata, passfail_list, flight_requirements)
            print(f"Inspection ID: {inspection_id}")

            # Call process_inspection here
            inspection = InspectionProcessor.process_inspection(db, merged_metadata, passfail_list, flight_requirements)
            print(f"Inspection processed: {inspection}")

            inspection = db.query(Inspection).options(
                joinedload(Inspection.sites).joinedload(SiteInspection.flights).joinedload(Flight.analysis)
            ).get(inspection_id)
            print(f"Retrieved inspection: {inspection}")

            inspection_dict = create_inspection_dict(inspection)
            print(f"Created inspection dict: {inspection_dict}")

            # Now load the metadata into the database
            db_loader.load_metadata(merged_metadata) 


            #export_flight_data(flight_data_df, passfail_list)

            json_output = json.dumps(inspection_dict, indent=4, default=str)
            #print(json_output)

            #print_db_contents(db)
            

            
            
            print("Inspection Dict final:", inspection_dict) 
            return jsonify(inspection_dict), 200 
        




    @app.route('/get_photo/<unique_identifier>')
    def get_photo(unique_identifier):
        with db_manager.get_db() as db:
            photo = db.query(Photo).filter_by(unique_identifier=unique_identifier).first()
            if photo and photo.file_path:
                try:
                    # Ensure the path is absolute and normalized
                    file_path = os.path.abspath(os.path.normpath(photo.file_path))
                    
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as img_file:
                            img = Image.open(img_file)
                            img.thumbnail((150, 150))

                            img_byte_arr = io.BytesIO()
                            img.save(img_byte_arr, format='JPEG')
                            img_byte_arr.seek(0)

                            return send_file(img_byte_arr, mimetype='image/jpeg', as_attachment=False)
                    else:
                        print(f"File not found: {file_path}")
                        return '', 404
                except Exception as e:
                    print(f"Error opening image file: {e}")
                    return '', 404
        return '', 404

