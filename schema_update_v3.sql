-- Create ICD-11 Mappings Table
CREATE TABLE IF NOT EXISTS icd11_mappings (
    id TEXT PRIMARY KEY,
    entity_text TEXT NOT NULL,
    icd11_code TEXT NOT NULL,
    icd11_title TEXT NOT NULL,
    parent_code TEXT, -- For hierarchical reasoning
    is_billable BOOLEAN DEFAULT 1,
    last_updated DATE DEFAULT CURRENT_DATE
);

-- Seed Data for ICD-11 Mappings
INSERT OR IGNORE INTO icd11_mappings (id, entity_text, icd11_code, icd11_title, parent_code, is_billable) VALUES 
('map_001', 'Type 2 Diabetes', '5A11', 'Type 2 diabetes mellitus', '5A1', 1),
('map_002', 'Hypertension', 'BA00', 'Essential hypertension', 'BA0', 1),
('map_003', 'Sprained Ankle', 'NC12', 'Strain or sprain of ankle', 'NC1', 1);

-- Update diagnosis_codes (Simulated via ALTER, allowing re-run safe logic)
-- SQLite doesn't support IF NOT EXISTS for ALTER COLUMN, so we use a try-catch block in python or ignore errors if running raw.
-- For this script, we assume columns might not exist. 
-- Note: SQLite ALTER TABLE ADD COLUMN is supported.

-- Adding justification
ALTER TABLE diagnosis_codes ADD COLUMN justification TEXT;
ALTER TABLE diagnosis_codes ADD COLUMN supporting_entities TEXT;
ALTER TABLE diagnosis_codes ADD COLUMN reasoning_trace TEXT;

-- Create Audit Logs Table if not exists (might already exist, but ensuring schema)
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT,
    action TEXT,
    entity_id TEXT,
    details TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
