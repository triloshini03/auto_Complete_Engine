const searchForm = document.querySelector("#search-form");
const searchInput = document.querySelector("#search-input");
const suggestionPanel = document.querySelector("#suggestion-panel");
const suggestionsList = document.querySelector("#suggestions");
const clearInputButton = document.querySelector("#clear-input");
const popularContainer = document.querySelector("#popular-searches");
const recentContainer = document.querySelector("#recent-searches");
const clearHistoryButton = document.querySelector("#clear-history");
const notice = document.querySelector("#notice");

let debounceTimer;
let activeSuggestion = -1;
let currentSuggestions = [];
let autocompleteController;

function showNotice(message, type = "") {
  notice.textContent = message;
  notice.className = `notice ${type}`.trim();
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Something went wrong. Please try again.");
  }
  return payload;
}

function setSuggestionPanelOpen(isOpen) {
  suggestionPanel.hidden = !isOpen;
  searchInput.setAttribute("aria-expanded", String(isOpen));
}

function renderSuggestions(suggestions) {
  currentSuggestions = suggestions;
  activeSuggestion = -1;
  suggestionsList.replaceChildren();

  if (!suggestions.length) {
    const empty = document.createElement("li");
    empty.className = "empty-suggestions";
    empty.textContent = "No close matches yet. Try another search.";
    suggestionsList.append(empty);
    setSuggestionPanelOpen(true);
    return;
  }

  suggestions.forEach((suggestion, index) => {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.className = "suggestion-row";
    button.type = "button";
    button.role = "option";
    button.id = `suggestion-${index}`;
    button.setAttribute("aria-selected", "false");

    const icon = document.createElement("span");
    icon.className = "row-icon";
    icon.textContent = suggestion.source === "history" ? "◷" : "⌕";
    icon.setAttribute("aria-hidden", "true");

    const copy = document.createElement("span");
    copy.className = "suggestion-copy";
    const query = document.createElement("span");
    query.className = "suggestion-query";
    query.textContent = suggestion.query;
    const meta = document.createElement("span");
    meta.className = "suggestion-meta";
    meta.textContent = suggestion.source === "typo"
      ? "A close spelling match"
      : `${suggestion.searches ? `${suggestion.searches} recent searches` : "Suggested for you"} · ${suggestion.frequency.toLocaleString()} searches`;
    copy.append(query, meta);

    const arrow = document.createElement("span");
    arrow.className = "suggestion-arrow";
    arrow.textContent = "↗";
    arrow.setAttribute("aria-hidden", "true");

    button.append(icon, copy, arrow);
    button.addEventListener("click", () => selectSearch(suggestion.query));
    item.append(button);
    suggestionsList.append(item);
  });
  setSuggestionPanelOpen(true);
}

function updateActiveSuggestion(nextIndex) {
  if (!currentSuggestions.length) return;
  activeSuggestion = (nextIndex + currentSuggestions.length) % currentSuggestions.length;
  [...suggestionsList.querySelectorAll(".suggestion-row")].forEach((row, index) => {
    const isActive = index === activeSuggestion;
    row.setAttribute("aria-selected", String(isActive));
    if (isActive) {
      searchInput.setAttribute("aria-activedescendant", row.id);
      row.scrollIntoView({ block: "nearest" });
    }
  });
}

async function loadSuggestions(query) {
  if (autocompleteController) autocompleteController.abort();
  autocompleteController = new AbortController();
  try {
    const payload = await fetchJson(
      `/api/autocomplete?q=${encodeURIComponent(query)}`,
      { signal: autocompleteController.signal },
    );
    if (searchInput.value.trim() === query) renderSuggestions(payload.suggestions);
  } catch (error) {
    if (error.name !== "AbortError") showNotice(error.message, "error");
  }
}

async function submitSearch(query) {
  const cleanQuery = query.trim();
  if (!cleanQuery) {
    showNotice("Type something to search for.", "error");
    searchInput.focus();
    return;
  }

  try {
    const payload = await fetchJson("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: cleanQuery }),
    });
    searchInput.value = payload.query;
    clearInputButton.hidden = false;
    setSuggestionPanelOpen(false);
    showNotice(`Search selected: “${payload.query}”`, "success");
    await loadRecentSearches();
  } catch (error) {
    showNotice(error.message, "error");
  }
}

function selectSearch(query) {
  searchInput.value = query;
  clearInputButton.hidden = false;
  submitSearch(query);
}

function makeSearchChip(query, className = "search-chip") {
  const button = document.createElement("button");
  button.type = "button";
  button.className = className;
  button.textContent = query;
  button.title = `Search for ${query}`;
  button.addEventListener("click", () => selectSearch(query));
  return button;
}

async function loadPopularSearches() {
  try {
    const payload = await fetchJson("/api/popular");
    popularContainer.replaceChildren(
      ...payload.suggestions.map((suggestion) => makeSearchChip(suggestion.query)),
    );
  } catch (error) {
    popularContainer.textContent = "Popular searches could not be loaded.";
    showNotice(error.message, "error");
  }
}

function formatRecentTime(dateString) {
  const elapsedMinutes = Math.floor((Date.now() - new Date(dateString).getTime()) / 60000);
  if (!Number.isFinite(elapsedMinutes) || elapsedMinutes < 1) return "Just now";
  if (elapsedMinutes < 60) return `${elapsedMinutes}m ago`;
  const elapsedHours = Math.floor(elapsedMinutes / 60);
  if (elapsedHours < 24) return `${elapsedHours}h ago`;
  return `${Math.floor(elapsedHours / 24)}d ago`;
}

async function loadRecentSearches() {
  try {
    const payload = await fetchJson("/api/history");
    recentContainer.replaceChildren();
    clearHistoryButton.hidden = payload.searches.length === 0;

    if (!payload.searches.length) {
      const empty = document.createElement("p");
      empty.className = "empty-state";
      empty.textContent = "Your recent searches will show up here.";
      recentContainer.append(empty);
      return;
    }

    payload.searches.forEach((entry) => {
      const button = makeSearchChip(entry.query, "recent-item");
      const icon = document.createElement("span");
      icon.className = "recent-item-icon";
      icon.textContent = "◷";
      icon.setAttribute("aria-hidden", "true");
      const query = document.createElement("span");
      query.className = "recent-item-query";
      query.textContent = entry.query;
      const time = document.createElement("span");
      time.className = "recent-item-time";
      time.textContent = formatRecentTime(entry.searched_at);
      button.replaceChildren(icon, query, time);
      recentContainer.append(button);
    });
  } catch (error) {
    recentContainer.textContent = "Recent searches could not be loaded.";
    showNotice(error.message, "error");
  }
}

searchInput.addEventListener("input", () => {
  const query = searchInput.value.trim();
  clearInputButton.hidden = query.length === 0;
  searchInput.removeAttribute("aria-activedescendant");
  if (!query) {
    clearTimeout(debounceTimer);
    if (autocompleteController) autocompleteController.abort();
    currentSuggestions = [];
    suggestionsList.replaceChildren();
    setSuggestionPanelOpen(false);
    return;
  }
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => loadSuggestions(query), 110);
});

searchInput.addEventListener("keydown", (event) => {
  if (event.key === "ArrowDown" && !suggestionPanel.hidden) {
    event.preventDefault();
    updateActiveSuggestion(activeSuggestion + 1);
  } else if (event.key === "ArrowUp" && !suggestionPanel.hidden) {
    event.preventDefault();
    updateActiveSuggestion(activeSuggestion <= 0 ? currentSuggestions.length - 1 : activeSuggestion - 1);
  } else if (event.key === "Enter" && activeSuggestion >= 0) {
    event.preventDefault();
    selectSearch(currentSuggestions[activeSuggestion].query);
  } else if (event.key === "Escape") {
    setSuggestionPanelOpen(false);
  }
});

searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (activeSuggestion >= 0 && currentSuggestions[activeSuggestion]) {
    selectSearch(currentSuggestions[activeSuggestion].query);
  } else {
    submitSearch(searchInput.value);
  }
});

clearInputButton.addEventListener("click", () => {
  searchInput.value = "";
  clearInputButton.hidden = true;
  currentSuggestions = [];
  suggestionsList.replaceChildren();
  setSuggestionPanelOpen(false);
  showNotice("");
  searchInput.focus();
});

clearHistoryButton.addEventListener("click", async () => {
  try {
    await fetchJson("/api/history", { method: "DELETE" });
    await loadRecentSearches();
    showNotice("Your recent search history has been cleared.", "success");
  } catch (error) {
    showNotice(error.message, "error");
  }
});

document.addEventListener("click", (event) => {
  if (!event.target.closest(".search-wrap")) setSuggestionPanelOpen(false);
});

Promise.all([loadPopularSearches(), loadRecentSearches()]);
