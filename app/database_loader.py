from .flight_models import Inspection, SiteInspection, Flight, Photo, AuditEntry
from .scope_checker import ScopeChecker 
from sqlalchemy.orm import Session
import json

class DatabaseLoader:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_inspection(self, inspection_id):
        existing_inspection = self.db.query(Inspection).filter_by(inspection_id=inspection_id).first()
        if existing_inspection:
            existing_inspection.status = "Updated"
            return existing_inspection
        else:
            new_inspection = Inspection(inspection_id=inspection_id, status="New")
            self.db.add(new_inspection)
            self.db.commit()
            return new_inspection

    def get_or_create_site_inspection(self, inspection, site_id, scope_requirement):
        site_inspection = self.db.query(SiteInspection).filter_by(site_id=site_id, inspection_id=inspection.inspection_id).first()
        if site_inspection:
            site_inspection.scope_requirement = scope_requirement
        else:
            site_inspection = SiteInspection(site_id=site_id, inspection_id=inspection.inspection_id, scope_requirement=scope_requirement)
            inspection.sites.append(site_inspection)
            self.db.add(site_inspection)
            self.db.commit()
        return site_inspection

    def add_flight(self, site_inspection, flight_name, status, is_captured, pilot_name, timestamp):
        
        flight_requirements = {}  
        required_flights = ScopeChecker.get_required_flights(flight_requirements, site_inspection.scope_requirement)

        flight = Flight(
            site_id=site_inspection.site_id,
            inspection_id=site_inspection.inspection_id,
            flight_name=flight_name,
            required=(flight_name in required_flights),
            status=status,
            is_captured=is_captured,
            pilot_name=pilot_name,
            created_at=timestamp
        )
        self.db.add(flight)
        self.db.commit()
        return flight

    def add_photo(self, flight, filename):
        photo_entry = Photo(flight_id=flight.flight_id, filename=filename, photo_metadata={})
        flight.photos.append(photo_entry)
        self.db.commit()

    def add_audit_entry(self, inspection_id, site_id, user, action, details, timestamp):
        entry = AuditEntry(
            inspection_id=inspection_id,
            site_id=site_id,
            user=user,
            action=action,
            details=details,
            timestamp=timestamp
        )
        self.db.add(entry)
        self.db.commit()

    def clear_audit_entries(self, inspection_id):
        self.db.query(AuditEntry).filter_by(inspection_id=inspection_id).delete()
        self.db.commit()



    def load_metadata(self, metadata_list):
        unique_metadata = {}
        for metadata in metadata_list:
            unique_identifier = metadata.get('Unique Identifier')
            if unique_identifier and unique_identifier not in unique_metadata:
                # Filter out entries with only the unique identifier
                if any(value is not None for key, value in metadata.items() if key != 'Unique Identifier'):
                    unique_metadata[unique_identifier] = metadata

        for metadata in unique_metadata.values():
            # Check if the photo already exists in the database
            existing_photo = self.db.query(Photo).filter_by(unique_identifier=metadata['Unique Identifier']).first()
            if existing_photo:
                # Update the existing photo metadata if necessary
                pass
            else:
                # Add new photo metadata
                self.add_new_photo(metadata)

    def add_new_photo(self, metadata):
        # Check if the photo already exists
        existing_photo = self.db.query(Photo).filter_by(unique_identifier=metadata['Unique Identifier']).first()
        if existing_photo:
            return  

        # # Convert datetime objects to strings in photo_metadata
        # photo_metadata = {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in metadata.items()}

        # Create a new Photo object and add it to the database
        new_photo = Photo(
            flight_id=None,  # Set the appropriate flight_id if available
            filename=metadata['File Name'],
            #photo_metadata=photo_metadata,
            create_date=metadata['Create Date'],
            gps_latitude=metadata.get('GPS Latitude'),
            gps_longitude=metadata.get('GPS Longitude'),
            gimbal_pitch_degree=metadata.get('Gimbal Pitch Degree'),
            flight_yaw_degree=metadata.get('Flight Yaw Degree'),
            flight_x_speed=metadata.get('Flight X Speed'),
            flight_y_speed=metadata.get('Flight Y Speed'),
            relative_altitude=metadata.get('Relative Altitude'),
            image_width=metadata.get('Image Width'),
            image_length=metadata.get('Image Length'),
            digital_zoom_ratio=metadata.get('Digital Zoom Ratio'),
            unique_identifier=metadata['Unique Identifier']
        )
        self.db.add(new_photo)
        self.db.commit()
        
        
    def query_metadata(self):
        # Query all photos and their metadata
        photos = self.db.query(Photo).filter(Photo.unique_identifier != None).all() # Only retrieve photos with a unique_identifier
        result = []
        for photo in photos:
            photo_data = {
                'filename': photo.filename,
                'create_date': photo.create_date.isoformat() if photo.create_date else None,
                'gps_latitude': photo.gps_latitude,
                'gps_longitude': photo.gps_longitude,
                'gimbal_pitch_degree': photo.gimbal_pitch_degree,
                'flight_yaw_degree': photo.flight_yaw_degree,
                'flight_x_speed': photo.flight_x_speed,
                'flight_y_speed': photo.flight_y_speed,
                'relative_altitude': photo.relative_altitude,
                'image_width': photo.image_width,
                'image_length': photo.image_length,
                'digital_zoom_ratio': photo.digital_zoom_ratio,
                'unique_identifier': photo.unique_identifier,
                'photo_metadata': photo.photo_metadata
            }
            result.append(photo_data)
        return result
    
    def get_existing_photos(self, unique_identifiers):
        """
        Retrieves existing photos from the database based on a list of unique identifiers.

        Args:
            unique_identifiers (list): A list of unique identifiers for the photos.

        Returns:
            list: A list of Photo objects found in the database, or an empty list if none are found.
        """
        
        return self.db.query(Photo).filter(Photo.unique_identifier.in_(unique_identifiers)).all()
    
    
## write main implementation for query metadata
if __name__ == '__main__':
    from database import DatabaseManager, DATABASE_URL

    # Initialize the database manager
    db_manager = DatabaseManager(DATABASE_URL)

    # Query metadata using query_metadata
    with db_manager.get_db() as db:
        db_loader = DatabaseLoader(db)
        metadata = db_loader.query_metadata()
        
        # Print the queried metadata in a readable format
        for photo_data in metadata:
            print(json.dumps(photo_data, indent=4))