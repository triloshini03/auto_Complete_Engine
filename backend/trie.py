"""Trie data structure for efficient, case-insensitive prefix lookups."""


class TrieNode:
    """A single node in a Trie."""

    def __init__(self):
        self.children = {}
        self.is_end_of_word = False


class Trie:
    """Store words and retrieve all words that begin with a prefix."""

    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        """Insert a non-empty word into the Trie."""
        if not isinstance(word, str):
            raise TypeError("word must be a string")
        normalized = word.strip().casefold()
        if not normalized:
            raise ValueError("word cannot be empty")

        node = self.root
        for character in normalized:
            node = node.children.setdefault(character, TrieNode())
        node.is_end_of_word = True

    def search(self, word):
        """Return whether the complete word exists in the Trie."""
        if not isinstance(word, str):
            raise TypeError("word must be a string")
        normalized = word.strip().casefold()
        if not normalized:
            return False

        node = self._find_node(normalized)
        return node is not None and node.is_end_of_word

    def starts_with(self, prefix):
        """Return whether at least one stored word begins with the prefix."""
        if not isinstance(prefix, str):
            raise TypeError("prefix must be a string")
        normalized = prefix.strip().casefold()
        if not normalized:
            return True
        return self._find_node(normalized) is not None

    def words_with_prefix(self, prefix, limit=None):
        """Return words for a prefix in alphabetical order."""
        if not isinstance(prefix, str):
            raise TypeError("prefix must be a string")
        if limit is not None and (not isinstance(limit, int) or limit < 0):
            raise ValueError("limit must be a non-negative integer or None")

        normalized = prefix.strip().casefold()
        start = self._find_node(normalized)
        if start is None or limit == 0:
            return []

        words = []

        def collect(node, current_word):
            if limit is not None and len(words) >= limit:
                return
            if node.is_end_of_word:
                words.append(current_word)
            for character in sorted(node.children):
                collect(node.children[character], current_word + character)
                if limit is not None and len(words) >= limit:
                    return

        collect(start, normalized)
        return words

    def _find_node(self, text):
        node = self.root
        for character in text:
            node = node.children.get(character)
            if node is None:
                return None
        return node
