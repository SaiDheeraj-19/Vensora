import logging
from typing import Dict, Any, Tuple
from app.core.audit import log_audit_event

logger = logging.getLogger(__name__)

class ConfidenceEvaluator:
    """
    Evaluates retrieval quality, intent, and guardrails to determine 
    if the AI is confident enough to answer, or if it should escalate.
    """
    
    def evaluate(self, call_id: str, retrieval_results: list, guardrail_safe: bool, guardrail_reason: str) -> Tuple[str, str]:
        """
        Returns a tuple: (DECISION, REASON)
        Decisions: HIGH, MEDIUM, LOW
        """
        decision = "HIGH"
        reason = "Normal processing"
        
        if not guardrail_safe:
            decision = "LOW"
            reason = f"Guardrail violation: {guardrail_reason}"
        elif not retrieval_results:
            decision = "MEDIUM"
            reason = "No relevant context found in RAG"
        else:
            # Check the best score from Qdrant
            best_score = retrieval_results[0].get("score", 0.0)
            if best_score < 0.6:
                decision = "LOW"
                reason = f"Retrieval confidence too low ({best_score})"
            elif best_score < 0.8:
                decision = "MEDIUM"
                reason = f"Retrieval confidence marginal ({best_score})"
                
        logger.info(f"[{call_id}] Confidence Evaluated: {decision} ({reason})")
        
        # Audit Log the decision
        log_audit_event(
            action="AI_CONFIDENCE_EVALUATION",
            resource_id=call_id,
            changes={
                "decision": decision,
                "reason": reason,
                "best_retrieval_score": retrieval_results[0].get("score", 0.0) if retrieval_results else 0.0
            }
        )
        
        return decision, reason

confidence_evaluator = ConfidenceEvaluator()
