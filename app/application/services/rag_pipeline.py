"""
Pipeline 1: Grounded Guideline RAG
Hybrid Search (BM25 + Vector) -> MedGemma Validation -> Gemini 3 Synthesis
"""
import json
import re
from typing import List, Dict, Any
from datetime import datetime

class HybridSearchRAG:
    def __init__(self):
        # Mock document store (In production: ChromaDB, Pinecone, or FAISS)
        self.document_store = self._init_mock_documents()
        print("HybridSearchRAG initialized with mock document store.")

    def _init_mock_documents(self) -> List[Dict]:
        """Initialize mock clinical guidelines for demo."""
        return [
            {
                "id": "SEP-2023-001",
                "title": "Sepsis Management Protocol v2.0",
                "year": 2023,
                "content": "For suspected sepsis: 1) Draw blood cultures before antibiotics. 2) Administer broad-spectrum antibiotics within 1 hour. 3) Measure lactate levels. 4) Start IV fluids 30mL/kg if hypotensive.",
                "source": "Hospital ICU Guidelines",
                "evidence_level": 1
            },
            {
                "id": "SEP-2025-001",
                "title": "Sepsis Management Protocol v3.0 (Updated)",
                "year": 2025,
                "content": "Updated 2025: 1) Draw cultures. 2) Antibiotics within 1 hour (prefer Piperacillin-Tazobactam). 3) Lactate q2h. 4) Balanced crystalloids 30mL/kg. 5) MAP target ≥65mmHg. 6) Consider vasopressors early if refractory.",
                "source": "Surviving Sepsis Campaign 2025",
                "evidence_level": 1
            },
            {
                "id": "DM-2024-001",
                "title": "Type 2 Diabetes Inpatient Management",
                "year": 2024,
                "content": "Inpatient glucose targets: 140-180 mg/dL. Use basal-bolus insulin regimen. Avoid sulfonylureas in hospitalized patients. Monitor for hypoglycemia q4h.",
                "source": "ADA Standards of Care 2024",
                "evidence_level": 1
            },
            {
                "id": "HTN-2023-001",
                "title": "Hypertensive Crisis Management",
                "year": 2023,
                "content": "For hypertensive emergency (BP >180/120 with end-organ damage): 1) IV Labetalol or Nicardipine. 2) Target 25% reduction in first hour. 3) Avoid rapid drops to prevent ischemia.",
                "source": "AHA/ACC Guidelines",
                "evidence_level": 1
            }
        ]

    # ============ LIMB: Hybrid Search ============
    def hybrid_search_rag(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Combines BM25 (lexical) and Vector (semantic) search.
        Mocked implementation: Uses keyword matching + recency scoring.
        """
        results = []
        query_lower = query.lower()
        
        for doc in self.document_store:
            # BM25 Score (Mocked: keyword overlap)
            content_lower = doc['content'].lower() + doc['title'].lower()
            keyword_score = sum(1 for word in query_lower.split() if word in content_lower)
            
            # Vector Score (Mocked: inverse of string distance, placeholder)
            vector_score = 0.5 if any(kw in content_lower for kw in query_lower.split()) else 0.1
            
            # Recency Boost
            recency_boost = (doc['year'] - 2020) * 0.1
            
            # Combined Score
            combined_score = (keyword_score * 0.4) + (vector_score * 0.3) + (recency_boost * 0.3)
            
            if combined_score > 0.2:
                results.append({
                    **doc,
                    "relevance_score": round(combined_score, 2),
                    "search_method": "hybrid"
                })
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results[:top_k]

    # ============ SPECIALIST: MedGemma Protocol Validation ============
    def validate_protocol_currency(self, snippets: List[Dict]) -> Dict:
        """
        MedGemma checks document dates and clinical validity.
        Mocked: Returns the most recent document as preferred.
        """
        if not snippets:
            return {"status": "no_results", "preferred_doc": None}
        
        # Sort by year (most recent first)
        sorted_by_year = sorted(snippets, key=lambda x: x.get('year', 0), reverse=True)
        preferred = sorted_by_year[0]
        
        return {
            "status": "validated",
            "preferred_doc": preferred,
            "validation_note": f"MedGemma prioritized {preferred['year']} protocol over older versions.",
            "all_candidates": [{"id": s['id'], "year": s['year']} for s in snippets]
        }

    # ============ BRAIN: Gemini 3 Synthesis ============
    def synthesize_answer(self, query: str, validated_result: Dict, ai_service) -> Dict:
        """
        Gemini 3 generates the final grounded answer with citations.
        """
        if validated_result['status'] == 'no_results':
            return {
                "answer": "No relevant clinical guidelines found in the knowledge base.",
                "citations": [],
                "evidence_grade": "N/A"
            }
        
        doc = validated_result['preferred_doc']
        
        prompt = f"""
        ROLE: Clinical Decision Support Specialist.
        
        QUERY: {query}
        
        RETRIEVED PROTOCOL (Source: {doc['source']}, Year: {doc['year']}):
        {doc['content']}
        
        TASK:
        1. Answer the clinician's query using ONLY the retrieved protocol.
        2. Provide inline citations in [Source ID] format.
        3. Assign an Evidence Grade (Level 1-5).
        
        OUTPUT FORMAT (JSON):
        {{
          "answer": "Your synthesized answer with [SEP-2025-001] citations",
          "citations": ["SEP-2025-001"],
          "evidence_grade": "Level 1"
        }}
        """
        
        try:
            response = ai_service.pro_model.generate_content(
                prompt,
                generation_config=ai_service.analytical_config
            )
            # Try to parse as JSON, fallback to text
            try:
                return json.loads(response.text)
            except:
                return {
                    "answer": response.text,
                    "citations": [doc['id']],
                    "evidence_grade": f"Level {doc.get('evidence_level', 3)}"
                }
        except Exception as e:
            return {
                "answer": doc['content'],
                "citations": [doc['id']],
                "evidence_grade": f"Level {doc.get('evidence_level', 3)}",
                "error": str(e)
            }

    # ============ ORCHESTRATED PIPELINE ============
    def run_pipeline(self, query: str, ai_service) -> Dict:
        """Full RAG pipeline execution."""
        print(f"[RAG] Query: {query}")
        
        # Step 1: Limb - Hybrid Search
        print("[RAG] Step 1: Running Hybrid Search...")
        search_results = self.hybrid_search_rag(query)
        
        # Step 2: Specialist - MedGemma Validation
        print("[RAG] Step 2: MedGemma validating protocol currency...")
        validated = self.validate_protocol_currency(search_results)
        
        # Step 3: Brain - Gemini 3 Synthesis
        print("[RAG] Step 3: Gemini 3 synthesizing answer...")
        final_answer = self.synthesize_answer(query, validated, ai_service)
        
        return {
            "query": query,
            "search_results_count": len(search_results),
            "validation": validated['validation_note'] if validated['status'] == 'validated' else 'No validation',
            "response": final_answer
        }

if __name__ == "__main__":
    rag = HybridSearchRAG()
    results = rag.hybrid_search_rag("sepsis management")
    print(json.dumps(results, indent=2))
