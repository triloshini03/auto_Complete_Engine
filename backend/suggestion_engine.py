"""Combine Trie prefix results, typo tolerance, and ranking."""

from .ranking import rank_suggestions
from .trie import Trie


class SuggestionEngine:
    """Generate ranked suggestions from dataset terms and search history."""

    def __init__(self, entries, history):
        self.history = history
        self.terms = {}
        self.frequencies = {}
        self.trie = Trie()

        for entry in entries:
            query = entry["query"].strip().casefold()
            if not query:
                continue
            frequency = int(entry.get("frequency", 0))
            self.terms[query] = entry
            self.frequencies[query] = max(0, frequency)
            self.trie.insert(query)

    def suggest(self, query, limit=8):
        """Return ranked prefix and close-spelling matches."""
        if not isinstance(query, str):
            raise TypeError("query must be a string")
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        normalized = query.strip().casefold()
        if not normalized:
            return []

        candidates = {
            term: {"source": "prefix", "distance": 0}
            for term in self.trie.words_with_prefix(normalized)
        }
        history_counts = self.history.counts()

        for term in history_counts:
            if term.startswith(normalized):
                candidates.setdefault(term, {"source": "history", "distance": 0})

        typo_threshold = 2 if len(normalized) >= 8 else 1
        if len(normalized) >= 4:
            all_terms = set(self.terms) | set(history_counts)
            for term in all_terms:
                if term in candidates:
                    continue
                distance = self._prefix_distance(normalized, term, typo_threshold)
                if distance is not None:
                    candidates[term] = {"source": "typo", "distance": distance}

        return rank_suggestions(
            candidates,
            normalized,
            self.frequencies,
            history_counts,
            limit=limit,
        )

    def popular(self, limit=8):
        """Return the most popular dataset terms, including local history."""
        candidates = {term: "popular" for term in self.terms}
        return rank_suggestions(
            candidates,
            "",
            self.frequencies,
            self.history.counts(),
            limit=limit,
        )

    @staticmethod
    def _prefix_distance(query, term, threshold):
        """Find the smallest edit distance to a term prefix near query length."""
        minimum_length = max(1, len(query) - threshold)
        maximum_length = min(len(term), len(query) + threshold)
        best_distance = threshold + 1

        for prefix_length in range(minimum_length, maximum_length + 1):
            distance = SuggestionEngine._edit_distance(
                query, term[:prefix_length], threshold
            )
            best_distance = min(best_distance, distance)
            if best_distance == 0:
                break

        return best_distance if best_distance <= threshold else None

    @staticmethod
    def _edit_distance(first, second, threshold):
        """Calculate Levenshtein distance, stopping when it exceeds a limit."""
        if abs(len(first) - len(second)) > threshold:
            return threshold + 1

        previous = list(range(len(second) + 1))
        for row, first_character in enumerate(first, start=1):
            current = [row]
            for column, second_character in enumerate(second, start=1):
                current.append(
                    min(
                        current[column - 1] + 1,
                        previous[column] + 1,
                        previous[column - 1]
                        + (first_character != second_character),
                    )
                )
            if min(current) > threshold:
                return threshold + 1
            previous = current
        return previous[-1]
