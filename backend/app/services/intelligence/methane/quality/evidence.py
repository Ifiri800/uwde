from __future__ import annotations

from datetime import timezone

from .models import (
    EvidenceRecord,
    QualityAssessment,
    QualityDimension,
    QualityIssue,
    QualityStatus,
)


def assess_evidence(
    evidence_records: tuple[EvidenceRecord, ...],
) -> QualityAssessment:
    """
    Assess evidence integrity and traceability.

    Checks:
    - evidence identity
    - evidence type
    - source
    - capture timestamp
    - duplicate evidence IDs
    - checksum availability
    - URI availability

    Evidence records are never modified.
    """

    if not isinstance(evidence_records, tuple):
        raise TypeError(
            "evidence_records must be a tuple"
        )

    if not evidence_records:
        return QualityAssessment(
            dimension=QualityDimension.EVIDENCE,
            status=QualityStatus.NOT_ASSESSED,
            score=None,
        )

    issues: list[QualityIssue] = []
    seen_ids: set[str] = set()
    error_count = 0

    for index, evidence in enumerate(evidence_records):
        if not isinstance(evidence, EvidenceRecord):
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.EVIDENCE,
                    code="invalid_evidence",
                    message="evidence must be an EvidenceRecord",
                    record_id=str(index),
                    severity="error",
                )
            )
            error_count += 1
            continue

        evidence_id = evidence.evidence_id or str(index)

        if not evidence.evidence_id.strip():
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.EVIDENCE,
                    code="invalid_evidence_id",
                    message="evidence_id is required",
                    record_id=evidence_id,
                    field="evidence_id",
                    severity="error",
                )
            )
            error_count += 1

        if not evidence.evidence_type.strip():
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.EVIDENCE,
                    code="invalid_evidence_type",
                    message="evidence_type is required",
                    record_id=evidence_id,
                    field="evidence_type",
                    severity="error",
                )
            )
            error_count += 1

        if not evidence.source.strip():
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.EVIDENCE,
                    code="invalid_source",
                    message="evidence source is required",
                    record_id=evidence_id,
                    field="source",
                    severity="error",
                )
            )
            error_count += 1

        if evidence.captured_at.tzinfo is None:
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.EVIDENCE,
                    code="invalid_timestamp",
                    message="captured_at must be timezone-aware",
                    record_id=evidence_id,
                    field="captured_at",
                    severity="error",
                )
            )
            error_count += 1

        if evidence.evidence_id in seen_ids:
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.EVIDENCE,
                    code="duplicate_evidence_id",
                    message="duplicate evidence ID detected",
                    record_id=evidence_id,
                    field="evidence_id",
                    severity="warning",
                )
            )

        seen_ids.add(evidence.evidence_id)

        if not evidence.checksum:
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.EVIDENCE,
                    code="missing_checksum",
                    message="evidence checksum is missing",
                    record_id=evidence_id,
                    field="checksum",
                    severity="warning",
                )
            )

        if not evidence.uri:
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.EVIDENCE,
                    code="missing_uri",
                    message="evidence URI is missing",
                    record_id=evidence_id,
                    field="uri",
                    severity="warning",
                )
            )

    score = round(
        max(
            0.0,
            (
                (len(evidence_records) - error_count)
                / len(evidence_records)
            )
            * 100.0,
        ),
        2,
    )

    if error_count:
        status = QualityStatus.FAIL
    elif issues:
        status = QualityStatus.WARNING
    else:
        status = QualityStatus.PASS

    return QualityAssessment(
        dimension=QualityDimension.EVIDENCE,
        status=status,
        score=score,
        issues=tuple(issues),
    )
