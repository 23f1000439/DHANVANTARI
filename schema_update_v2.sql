-- Schema Update V2 for Hierarchical Agents

-- appointments (SchedulingAgent)
CREATE TABLE IF NOT EXISTS appointments (
    id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    doctor_id TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    status TEXT DEFAULT 'Scheduled', -- Scheduled, Completed, Cancelled
    reason TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES users(id)
);

-- payments (PaymentReconciliationAgent)
CREATE TABLE IF NOT EXISTS payments (
    id TEXT PRIMARY KEY,
    claim_id TEXT,
    patient_id TEXT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status TEXT DEFAULT 'Pending', -- Pending, Completed, Failed
    method TEXT,
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (claim_id) REFERENCES claims(id),
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

-- wearable_metrics (WearableAgent)
CREATE TABLE IF NOT EXISTS wearable_metrics (
    id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    device_type TEXT, -- Apple Watch, Fitbit
    metric_type TEXT, -- Heart Rate, Steps, SpO2
    value REAL,
    unit TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

-- audit_logs (GovernanceAgent)
CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_id TEXT, -- related record id
    details TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- protocols (ProtocolAgent)
CREATE TABLE IF NOT EXISTS protocols (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT,
    content TEXT NOT NULL, -- The actual guideline text/JSON
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    source TEXT -- e.g. AHA, CDC
);

-- Note: No seed data needed immediately, agents will populate.
