from .flight_models import *
from .audit_manager import AuditManager
from datetime import datetime
import pytz



class InspectionChecker:
    @staticmethod
    def check_inspection_status(db, site_inspection: SiteInspection) -> InspectionStatus:
        # Check if scope status is passed
        if site_inspection.scope_status != InspectionStatus.SCOPE_PASSED:
            print("Scope status is not passed")
            site_inspection.site_status = SiteStatus.PENDING  # Update site_status
            return InspectionStatus.IN_PROGRESS

        # Check if all required flights are passed
        for flight in site_inspection.flights:
            if flight.required and flight.status != FlightStatus.PASSED:
                print("Required flight status is not passed")
                site_inspection.site_status = SiteStatus.PENDING  # Update site_status
                return InspectionStatus.IN_PROGRESS

        # If scope is passed and all required flights are passed, set status to COMPLETED
        print("Inspection is completed")
        site_inspection.site_status = SiteStatus.PASSED  # Update site_status
        # Log the event of site status changing to passed
        AuditManager.add_audit_entry(
            db,
            inspection_id=site_inspection.inspection_id,
            site_id=site_inspection.site_id,
            user="System",
            action="Site Status Changed",
            details={"new_status": "PASSED"},
            timestamp=datetime.now(pytz.timezone('US/Central'))
        )
        return InspectionStatus.COMPLETED

    @staticmethod
    def update_inspection_status(db, site_inspection: SiteInspection):
        new_status = InspectionChecker.check_inspection_status(site_inspection)
        if site_inspection.status != new_status:
            site_inspection.status = new_status
            db.commit()

        return new_status
