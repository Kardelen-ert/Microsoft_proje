"""Service layer for evaluation and regression checks."""

from __future__ import annotations

from app.db.repositories import TestRepository
from app.schemas.query import QuestionRequest
from app.schemas.testing import (
    TestCaseCreateRequest,
    TestCaseResponse,
    TestRunResponse,
)
from app.services.diagnostic_service import DiagnosticService


class TestService:
    """Coordinates saved test cases and their execution."""

    def __init__(self, diagnostic_service: DiagnosticService | None = None) -> None:
        self.repository = TestRepository()
        self.diagnostic_service = diagnostic_service or DiagnosticService()

    def create_test_case(self, payload: TestCaseCreateRequest) -> TestCaseResponse:
        """Persist a new evaluation case."""

        test_case_id = self.repository.create_test_case(
            question=payload.question,
            expected_behavior=payload.expected_behavior,
            expected_answer=payload.expected_answer,
            expected_keywords=payload.expected_keywords,
        )
        saved_case = self.repository.get_test_case(test_case_id)
        assert saved_case is not None

        return TestCaseResponse(
            id=saved_case.id,
            question=saved_case.question,
            expected_behavior=saved_case.expected_behavior,
            expected_answer=saved_case.expected_answer,
            expected_keywords=saved_case.expected_keywords,
            created_at=saved_case.created_at,
        )

    def list_test_cases(self) -> list[TestCaseResponse]:
        """Return all saved evaluation cases."""

        cases = self.repository.list_test_cases()
        return [
            TestCaseResponse(
                id=item.id,
                question=item.question,
                expected_behavior=item.expected_behavior,
                expected_answer=item.expected_answer,
                expected_keywords=item.expected_keywords,
                created_at=item.created_at,
            )
            for item in cases
        ]

    def run_test_case(self, test_case_id: int, top_k: int) -> TestRunResponse:
        """Execute one saved test case against the current RAG flow."""

        test_case = self.repository.get_test_case(test_case_id)
        if test_case is None:
            raise ValueError(f"Test case not found: {test_case_id}")

        response = self.diagnostic_service.run_query(
            QuestionRequest(
                question=test_case.question,
                top_k=top_k,
            )
        )

        passed, notes = self._evaluate_response(
            expected_behavior=test_case.expected_behavior,
            expected_answer=test_case.expected_answer,
            expected_keywords=test_case.expected_keywords,
            actual_answer=response.answer,
            grounded=response.grounded,
        )
        self.repository.add_test_run(
            test_case_id=test_case.id,
            actual_answer=response.answer,
            grounded=response.grounded,
            confidence=response.confidence,
            passed=passed,
            notes=notes,
        )

        return TestRunResponse(
            test_case_id=test_case.id,
            passed=passed,
            notes=notes,
            response=response,
        )

    def _evaluate_response(
        self,
        expected_behavior: str,
        expected_answer: str | None,
        expected_keywords: str | None,
        actual_answer: str,
        grounded: bool,
    ) -> tuple[bool, str]:
        """Score a response against a lightweight classroom-friendly rubric."""

        answer_lower = actual_answer.lower()
        notes: list[str] = []
        passed = True

        if expected_behavior == "unanswerable":
            has_fallback = (
                "bulunamadi" in answer_lower
                or "bilmiyorum" in answer_lower
                or "yeterli kaynak" in answer_lower
                or grounded is False
            )
            if not has_fallback:
                passed = False
                notes.append("Beklenen fallback davranisi gorulmedi.")
        else:
            if not grounded:
                passed = False
                notes.append("Beklenen grounded cevap uretilmedi.")

        if expected_answer:
            if expected_answer.lower() not in answer_lower:
                passed = False
                notes.append("Beklenen cevabin birebir ozeti bulunamadi.")

        if expected_keywords:
            missing_keywords = [
                item.strip()
                for item in expected_keywords.split(",")
                if item.strip() and item.strip().lower() not in answer_lower
            ]
            if missing_keywords:
                passed = False
                notes.append(
                    f"Eksik anahtar kelimeler: {', '.join(missing_keywords)}."
                )

        if not notes:
            notes.append("Test basarili.")

        return passed, " ".join(notes)
