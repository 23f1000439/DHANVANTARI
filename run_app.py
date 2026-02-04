import uvicorn
import os

if __name__ == "__main__":
    # Ensure PYTHONPATH includes the current directory
    # Run with: python3 run_app.py
    uvicorn.run("app.infrastructure.web.main:app", host="127.0.0.1", port=8000, reload=True)
