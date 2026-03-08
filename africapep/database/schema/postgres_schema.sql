CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS pep_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    neo4j_id VARCHAR(36) UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    name_variants TEXT[] DEFAULT '{}',
    date_of_birth DATE,
    nationality CHAR(2),
    pep_tier SMALLINT CHECK (pep_tier IN (1, 2, 3)),
    is_active_pep BOOLEAN DEFAULT TRUE,
    current_positions JSONB DEFAULT '[]',
    country VARCHAR(2),
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    search_vector TSVECTOR
);

CREATE TABLE IF NOT EXISTS screening_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_name VARCHAR(255) NOT NULL,
    query_date TIMESTAMPTZ DEFAULT NOW(),
    match_count INT DEFAULT 0,
    top_match_score FLOAT DEFAULT 0.0,
    results JSONB DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS source_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    neo4j_id VARCHAR(36),
    source_url TEXT,
    source_type VARCHAR(50),
    country CHAR(2),
    scraped_at TIMESTAMPTZ,
    raw_text TEXT
);

CREATE TABLE IF NOT EXISTS change_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id VARCHAR(36) NOT NULL,
    field_changed VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    detected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scheduler_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_name VARCHAR(100) NOT NULL,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    records_processed INT DEFAULT 0,
    status VARCHAR(20),
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_pep_search ON pep_profiles USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_pep_variants ON pep_profiles USING GIN(name_variants);
CREATE INDEX IF NOT EXISTS idx_pep_trgm ON pep_profiles USING GIN(full_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_pep_country ON pep_profiles(country);
CREATE INDEX IF NOT EXISTS idx_pep_tier ON pep_profiles(pep_tier);
CREATE INDEX IF NOT EXISTS idx_change_entity ON change_log(entity_id);
CREATE INDEX IF NOT EXISTS idx_change_detected_at ON change_log(detected_at);
CREATE INDEX IF NOT EXISTS idx_screening_date ON screening_log(query_date);
CREATE INDEX IF NOT EXISTS idx_source_neo4j_id ON source_records(neo4j_id);
CREATE INDEX IF NOT EXISTS idx_source_country ON source_records(country);
CREATE INDEX IF NOT EXISTS idx_pep_nationality ON pep_profiles(nationality);

CREATE OR REPLACE FUNCTION update_search_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english',
        COALESCE(NEW.full_name, '') || ' ' ||
        COALESCE(array_to_string(NEW.name_variants, ' '), ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS pep_search_vector_update ON pep_profiles;
CREATE TRIGGER pep_search_vector_update
    BEFORE INSERT OR UPDATE ON pep_profiles
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();
