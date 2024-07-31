from flight_models import *
import json
from flight_models import SiteInspection
from sqlalchemy.orm import joinedload
from scope_checker import ScopeChecker

# This module processes flight data for site inspections, ensuring that each site has a set of required flights.
# The process involves the following steps:
# 1. Retrieve the site inspection data from the database.
# 2. Determine the required flights based on the site's scope requirement.
# 3. Create empty Flight objects for each required flight with default values.
# 4. Process the pass/fail list to create Flight objects with their associated FlightAnalysis.
# 5. For each flight in the pass/fail list:
#    - If the flight already exists and its list of photos is different from the incoming flight's list, update it.
#    - If the flight does not exist, add it to the site inspection.
# 6. Ensure that flights with matching photos are not unnecessarily replaced.
# 7. Add new flights to the site inspection and commit changes to the database.
# 8. Handle special cases in data processing, such as converting 'N/A' to None and processing specific fields like 'total_rotation' and 'north_facing_check'.
# 9. Add system flight audit entries for tracking changes and maintaining a history of flight data.
#
# The goal is to fulfill the scope requirements by allowing the uploader to upload the correct photos, 
# while ensuring that existing data is preserved and only updated when necessary.



class FlightProcessor:
    @staticmethod
    def check_scope_status(required_flights, captured_flights):
        return InspectionStatus.SCOPE_PASSED if set(required_flights) == captured_flights else InspectionStatus.SCOPE_FAILED

    @staticmethod
    def process_flights(db, site_inspection, passfail_list, flight_requirements, timestamp):
        # Step 1: Retrieve the site inspection data from the database
        print(f"Processing flights for site_inspection: {site_inspection.site_id}, inspection_id: {site_inspection.inspection_id}")
        site_inspection = db.query(SiteInspection).options(joinedload(SiteInspection.flights)).get((site_inspection.site_id, site_inspection.inspection_id))
        if site_inspection is None:
            print("Error: site_inspection is None")
            return

        # Step 2: Determine the required flights based on the site's scope requirement
        required_flights = flight_requirements.get(site_inspection.scope_requirement, [])
        if required_flights and isinstance(required_flights[0], str):
            required_flights = [flight.strip().lower() for flight in required_flights[0].split(',')]
        else:
            required_flights = []  # or handle this case as appropriate for your application
        print(f"Required flights: {required_flights}")

        # Step 3: Create empty Flight objects for each required flight with default values
        all_flights = {flight_name: Flight(
            site_id=site_inspection.site_id,
            inspection_id=site_inspection.inspection_id,
            flight_name=flight_name,
            required=True,
            status=FlightStatus.PENDING,
            is_captured=False,
            created_at=timestamp
        ) for flight_name in required_flights}

        # Step 4: Process the pass/fail list to create Flight objects with their associated FlightAnalysis
        for item in passfail_list:
            item['Site ID'] = site_inspection.site_id  

        # Step 5: For each flight in the pass/fail list
        for item in passfail_list:
            # Step 5: For each flight in the pass/fail list
            #print(f"Item: {item}")
            if 'Photos' not in item:
                print(f"Photos key missing in item: {item}")
            if item.get('Site ID') == site_inspection.site_id:
                flight_name = item.get('Flight Category', 'Unknown').lower()
                status = FlightProcessor.determine_flight_status(item)
                print(f"FLIGHT {flight_name} status: {status}")
                print(f"Processing flight: {flight_name}, status: {status}")

                flight = Flight(
                    site_id=site_inspection.site_id,
                    inspection_id=site_inspection.inspection_id,
                    flight_name=flight_name,
                    required=(flight_name in required_flights),
                    status=status,
                    is_captured=True,
                    pilot_name="john doe",
                    created_at=timestamp
                )
                flight.analysis = FlightProcessor.create_flight_analysis(flight, item)
                print('adding photos')
                FlightProcessor.add_photos(flight, item.get('Photos', []))

                all_flights[flight_name] = flight



        # Step 6: Ensure that flights with matching photos are not unnecessarily replaced
        existing_flights = {flight.flight_name: flight for flight in site_inspection.flights}
        print(f"Existing flights: {list(existing_flights.keys())}")

        for item in passfail_list:  # Iterate through all flights from passfail_list
            flight_name = item.get('Flight Category', 'Unknown').lower()
            print(f"Processing flight: {flight_name}") # Debug: Indicate which flight is being processed

            if flight_name in existing_flights:
                existing_flight = existing_flights[flight_name]
                print(f"Found existing flight: {existing_flight}") # Debug: Confirm existing flight found
                new_flight = all_flights.get(flight_name)
                new_photos = {photo.filename for photo in new_flight.photos} if new_flight else set()
                existing_photos = {photo.filename for photo in existing_flight.photos}

                print(f"Existing photos for {flight_name}: {existing_photos}") # Debug: Show existing photos
                print(f"New photos for {flight_name}: {new_photos}") # Debug: Show new photos
                print(f"New photos == existing photos: {new_photos == existing_photos}") # Debug: Show comparison result

                photos_to_add = new_photos - existing_photos  # Find photos that are new
                print(f"Photos to add: {photos_to_add}") # Debug: Show photos to add

                if photos_to_add:
                    print(f"Adding {len(photos_to_add)} new photos to flight: {flight_name}")
                    FlightProcessor.add_photos(existing_flight, photos_to_add)  # Add only the new photos

                    # Update flight status based on all photos
                    existing_flight.status = FlightProcessor.determine_flight_status(item)
                    db.add(existing_flight)
                    print(f"Updated flight with new photos: {existing_flight}")
                else:
                    print(f"No new unique photos found for flight: {flight_name}") # Debug: Indicate no new photos

            else:
                # Flight doesn't exist, create and add photos
                if flight_name in all_flights:
                    print(f"Flight '{flight_name}' already exists in all_flights. Skipping creation.")
                else:
                    # Flight doesn't exist, create and add photos
                    print(f"Creating new flight: {flight_name}")
                    flight = Flight(
                        site_id=site_inspection.site_id,
                        inspection_id=site_inspection.inspection_id,
                        flight_name=flight_name,
                        required=(flight_name in required_flights),
                        status=FlightProcessor.determine_flight_status(item),
                        is_captured=True,
                        pilot_name="john doe",
                        created_at=timestamp
                    )
                    flight.analysis = FlightProcessor.create_flight_analysis(flight, item)
                    FlightProcessor.add_photos(flight, item.get('Photos', []))
                    site_inspection.flights.append(flight)
                    db.add(flight)

        # Step 7: Add new flights to the site inspection and commit changes to the database
        for flight in all_flights.values():
            if flight.flight_name not in existing_flights:
                print(f"Adding flight: {flight}")
                site_inspection.flights.append(flight)
                db.add(flight)
                
        captured_flights = set()
        for flight in all_flights.values():
            if flight.is_captured:
                captured_flights.add(flight.flight_name)
                
                
        # print(f"Site Inspection ID: {site_inspection.site_id}")
        # print(f"Scope Requirement: {site_inspection.scope_requirement}")
        # print(f"Pass/Fail List: {passfail_list}")
        
        required_flights, captured_flights = ScopeChecker.process_scope(db, site_inspection, flight_requirements)


        
            

        db.commit()



    @staticmethod
    def add_required_flights_audit_entry(db, site_inspection, required_flights, timestamp):
        from audit_manager import AuditManager
        AuditManager.add_required_flights_audit_entry(
            db,
            site_inspection.inspection_id,
            site_inspection.site_id,
            required_flights,
            timestamp
        )




    @staticmethod
    def create_flight_analysis(flight, item):
        print(f"Creating flight analysis for flight: {flight.flight_name}")
        analysis_data = {}
        excluded_categories = ['top down', 'cable anchor', 'cable run']
        for k, v in item.items():
            if k in ['Flight Category', 'Photos', 'Pass/Fail', 'Orbit Type']:  # Exclude 'Orbit Type'
                continue

            key = k.lower().replace(' ', '_')
            status_key = f"{key}_status"
            value_key = f"{key}_value"

            # Skip 'total_rotation' for excluded categories
            if flight.flight_name.lower() in excluded_categories and key == 'total_rotation':
                continue

            if hasattr(FlightAnalysis, status_key) or hasattr(FlightAnalysis, value_key):
                print(f"Processing key: {key}, value: {v}")
                if isinstance(v, tuple):
                    print(f"Value is a tuple: {v}")
                    if len(v) == 2 and isinstance(v[0], str) and (isinstance(v[1], (int, float, list, str)) or v[1] is None):
                        analysis_data[status_key] = v[0]
                        analysis_data[value_key] = v[1]
                        print(f"Added tuple values for {key}: status={v[0]}, value={v[1]}")
                    elif len(v) == 1 and v[0].lower() == 'n/a':  # Handle ('N/A',) case
                        analysis_data[status_key] = 'N/A'
                        analysis_data[value_key] = None
                        print(f"Processed ('N/A',) tuple for {key}")
                    else:
                        print(f"Unexpected tuple format for {key}: {v}")
                        analysis_data[key] = str(v)  # Convert to string as a fallback
                elif isinstance(v, str):
                    if v.lower() == 'n/a':
                        analysis_data[key] = None
                    else:
                        analysis_data[key] = v
                    print(f"Processed string value for {key}: {analysis_data[key]}")
                else:
                    analysis_data[key] = v
                    print(f"Processed other value for {key}: {analysis_data[key]}")

                #print(f"Added key: {key} with value: {analysis_data.get(key)} to analysis data")
            else:
                print(f"Warning: Attribute {key} not found in FlightAnalysis")

        print(f"DEBUG: create_flight_analysis - item['Radial Distance Check']: {item.get('Radial Distance Check')}")

        try:
            return FlightAnalysis(flight_id=flight.flight_id, **analysis_data)
        except Exception as e:
            print(f"Error creating FlightAnalysis for {flight.flight_name}: {str(e)}")
            print(f"Analysis data causing the error: {analysis_data}")
            return None






    @staticmethod
    def determine_flight_status(flight_row):
        """
        Determines the flight status based on pass/fail criteria in the flight row.

        Args:
            flight_row (dict): A dictionary representing a single flight's data.

        Returns:
            FlightStatus: The determined flight status (PASSED, FAILED, or PENDING).
        """

        # Explicitly define keys to skip
        skip_keys = ['Site ID', 'Site IDs', 'Orbit Type', 'Photos']

        # Assume pending status initially
        flight_status = FlightStatus.PENDING 

        for key, value in flight_row.items():
            # Skip specified keys
            if key in skip_keys:
                continue

            # Check for 'fail' in strings and tuples (case-insensitive)
            if isinstance(value, str) and 'fail' in value.lower():
                print(f"Found 'fail' in value: {value}, returning FAILED")
                return FlightStatus.FAILED
            elif isinstance(value, tuple):
                for v in value:
                    if isinstance(v, str) and 'fail' in v.lower():
                        print(f"Found 'fail' in tuple value: {v}, returning FAILED")
                        return FlightStatus.FAILED

            # Add checks for other failure conditions here
            # Example:
            # elif key == 'Tower Coverage Percent' and value < 80:
            #     print(f"Tower Coverage Percent below threshold: {value}, returning FAILED")
            #     return FlightStatus.FAILED

            # If the loop completes without finding a failure condition and the status is still pending, mark as passed
            if flight_status == FlightStatus.PENDING:
                flight_status = FlightStatus.PASSED

        return flight_status











    @staticmethod
    def process_analysis_value(key, value):
        print(f"Processing value for {key}: {value}")
        if isinstance(value, str):
            print(f"Value is a string")
            if value.lower() == 'n/a':
                print(f"Value is N/A so returning None")
                return None
            else:
                print(f"Value is not N/A so returning {value}")
                return value  # Return the string value if it's not "N/A"
        elif isinstance(value, tuple) and len(value) == 2: 
            print(f"Value is a tuple so returning a dictionary")
            return {
                f'{key}_status': value[0],
                f'{key}_value': value[1]
            }
        print(f"Value is of type {type(value).__name__} so returning it as is")
        return value  # Return other value types as is








    @staticmethod
    def add_photos(flight, photos):
        for photo in photos:
            photo_entry = Photo(flight_id=flight.flight_id, filename=photo, photo_metadata={})
            #print(f"Adding photo {photo} for flight {flight.flight_name}")
            flight.photos.append(photo_entry)
    #print(f"Added photos for flight {Flight.flight_name}: {[photo.filename for photo in Flight.photos]}")

    @staticmethod
    def add_system_flight_audit_entry(db, site_inspection, flight, timestamp):
        from audit_manager import AuditManager
        AuditManager.add_system_flight_entry(
            db,
            site_inspection.inspection_id,
            site_inspection.site_id,
            flight.flight_name,
            site_inspection.scope_requirement,
            timestamp
        )
