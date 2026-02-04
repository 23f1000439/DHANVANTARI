-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL, -- In a real app, this would be hashed. For demo, plain text or simple hash.
    role TEXT CHECK(role IN ('patient', 'doctor', 'admin')) NOT NULL,
    full_name TEXT NOT NULL,
    profile_data TEXT, -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Patients Table
CREATE TABLE IF NOT EXISTS patients (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    dob DATE NOT NULL,
    gender TEXT,
    mrn TEXT UNIQUE NOT NULL,
    allergies TEXT, -- JSON Array
    conditions TEXT, -- JSON Array
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Encounters Table
CREATE TABLE IF NOT EXISTS encounters (
    id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    doctor_id TEXT NOT NULL, -- User ID of the doctor
    date DATETIME DEFAULT CURRENT_TIMESTAMP,
    type TEXT,
    clinical_notes TEXT,
    ai_summary TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES users(id)
);

-- Prescriptions Table
CREATE TABLE IF NOT EXISTS prescriptions (
    id TEXT PRIMARY KEY,
    encounter_id TEXT, -- Can be null if not linked to a specific encounter (e.g. uploaded)
    patient_id TEXT NOT NULL,
    doctor_id TEXT, -- Can be null if uploaded by patient without doctor link yet
    prescribed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'Active',
    image_path TEXT,
    is_ai_generated BOOLEAN DEFAULT 0,
    FOREIGN KEY (encounter_id) REFERENCES encounters(id),
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES users(id)
);

-- Prescription Items Table
CREATE TABLE IF NOT EXISTS prescription_items (
    id TEXT PRIMARY KEY,
    prescription_id TEXT NOT NULL,
    medication_name TEXT NOT NULL,
    dosage TEXT,
    frequency TEXT,
    duration TEXT,
    instructions TEXT,
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(id) ON DELETE CASCADE
);

-- Claims Table
CREATE TABLE IF NOT EXISTS claims (
    id TEXT PRIMARY KEY,
    encounter_id TEXT NOT NULL,
    status TEXT DEFAULT 'Draft',
    total_amount DECIMAL(10, 2),
    ai_analysis TEXT, -- JSON with denial probability
    FOREIGN KEY (encounter_id) REFERENCES encounters(id)
);

-- Diagnosis Codes Table
CREATE TABLE IF NOT EXISTS diagnosis_codes (
    id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL,
    code TEXT NOT NULL,
    description TEXT,
    confidence_score REAL,
    FOREIGN KEY (claim_id) REFERENCES claims(id) ON DELETE CASCADE
);

-- Conversations Table
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    context_type TEXT,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    title TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Messages Table
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT CHECK(role IN ('user', 'model', 'system')) NOT NULL,
    content TEXT NOT NULL,
    thought_chain TEXT, -- JSON
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- SEED DATA
-- 1. Users
INSERT OR IGNORE INTO users (id, email, password_hash, role, full_name, profile_data) VALUES
('u_patient_1', 'rajesh@example.com', 'pass', 'patient', 'Rajesh Kumar', '{"language": "en"}'),
('u_doctor_1', 'priya@hospital.com', 'pass', 'doctor', 'Dr. Priya Sharma', '{"specialty": "Cardiology"}'),
('u_admin_1', 'sarah@admin.com', 'pass', 'admin', 'Sarah Admin', '{"department": "Billing"}');

-- 2. Patients
INSERT OR IGNORE INTO patients (id, user_id, dob, gender, mrn, allergies, conditions) VALUES
('p_1', 'u_patient_1', '1968-05-15', 'Male', 'MRN-2026-001', '["Penicillin"]', '["Type 2 Diabetes", "Hypertension", "Hyperlipidemia"]');

-- 3. Encounters (Initial history)
INSERT OR IGNORE INTO encounters (id, patient_id, doctor_id, date, type, clinical_notes) VALUES
('e_1', 'p_1', 'u_doctor_1', '2025-12-10 10:00:00', 'In-Person', 'Patient presents with elevated blood glucose levels. Reporting fatigue and increased thirst. BP 145/90. Current Metformin dosage may need adjustment.');

-- 4. Prescriptions (Current meds)
INSERT OR IGNORE INTO prescriptions (id, patient_id, doctor_id, prescribed_at, status, is_ai_generated) VALUES
('rx_1', 'p_1', 'u_doctor_1', '2025-12-10 10:30:00', 'Active', 0);

INSERT OR IGNORE INTO prescription_items (id, prescription_id, medication_name, dosage, frequency, duration, instructions) VALUES
('pi_1', 'rx_1', 'Metformin', '500mg', 'BID', '30 days', 'Take with meals'),
('pi_2', 'rx_1', 'Lisinopril', '10mg', 'QD', '30 days', 'Take in the morning');
