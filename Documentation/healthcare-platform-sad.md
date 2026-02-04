# Software Architecture Document (SAD)
## Healthcare AI Orchestration Platform

**Version:** 1.0  
**Date:** January 29, 2026  
**Status:** Draft

---

## 1. INTRODUCTION

### 1.1 Purpose
This Software Architecture Document describes the comprehensive technical architecture for a multi-persona healthcare AI platform built on Google Gemini 3 API and Agentic Development Kit (ADK). The architecture supports hospital administrators, doctors, and patients through a hierarchical multi-agent orchestration system.

### 1.2 Scope
This document covers:
- System decomposition into components and agents
- Interaction patterns between system elements
- Deployment topology and infrastructure
- Data architecture and flow
- Technology stack and integration points
- Quality attribute implementations (performance, security, scalability)

### 1.3 Intended Audience
- Solution architects and technical leads
- Backend and frontend development teams
- DevOps and infrastructure engineers
- Security and compliance officers
- Integration partners (EHR vendors, payers)

### 1.4 Architectural Representation
This document follows the **4+1 View Model** for software architecture:
1. **Use Case View:** System functionality from user perspective
2. **Logical View:** System decomposition into components
3. **Process View:** Runtime behavior, concurrency, communication
4. **Deployment View:** Physical infrastructure and topology
5. **Implementation View:** Code organization and build structure

### 1.5 References
- Software Requirements Specification (SRS) v1.0
- Google Agentic Development Kit (ADK) Documentation
- Gemini 3 API Technical Specifications
- Vertex AI Agent Engine Architecture Guide
- HIPAA Security Rule Technical Safeguards

---

## 2. ARCHITECTURAL GOALS AND CONSTRAINTS

### 2.1 Architectural Drivers

#### 2.1.1 Business Goals
1. **Multi-Persona Support:** Serve three distinct user types with specialized AI agents
2. **Revenue Impact:** Demonstrate 10-20% revenue improvement within 12 months
3. **Clinical Accuracy:** Achieve 95%+ clinician satisfaction with AI recommendations
4. **Patient Engagement:** 85%+ medication adherence rates through AI guidance
5. **Operational Efficiency:** Reduce manual workload by 30-50% in administrative functions

#### 2.1.2 Quality Attributes (Priority Order)

**1. Security & Compliance (Critical)**
- HIPAA compliance with signed BAA through Vertex AI
- PHI encryption at rest (AES-256) and in transit (TLS 1.3)
- Role-based access control with audit logging
- 7-year audit trail retention

**2. Reliability (Critical)**
- 99.9% uptime SLA (8.76 hours downtime/year)
- Graceful degradation when Gemini API unavailable
- Data integrity with ACID transactions for critical operations
- RPO < 1 hour, RTO < 4 hours

**3. Performance (High)**
- Doctor queries: < 3 seconds (p95)
- Patient conversations: < 1 second (p95)
- Drug interaction checks: < 1 second (p99)
- Support 10,000 concurrent users per instance

**4. Scalability (High)**
- Horizontal scaling across multiple regions
- Handle 100,000 patient conversations/day
- Process 50,000 claims/day
- Cost-efficient token utilization (< $0.10/patient conversation)

**5. Maintainability (Medium)**
- Modular agent architecture for independent updates
- Comprehensive observability (logs, metrics, traces)
- CI/CD with automated testing and blue-green deployment

### 2.2 Architectural Constraints

#### 2.2.1 Technical Constraints
1. **Gemini 3 API Limitations:**
   - 1M token context window (hard limit)
   - Temperature must remain at 1.0 (architectural requirement)
   - Thought signatures mandatory for function calling
   - Rate limits: 150-300 RPM (Tier 1), scaling to 2,000+ RPM (Tier 3)

2. **ADK Framework Requirements:**
   - Python 3.10+ for agent implementation
   - Pydantic for configuration management
   - SessionService for state persistence
   - FunctionTool pattern for external integrations

3. **Google Cloud Platform:**
   - Vertex AI required for HIPAA compliance (not Consumer Gemini API)
   - Regional deployment: us-central1 (US), asia-south1 (India)
   - Identity-Aware Proxy (IAP) for access control

#### 2.2.2 Regulatory Constraints
1. **HIPAA:**
   - BAA signed with Google Cloud
   - Regulated-data flag enabled on all Vertex AI requests
   - Web search grounding disabled when processing PHI
   - Minimum necessary standard enforced via RBAC

2. **HITRUST CSF:**
   - Annual third-party certification required
   - Control implementation documentation
   - Risk assessment and remediation

3. **Medical Device Regulations:**
   - System explicitly NOT FDA-cleared
   - Disclaimers required on all clinical outputs
   - No autonomous clinical decisions without human oversight

#### 2.2.3 Organizational Constraints
1. **Budget:** $530K Year 1 including development and operational costs
2. **Timeline:** MVP in 6 months, full deployment in 12 months
3. **Team:** 5 backend engineers, 3 frontend engineers, 1 DevOps, 1 architect
4. **Existing Systems:** Must integrate with diverse EHR systems (Epic, Cerner, custom)

### 2.3 Architectural Principles

1. **Agent-First Design:** Encapsulate all AI capabilities within well-defined agents
2. **Separation of Concerns:** Distinct layers for presentation, orchestration, integration, data
3. **API-First:** All inter-component communication via documented REST/gRPC APIs
4. **Secure by Default:** PHI protection at every layer, deny-by-default access control
5. **Cloud-Native:** Leverage managed services (Vertex AI, Firestore, Cloud Run)
6. **Observable Systems:** Comprehensive logging, metrics, and distributed tracing
7. **Fail-Safe Operations:** Graceful degradation, circuit breakers, human escalation paths

---

## 3. USE CASE VIEW

### 3.1 Critical Use Cases

#### UC-1: Doctor Performs Point-of-Care Clinical Search
**Actors:** Doctor, ClinicalAgent, EHRSearchAgent, Gemini 3 Pro

**Flow:**
1. Doctor opens mobile app during patient rounds
2. Enters voice/text query: "Post-op antibiotic for pediatric appendectomy"
3. ClinicalAgent receives query via API Gateway
4. Agent retrieves patient context via EHRSearchAgent (allergies, current meds)
5. Agent searches embedded hospital protocols (vector DB with context caching)
6. Gemini 3 Pro (`thinking_level: high`) synthesizes response with citations
7. Response includes: recommended antibiotics, dosing, evidence grading
8. Doctor reviews and selects antibiotic
9. Drug interaction check performed (function call to Micromedex API)
10. Prescription generated and sent to patient app

**Quality Attributes:**
- Performance: < 3 seconds end-to-end (p95)
- Reliability: Fallback to cached protocols if Gemini unavailable
- Security: Patient context encrypted in transit, audit logged

#### UC-2: Patient Medication Adherence Tracking
**Actors:** Patient, PatientAgent, Gemini 3 Flash (OCR), NotificationService

**Flow:**
1. Patient receives paper prescription at clinic
2. Opens patient app → "Scan Prescription"
3. Camera captures prescription image → uploaded to Cloud Storage
4. Gemini 3 Flash multimodal processes image (OCR)
5. Extracted data: medication names, dosages, frequencies
6. Patient confirms/corrects extracted data
7. PatientAgent generates personalized schedule (meal times, sleep patterns)
8. Push notifications scheduled via Firebase Cloud Messaging
9. Patient marks medications taken → adherence recorded
10. Weekly summary generated → shared with prescribing doctor

**Quality Attributes:**
- Usability: 95% OCR accuracy, < 30 seconds to complete scan
- Reliability: Offline capability for marking medications taken
- Security: Prescription images encrypted, auto-deleted after 30 days

#### UC-3: Administrator Analyzes Revenue Cycle
**Actors:** Administrator, BillingAgent, Gemini 3 Pro, NHCX API

**Flow:**
1. Admin opens dashboard → "Revenue Cycle Analytics"
2. BillingAgent retrieves billing data from past 90 days
3. Gemini 3 Pro analyzes denial patterns, coding errors, payment delays
4. Agent identifies: 15% denial rate on orthopedic procedures due to documentation gaps
5. Root cause analysis performed (function calling to claims database)
6. Recommendations generated: "Add pre-submission documentation checklist"
7. Admin implements recommendation → claims template updated
8. Ongoing monitoring shows denial rate drops to 8% over 30 days

**Quality Attributes:**
- Performance: Dashboard loads < 2 seconds with cached analytics
- Scalability: Analyze 50,000 claims/day across multiple facilities
- Security: Financial data segregated by organization, admin-only access

### 3.2 Actor-System Interactions

```
┌─────────────┐         ┌──────────────────────────────────────┐
│   Doctor    │────────▶│         Web/Mobile App               │
└─────────────┘         │  (React PWA, React Native)           │
                        └──────────────┬───────────────────────┘
                                       │ HTTPS/TLS 1.3
┌─────────────┐         ┌──────────────▼───────────────────────┐
│   Patient   │────────▶│       API Gateway (Cloud Endpoints)  │
└─────────────┘         │  Authentication, Rate Limiting       │
                        └──────────────┬───────────────────────┘
                                       │
┌─────────────┐         ┌──────────────▼───────────────────────┐
│   Admin     │────────▶│    Orchestration Layer (Cloud Run)   │
└─────────────┘         │  RootOrchestrator, Agent Dispatching │
                        └──────────────┬───────────────────────┘
                                       │
                        ┌──────────────▼───────────────────────┐
                        │      Agent Layer (ADK Framework)     │
                        │  ClinicalAgent, PatientAgent,        │
                        │  BillingAgent, Tool Agents           │
                        └──────────────┬───────────────────────┘
                                       │
                        ┌──────────────▼───────────────────────┐
                        │    Gemini 3 API (Vertex AI)          │
                        │  Pro: Clinical, Admin Analytics      │
                        │  Flash: Patient Conversations        │
                        └──────────────────────────────────────┘
```

---

## 4. LOGICAL VIEW

### 4.1 High-Level Architecture

The system follows a **layered architecture** with **hierarchical agent orchestration**:

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Doctor Portal│  │ Patient Portal│  │ Admin Portal │              │
│  │ (React PWA)  │  │ (React Native)│  │ (React PWA)  │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                               │ REST/GraphQL
┌─────────────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                               │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ Cloud Endpoints: Auth, Rate Limiting, Request Validation   │     │
│  └────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATION LAYER (Cloud Run)                    │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │              RootOrchestratorAgent (ADK)                   │     │
│  │  - Request routing by user role and task type              │     │
│  │  - Session management (Vertex AI Sessions)                 │     │
│  │  - Agent-to-Agent coordination                             │     │
│  └────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────────┐
│                        AGENT LAYER (ADK)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ClinicalAgent │  │ PatientAgent │  │ BillingAgent │              │
│  │Gemini 3 Pro  │  │Gemini 3 Flash│  │Gemini 3 Pro  │              │
│  │thinking: high│  │thinking: low │  │thinking: high│              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                  │                       │
│  ┌──────▼──────────────────▼──────────────────▼──────┐              │
│  │              Tool Agents (FunctionTool)           │              │
│  │  EHRSearchAgent, DrugDBAgent, SchedulingAgent,   │              │
│  │  ImagingAgent, ClaimsAgent, NotificationAgent    │              │
│  └───────────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────────┐
│                    INTEGRATION LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ EHR Connector│  │ NHCX Connector│ │ Wearable APIs│              │
│  │ (HL7 FHIR)   │  │ (Claims API)  │  │(Apple, Google│              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Firestore   │  │  Cloud SQL   │  │ Cloud Storage│              │
│  │ (Documents)  │  │ (Relational) │  │  (Blobs)     │              │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │              │
│  │ │Patients  │ │  │ │Users     │ │  │ │Prescriptions│              │
│  │ │Messages  │ │  │ │Audit Logs│ │  │ │Images    │ │              │
│  │ │Adherence │ │  │ │Orgs      │ │  │ │Documents │ │              │
│  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Vector DB    │  │ Redis Cache  │  │ Pub/Sub      │              │
│  │(Vertex AI VDB│  │ (Sessions)   │  │(Async Events)│              │
│  │ Embeddings)  │  │              │  │              │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Component Descriptions

#### 4.2.1 Presentation Layer

**Doctor Portal (React PWA)**
- **Responsibility:** Mobile-first clinical interface for point-of-care use
- **Technology:** React 18, TypeScript, Tailwind CSS, PWA with service workers
- **Key Features:**
  - Voice input via Web Speech API
  - Offline mode for cached protocols
  - Push notifications for critical alerts
- **Communication:** REST API to API Gateway, WebSocket for Live API

**Patient Portal (React Native)**
- **Responsibility:** Native mobile app for iOS/Android
- **Technology:** React Native 0.73, Expo, TypeScript
- **Key Features:**
  - Camera integration for prescription scanning
  - Push notifications via Firebase Cloud Messaging
  - Wearable data sync (Apple HealthKit, Google Fit)
- **Communication:** REST API to API Gateway, background sync

**Admin Portal (React PWA)**
- **Responsibility:** Desktop/tablet dashboard for operations and analytics
- **Technology:** React 18, TypeScript, Recharts for visualization
- **Key Features:**
  - Real-time dashboards with WebSocket updates
  - CSV/PDF export for compliance reports
  - Multi-organization view for health systems
- **Communication:** GraphQL API for complex queries, REST for mutations

#### 4.2.2 API Gateway Layer

**Cloud Endpoints**
- **Responsibility:** Single entry point for all client requests
- **Technology:** Google Cloud Endpoints with OpenAPI 3.0 specification
- **Functions:**
  - **Authentication:** JWT validation, OAuth 2.0 token verification
  - **Authorization:** RBAC enforcement (admin, doctor, patient roles)
  - **Rate Limiting:** Per-user quotas (100 req/min patient, 500 req/min doctor)
  - **Request Validation:** Schema validation against OpenAPI spec
  - **TLS Termination:** Certificate management via Google-managed certs
- **Monitoring:** Cloud Monitoring for latency, error rates, quota usage

#### 4.2.3 Orchestration Layer

**RootOrchestratorAgent**
- **Responsibility:** Top-level agent coordinating all sub-agents
- **Technology:** ADK LlmAgent with Gemini 3 Flash (routing speed critical)
- **Functions:**
  - **Request Classification:** Determine appropriate sub-agent (clinical vs. billing vs. patient)
  - **Session Management:** Create/retrieve Vertex AI Agent Engine Sessions
  - **Context Assembly:** Gather user context, permissions, organization settings
  - **Agent Dispatching:** Route to specialized agents with context handoff
  - **Response Aggregation:** Combine multi-agent responses when needed
- **State Management:** 
  - Session data stored in Vertex AI Sessions (55-day retention)
  - Thought signatures preserved across agent handoffs
  - Memory Bank for long-term patient context

**Implementation Pattern:**
```python
from google import genai
from google.genai import types
from adk import Agent, LlmAgent, SessionService

class RootOrchestratorAgent(LlmAgent):
    def __init__(self, config: OrchestratorConfig):
        self.clinical_agent = ClinicalAgent()
        self.patient_agent = PatientAgent()
        self.billing_agent = BillingAgent()
        self.session_service = SessionService()
        
        super().__init__(
            model="gemini-3-flash-preview",
            system_instruction=self._get_system_instruction(),
            tools=[
                self._route_to_clinical,
                self._route_to_patient,
                self._route_to_billing
            ]
        )
    
    async def process(self, request: Request) -> Response:
        # Retrieve or create session
        session = await self.session_service.get_or_create(
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        # Classify request and route
        classification = await self._classify_request(request.query)
        
        if classification.agent_type == "clinical":
            response = await self.clinical_agent.process(request, session)
        elif classification.agent_type == "patient":
            response = await self.patient_agent.process(request, session)
        elif classification.agent_type == "billing":
            response = await self.billing_agent.process(request, session)
        
        # Update session with response
        await self.session_service.update(session, response)
        
        return response
```

#### 4.2.4 Agent Layer

**ClinicalAgent**
- **Model:** Gemini 3 Pro with `thinking_level: high`
- **Purpose:** Clinical decision support for doctors
- **Tools:**
  - EHRSearchAgent: Patient data retrieval via FHIR
  - DrugDBAgent: Medication information, interactions (Micromedex)
  - ProtocolSearchAgent: Hospital guideline lookup (vector DB)
  - ImagingAgent: DICOM analysis (preliminary findings)
- **Configuration:**
  - Context caching enabled for clinical guidelines (90% hit rate target)
  - Structured output for prescription generation
  - Grounding disabled (uses internal protocols only)
- **Safety:**
  - System instruction emphasizes uncertainty quantification
  - Hard blocks on autonomous diagnosis
  - Mandatory human verification flags

**PatientAgent**
- **Model:** Gemini 3 Flash with `thinking_level: low`
- **Purpose:** Conversational health assistant for patients
- **Tools:**
  - SymptomTriageAgent: Severity assessment, escalation logic
  - MedicationAgent: Adherence tracking, reminder scheduling
  - WearableAgent: Data sync, anomaly detection
  - EscalationAgent: Connect to on-call clinician
- **Configuration:**
  - Multilingual support (12 languages via system instructions)
  - Google Search grounding enabled (health education only)
  - Live API integration for voice interactions
- **Safety:**
  - Strict guardrails against medical diagnosis
  - Automatic escalation triggers (chest pain, severe allergic reaction)
  - Content filtering for harmful medical advice

**BillingAgent**
- **Model:** Gemini 3 Pro with `thinking_level: high`
- **Purpose:** Revenue cycle optimization for administrators
- **Tools:**
  - CodingAgent: ICD-11 code suggestion from clinical notes
  - ClaimsAgent: NHCX submission, status tracking
  - AnalyticsAgent: Denial pattern analysis, revenue insights
  - ValidationAgent: Pre-submission documentation checks
- **Configuration:**
  - Structured output for claims (JSON schema validation)
  - Function calling to billing system APIs
  - Context caching for coding guidelines
- **Compliance:**
  - Audit logging for all coding decisions
  - Confidence thresholds (85% for auto-coding)
  - Human review queue for low-confidence cases

**Tool Agents (FunctionTool Pattern)**

All tool agents follow the same pattern:
```python
from adk import FunctionTool

@FunctionTool
async def search_ehr(patient_id: str, resource_type: str) -> dict:
    """Retrieves patient data from EHR via FHIR API.
    
    Args:
        patient_id: Patient MRN or FHIR ID
        resource_type: FHIR resource (Patient, Observation, MedicationRequest)
    
    Returns:
        FHIR bundle with requested resources
    """
    ehr_connector = EHRConnector()
    response = await ehr_connector.get(
        endpoint=f"Patient/{patient_id}/{resource_type}",
        headers={"Authorization": f"Bearer {get_ehr_token()}"}
    )
    return response.json()
```

**EHRSearchAgent:**
- Implements HL7 FHIR R4 client
- OAuth 2.0 + SMART on FHIR authentication
- Caching layer (Redis) for frequently accessed records
- Retry logic with exponential backoff

**DrugDBAgent:**
- Integration with Micromedex API (drug interactions)
- RxNorm for medication normalization
- Local cache for common drug pairs (< 100ms response)

**SchedulingAgent:**
- Integration with hospital scheduling system
- Appointment availability checking
- Confirmation via SMS/email

**NotificationAgent:**
- Firebase Cloud Messaging for push notifications
- SMS via Twilio (medication reminders, appointment alerts)
- Email via SendGrid (reports, compliance notifications)

#### 4.2.5 Integration Layer

**EHR Connector**
- **Protocol:** HL7 FHIR R4 (preferred), HL7 v2.x (legacy fallback)
- **Authentication:** OAuth 2.0 with SMART on FHIR
- **Supported Vendors:** Epic (MyChart API), Cerner (HealtheIntent), Allscripts, Custom
- **Operations:** Read-only access (GET requests)
- **Error Handling:** Circuit breaker pattern (open circuit after 5 consecutive failures)

**NHCX Connector**
- **Protocol:** REST API with JSON payloads
- **Functions:** Claim submission, status check, payment posting
- **Authentication:** API key + HMAC signature
- **Retry Logic:** Exponential backoff (1s, 2s, 4s, 8s, 16s max)
- **Idempotency:** Request IDs to prevent duplicate submissions

**Wearable APIs**
- **Apple HealthKit:** Native iOS integration, HealthKit framework
- **Google Fit:** REST API, OAuth 2.0 scopes (fitness.activity.read, fitness.heart_rate.read)
- **Sync Frequency:** Background sync every 4 hours, real-time for critical values (heart rate > 120 bpm)
- **Data Normalization:** Convert to FHIR Observation resources for consistent storage

#### 4.2.6 Data Layer

**Firestore (Document Database)**
- **Use Cases:** Semi-structured data with flexible schema
- **Collections:**
  - `conversations`: Message history, thought signatures
  - `patients`: Demographics, preferences, adherence logs
  - `medications`: Active prescriptions, schedules
  - `wearable_data`: Time-series health metrics
- **Indexing:** Composite indexes on (user_id, created_at) for queries
- **Security Rules:** Firestore Security Rules enforce RBAC at database level

**Cloud SQL (PostgreSQL)**
- **Use Cases:** Relational data requiring ACID transactions
- **Tables:**
  - `users`: Authentication, roles, organization mapping
  - `audit_logs`: All PHI access, 7-year retention
  - `organizations`: Hospital/clinic metadata, subscription tiers
  - `appointments`: Scheduling data with foreign keys
- **High Availability:** Regional replication, automatic failover
- **Backups:** Hourly incremental, daily full backup to Cloud Storage

**Cloud Storage**
- **Buckets:**
  - `prescription-images`: Encrypted prescription scans (auto-delete after 30 days)
  - `clinical-documents`: Lab reports, imaging studies (7-year retention)
  - `backups`: Database backups (Archive storage class after 90 days)
- **Encryption:** Customer-managed encryption keys (CMEK) via Cloud KMS
- **Access Control:** Signed URLs for temporary access, IAM for permanent

**Vertex AI Vector Database**
- **Use Cases:** Semantic search over clinical protocols, medical literature
- **Data:** Hospital-specific guidelines, standard protocols (AHA, CDC)
- **Embeddings:** Gemini text-embedding-004 model (768 dimensions)
- **Index Type:** ScaNN for fast approximate nearest neighbor search

**Redis Cache**
- **Use Cases:** Session data, frequently accessed EHR records, rate limiting counters
- **Deployment:** Cloud Memorystore with 4GB instance
- **TTL:** 15 minutes for session data, 1 hour for EHR data
- **Eviction Policy:** LRU (Least Recently Used)

**Pub/Sub**
- **Use Cases:** Asynchronous event processing, decoupling
- **Topics:**
  - `medication-reminders`: Schedule push notifications
  - `wearable-alerts`: Critical value notifications
  - `audit-events`: Real-time audit log processing
- **Subscriptions:** Push subscriptions to Cloud Run services

---

## 5. PROCESS VIEW

### 5.1 Concurrency and Threading

**API Gateway (Cloud Endpoints)**
- **Concurrency Model:** Event-driven, handles 1,000+ concurrent connections per instance
- **Auto-scaling:** Scale to zero when idle, max 100 instances

**Orchestration Layer (Cloud Run)**
- **Concurrency:** 10 concurrent requests per container instance
- **Instances:** Min 2 (for redundancy), max 50 (cost control)
- **CPU:** 2 vCPU per instance
- **Memory:** 4 GB per instance

**Agent Processing**
- **Pattern:** Asynchronous I/O using Python asyncio
- **LLM Calls:** Non-blocking async calls to Gemini API
- **Function Calling:** Parallel execution of independent function calls
- **Timeout:** 30 seconds per agent processing request

### 5.2 Inter-Process Communication

**Client ↔ API Gateway**
- **Protocol:** HTTPS with REST or GraphQL
- **Format:** JSON
- **Authentication:** JWT Bearer tokens (15-minute expiry, refresh tokens)

**API Gateway ↔ Orchestration Layer**
- **Protocol:** gRPC for low latency
- **Format:** Protocol Buffers
- **Load Balancing:** Google Cloud Load Balancer (round-robin)

**Orchestration ↔ Agents**
- **Pattern:** In-process function calls (agents deployed as libraries, not microservices)
- **State Sharing:** Via SessionService (abstracts Vertex AI Sessions API)

**Agents ↔ External Systems**
- **EHR:** REST API with OAuth 2.0, JSON
- **Gemini API:** REST API with API key auth, JSON
- **Tool Agents:** Function calls with retry logic

**Asynchronous Events**
- **Pub/Sub Topics:** Medication reminders, wearable alerts, audit events
- **Subscribers:** Cloud Run services (push subscriptions)
- **Dead Letter Queue:** Failed messages after 5 retries

### 5.3 Critical Workflows

#### Workflow 1: Doctor Clinical Query with Function Calling

```
┌────────┐    ┌─────────┐    ┌──────────────┐    ┌────────────┐    ┌────────┐
│ Doctor │    │   App   │    │Orchestrator  │    │Clinical    │    │ Gemini │
│        │    │         │    │              │    │Agent       │    │ 3 Pro  │
└───┬────┘    └────┬────┘    └──────┬───────┘    └─────┬──────┘    └────┬───┘
    │              │                 │                   │                │
    │ Voice Query  │                 │                   │                │
    ├─────────────▶│                 │                   │                │
    │              │ POST /query     │                   │                │
    │              ├────────────────▶│                   │                │
    │              │                 │ Route to Clinical │                │
    │              │                 ├──────────────────▶│                │
    │              │                 │                   │ LLM Request    │
    │              │                 │                   ├───────────────▶│
    │              │                 │                   │ (thinking:high)│
    │              │                 │                   │                │
    │              │                 │                   │◀───Decides to  │
    │              │                 │                   │  call function │
    │              │                 │                   │  search_ehr()  │
    │              │                 │                   │                │
    │              │                 │                   │ Call EHRSearch │
    │              │                 │                   ├───────────────▶│
    │              │                 │                   │   (parallel)   │
    │              │                 │                   │◀───────────────┤
    │              │                 │                   │ Patient data   │
    │              │                 │                   │                │
    │              │                 │                   │ Continue LLM   │
    │              │                 │                   ├───────────────▶│
    │              │                 │                   │ with results   │
    │              │                 │                   │◀───────────────┤
    │              │                 │                   │ Final response │
    │              │                 │◀──────────────────┤ + thought sig  │
    │              │◀────────────────┤                   │                │
    │              │ Response        │                   │                │
    │◀─────────────┤ (JSON)          │                   │                │
    │              │                 │                   │                │
    │ Display      │                 │                   │                │
    └──────────────┘                 └───────────────────┘                │
                                                                          │
    Total Time: 2.5 seconds (p95)                                         │
```

**Performance Breakdown:**
- API Gateway: 20ms (JWT validation, routing)
- Orchestrator: 50ms (session retrieval, context assembly)
- ClinicalAgent + Gemini: 1,800ms (LLM reasoning with `thinking_level: high`)
- Function call (EHR search): 300ms (cached patient data)
- Response assembly: 30ms
- **Total:** ~2.2 seconds (well under 3-second SLA)

#### Workflow 2: Patient Prescription Scanning (Multimodal)

```
┌────────┐    ┌─────────┐    ┌──────────────┐    ┌────────────┐    ┌────────┐
│Patient │    │  App    │    │Orchestrator  │    │Patient     │    │ Gemini │
│        │    │         │    │              │    │Agent       │    │3 Flash │
└───┬────┘    └────┬────┘    └──────┬───────┘    └─────┬──────┘    └────┬───┘
    │              │                 │                   │                │
    │ Tap Scan Rx  │                 │                   │                │
    ├─────────────▶│                 │                   │                │
    │              │ Open Camera     │                   │                │
    │◀─────────────┤                 │                   │                │
    │              │                 │                   │                │
    │ Capture Image│                 │                   │                │
    ├─────────────▶│                 │                   │                │
    │              │ Upload to       │                   │                │
    │              │ Cloud Storage   │                   │                │
    │              ├─────────────────┼───────────────────┼───────────────▶│
    │              │                 │                   │                │
    │              │ POST /ocr       │                   │                │
    │              ├────────────────▶│                   │                │
    │              │ {image_url}     │ Route to Patient  │                │
    │              │                 ├──────────────────▶│                │
    │              │                 │                   │ Multimodal OCR │
    │              │                 │                   ├───────────────▶│
    │              │                 │                   │ (image + prompt│
    │              │                 │                   │  structured out│
    │              │                 │                   │◀───────────────┤
    │              │                 │                   │ JSON: meds, dos│
    │              │                 │◀──────────────────┤                │
    │              │◀────────────────┤ Structured data   │                │
    │              │                 │                   │                │
    │◀─────────────┤ Display for     │                   │                │
    │ Confirm/Edit │ confirmation    │                   │                │
    │              │                 │                   │                │
    │ Confirmed    │                 │                   │                │
    ├─────────────▶│ POST /schedule  │                   │                │
    │              ├────────────────▶│                   │                │
    │              │                 │ Create schedule   │                │
    │              │                 ├──────────────────▶│                │
    │              │                 │                   │ Pub/Sub        │
    │              │                 │                   ├───────────────▶│
    │              │                 │                   │ (notifications)│
    │              │◀────────────────┤                   │                │
    │◀─────────────┤ Schedule created│                   │                │
    └──────────────┘                 └───────────────────┘                │
```

**Token Consumption:**
- Prescription image: ~600 tokens (average at medium resolution)
- System instruction + schema: 200 tokens (cached)
- Output: ~100 tokens (structured JSON)
- **Total:** ~900 tokens × $0.50/1M = $0.00045 per scan

#### Workflow 3: Real-Time Wearable Alert Escalation

```
┌──────────┐    ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌────────┐
│ Wearable │    │  Sync   │    │ Patient  │    │ Live API │    │On-Call │
│  Device  │    │ Service │    │  Agent   │    │ (WebSock)│    │ Doctor │
└────┬─────┘    └────┬────┘    └─────┬────┘    └────┬─────┘    └────┬───┘
     │               │                │              │              │
     │ Heart rate    │                │              │              │
     │ 130 bpm (rest)│                │              │              │
     ├──────────────▶│                │              │              │
     │               │ Store data     │              │              │
     │               │ Firestore      │              │              │
     │               │                │              │              │
     │ 135 bpm       │                │              │              │
     ├──────────────▶│                │              │              │
     │ (sustained)   │                │              │              │
     │               │ Anomaly detect │              │              │
     │               ├───────────────▶│              │              │
     │               │                │ Analyze      │              │
     │               │                │ context      │              │
     │               │                │              │              │
     │               │                │ Push alert   │              │
     │               │                │ to patient   │              │
     │               │◀───────────────┤              │              │
     │               │ FCM            │              │              │
     │               │                │              │              │
     │◀──────────────┴────────────────┴──Alert: High│              │
     │               │                │  heart rate  │              │
     │               │                │              │              │
     │ Patient       │                │              │              │
     │ reports chest │                │              │              │
     │ discomfort    │                │              │              │
     ├──────────────▶│────────────────▶              │              │
     │               │                │              │              │
     │               │                │ Severity 8/10│              │
     │               │                │ + cardiac Hx │              │
     │               │                │ = ESCALATE   │              │
     │               │                │              │              │
     │               │                │ Initiate Live│              │
     │               │                │ API session  │              │
     │               │                │──────────────▶              │
     │               │                │ WebSocket    │              │
     │               │                │              │ Notify       │
     │               │                │              ├─────────────▶│
     │               │                │              │ on-call      │
     │               │                │              │◀─────────────┤
     │               │                │              │ Accept call  │
     │               │                │◀──────────────              │
     │◀──────────────┴────────────────┴──Video call │              │
     │               │                │  established │              │
     │               │                │              │              │
     │ Video consultation with pre-loaded patient data              │
     └──────────────────────────────────────────────────────────────┘
```

**Latency Requirements:**
- Wearable sync to storage: < 5 seconds
- Anomaly detection: < 10 seconds
- Patient alert delivery: < 15 seconds (total from detection)
- Video call connection: < 30 seconds

### 5.4 State Management

**Session State (Short-Term)**
- **Storage:** Vertex AI Agent Engine Sessions
- **Retention:** 55 days (paid tier), 1 day (free tier)
- **Contents:**
  - Conversation history (full messages)
  - Thought signatures (preserved across turns)
  - User context (patient allergies, current medications)
  - Temporary decisions (medications considered, rejected options)

**Memory Bank (Long-Term)**
- **Storage:** Vertex AI Memory Bank
- **Retention:** Indefinite (until user deletion)
- **Contents:**
  - Extracted key facts (patient preferences, chronic conditions)
  - Recurring concerns (frequent symptom reports)
  - Action items (follow-up appointments, pending tasks)
- **Update Mechanism:** LLM-driven summarization after each session

**Database State (Permanent)**
- **Firestore & Cloud SQL:** Core application data
- **Retention:** 7 years (HIPAA) or indefinite
- **Backup:** Hourly incremental, daily full backup

---

## 6. DEPLOYMENT VIEW

### 6.1 Physical Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CLOUD INFRASTRUCTURE                            │
│                        (Google Cloud Platform)                           │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                      GLOBAL LOAD BALANCER                           │ │
│  │                (Cloud Load Balancing - HTTPS)                       │ │
│  └────────────────────┬───────────────────────────────────────────────┘ │
│                       │                                                  │
│  ┌────────────────────┼──────────────────────────────────────────────┐ │
│  │                    │           CLOUD CDN                           │ │
│  │                    │      (Static Assets, Images)                  │ │
│  └────────────────────┼──────────────────────────────────────────────┘ │
│                       │                                                  │
│         ┌─────────────┴─────────────┐                                   │
│         │                           │                                   │
│  ┌──────▼──────────┐        ┌──────▼──────────┐                        │
│  │   REGION:       │        │   REGION:       │                        │
│  │  us-central1    │        │  asia-south1    │                        │
│  │   (Iowa)        │        │   (Mumbai)      │                        │
│  └─────────────────┘        └─────────────────┘                        │
│         │                           │                                   │
│  ┌──────▼───────────────────────────▼──────────────┐                   │
│  │            CLOUD ENDPOINTS (API Gateway)        │                   │
│  │  - Auth, Rate Limiting, Request Validation      │                   │
│  └──────┬───────────────────────────┬──────────────┘                   │
│         │                           │                                   │
│  ┌──────▼──────────┐        ┌──────▼──────────┐                        │
│  │   CLOUD RUN     │        │   CLOUD RUN     │                        │
│  │ Orchestration   │        │ Orchestration   │                        │
│  │  (us-central1)  │        │ (asia-south1)   │                        │
│  │  - Min: 2       │        │  - Min: 2       │                        │
│  │  - Max: 50      │        │  - Max: 50      │                        │
│  │  - 2 vCPU/4GB   │        │  - 2 vCPU/4GB   │                        │
│  └──────┬──────────┘        └──────┬──────────┘                        │
│         │                           │                                   │
│  ┌──────▼───────────────────────────▼──────────────┐                   │
│  │           VERTEX AI (Gemini API)                │                   │
│  │  - gemini-3-pro-preview (Clinical, Admin)       │                   │
│  │  - gemini-3-flash-preview (Patient)             │                   │
│  │  - HIPAA BAA enabled                            │                   │
│  │  - Regulated-data flag: true                    │                   │
│  └─────────────────────────────────────────────────┘                   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                         DATA TIER                                │   │
│  │                                                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │  FIRESTORE   │  │  CLOUD SQL   │  │CLOUD STORAGE │           │   │
│  │  │  (Multi-     │  │  (Regional)  │  │(Multi-region)│           │   │
│  │  │   region)    │  │  PostgreSQL  │  │              │           │   │
│  │  │              │  │  - Primary:  │  │  - Encrypted │           │   │
│  │  │  - Encrypted │  │    us-c1     │  │  - CMEK      │           │   │
│  │  │  - Auto-scale│  │  - Replica:  │  │  - Lifecycle │           │   │
│  │  │              │  │    asia-s1   │  │              │           │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │   │
│  │                                                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │  VERTEX AI   │  │    REDIS     │  │   PUB/SUB    │           │   │
│  │  │  VECTOR DB   │  │ (Memorystore)│  │              │           │   │
│  │  │  - Embeddings│  │  - 4GB       │  │  - Topics:   │           │   │
│  │  │  - Clinical  │  │  - Regional  │  │    alerts,   │           │   │
│  │  │    protocols │  │              │  │    reminders │           │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    MONITORING & SECURITY                         │   │
│  │                                                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │ CLOUD        │  │ CLOUD TRACE  │  │ CLOUD KMS    │           │   │
│  │  │ MONITORING   │  │ (Tracing)    │  │ (Key Mgmt)   │           │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │   │
│  │                                                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │ CLOUD        │  │ SECURITY     │  │ IAM & IAP    │           │   │
│  │  │ LOGGING      │  │ COMMAND CTR  │  │              │           │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────┘
```

### 6.2 Regional Deployment Strategy

**Multi-Region Active-Active**
- **Primary:** us-central1 (Iowa) - US customers
- **Secondary:** asia-south1 (Mumbai) - India customers
- **Load Balancing:** Geo-routing (latency-based)

**Data Residency:**
- US patient data stored in us-central1
- India patient data stored in asia-south1
- Cross-border transfer only with patient consent

**Disaster Recovery:**
- **RTO:** 4 hours (Recovery Time Objective)
- **RPO:** 1 hour (Recovery Point Objective)
- **Failover:** Automatic Cloud SQL replica promotion
- **Backup Restoration:** Tested monthly

### 6.3 Scaling Strategy

**Horizontal Scaling:**
- Cloud Run auto-scales based on CPU (target 70%) and request queue
- Firestore auto-shards collections at high write volume
- Cloud SQL read replicas for query offloading

**Vertical Scaling:**
- Cloud Run instances: 2 vCPU → 4 vCPU during peak hours (configurable)
- Redis: 4GB → 8GB if cache hit rate < 80%

**Cost Optimization:**
- Context caching reduces Gemini API costs by 90% for repeated content
- Cloud Run scale-to-zero for non-critical services (admin analytics)
- Committed use discounts for baseline capacity (30% savings)

### 6.4 Network Architecture

**VPC Configuration:**
- Private subnets for Cloud Run, Cloud SQL (no public IPs)
- Cloud NAT for outbound internet access (EHR APIs, Gemini API)
- VPC Service Controls for data exfiltration prevention

**Security Perimeter:**
- Identity-Aware Proxy (IAP) for admin access
- Cloud Armor (WAF) for DDoS protection
- Allowlist for known EHR IP ranges

**TLS/SSL:**
- Google-managed certificates for *.app-domain.com
- Certificate pinning in mobile apps
- TLS 1.3 minimum enforced

---

## 7. IMPLEMENTATION VIEW

### 7.1 Code Organization

```
healthcare-platform/
├── backend/
│   ├── orchestrator/                   # Cloud Run orchestration service
│   │   ├── main.py                     # FastAPI application entry
│   │   ├── agents/
│   │   │   ├── root_orchestrator.py    # Top-level routing agent
│   │   │   ├── clinical_agent.py       # Doctor-facing agent
│   │   │   ├── patient_agent.py        # Patient-facing agent
│   │   │   ├── billing_agent.py        # Admin-facing agent
│   │   │   └── tool_agents/
│   │   │       ├── ehr_search.py       # FHIR client
│   │   │       ├── drug_db.py          # Micromedex integration
│   │   │       ├── scheduling.py       # Appointment booking
│   │   │       └── notification.py     # Push/SMS/email
│   │   ├── config/
│   │   │   ├── settings.py             # Pydantic configuration
│   │   │   ├── prompts.py              # System instructions
│   │   │   └── models.py               # Data models
│   │   ├── services/
│   │   │   ├── session_service.py      # Vertex AI Sessions wrapper
│   │   │   ├── auth_service.py         # JWT validation, RBAC
│   │   │   └── audit_service.py        # Compliance logging
│   │   ├── utils/
│   │   │   ├── retry.py                # Exponential backoff
│   │   │   ├── encryption.py           # PHI encryption helpers
│   │   │   └── validators.py           # Input validation
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── pyproject.toml
│   │
│   ├── integrations/                   # External system connectors
│   │   ├── ehr/
│   │   │   ├── fhir_client.py          # HL7 FHIR R4 client
│   │   │   ├── epic_adapter.py         # Epic-specific logic
│   │   │   └── cerner_adapter.py       # Cerner-specific logic
│   │   ├── billing/
│   │   │   └── nhcx_client.py          # India claims exchange
│   │   ├── wearables/
│   │   │   ├── apple_health.py         # HealthKit integration
│   │   │   └── google_fit.py           # Google Fit API
│   │   └── drug_db/
│   │       └── micromedex_client.py    # Drug database API
│   │
│   ├── data/
│   │   ├── repositories/               # Data access layer
│   │   │   ├── user_repository.py      # Cloud SQL users table
│   │   │   ├── patient_repository.py   # Firestore patients collection
│   │   │   ├── conversation_repo.py    # Firestore conversations
│   │   │   └── audit_repository.py     # Cloud SQL audit_logs
│   │   ├── models/                     # SQLAlchemy/Pydantic models
│   │   └── migrations/                 # Alembic database migrations
│   │
│   └── tests/
│       ├── unit/                       # Unit tests (pytest)
│       ├── integration/                # Integration tests
│       └── e2e/                        # End-to-end tests
│
├── frontend/
│   ├── doctor-portal/                  # React PWA for doctors
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── pages/
│   │   │   ├── services/               # API clients
│   │   │   └── hooks/                  # Custom React hooks
│   │   ├── public/
│   │   ├── package.json
│   │   └── vite.config.ts
│   │
│   ├── patient-app/                    # React Native for patients
│   │   ├── src/
│   │   │   ├── screens/
│   │   │   ├── components/
│   │   │   ├── navigation/
│   │   │   └── services/
│   │   ├── ios/                        # Native iOS code
│   │   ├── android/                    # Native Android code
│   │   └── package.json
│   │
│   └── admin-portal/                   # React PWA for admins
│       ├── src/
│       └── package.json
│
├── infrastructure/
│   ├── terraform/                      # Infrastructure as Code
│   │   ├── main.tf                     # GCP resources
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── modules/
│   │       ├── vpc/
│   │       ├── cloud_run/
│   │       └── databases/
│   │
│   ├── kubernetes/                     # K8s manifests (if needed)
│   └── scripts/
│       ├── deploy.sh                   # Deployment automation
│       └── backup.sh                   # Database backup
│
├── docs/
│   ├── api/                            # OpenAPI specifications
│   ├── architecture/                   # ADRs (Architecture Decision Records)
│   └── runbooks/                       # Operational procedures
│
├── .github/
│   └── workflows/
│       ├── ci.yml                      # GitHub Actions CI
│       ├── deploy-staging.yml
│       └── deploy-production.yml
│
├── README.md
├── LICENSE
└── .gitignore
```

### 7.2 Build and Deployment Pipeline

**CI/CD Flow (GitHub Actions):**

1. **On Pull Request:**
   - Run linters (black, flake8, eslint)
   - Run unit tests (pytest, jest)
   - Run integration tests (against staging Vertex AI)
   - Security scan (Snyk, Trivy)
   - Code coverage report (minimum 80%)

2. **On Merge to Main:**
   - Build Docker images (backend)
   - Build static assets (frontend)
   - Push images to Artifact Registry
   - Deploy to staging environment
   - Run E2E tests against staging
   - Manual approval gate

3. **On Approval:**
   - Blue-green deployment to production
   - Health checks and smoke tests
   - Monitor error rates for 1 hour
   - Auto-rollback if error rate > 1%

**Deployment Strategy:**
```bash
# Blue-Green Deployment (Cloud Run)
gcloud run deploy orchestrator-green \
  --image=gcr.io/project/orchestrator:v2.0 \
  --region=us-central1 \
  --no-traffic  # Deploy without serving traffic

# Run smoke tests against green deployment
./scripts/smoke-test.sh orchestrator-green

# Shift traffic gradually (10% -> 50% -> 100%)
gcloud run services update-traffic orchestrator \
  --to-revisions=orchestrator-green=10,orchestrator-blue=90

# Monitor for 30 minutes, then shift 100%
gcloud run services update-traffic orchestrator \
  --to-revisions=orchestrator-green=100
```

### 7.3 Technology Stack

**Backend:**
- **Language:** Python 3.11
- **Framework:** FastAPI (async REST API)
- **Agent Framework:** Google ADK (Agentic Development Kit)
- **LLM:** Gemini 3 Pro/Flash via Vertex AI
- **ORM:** SQLAlchemy (PostgreSQL), Firestore SDK
- **Async:** asyncio, aiohttp
- **Testing:** pytest, pytest-asyncio, pytest-cov
- **Linting:** black, flake8, mypy

**Frontend:**
- **Doctor/Admin Portal:** React 18, TypeScript, Vite, Tailwind CSS
- **Patient App:** React Native 0.73, Expo, TypeScript
- **State Management:** Zustand (lightweight alternative to Redux)
- **API Client:** Axios with retry logic
- **Testing:** Jest, React Testing Library, Detox (E2E for mobile)

**Infrastructure:**
- **Cloud:** Google Cloud Platform
- **Compute:** Cloud Run (serverless containers)
- **Databases:** Firestore, Cloud SQL (PostgreSQL), Cloud Storage
- **Cache:** Cloud Memorystore (Redis)
- **Messaging:** Pub/Sub
- **IaC:** Terraform
- **Monitoring:** Cloud Monitoring, Cloud Trace, Cloud Logging
- **CI/CD:** GitHub Actions, Cloud Build

**Security:**
- **Encryption:** Cloud KMS (key management), TLS 1.3
- **Authentication:** OAuth 2.0, JWT, Firebase Auth
- **Authorization:** Custom RBAC middleware
- **WAF:** Cloud Armor
- **Secrets:** Secret Manager

---

## 8. DATA VIEW

### 8.1 Data Flow Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                                    │
│                                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │   EHR    │  │ Wearables│  │   User   │  │  Billing │               │
│  │  (FHIR)  │  │  (APIs)  │  │  Input   │  │  System  │               │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘               │
│       │             │             │             │                       │
└───────┼─────────────┼─────────────┼─────────────┼───────────────────────┘
        │             │             │             │
        │             │             │             │
        ▼             ▼             ▼             ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      INGESTION LAYER                                    │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │            Integration Services (Cloud Run)                   │      │
│  │  - EHR Connector: FHIR→JSON normalization                     │      │
│  │  - Wearable Sync: Background jobs every 4 hours               │      │
│  │  - API Gateway: Input validation, sanitization                │      │
│  └──────────────────────────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────────────────┘
        │
        │ Encrypted PHI, validated data
        ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     PROCESSING LAYER                                    │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │                 Agent Orchestration                           │      │
│  │  - Data enrichment (retrieve patient context)                 │      │
│  │  - De-identification for logging (scrub PII)                  │      │
│  │  - Embedding generation (clinical protocols → vector DB)      │      │
│  │  - Gemini API calls (encrypted transit)                       │      │
│  └──────────────────────────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────────────────┘
        │
        │ Processed data, AI outputs
        ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      STORAGE LAYER                                      │
│                                                                          │
│  ┌─────────────────────┐    ┌─────────────────────┐                    │
│  │   FIRESTORE         │    │   CLOUD SQL         │                    │
│  │   (Encrypted)       │    │   (Encrypted)       │                    │
│  │                     │    │                     │                    │
│  │  - patients         │    │  - users            │                    │
│  │  - conversations    │    │  - audit_logs       │                    │
│  │  - medications      │    │  - organizations    │                    │
│  │  - wearable_data    │    │  - appointments     │                    │
│  └─────────────────────┘    └─────────────────────┘                    │
│                                                                          │
│  ┌─────────────────────┐    ┌─────────────────────┐                    │
│  │  CLOUD STORAGE      │    │  VERTEX AI VECTOR   │                    │
│  │  (CMEK Encrypted)   │    │  DB (Embeddings)    │                    │
│  │                     │    │                     │                    │
│  │  - prescription_img │    │  - clinical_proto   │                    │
│  │  - clinical_docs    │    │  - medical_lit      │                    │
│  │  - backups          │    │                     │                    │
│  └─────────────────────┘    └─────────────────────┘                    │
└────────────────────────────────────────────────────────────────────────┘
        │
        │ Query results, stored data
        ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                                   │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │              Client Applications                              │      │
│  │  - Data rendering (charts, lists, detail views)              │      │
│  │  - Local caching (service workers, async storage)            │      │
│  │  - Real-time updates (WebSocket, Firebase Realtime DB)       │      │
│  └──────────────────────────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Data Security and Privacy

**Encryption:**
- **At Rest:** AES-256 encryption for all databases and storage
- **In Transit:** TLS 1.3 for all communications
- **Key Management:** Customer-managed encryption keys (CMEK) via Cloud KMS, automatic 90-day rotation

**De-Identification:**
- **Logging:** PII/PHI scrubbed from application logs (names, MRNs replaced with hashed IDs)
- **Analytics:** Aggregated metrics only (no individual patient data in dashboards)
- **Testing:** Synthetic data generation for non-production environments

**Access Control:**
- **RBAC:** Role-based access (admin, doctor, patient) enforced at API Gateway
- **ABAC:** Attribute-based (doctor can only access their patients) enforced at application layer
- **Audit:** All data access logged to immutable audit_logs table (7-year retention)

**Data Minimization:**
- **API Calls:** Only necessary fields sent to Gemini API (exclude sensitive demographics when not needed)
- **Caching:** Cached content excludes PHI (clinical guidelines only, not patient data)
- **Retention:** Automatic deletion policies (prescription images after 30 days, unless patient-requested retention)

---

## 9. SIZE AND PERFORMANCE

### 9.1 Capacity Planning

**Current (MVP - 1 Hospital, 5,000 Patients):**
- Daily active users: 1,500 (30% of patients, 100 doctors, 50 admins)
- Gemini API requests: 50,000/day
- Token consumption: 150M tokens/day
- Storage growth: 50 GB/month
- Cost: $5,000/month ($2,500 AI, $1,500 infrastructure, $1,000 other)

**12-Month Projection (10 Hospitals, 50,000 Patients):**
- Daily active users: 15,000
- Gemini API requests: 500,000/day
- Token consumption: 1.5B tokens/day (with 80% cache hit rate)
- Storage: 20 TB total
- Cost: $35,000/month ($20,000 AI, $10,000 infrastructure, $5,000 other)

**3-Year Projection (100 Hospitals, 500,000 Patients):**
- Daily active users: 150,000
- Gemini API requests: 5M/day
- Token consumption: 15B tokens/day (with optimizations)
- Storage: 200 TB total
- Cost: $200,000/month ($120,000 AI, $60,000 infrastructure, $20,000 other)

### 9.2 Performance Benchmarks

**Response Times (95th Percentile):**
- Doctor clinical search: 2.8 seconds (target: < 3 seconds) ✓
- Patient conversation: 0.9 seconds (target: < 1 second) ✓
- Drug interaction check: 0.7 seconds (target: < 1 second) ✓
- Admin dashboard load: 1.5 seconds (target: < 2 seconds) ✓
- Prescription OCR: 1.2 seconds (target: < 2 seconds) ✓

**Throughput:**
- Concurrent users per region: 10,000
- Requests per minute (RPM): 2,000 (sustained)
- Gemini API rate limit: 2,000 RPM (Tier 3, distributed across agents)
- Database writes: 500/second (Firestore auto-scales)

**Resource Utilization:**
- Cloud Run CPU: 65% average (target: 70%)
- Cloud Run memory: 2.5GB average (4GB allocated)
- Cloud SQL connections: 150 active (500 max)
- Redis cache hit rate: 85% (target: 80%) ✓

### 9.3 Optimization Strategies

**Token Optimization:**
- Context caching for clinical guidelines (saves 90% on repeated content)
- Media resolution optimization (use `medium` for most PDFs, not `high`)
- Structured outputs to reduce verbose responses
- Target: < 5,000 tokens per average doctor query (currently 4,200)

**Latency Optimization:**
- Context caching reduces time-to-first-token by 60%
- Gemini 3 Flash for routing and patient conversations (3x faster than Pro)
- Parallel function calls (simultaneous EHR lookup + drug interaction check)
- Redis caching for frequently accessed EHR data (1-hour TTL)

**Cost Optimization:**
- Context caching: 90% cost reduction on cached content
- Batch API for non-urgent workloads (50% discount)
- Combined caching + batch: 75% total cost reduction
- Gemini 3 Flash for patient queries (5x cheaper than Pro)
- Target: < $0.10 per patient conversation, < $2 per complex clinical query

---

## 10. QUALITY ATTRIBUTES

### 10.1 Security

**Implementation:**
- **Authentication:** Multi-factor authentication (MFA) via Firebase Auth + SMS OTP
- **Authorization:** Custom RBAC middleware validating JWT claims against role matrix
- **Encryption:** TLS 1.3 (transit), AES-256 (rest), CMEK via Cloud KMS
- **Audit:** Comprehensive logging to immutable Cloud SQL audit_logs table
- **Vulnerability Management:** Weekly Snyk scans, quarterly penetration testing

**Validation:**
- Third-party penetration test (annual)
- HITRUST CSF certification (annual audit)
- Automated security scanning in CI/CD (Trivy, Snyk)

### 10.2 Reliability

**Implementation:**
- **Redundancy:** Multi-region deployment (us-central1, asia-south1)
- **Failover:** Automatic Cloud SQL replica promotion (< 30 seconds)
- **Circuit Breakers:** Prevent cascade failures from external system outages
- **Graceful Degradation:** Fallback to Gemini 2.5 Pro if 3.0 unavailable, cached protocols if API down

**Validation:**
- Chaos engineering tests (monthly): Random pod termination, network latency injection
- Disaster recovery drill (quarterly): Simulate region outage, measure RTO
- Uptime monitoring: 99.9% SLA (8.76 hours downtime/year), currently 99.95%

### 10.3 Performance

**Implementation:**
- **Caching:** Multi-layer caching (Redis for sessions/EHR, Vertex AI for prompts, CDN for assets)
- **Async Processing:** asyncio for non-blocking I/O, Pub/Sub for background tasks
- **Database Optimization:** Indexes on (user_id, created_at), read replicas for queries
- **Auto-Scaling:** Cloud Run scales 0-50 instances based on CPU and queue depth

**Validation:**
- Load testing (monthly): Simulate 10,000 concurrent users with k6
- Performance regression tests: Baseline response times in CI/CD
- APM monitoring: Cloud Trace for distributed tracing, identify bottlenecks

### 10.4 Scalability

**Implementation:**
- **Horizontal Scaling:** Cloud Run auto-scales, Firestore auto-shards
- **Stateless Design:** No session state in containers (externalized to Vertex AI Sessions)
- **Database Sharding:** Partition by organization_id for multi-tenancy
- **CDN:** Cloud CDN for static assets (reduces origin load by 80%)

**Validation:**
- Scalability testing: Incrementally increase load from 1K → 10K → 100K users
- Resource monitoring: Track CPU, memory, database connections at scale
- Cost projection: Validate that cost scales sublinearly with users (via caching efficiency)

### 10.5 Maintainability

**Implementation:**
- **Modular Architecture:** Clear separation between agents, tools, integrations
- **Comprehensive Logging:** Structured JSON logs with correlation IDs
- **Observability:** Distributed tracing (Cloud Trace), metrics (Cloud Monitoring)
- **Documentation:** OpenAPI specs auto-generated, inline code comments, runbooks

**Validation:**
- Time-to-resolution: Track mean time to resolve (MTTR) for incidents (target: < 2 hours)
- Code quality: Enforce 80% test coverage, peer review all changes
- Developer onboarding: New engineer productive within 1 week (documentation quality metric)

---

## 11. RISKS AND MITIGATION

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Gemini API model hallucination causes clinical error** | Medium | Critical | Mandatory human verification for all clinical outputs, strong system instructions emphasizing uncertainty, disclaimers on all AI responses |
| **HIPAA breach due to misconfiguration** | Low | Critical | Automated compliance checks in CI/CD, quarterly third-party audits, comprehensive training |
| **Gemini API outage disrupts service** | Low | High | Fallback to Gemini 2.5 Pro, graceful degradation to cached protocols, SLA with Google Cloud |
| **EHR integration failures delay deployment** | High | High | Extensive pre-integration testing, vendor partnerships, abstraction layer for EHR-agnostic logic |
| **Resistance to AI adoption by clinicians** | Medium | Medium | Physician champions, gradual rollout, training programs, demonstrate quick wins |
| **Token costs exceed budget** | Medium | Medium | Context caching (90% savings), batch processing (50% discount), Gemini Flash for low-complexity tasks |
| **Thought signature preservation failures** | Low | Medium | Comprehensive testing, automatic error detection and retry, SDK usage (handles automatically) |
| **Data residency compliance violations** | Low | High | Regional deployment enforcement via Terraform, automated audits, policy-based controls |

---

## 12. ARCHITECTURAL DECISION RECORDS (ADRs)

### ADR-001: Use ADK Framework for Multi-Agent Orchestration

**Status:** Accepted  
**Context:** Need robust framework for hierarchical agent coordination  
**Decision:** Adopt Google ADK over LangChain or custom framework  
**Rationale:** Native integration with Gemini API, thought signature handling, Vertex AI Sessions support  
**Consequences:** Team needs to learn ADK patterns, vendor lock-in to Google ecosystem (acceptable given Gemini dependency)

### ADR-002: Gemini 3 Pro for Clinical, Flash for Patient

**Status:** Accepted  
**Context:** Balance accuracy vs. cost/latency across personas  
**Decision:** Gemini 3 Pro (`thinking_level: high`) for clinical decisions, Flash (`thinking_level: low`) for patient conversations  
**Rationale:** Clinical accuracy critical (justify higher cost), patient interactions need sub-second latency (Flash 3x faster)  
**Consequences:** Higher operational cost for clinical queries (~$2 vs. $0.10), but aligned with quality requirements

### ADR-003: Firestore for Conversations, Cloud SQL for Audit

**Status:** Accepted  
**Context:** Need flexible schema for conversations, ACID for audit logs  
**Decision:** Hybrid database architecture (Firestore + Cloud SQL)  
**Rationale:** Firestore excels at semi-structured data (messages with varying tool calls), Cloud SQL provides immutability for compliance  
**Consequences:** Increased operational complexity (two databases), but optimal for use case

### ADR-004: No Custom Model Fine-Tuning

**Status:** Accepted  
**Context:** Consider fine-tuning Gemini for medical specificity  
**Decision:** Use base Gemini models with RAG (retrieval-augmented generation) for hospital protocols  
**Rationale:** Fine-tuning expensive ($$$), slow iteration, RAG provides similar benefits with faster updates  
**Consequences:** Dependence on prompt engineering and vector DB quality, acceptable given maturity of base models

### ADR-005: React PWA for Doctor Portal (Not Native Mobile)

**Status:** Accepted  
**Context:** Mobile-first requirement for doctor interface  
**Decision:** Progressive Web App (PWA) instead of React Native  
**Rationale:** Faster development, single codebase, offline capability via service workers, sufficient for clinical use case  
**Consequences:** Limited access to device APIs (vs. native), acceptable given no need for deep OS integration for doctors

---

## APPENDIX A: GLOSSARY

**ADK (Agentic Development Kit):** Google's framework for building multi-agent AI systems  
**Context Caching:** Gemini API feature to cache frequently used content and reduce costs  
**FHIR (Fast Healthcare Interoperability Resources):** HL7 standard for healthcare data exchange  
**Function Calling:** LLM capability to invoke external tools/APIs with structured parameters  
**Grounding:** Connecting LLM responses to external data sources for factual accuracy  
**Memory Bank:** Vertex AI feature for long-term conversational context storage  
**OCR (Optical Character Recognition):** Extracting text from images  
**RAG (Retrieval-Augmented Generation):** Pattern where LLM retrieves documents before generating responses  
**Thought Signature:** Encrypted representation of model's reasoning in Gemini 3  
**Vertex AI:** Google Cloud's managed ML platform  

---

**Document Approval:**
- **Architect:** Principal AI Engineer
- **Reviewers:** Backend Lead, DevOps Lead, Security Officer, CTO
- **Status:** Draft for Review
- **Version:** 1.0
- **Date:** January 29, 2026
