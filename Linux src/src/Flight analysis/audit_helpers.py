from sqlalchemy import func
from flight_models import AuditEntry, Inspection, SiteInspection, Flight
from typing import List, Dict, Any

def format_audit_trail(audit_entries):
    formatted_trail = []
    current_inspection = None
    for entry in sorted(audit_entries, key=lambda x: x.timestamp):
        if current_inspection != entry.inspection_id:
            current_inspection = entry.inspection_id
            formatted_trail.append(f"Audit for inspection {entry.inspection_id}")
            formatted_trail.append(f"Site ID: {entry.site_id}")
        
        if entry.action == "Initial Review":
            formatted_trail.append(f"Initial review: {entry.details['status']}")
        elif entry.action == "Added Flight":
            formatted_trail.append(f"Pilot {entry.user} added flight {entry.details['flight_name']}, result: {entry.details['result']}")
        elif entry.action == "Scope Check":
            formatted_trail.append(f"Required flights: {', '.join(entry.details['required_flights'])}")
            formatted_trail.append(f"Captured flights: {', '.join(entry.details['captured_flights'])}")
            formatted_trail.append(f"Scope check: {entry.details['result']}")
        elif entry.action == "Inspection Check":
            formatted_trail.append(f"Inspection check: {entry.details['result']}")
        elif entry.action == "Inspection Committed":
            formatted_trail.append(f"Pilot {entry.user} committed for upload")
        
    return "\n".join(formatted_trail)


def display_audit_trail(inspection_id: str, db_session) -> List[Dict[str, Any]]:
    audit_entries = db_session.query(AuditEntry).filter_by(inspection_id=inspection_id).order_by(AuditEntry.timestamp).all()
    return format_audit_trail(audit_entries)

def query_pilot_stats(pilot_name: str, db_session) -> Dict[str, Any]:
    stats = {
        'total_flights': db_session.query(AuditEntry).filter_by(user=pilot_name, action='Added Flight').count(),
        'retrips': db_session.query(AuditEntry).filter_by(user=pilot_name, action='Retrip Requested').count(),
        'override_requests': db_session.query(AuditEntry).filter_by(user=pilot_name, action='Override Requested').count()
    }
    return stats

def query_site_reviewer_stats(reviewer_name: str, db_session) -> Dict[str, Any]:
    stats = {
        'total_reviews': db_session.query(AuditEntry).filter_by(user=reviewer_name, action='Review Completed').count(),
        'override_approvals': db_session.query(AuditEntry).filter_by(user=reviewer_name, action='Override Approved').count(),
        'override_denials': db_session.query(AuditEntry).filter_by(user=reviewer_name, action='Override Denied').count()
    }
    return stats

def get_retrip_numbers(db_session) -> Dict[str, int]:
    retrip_numbers = db_session.query(
        AuditEntry.user,
        func.count(AuditEntry.audit_id).label('retrip_count')
    ).filter_by(action='Retrip Requested').group_by(AuditEntry.user).all()
    
    return {user: count for user, count in retrip_numbers}
