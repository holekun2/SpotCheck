from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
from sqlalchemy import Enum as SQLAlchemyEnum
from enum import Enum as PyEnum
from sqlalchemy import UniqueConstraint
import pytz



Base = declarative_base()

class FlightStatus(PyEnum):  
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    REVIEW_FAILED = "review_failed"
    REVIEW_PASSED = "review_passed"
    OVERRIDE_REQUESTED = "override_requested"
    OVERRIDE_APPROVED = "override_approved"
    OVERRIDE_REJECTED = "override_rejected"

class InspectionStatus(PyEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "in_progress"
    REQUIRES_RETRIP = "requires_retrip"
    DELIVERED = "delivered"
    SCOPE_FAILED = "failed, check scope"
    SCOPE_PASSED = "passed"
    
class SiteStatus(PyEnum):
    PASS_REQUEST = "pass_request"
    PASSED = "passed"
    PENDING = "pending"
   
class OrbitType(PyEnum):
    FULL = "FULL"
    PARTIAL = "PARTIAL"

class Photo(Base):
    __tablename__ = 'photos'

    photo_id = Column(Integer, primary_key=True, autoincrement=True)
    flight_id = Column(Integer, ForeignKey('flights.flight_id'))
    filename = Column(String)
    photo_metadata = Column(JSON)
    create_date = Column(DateTime)
    gps_latitude = Column(Float)
    gps_longitude = Column(Float)
    gimbal_pitch_degree = Column(Float)
    flight_yaw_degree = Column(Float)
    flight_x_speed = Column(Float)
    flight_y_speed = Column(Float)
    relative_altitude = Column(Float)
    image_width = Column(Integer)
    image_length = Column(Integer)
    digital_zoom_ratio = Column(Float)
    unique_identifier = Column(String, unique=True)

    flight = relationship("Flight", back_populates="photos")



    def to_dict(self):
        return {
            'photo_id': self.photo_id,
            'flight_id': self.flight_id,
            'filename': self.filename,
            'photo_metadata': self.photo_metadata,
            'create_date': self.create_date,
            'gps_latitude': self.gps_latitude,
            'gps_longitude': self.gps_longitude,
            'gimbal_pitch_degree': self.gimbal_pitch_degree,
            'flight_yaw_degree': self.flight_yaw_degree,
            'flight_x_speed': self.flight_x_speed,
            'flight_y_speed': self.flight_y_speed,
            'relative_altitude': self.relative_altitude,
            'image_width': self.image_width,
            'image_length': self.image_length,
            'digital_zoom_ratio': self.digital_zoom_ratio,
            'unique_identifier': self.unique_identifier
        }
        
    def __repr__(self):
        return f"<Photo(photo_id={self.photo_id}, flight_id={self.flight_id}, filename='{self.filename}')>"


class AuditEntry(Base):
    __tablename__ = 'audit_trail'

    audit_id = Column(Integer, primary_key=True, autoincrement=True)
    inspection_id = Column(String, ForeignKey('inspections.inspection_id'))
    site_id = Column(String, ForeignKey('sites.site_id'))
    flight_id = Column(Integer, ForeignKey('flights.flight_id'))
    timestamp = Column(DateTime, default=lambda: datetime.now(pytz.timezone('US/Central')))
    user = Column(String)
    action = Column(String)
    details = Column(JSON)
    pilot_name = Column(String)
    flight_name = Column(String)
    result = Column(String)
    auditor_name = Column(String)
    
    
    def __repr__(self):
        return f"<AuditEntry(audit_id={self.audit_id}, inspection_id='{self.inspection_id}', action='{self.action}')>"

    @classmethod
    def create_flight_entry(cls, inspection_id, site_id, flight_id, pilot_name, flight_name, result, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now(pytz.timezone('US/Central'))
        return cls(
            inspection_id=inspection_id,
            site_id=site_id,
            flight_id=flight_id,
            user="user",
            action=f"Added Flight {flight_name}",
            pilot_name=pilot_name,
            flight_name=flight_name,
            result=result,
            timestamp=timestamp,
            details={
                "flight_name": flight_name,
                "result": result
            }
        )

    @classmethod
    def create_scope_check_entry(cls, inspection_id, site_id, required_flights, captured_flights, result, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now(pytz.timezone('US/Central'))
        return cls(
            inspection_id=inspection_id,
            site_id=site_id,
            user="System",
            action="Scope Check",
            result=result,
            timestamp=timestamp,
            details={
                "required_flights": required_flights,
                "captured_flights": captured_flights,
                "result": result
            }
        )

    @classmethod
    def create_inspection_check_entry(cls, inspection_id, site_id, result, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now(pytz.timezone('US/Central'))
        return cls(
            inspection_id=inspection_id,
            site_id=site_id,
            user="System",
            action="Inspection Check",
            result=result,
            timestamp=timestamp,
            details={
                "result": result
            }
        )

    @classmethod
    def create_override_request_entry(cls, inspection_id, site_id, flight_id, user, details, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now(pytz.timezone('US/Central'))
        return cls(
            inspection_id=inspection_id,
            site_id=site_id,
            flight_id=flight_id,
            user=user,
            action="Override Requested",
            details=details,
            timestamp=timestamp
        )

    @classmethod
    def create_override_approval_entry(cls, inspection_id, site_id, flight_id, user, details, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now(pytz.timezone('US/Central'))
        return cls(
            inspection_id=inspection_id,
            site_id=site_id,
            flight_id=flight_id,
            user=user,
            action="Override Approved",
            details=details,
            timestamp=timestamp
        )

    @classmethod
    def create_override_denial_entry(cls, inspection_id, site_id, flight_id, user, details, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now(pytz.timezone('US/Central'))
        return cls(
            inspection_id=inspection_id,
            site_id=site_id,
            flight_id=flight_id,
            user=user,
            action="Override Denied",
            details=details,
            timestamp=timestamp
        )

    @classmethod
    def create_photo_addition_entry(cls, inspection_id, site_id, flight_id, user, details, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now(pytz.timezone('US/Central'))
        return cls(
            inspection_id=inspection_id,
            site_id=site_id,
            flight_id=flight_id,
            user=user,
            action=f"Photos Added",
            details=details,
            timestamp=timestamp
    )


    @classmethod
    def create_note_addition_entry(cls, inspection_id, site_id, flight_id, user, details, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now(pytz.timezone('US/Central'))
        return cls(
            inspection_id=inspection_id,
            site_id=site_id,
            flight_id=flight_id,
            user=user,
            action="Note Added",
            details=details,
            timestamp=timestamp
        )


    @classmethod
    def create_scope_change_entry(cls, inspection_id, site_id, user, new_scope, details, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now(pytz.timezone('US/Central'))
        return cls(
            inspection_id=inspection_id,
            site_id=site_id,
            user=user,
            action="Scope Changed",
            details={
                "new_scope": new_scope,
                "user_details": details
            },
            timestamp=timestamp
        )


class FlightAnalysis(Base):
    __tablename__ = 'flight_analysis'

    flight_id = Column(Integer, ForeignKey('flights.flight_id'), primary_key=True)
    weakest_link_horizontal_overlap_status = Column(String, nullable=True)
    weakest_link_horizontal_overlap_value = Column(Float, nullable=True)
    orientation_status = Column(JSON, nullable=True)
    orientation_value = Column(JSON, nullable=True)
    radial_distance_check_status = Column(String, nullable=True)
    radial_distance_check_value = Column(JSON, nullable=True)
    average_radius_meters = Column(Float, nullable=True)
    total_rotation_status = Column(String, nullable=True)
    total_rotation_value = Column(Float, nullable=True)
    horizontal_spacing_status = Column(String, nullable=True)  
    horizontal_spacing_value = Column(JSON, nullable=True)  
    tower_coverage_check_status = Column(String, nullable=True)
    tower_coverage_check_value = Column(Float, nullable=True)
    vertical_spacing_status = Column(String, nullable=True)
    vertical_spacing_value = Column(JSON, nullable=True)
    weakest_link_vertical_overlap_status = Column(String, nullable=True)
    weakest_link_vertical_overlap_value = Column(Float, nullable=True)
    height_check_status = Column(JSON, nullable=True)
    height_check_value = Column(JSON, nullable=True)
    north_facing_check_status = Column(String, nullable=True)
    north_facing_check_value = Column(Float, nullable=True)
    compound_check_status = Column(String, nullable=True)
    compound_check_value = Column(Float, nullable=True)
    tower_flight_type_2_orbit_check_status = Column(String, nullable=True)
    tower_flight_type_2_orbit_check_value = Column(String, nullable=True)
    tower_flight_type_2_ascent_descent_count_status = Column(String, nullable=True)
    tower_flight_type_2_ascent_descent_count_value = Column(String, nullable=True)
    site_id = Column(String, ForeignKey('sites.site_id'))
    orbit_type = Column(String, nullable=True)
    average_radius_meters = Column(Float, nullable=True)

    
    
    
    
    def __repr__(self):
        return f"<FlightAnalysis(flight_id={self.flight_id}, compound_check='{self.compound_check}')>"

    def to_dict(self):
        """Converts the FlightAnalysis object to a dictionary, excluding null values and flight_id."""
        data = {}
        for column in self.__table__.columns:
            if column.name != 'flight_id':  # Skip the flight_id
                value = getattr(self, column.name)
                if value is not None:
                    if isinstance(value, OrbitType):
                        value = value.value  # Convert OrbitType to its string representation
                    data[column.name] = value
        return data


class Flight(Base):
    __tablename__ = 'flights'

    flight_id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String, ForeignKey('sites.site_id'))
    inspection_id = Column(String, ForeignKey('inspections.inspection_id'))
    flight_name = Column(String)
    required = Column(Boolean)
    pilot_name = Column(String)
    status = Column(SQLAlchemyEnum(FlightStatus), default=FlightStatus.FAILED)
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('US/Central')))
    is_current = Column(Boolean, default=True)
    is_captured = Column(Boolean, default=False)  
    photos = relationship("Photo", back_populates="flight", cascade="all, delete-orphan")
    analysis = relationship("FlightAnalysis", backref="flight", uselist=False, cascade="all, delete-orphan")
    audit_trail = relationship("AuditEntry", backref="flight", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Flight(flight_id={self.flight_id}, flight_name='{self.flight_name}', status={self.status})>"

# TODO: make sure to revisit this when pass override is implemented
class SiteInspection(Base):
    __tablename__ = 'sites'
    __table_args__ = (UniqueConstraint('site_id', 'inspection_id', name='uix_1'),)

    site_id = Column(String, primary_key=True)
    inspection_id = Column(String, ForeignKey('inspections.inspection_id'), primary_key=True)
    scope_requirement = Column(String)
    status = Column(SQLAlchemyEnum(InspectionStatus), default=InspectionStatus.IN_PROGRESS)
    initial_visit_time = Column(DateTime)
    retrip_reason = Column(String)
    flights = relationship("Flight", backref="site", cascade="all, delete-orphan")
    audit_trail = relationship("AuditEntry", backref="site", cascade="all, delete-orphan")
    scope_status = Column(SQLAlchemyEnum(InspectionStatus), nullable=True, default=InspectionStatus.IN_PROGRESS)
    site_status = Column(SQLAlchemyEnum(SiteStatus), nullable=True, default=SiteStatus.PENDING)
    #user_name = Column(String)
    #reviewer_name = Column(String)
    #pilot_name = Column(String)
    
    def __repr__(self):
        return f"<SiteInspection(site_id='{self.site_id}', inspection_id='{self.inspection_id}', status={self.status})>"

    def initiate_inspection(self):
        self.status = InspectionStatus.IN_PROGRESS
        
    def complete_inspection(self):
        self.status = InspectionStatus.COMPLETED


    def update_scope(self, new_scope):
        self.scope_requirement = new_scope

    @staticmethod
    def get_pilot_name(site_inspection):
        # Implement logic to get the pilot name
        # For example, return a default name if not set
        return site_inspection.pilot_name or "Unknown Pilot"

class Inspection(Base):
    __tablename__ = 'inspections'

    inspection_id = Column(String, primary_key=True)
    status = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('US/Central')))
    updated_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('US/Central')), onupdate=lambda: datetime.now(pytz.timezone('US/Central')))
    sites = relationship("SiteInspection", backref="inspection", cascade="all, delete-orphan")
    audit_trail = relationship("AuditEntry", backref="inspection", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Inspection(inspection_id='{self.inspection_id}', status='{self.status}')>"
