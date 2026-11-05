"""Scoring helpers for autocomplete and popular-search results."""

from math import log1p


def rank_suggestions(candidates, query, frequencies, history_counts, limit=8):
    """Rank candidate terms by match quality, dataset frequency, and history.

    ``candidates`` maps a normalized query string to either a source label or a
    dictionary containing ``source`` and (for typo matches) ``distance``.
    """
    normalized_query = query.casefold()
    ranked = []

    for candidate, details in candidates.items():
        if isinstance(details, str):
            source = details
            distance = 0
        else:
            source = details.get("source", "prefix")
            distance = details.get("distance", 0)

        if source == "prefix":
            relevance = 100
        elif source == "history":
            relevance = 100 if candidate.startswith(normalized_query) else 55
        elif source == "popular":
            relevance = 0
        else:
            relevance = max(0, 60 - distance * 15)

        frequency = frequencies.get(candidate, 0)
        searches = history_counts.get(candidate, 0)
        score = relevance + 4 * log1p(frequency) + 12 * log1p(searches)
        ranked.append(
            {
                "query": candidate,
                "score": round(score, 2),
                "source": source,
                "frequency": frequency,
                "searches": searches,
            }
        )

    ranked.sort(key=lambda item: (-item["score"], item["query"]))
    return ranked[:limit]
