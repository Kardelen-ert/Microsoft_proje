"""Request and response schemas for evaluation endpoints."""

from pydantic import BaseModel, Field

from app.schemas.query import DiagnosticResponse


class TestCaseCreateRequest(BaseModel):
    """Payload used to create an evaluation case."""

    question: str = Field(..., min_length=5)
    expected_behavior: str = Field(
        ...,
        pattern="^(answerable|unanswerable)$",
        description="Whether the system should answer or refuse due to missing context",
    )
    expected_answer: str | None = None
    expected_keywords: str | None = Field(
        default=None,
        description="Comma-separated keywords expected in the answer",
    )


class TestCaseResponse(BaseModel):
    """Saved evaluation case returned by the API."""

    id: int
    question: str
    expected_behavior: str
    expected_answer: str | None = None
    expected_keywords: str | None = None
    created_at: str


class TestRunRequest(BaseModel):
    """Payload used to execute a saved test case."""

    top_k: int = Field(default=3, ge=1, le=10)


class TestRunResponse(BaseModel):
    """Evaluation result for one saved test case."""

    test_case_id: int
    passed: bool
    notes: str
    response: DiagnosticResponse
