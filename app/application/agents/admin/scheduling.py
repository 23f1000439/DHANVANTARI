from ...infrastructure.ai.gemini import GeminiAgent
from ...infrastructure.persistence.database import get_db_connection

class SchedulingAgent(GeminiAgent):
    def __init__(self):
        super().__init__("SchedulingAgent")
        
    def book_appointment(self, patient_id, doctor_id, time, reason):
        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO appointments (id, patient_id, doctor_id, start_time, end_time, reason) VALUES (?, ?, ?, ?, ?, ?)",
                (f"appt_{time}", patient_id, doctor_id, time, time, reason)
            )
            conn.commit()
            return "Appointment Booked Successfully."
        except Exception as e:
            return f"Booking Failed: {e}"
        finally:
            conn.close()

    def generate_response(self, prompt, conversation_id, context=None):
        # In full implementation, we would extract tools here
        instruction = "Extract appointment details (Time, Doctor) from input."
        full_prompt = f"{instruction}\n\nInput: {prompt}"
        return super().generate_response(full_prompt, conversation_id, context)
