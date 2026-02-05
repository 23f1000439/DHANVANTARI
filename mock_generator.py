import sqlite3
import json
import random
import os
from datetime import datetime, timedelta

class MockDataGenerator:
    def __init__(self, db_path="healthcare.db"):
        self.db_path = db_path
        self.specialties = ["Cardiology", "Orthopedics", "General Medicine"]
        self.status_options = ["Draft", "Submitted", "Denied", "Paid"]

    def generate_scenario_data(self):
        print(f"Seeding mock data into {self.db_path}...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Ensure tables exist (basic check, relying on schema.sql having been run)
        # 1. Create a "Documentation Gap" Scenario (High Risk)
        encounter_id = "enc_gap_001"
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO encounters (id, patient_id, doctor_id, clinical_notes, type)
                VALUES (?, 'p_1', 'u_doctor_1', 'Patient seen for follow-up. Doing okay. Continue meds.', 'Outpatient')
            """, (encounter_id,))

            cursor.execute("""
                INSERT OR IGNORE INTO claims (id, encounter_id, status, total_amount, ai_analysis)
                VALUES ('claim_gap_001', ?, 'Draft', 4500.00, NULL)
            """, (encounter_id,))
        except sqlite3.OperationalError as e:
            print(f"Error seeding Gap Scenario: {e}")

        # 2. Create a "Coding Mismatch" Scenario (High Risk)
        # Billed for Chest X-Ray (Conceptually) but diagnosis is Sprained Ankle
        try:
            # Needing a claim first for the foreign key
            mismatch_claim_id = "claim_mismatch_001"
            mismatch_enc_id = "enc_mismatch_001"
            
            cursor.execute("""
                INSERT OR IGNORE INTO encounters (id, patient_id, doctor_id, clinical_notes, type)
                VALUES (?, 'p_1', 'u_doctor_1', 'Patient complains of ankle pain after twisting it. Swelling present.', 'Urgent Care')
            """, (mismatch_enc_id,))

            cursor.execute("""
                INSERT OR IGNORE INTO claims (id, encounter_id, status, total_amount, ai_analysis)
                VALUES (?, ?, 'Draft', 1200.00, NULL)
            """, (mismatch_claim_id, mismatch_enc_id))

            cursor.execute("""
                INSERT OR IGNORE INTO diagnosis_codes (id, claim_id, code, description, confidence_score)
                VALUES ('diag_001', ?, 'NA01', 'Sprained Ankle', 0.95)
            """, (mismatch_claim_id,))
        except sqlite3.OperationalError as e:
             print(f"Error seeding Mismatch Scenario: {e}")

        # 3. Add Wearable Data for Gemini 3 context
        # Note: 'wearable_metrics' table wasn't in the original schema.sql view I saw earlier.
        # I will check if it exists or CREATE it if not, to adhere to the request.
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wearable_metrics (
                    id TEXT PRIMARY KEY,
                    patient_id TEXT NOT NULL,
                    metric_type TEXT,
                    value REAL,
                    unit TEXT,
                    timestamp DATETIME
                );
            """)
            
            cursor.execute("""
                INSERT OR IGNORE INTO wearable_metrics (id, patient_id, metric_type, value, unit, timestamp)
                VALUES ('w_001', 'p_1', 'Heart Rate', 115.0, 'bpm', ?)
            """, (datetime.now().isoformat(),))
        except sqlite3.OperationalError as e:
            print(f"Error seeding Wearable Data: {e}")

        conn.commit()
        conn.close()
        print("✅ Mock billing scenarios seeded into healthcare.db")

if __name__ == "__main__":
    gen = MockDataGenerator()
    gen.generate_scenario_data()
