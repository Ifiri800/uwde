from __future__ import annotations

from collections.abc import Iterable

from .models import QAQCProcedure


def validate_qa_qc_procedures(
    procedures: Iterable[QAQCProcedure],
) -> tuple[str, ...]:
    errors: list[str] = []
    seen: set[str] = set()

    for procedure in procedures:
        if not isinstance(procedure, QAQCProcedure):
            errors.append("invalid QA/QC procedure")
            continue

        if procedure.procedure_id in seen:
            errors.append(
                f"duplicate procedure_id: {procedure.procedure_id}"
            )

        seen.add(procedure.procedure_id)

    return tuple(errors)


def build_qa_qc_program(
    procedures: Iterable[QAQCProcedure],
) -> tuple[QAQCProcedure, ...]:
    result = tuple(procedures)

    errors = validate_qa_qc_procedures(result)

    if errors:
        raise ValueError("; ".join(errors))

    return result


def mandatory_procedures(
    procedures: Iterable[QAQCProcedure],
) -> tuple[QAQCProcedure, ...]:
    return tuple(
        procedure
        for procedure in procedures
        if procedure.mandatory
    )
