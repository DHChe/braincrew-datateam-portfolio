from __future__ import annotations

from braincrew.contracts import FixtureCaseDocument, NormalizedObservation


def normalize_fixture_response(case_document: FixtureCaseDocument) -> NormalizedObservation:
    return NormalizedObservation(
        schema_version="normalized-observation-v1",
        case_id=case_document.case.id,
        answer=case_document.fixture_sut.answer,
        answer_mode=case_document.fixture_sut.answer_mode,
    )
