from backend.models import Report, AlertResult, AnalyzeResponse
from backend.services.filter import filter_reports, classify_alert
from backend.services.rag import generate_digest


def process_reports(reports: list[Report], user_location: str) -> AnalyzeResponse:
    """
    Full pipeline: filter → location check → classify → digest.
    Category is passed to the digest generator so advice is context-specific.
    """
    filtered = filter_reports(reports)
    filtered_out = len(reports) - len(filtered)

    results: list[AlertResult] = []

    for r in filtered:
        if r.location.lower() not in (user_location.lower(), "national"):
            filtered_out += 1
            continue

        category, severity = classify_alert(r.text)
        digest, method = generate_digest(r.text, category=category)

        results.append(AlertResult(
            alert=r.text,
            location=r.location,
            category=category,
            severity=severity,
            digest=digest,
            method=method,
        ))

    return AnalyzeResponse(
        alerts=results,
        processed=len(results),
        filtered_out=filtered_out,
    )
