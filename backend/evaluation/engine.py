import json
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from jsonschema import ValidationError, validate

from models.schemas import EvaluationRecord
from services.db_service import SessionLocal


Rule = Callable[[Any], Tuple[bool, Optional[str]]]


class EvaluationEngine:
    def evaluate(
        self,
        output: Any,
        agent_name: str,
        task_id: Optional[int] = None,
        schema: Optional[Dict[str, Any]] = None,
        rules: Optional[Iterable[Rule]] = None,
        retrieved_context: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        structural_ok = self._validate_schema(output, schema, errors)
        rules_ok = self._validate_rules(output, rules or [], errors)
        completeness_score = self._completeness_score(output)
        relevance_score = self._relevance_score(output, retrieved_context or [])
        groundedness_score = self._groundedness_score(output, retrieved_context or [])

        confidence = round(
            (
                (1.0 if structural_ok else 0.35)
                + (1.0 if rules_ok else 0.35)
                + completeness_score
                + relevance_score
                + groundedness_score
            )
            / 5,
            4,
        )
        validation_status = "passed" if not errors and confidence >= 0.55 else "failed"
        reasoning_summary = self._summarize(output, confidence, validation_status, errors)

        result = {
            "validation_status": validation_status,
            "confidence_score": confidence,
            "completeness_score": completeness_score,
            "relevance_score": relevance_score,
            "groundedness_score": groundedness_score,
            "reasoning_summary": reasoning_summary,
            "errors": errors,
        }
        self._record(task_id, agent_name, result)
        return result

    def _validate_schema(self, output, schema, errors):
        if not schema:
            return True
        try:
            validate(instance=output, schema=schema)
            return True
        except ValidationError as exc:
            errors.append(f"Structural validation failed: {exc.message}")
            return False

    def _validate_rules(self, output, rules, errors):
        ok = True
        for rule in rules:
            passed, message = rule(output)
            if not passed:
                ok = False
                errors.append(message or "Rule validation failed")
        return ok

    def _completeness_score(self, output) -> float:
        if output is None:
            return 0.0
        if isinstance(output, dict):
            if not output:
                return 0.15
            populated = sum(1 for value in output.values() if value not in (None, "", [], {}))
            return round(populated / max(1, len(output)), 4)
        if isinstance(output, list):
            return 1.0 if output else 0.2
        return 0.85 if str(output).strip() else 0.1

    def _relevance_score(self, output, context) -> float:
        if not context:
            return 0.72
        output_text = json.dumps(output, default=str).lower()
        context_terms = set()
        for item in context:
            context_terms.update(str(item.get("content", "")).lower().split()[:80])
        if not context_terms:
            return 0.72
        matched = sum(1 for term in context_terms if len(term) > 3 and term in output_text)
        return round(min(1.0, matched / 20), 4)

    def _groundedness_score(self, output, context) -> float:
        if not context:
            return 0.7
        context_text = " ".join(str(item.get("content", "")).lower() for item in context)
        output_terms = [term for term in json.dumps(output, default=str).lower().split() if len(term) > 4]
        if not output_terms:
            return 0.25
        grounded = sum(1 for term in output_terms[:120] if term in context_text)
        return round(min(1.0, grounded / max(1, min(len(output_terms), 120))), 4)

    def _summarize(self, output, confidence, validation_status, errors):
        if errors:
            return f"Validation {validation_status}; confidence {confidence}. Issues: {'; '.join(errors[:3])}"
        if isinstance(output, dict):
            keys = ", ".join(list(output.keys())[:6])
            return f"Validation {validation_status}; confidence {confidence}. Output contains keys: {keys}."
        if isinstance(output, list):
            return f"Validation {validation_status}; confidence {confidence}. Output contains {len(output)} items."
        return f"Validation {validation_status}; confidence {confidence}."

    def _record(self, task_id, agent_name, result):
        db = SessionLocal()
        try:
            db.add(
                EvaluationRecord(
                    task_id=task_id,
                    agent_name=agent_name,
                    validation_status=result["validation_status"],
                    confidence_score=result["confidence_score"],
                    completeness_score=result["completeness_score"],
                    relevance_score=result["relevance_score"],
                    groundedness_score=result["groundedness_score"],
                    reasoning_summary=result["reasoning_summary"],
                    errors=json.dumps(result["errors"]),
                )
            )
            db.commit()
        finally:
            db.close()


evaluation_engine = EvaluationEngine()
