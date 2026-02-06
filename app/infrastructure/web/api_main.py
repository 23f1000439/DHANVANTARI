"""
Dhanvantr.ai FastAPI Application
Main entry point for the backend API.
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.infrastructure.persistence.models import init_db, get_db
from app.infrastructure.web.schemas import HealthResponse

# Import routers
from app.infrastructure.web.routes.clinical_routes import router as clinical_router
from app.infrastructure.web.routes.imaging_routes import router as imaging_router
from app.infrastructure.web.routes.admin_routes import router as admin_router
from app.infrastructure.web.routes.monitoring_routes import router as monitoring_router

# ============================================================
# App Configuration
# ============================================================
app = FastAPI(
    title="Dhanvantr.ai API",
    description="""
    Clinical AI Platform API
    
    ## Features
    - **Clinical**: Triage, Symptom Analysis, Prescription Validation, Lab Interpretation
    - **Imaging**: Radiology Analysis, Dermatology Assessment
    - **Admin/RCM**: Claims Analysis, ICD-11 Coding, Appeals
    - **Monitoring**: RPM Analysis, ED Triage, Alerts Dashboard
    
    ## AI Models
    - Gemini 3 Pro (Cloud) - Complex reasoning
    - MedGemma 4B (Local) - Clinical validation
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Startup Events
# ============================================================
@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup."""
    print("[API] Starting Dhanvantr.ai API...")
    
    # Initialize database
    init_db()
    print("[API] Database initialized.")
    
    # Initialize AI services (lazy loading)
    print("[API] AI services will be loaded on first request.")
    
    print("[API] ✅ Dhanvantr.ai API started successfully!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("[API] Shutting down Dhanvantr.ai API...")
    
    # Unload MedGemma if loaded
    try:
        from app.application.services.unified_ai_service import get_unified_ai_service
        service = get_unified_ai_service()
        service.unload_medgemma()
    except:
        pass
    
    print("[API] Shutdown complete.")


# ============================================================
# Health Check Endpoints
# ============================================================
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint."""
    return {
        "name": "Dhanvantr.ai API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    try:
        from app.application.services.unified_ai_service import get_unified_ai_service
        ai_service = get_unified_ai_service()
        ai_status = ai_service.get_status()
    except Exception as e:
        ai_status = {"gemini_available": False, "medgemma_available": False}
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        services={
            "database": True,
            "gemini": ai_status.get("gemini_available", False),
            "medgemma": ai_status.get("medgemma_available", False)
        }
    )


@app.get("/ai/status", tags=["Health"])
async def ai_status():
    """Get detailed AI service status."""
    try:
        from app.application.services.unified_ai_service import get_unified_ai_service
        service = get_unified_ai_service()
        return service.get_status()
    except Exception as e:
        return {"error": str(e)}


@app.post("/ai/medgemma/load", tags=["Health"])
async def load_medgemma():
    """Explicitly load MedGemma model into memory."""
    try:
        from app.application.services.unified_ai_service import get_unified_ai_service
        service = get_unified_ai_service()
        success = service.load_medgemma()
        return {"loaded": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Include Routers
# ============================================================
app.include_router(clinical_router, prefix="/api/v1")
app.include_router(imaging_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(monitoring_router, prefix="/api/v1")


# ============================================================
# Central Orchestrator Direct Access
# ============================================================
@app.post("/api/v1/orchestrator/route", tags=["Orchestrator"])
async def route_request(request_type: str, payload: dict):
    """
    Direct access to Central Orchestrator.
    Bypasses individual routes for advanced use cases.
    """
    try:
        from app.application.services.central_orchestrator import DhanvantariCentralOrchestrator
        
        orchestrator = DhanvantariCentralOrchestrator()
        result = orchestrator.route_request(request_type, payload)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Run with: uvicorn app.infrastructure.web.api_main:app --reload
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
