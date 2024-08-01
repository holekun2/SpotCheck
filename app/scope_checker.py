# scope_checker.py

from flight_models import *

class ScopeChecker:
    @staticmethod
    def check_scope_completeness(required_flights, captured_flights):
        result = InspectionStatus.SCOPE_PASSED if set(required_flights).issubset(set(captured_flights)) else InspectionStatus.SCOPE_FAILED
        return result


    @staticmethod
    def get_required_flights(flight_requirements, scope_requirement):
        required_flights = flight_requirements.get(scope_requirement, [])
        if required_flights and isinstance(required_flights[0], str):
            return [flight.strip().lower() for flight in required_flights[0].split(',')]
        return []


    @staticmethod
    def get_captured_flights(flights):
        return {flight.flight_name for flight in flights if flight.is_captured}

    @staticmethod
    def process_scope(db, site_inspection, flight_requirements):
        required_flights = ScopeChecker.get_required_flights(flight_requirements, site_inspection.scope_requirement)
        captured_flights = ScopeChecker.get_captured_flights(site_inspection.flights)
        site_inspection.scope_status = ScopeChecker.check_scope_completeness(required_flights, captured_flights)
        db.commit()
        return required_flights, captured_flights

    @staticmethod
    def update_flight_statuses(site_inspection, required_flights):
        for flight in site_inspection.flights:
            if flight.flight_name in required_flights:
                flight.required = True
            else:
                flight.required = False
