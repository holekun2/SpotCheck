from flight_models import *
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime
import pytz


class AuditManager:
    @staticmethod
    def clear_and_add_audit_entries(db: Session, inspection: Inspection, flight_requirements: Dict[str, List[str]], timestamp: datetime) -> None:
        db.query(AuditEntry).filter_by(inspection_id=inspection.inspection_id).delete()
        db.commit()

        AuditManager.add_audit_entry(db, inspection.inspection_id, inspection.sites[0].site_id, "System", "Initial Review", {"status": "Started"}, inspection.created_at)

        for site_inspection in inspection.sites:
            site_inspection.initiate_inspection()

            for flight in site_inspection.flights:
                AuditManager.add_flight_audit_entry(db, inspection.inspection_id, site_inspection.site_id, flight, flight.created_at)

            site_inspection.complete_inspection()

            AuditManager.add_scope_check_audit_entry(db, inspection.inspection_id, site_inspection, flight_requirements, inspection.created_at)
            AuditManager.add_inspection_check_audit_entry(db, inspection.inspection_id, site_inspection, inspection.created_at)
            AuditManager.add_audit_entry(db, inspection.inspection_id, site_inspection.site_id, "Pilot", "Inspection Committed", {}, inspection.created_at)

        db.commit()

    @staticmethod
    def add_audit_entry(db, inspection_id, site_id, user, action, details, timestamp):
        entry = AuditEntry(
            inspection_id=inspection_id,
            site_id=site_id,
            user=user,
            action=action,
            details=details,
            timestamp=timestamp
        )
        db.add(entry)
        db.commit()

    @staticmethod
    def add_flight_audit_entry(db, inspection_id, site_id, flight, timestamp):
        pilot_name = flight.pilot_name or "System" if flight.pilot_name == "Unknown Pilot" else flight.pilot_name
        entry = AuditEntry.create_flight_entry(
            inspection_id=inspection_id,
            site_id=site_id,
            flight_id=flight.flight_id,
            pilot_name=pilot_name,
            flight_name=flight.flight_name,
            result=flight.status.value,
            timestamp=timestamp
        )
        db.add(entry)
        db.commit()

    @staticmethod
    def add_scope_check_audit_entry(db, inspection_id, site_inspection, flight_requirements, timestamp):
        required_flights = flight_requirements.get(site_inspection.scope_requirement, [])
        captured_flights = [flight.flight_name for flight in site_inspection.flights]
        result = site_inspection.scope_status.value
        entry = AuditEntry.create_scope_check_entry(
            inspection_id=inspection_id,
            site_id=site_inspection.site_id,
            required_flights=required_flights,
            captured_flights=captured_flights,
            result=result,
            timestamp=timestamp
        )
        db.add(entry)
        db.commit()

    @staticmethod
    def add_inspection_check_audit_entry(db, inspection_id, site_inspection, timestamp):
        result = "Completed" if site_inspection.status == InspectionStatus.COMPLETED else "In Progress"
        entry = AuditEntry.create_inspection_check_entry(
            inspection_id=inspection_id,
            site_id=site_inspection.site_id,
            result=result,
            timestamp=timestamp
        )
        db.add(entry)
        db.commit()


    @staticmethod
    def add_required_flights_audit_entry(db, inspection_id, site_id, required_flights, timestamp):
        entry = AuditEntry(
            inspection_id=inspection_id,
            site_id=site_id,
            user="System",
            action="Added Required Flights",
            details={
                "required_flights": ", ".join(required_flights)
            },
            timestamp=timestamp
        )
        db.add(entry)
        db.commit()


    @staticmethod
    def add_system_flight_entry(db, inspection_id, site_id, flight_name, scope_package, timestamp):
        entry = AuditEntry(
            inspection_id=inspection_id,
            site_id=site_id,
            user="System",
            action=f"Added Flight {flight_name}",
            details={
                "flight_name": flight_name,
                "scope_package": scope_package,
                "method": "System via Scope Package"
            },
            timestamp=timestamp
        )
        db.add(entry)
        db.commit()

    @staticmethod
    def add_override_request_entry(db, inspection_id, site_id, flight_id, user, details, timestamp):
        entry = AuditEntry.create_override_request_entry(inspection_id, site_id, flight_id, user, details, timestamp)
        db.add(entry)
        db.commit()

    @staticmethod
    def add_override_approval_entry(db, inspection_id, site_id, flight_id, user, details, timestamp):
        entry = AuditEntry.create_override_approval_entry(inspection_id, site_id, flight_id, user, details, timestamp)
        db.add(entry)
        db.commit()

    @staticmethod
    def add_override_denial_entry(db, inspection_id, site_id, flight_id, user, details, timestamp):
        entry = AuditEntry.create_override_denial_entry(inspection_id, site_id, flight_id, user, details, timestamp)
        db.add(entry)
        db.commit()

    @staticmethod
    def add_photo_addition_entry(db, inspection_id, site_id, flight_id, user, details, timestamp):
        entry = AuditEntry.create_photo_addition_entry(inspection_id, site_id, flight_id, user, details, timestamp)
        db.add(entry)
        db.commit()

    @staticmethod
    def add_photo_addition_entry(db, inspection_id, site_id, flight_id, user, photos, timestamp):
        details = {
            "number_of_photos": len(photos),
            "photo_names": [photo.filename for photo in photos]
        }
        entry = AuditEntry.create_photo_addition_entry(inspection_id, site_id, flight_id, user, details, timestamp)
        db.add(entry)
        db.commit()

