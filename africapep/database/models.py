from sqlalchemy import (
    Column, String, Boolean, SmallInteger, Date,
    ARRAY, Text, Float, Integer,
)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMPTZ, TSVECTOR, JSONB
from sqlalchemy.orm import DeclarativeBase
import uuid


class Base(DeclarativeBase):
    pass


class PepProfile(Base):
    __tablename__ = "pep_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    neo4j_id = Column(String(36), unique=True, index=True)
    full_name = Column(String(255), nullable=False)
    name_variants = Column(ARRAY(String), default=list)
    date_of_birth = Column(Date)
    nationality = Column(String(2))
    pep_tier = Column(SmallInteger)
    is_active_pep = Column(Boolean, default=True)
    current_positions = Column(JSONB, default=list)
    country = Column(String(2))
    updated_at = Column(TIMESTAMPTZ)
    search_vector = Column(TSVECTOR)


class ScreeningLog(Base):
    __tablename__ = "screening_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_name = Column(String(255), nullable=False)
    query_date = Column(TIMESTAMPTZ)
    match_count = Column(Integer, default=0)
    top_match_score = Column(Float, default=0.0)
    results = Column(JSONB, default=list)


class SourceRecord(Base):
    __tablename__ = "source_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    neo4j_id = Column(String(36))
    source_url = Column(Text)
    source_type = Column(String(50))
    country = Column(String(2))
    scraped_at = Column(TIMESTAMPTZ)
    raw_text = Column(Text)


class ChangeLog(Base):
    __tablename__ = "change_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(String(36), nullable=False, index=True)
    field_changed = Column(String(100), nullable=False)
    old_value = Column(Text)
    new_value = Column(Text)
    detected_at = Column(TIMESTAMPTZ)


class SchedulerLog(Base):
    __tablename__ = "scheduler_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_name = Column(String(100), nullable=False)
    started_at = Column(TIMESTAMPTZ)
    finished_at = Column(TIMESTAMPTZ)
    records_processed = Column(Integer, default=0)
    status = Column(String(20))
    error_message = Column(Text)
