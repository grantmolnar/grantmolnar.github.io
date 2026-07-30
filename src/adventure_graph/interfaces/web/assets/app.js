(() => {
  "use strict";

  const THEME_KEY = "adventure-graph:appearance";
  const LIGHT_THEME = "light";
  const DARK_THEME = "dark";

  function readStoredValue(key) {
    try {
      return localStorage.getItem(key);
    } catch (_error) {
      return null;
    }
  }

  function writeStoredValue(key, value) {
    try {
      localStorage.setItem(key, value);
      return true;
    } catch (_error) {
      return false;
    }
  }

  function removeStoredValue(key) {
    try {
      localStorage.removeItem(key);
    } catch (_error) {
      // Local preferences and drafts are optional browser conveniences.
    }
  }

  function normalizedTheme(value) {
    return value === DARK_THEME ? DARK_THEME : LIGHT_THEME;
  }

  function applyTheme(theme) {
    const normalized = normalizedTheme(theme);
    document.documentElement.dataset.theme = normalized;
    document.documentElement.style.colorScheme = normalized;
    return normalized;
  }

  // Apply the stored appearance before the stylesheet is parsed to avoid a light-mode flash.
  applyTheme(readStoredValue(THEME_KEY));

  function initializeThemeToggle() {
    const buttons = Array.from(document.querySelectorAll("[data-theme-toggle]"));
    if (buttons.length === 0) {
      return;
    }

    function refreshButtons(theme) {
      const dark = theme === DARK_THEME;
      for (const button of buttons) {
        button.setAttribute("aria-pressed", String(dark));
        button.setAttribute("title", dark ? "Switch to light mode" : "Switch to dark mode");
        const label = button.querySelector("[data-theme-label]");
        if (label) {
          label.textContent = dark ? "Light mode" : "Dark mode";
        }
      }
    }

    let theme = applyTheme(readStoredValue(THEME_KEY));
    refreshButtons(theme);
    for (const button of buttons) {
      button.addEventListener("click", () => {
        theme = applyTheme(theme === DARK_THEME ? LIGHT_THEME : DARK_THEME);
        writeStoredValue(THEME_KEY, theme);
        refreshButtons(theme);
      });
    }
  }

  function initializeEditableSurfaces() {
    const surfaces = Array.from(document.querySelectorAll("[data-edit-href]"));
    for (const surface of surfaces) {
      const href = surface.dataset.editHref;
      if (!href) {
        continue;
      }
      const openEditor = () => window.location.assign(href);
      const cameFromNestedControl = (event) => {
        const control = event.target.closest?.("a, button, input, textarea, select, summary");
        return control && control !== surface;
      };
      surface.addEventListener("dblclick", (event) => {
        if (cameFromNestedControl(event)) {
          return;
        }
        event.preventDefault();
        openEditor();
      });
      surface.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !cameFromNestedControl(event)) {
          event.preventDefault();
          openEditor();
        }
      });
    }
  }

  function readField(field) {
    return field.type === "checkbox" ? field.checked : field.value;
  }

  function writeField(field, value) {
    if (field.type === "checkbox") {
      field.checked = Boolean(value);
    } else if (typeof value === "string") {
      field.value = value;
    }
  }

  function initializeAuthoringForm() {
    const form = document.querySelector("[data-authoring-form]");
    if (!form) {
      return;
    }

    const draftKey = form.dataset.draftKey;
    const currentRevision = form.dataset.currentRevision;
    const hasServerValues = form.dataset.serverValues === "true";
    const status = document.querySelector("[data-draft-status]");
    const recoverButton = document.querySelector("[data-recover-draft]");
    const discardButton = document.querySelector("[data-discard-draft]");
    const fields = Array.from(form.querySelectorAll("[data-draft-field]"));
    const expectedRevision = form.querySelector('input[name="expected_revision"]');
    const cancelHref = form.dataset.cancelHref;
    let saveTimer;
    let dirty = false;

    if (!draftKey || !currentRevision || !expectedRevision) {
      return;
    }

    const serverValues = {};
    for (const field of fields) {
      serverValues[field.name] = readField(field);
    }

    function setStatus(message) {
      if (status) {
        status.textContent = message;
      }
    }

    function showDiscard(show) {
      if (discardButton) {
        discardButton.hidden = !show;
      }
    }

    function captureDraft() {
      const values = {};
      for (const field of fields) {
        values[field.name] = readField(field);
      }
      return {
        baseRevision: expectedRevision.value,
        savedAt: new Date().toISOString(),
        values,
      };
    }

    function persistDraft() {
      const stored = writeStoredValue(draftKey, JSON.stringify(captureDraft()));
      setStatus(
        stored
          ? "Draft saved in this browser."
          : `Browser draft storage is unavailable; use ${form.dataset.saveLabel || "Save"} to commit your work.`,
      );
      showDiscard(stored);
    }

    function scheduleDraft() {
      dirty = true;
      setStatus("Saving browser draft…");
      window.clearTimeout(saveTimer);
      saveTimer = window.setTimeout(persistDraft, 250);
    }

    function applyDraft(draft, message) {
      for (const field of fields) {
        if (Object.hasOwn(draft.values, field.name)) {
          writeField(field, draft.values[field.name]);
        }
      }
      dirty = true;
      setStatus(message);
      showDiscard(true);
    }

    function restoreServerValues() {
      for (const field of fields) {
        writeField(field, serverValues[field.name]);
      }
      if (!hasServerValues) {
        expectedRevision.value = currentRevision;
        dirty = false;
      }
      removeStoredValue(draftKey);
      showDiscard(false);
      if (recoverButton) {
        recoverButton.hidden = true;
      }
      setStatus(
        hasServerValues
          ? "Browser draft discarded. The server-rendered submission remains unchanged."
          : "Browser draft discarded. The loaded project values are shown.",
      );
    }

    function parseStoredDraft() {
      const stored = readStoredValue(draftKey);
      if (!stored) {
        return null;
      }
      try {
        const draft = JSON.parse(stored);
        if (!draft || typeof draft !== "object" || !draft.values) {
          throw new Error("Invalid draft");
        }
        return draft;
      } catch (_error) {
        removeStoredValue(draftKey);
        return null;
      }
    }

    const draft = parseStoredDraft();
    if (draft) {
      showDiscard(true);
    }
    if (draft && !hasServerValues) {
      if (draft.baseRevision === currentRevision) {
        applyDraft(draft, "Recovered an unsaved browser draft.");
      } else {
        setStatus("An unsaved draft from an older project revision is available.");
        if (recoverButton) {
          recoverButton.hidden = false;
          recoverButton.addEventListener("click", () => {
            applyDraft(
              draft,
              "Recovered the older draft onto the current revision. Review before saving.",
            );
            expectedRevision.value = currentRevision;
            recoverButton.hidden = true;
            persistDraft();
          });
        }
      }
    }

    if (discardButton) {
      discardButton.addEventListener("click", restoreServerValues);
    }

    for (const field of fields) {
      field.addEventListener("input", scheduleDraft);
      field.addEventListener("change", scheduleDraft);
    }

    document.addEventListener("keydown", (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
        event.preventDefault();
        window.clearTimeout(saveTimer);
        persistDraft();
        form.requestSubmit();
      }
      if (event.key === "Escape" && cancelHref && document.activeElement?.closest("[data-authoring-form]")) {
        event.preventDefault();
        window.clearTimeout(saveTimer);
        if (dirty) {
          persistDraft();
        }
        window.location.assign(cancelHref);
      }
    });

    form.addEventListener("submit", () => {
      window.clearTimeout(saveTimer);
      persistDraft();
    });

    window.addEventListener("storage", (event) => {
      if (event.key === draftKey && event.newValue !== event.oldValue) {
        setStatus("This draft changed in another tab. Reload to review that version.");
      }
    });

    const targetId = decodeURIComponent(window.location.hash.slice(1));
    const target = targetId ? document.getElementById(targetId) : null;
    if (target && form.contains(target)) {
      window.requestAnimationFrame(() => {
        target.focus({ preventScroll: true });
        target.scrollIntoView({ behavior: "smooth", block: "center" });
        if (typeof target.setSelectionRange === "function") {
          const end = target.value.length;
          target.setSelectionRange(end, end);
        }
      });
    }
  }


  function initializeDisclosures() {
    const disclosures = Array.from(document.querySelectorAll("[data-ui-disclosure]"));
    for (const disclosure of disclosures) {
      const toggle = disclosure.querySelector("[data-ui-disclosure-toggle]");
      const content = disclosure.querySelector("[data-ui-disclosure-content]");
      if (!toggle || !content) {
        continue;
      }
      const storageKey = disclosure.dataset.disclosureStorageKey || "";
      const defaultExpanded = disclosure.dataset.disclosureDefault !== "collapsed";
      const storedPreference = storageKey ? readStoredValue(storageKey) : null;
      let preferredExpanded =
        storedPreference === "expanded"
          ? true
          : storedPreference === "collapsed"
            ? false
            : defaultExpanded;
      let expanded = preferredExpanded;

      function applyDisclosure(nextExpanded, { persist = false, updatePreference = false } = {}) {
        expanded = Boolean(nextExpanded);
        disclosure.classList.toggle("is-expanded", expanded);
        toggle.setAttribute("aria-expanded", String(expanded));
        content.hidden = !expanded;
        if (updatePreference) {
          preferredExpanded = expanded;
        }
        if (persist && storageKey) {
          writeStoredValue(storageKey, expanded ? "expanded" : "collapsed");
        }
      }

      function togglePreferredDisclosure() {
        applyDisclosure(!expanded, { persist: true, updatePreference: true });
      }

      toggle.addEventListener("click", togglePreferredDisclosure);
      disclosure.addEventListener("adventure-graph:disclosure", (event) => {
        const detail = event.detail || {};
        if (detail.reset) {
          applyDisclosure(preferredExpanded);
        } else if (typeof detail.expanded === "boolean") {
          applyDisclosure(detail.expanded);
        }
      });
      applyDisclosure(expanded);
    }
  }

  function overrideDisclosure(disclosure, expanded) {
    disclosure.dispatchEvent(
      new CustomEvent("adventure-graph:disclosure", { detail: { expanded } }),
    );
  }

  function resetDisclosure(disclosure) {
    disclosure.dispatchEvent(
      new CustomEvent("adventure-graph:disclosure", { detail: { reset: true } }),
    );
  }

  function initializeNavigationFilter() {
    const input = document.querySelector("[data-navigation-filter]");
    const status = document.querySelector("[data-navigation-filter-status]");
    const groups = Array.from(document.querySelectorAll("[data-navigation-group]"));
    if (!input || groups.length === 0) {
      return;
    }

    const items = Array.from(document.querySelectorAll("[data-navigation-item]"));

    function applyFilter() {
      const query = input.value.trim().toLocaleLowerCase();
      let visibleCount = 0;
      for (const group of groups) {
        const groupItems = Array.from(group.querySelectorAll("[data-navigation-item]"));
        let groupVisible = 0;
        for (const item of groupItems) {
          const title = (item.dataset.navigationTitle || item.textContent || "").toLocaleLowerCase();
          const visible = query === "" || title.includes(query);
          item.hidden = !visible;
          if (visible) {
            visibleCount += 1;
            groupVisible += 1;
          }
        }
        const empty = group.querySelector("[data-navigation-group-empty]");
        if (empty) {
          empty.hidden = query === "" || groupVisible > 0;
        }
        if (query === "") {
          resetDisclosure(group);
        } else if (groupVisible > 0) {
          overrideDisclosure(group, true);
        } else {
          resetDisclosure(group);
        }
      }
      if (status) {
        status.textContent = query === "" ? "" : `${visibleCount} matching title${visibleCount === 1 ? "" : "s"}`;
      }
    }

    input.addEventListener("input", applyFilter);
    input.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && input.value) {
        event.preventDefault();
        input.value = "";
        applyFilter();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key !== "/" || event.ctrlKey || event.metaKey || event.altKey) {
        return;
      }
      const active = document.activeElement;
      if (active?.matches("input, textarea, select, [contenteditable='true']")) {
        return;
      }
      event.preventDefault();
      input.focus();
      input.select();
    });

    for (const item of items) {
      item.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && input.value) {
          input.value = "";
          applyFilter();
        }
      });
    }
  }

  function initializeEncounterGraphs() {
    const graphs = Array.from(document.querySelectorAll("[data-encounter-graph]"));
    for (const svg of graphs) {
      const shell = svg.closest("[data-graph-shell]");
      const viewport = shell?.querySelector("[data-graph-viewport]");
      const status = shell?.querySelector("[data-graph-status]");
      const initialValues = (svg.dataset.initialViewBox || "")
        .trim()
        .split(/\s+/)
        .map(Number);
      if (!shell || !viewport || initialValues.length !== 4 || initialValues.some(Number.isNaN)) {
        continue;
      }

      const initial = {
        x: initialValues[0],
        y: initialValues[1],
        width: initialValues[2],
        height: initialValues[3],
      };
      let view = { ...initial };
      let pointerState = null;

      function updateStatus() {
        if (status) {
          const percentage = Math.round((initial.width / view.width) * 100);
          status.textContent = `${percentage}%`;
        }
      }

      function applyView() {
        svg.setAttribute("viewBox", `${view.x} ${view.y} ${view.width} ${view.height}`);
        updateStatus();
      }

      function constrainView() {
        const paddingX = initial.width * 0.3;
        const paddingY = initial.height * 0.3;
        const centerX = Math.min(
          initial.x + initial.width + paddingX,
          Math.max(initial.x - paddingX, view.x + view.width / 2),
        );
        const centerY = Math.min(
          initial.y + initial.height + paddingY,
          Math.max(initial.y - paddingY, view.y + view.height / 2),
        );
        view.x = centerX - view.width / 2;
        view.y = centerY - view.height / 2;
      }

      function zoom(factor, clientX = null, clientY = null) {
        const minimumWidth = initial.width / 4;
        const maximumWidth = initial.width * 1.25;
        const nextWidth = Math.min(maximumWidth, Math.max(minimumWidth, view.width * factor));
        const nextHeight = nextWidth * (initial.height / initial.width);
        const rect = viewport.getBoundingClientRect();
        const proportionX = clientX === null ? 0.5 : (clientX - rect.left) / rect.width;
        const proportionY = clientY === null ? 0.5 : (clientY - rect.top) / rect.height;
        const anchorX = view.x + proportionX * view.width;
        const anchorY = view.y + proportionY * view.height;
        view = {
          x: anchorX - proportionX * nextWidth,
          y: anchorY - proportionY * nextHeight,
          width: nextWidth,
          height: nextHeight,
        };
        constrainView();
        applyView();
      }

      function resetView() {
        view = { ...initial };
        applyView();
      }

      function pan(horizontal, vertical) {
        view.x += horizontal;
        view.y += vertical;
        constrainView();
        applyView();
      }

      shell.querySelector('[data-graph-zoom="in"]')?.addEventListener("click", () => zoom(0.82));
      shell.querySelector('[data-graph-zoom="out"]')?.addEventListener("click", () => zoom(1.22));
      shell.querySelector("[data-graph-reset]")?.addEventListener("click", resetView);

      const expandButton = shell.querySelector("[data-graph-expand]");
      function setExpanded(expanded) {
        shell.classList.toggle("is-expanded", expanded);
        document.body.classList.toggle("has-expanded-graph", expanded);
        if (expandButton) {
          expandButton.setAttribute("aria-pressed", String(expanded));
          expandButton.textContent = expanded ? "Close" : "Expand";
        }
        window.requestAnimationFrame(() => {
          if (expanded) {
            resetView();
          } else {
            resetView();
          }
        });
      }
      expandButton?.addEventListener("click", () => {
        setExpanded(!shell.classList.contains("is-expanded"));
      });
      document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && shell.classList.contains("is-expanded")) {
          event.preventDefault();
          setExpanded(false);
          expandButton?.focus();
        }
      });

      viewport.addEventListener(
        "wheel",
        (event) => {
          event.preventDefault();
          zoom(event.deltaY < 0 ? 0.88 : 1.14, event.clientX, event.clientY);
        },
        { passive: false },
      );

      viewport.addEventListener("pointerdown", (event) => {
        if (event.button !== 0 || event.target.closest?.("a")) {
          return;
        }
        pointerState = {
          pointerId: event.pointerId,
          clientX: event.clientX,
          clientY: event.clientY,
          viewX: view.x,
          viewY: view.y,
        };
        viewport.setPointerCapture(event.pointerId);
        viewport.classList.add("is-panning");
      });

      viewport.addEventListener("pointermove", (event) => {
        if (!pointerState || pointerState.pointerId !== event.pointerId) {
          return;
        }
        const rect = viewport.getBoundingClientRect();
        view.x = pointerState.viewX - ((event.clientX - pointerState.clientX) / rect.width) * view.width;
        view.y = pointerState.viewY - ((event.clientY - pointerState.clientY) / rect.height) * view.height;
        constrainView();
        applyView();
      });

      function endPan(event) {
        if (!pointerState || pointerState.pointerId !== event.pointerId) {
          return;
        }
        if (viewport.hasPointerCapture(event.pointerId)) {
          viewport.releasePointerCapture(event.pointerId);
        }
        pointerState = null;
        viewport.classList.remove("is-panning");
      }

      viewport.addEventListener("pointerup", endPan);
      viewport.addEventListener("pointercancel", endPan);

      viewport.addEventListener("keydown", (event) => {
        const stepX = view.width * 0.08;
        const stepY = view.height * 0.08;
        if (event.key === "+" || event.key === "=") {
          event.preventDefault();
          zoom(0.82);
        } else if (event.key === "-") {
          event.preventDefault();
          zoom(1.22);
        } else if (event.key === "0") {
          event.preventDefault();
          resetView();
        } else if (event.key === "ArrowLeft") {
          event.preventDefault();
          pan(-stepX, 0);
        } else if (event.key === "ArrowRight") {
          event.preventDefault();
          pan(stepX, 0);
        } else if (event.key === "ArrowUp") {
          event.preventDefault();
          pan(0, -stepY);
        } else if (event.key === "ArrowDown") {
          event.preventDefault();
          pan(0, stepY);
        }
      });

      const encounterLinks = Array.from(svg.querySelectorAll("[data-graph-encounter-link]"));
      const encounterShapes = Array.from(svg.querySelectorAll("[data-graph-encounter-id]"));
      const edges = Array.from(svg.querySelectorAll("[data-source-encounter][data-target-encounter]"));

      function clearEncounterFocus() {
        svg.classList.remove("has-encounter-focus");
        for (const encounter of encounterShapes) {
          encounter.classList.remove("is-focused", "is-neighbor");
        }
        for (const edge of edges) {
          edge.classList.remove("is-connected");
        }
      }

      function focusEncounter(encounterId) {
        const neighborIds = new Set();
        svg.classList.add("has-encounter-focus");
        for (const edge of edges) {
          const connected =
            edge.dataset.sourceEncounter === encounterId || edge.dataset.targetEncounter === encounterId;
          edge.classList.toggle("is-connected", connected);
          if (connected) {
            neighborIds.add(edge.dataset.sourceEncounter);
            neighborIds.add(edge.dataset.targetEncounter);
          }
        }
        for (const encounter of encounterShapes) {
          const id = encounter.dataset.graphEncounterId;
          encounter.classList.toggle("is-focused", id === encounterId);
          encounter.classList.toggle("is-neighbor", id !== encounterId && neighborIds.has(id));
        }
      }

      for (const link of encounterLinks) {
        const encounterId = link.dataset.graphEncounterLink;
        if (!encounterId) {
          continue;
        }
        link.addEventListener("mouseenter", () => focusEncounter(encounterId));
        link.addEventListener("mouseleave", clearEncounterFocus);
        link.addEventListener("focus", () => focusEncounter(encounterId));
        link.addEventListener("blur", () => {
          window.requestAnimationFrame(() => {
            if (!svg.contains(document.activeElement)) {
              clearEncounterFocus();
            }
          });
        });
      }

      resetView();
    }
  }

  function clearCommittedDraft() {
    const clearDraftKey = document.body.dataset.clearDraftKey;
    if (!clearDraftKey) {
      return;
    }
    removeStoredValue(clearDraftKey);
    const url = new URL(window.location.href);
    url.searchParams.delete("saved");
    url.searchParams.delete("draft");
    url.searchParams.delete("created");
    window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
  }

  function initializePrintButtons() {
    document.querySelectorAll("[data-print-page]").forEach((button) => {
      button.addEventListener("click", () => window.print());
    });
  }

  function readStoredArray(key) {
    const stored = readStoredValue(key);
    if (!stored) {
      return [];
    }
    try {
      const parsed = JSON.parse(stored);
      return Array.isArray(parsed) ? parsed.filter((value) => typeof value === "string") : [];
    } catch (_error) {
      removeStoredValue(key);
      return [];
    }
  }

  function readStoredPins(key) {
    const stored = readStoredValue(key);
    if (!stored) {
      return [];
    }
    try {
      const parsed = JSON.parse(stored);
      if (!Array.isArray(parsed)) {
        removeStoredValue(key);
        return [];
      }
      const pins = [];
      const keys = new Set();
      for (const value of parsed) {
        let pin = null;
        if (typeof value === "string") {
          pin = { kind: "encounter", id: value };
        } else if (
          value &&
          typeof value === "object" &&
          (value.kind === "encounter" || value.kind === "reference") &&
          typeof value.id === "string"
        ) {
          pin = { kind: value.kind, id: value.id };
        }
        if (!pin) {
          continue;
        }
        const recordKey = `${pin.kind}:${pin.id}`;
        if (!keys.has(recordKey)) {
          keys.add(recordKey);
          pins.push(pin);
        }
      }
      return pins;
    } catch (_error) {
      removeStoredValue(key);
      return [];
    }
  }

  function initializePlaySharedChrome() {
    const body = document.querySelector("[data-play-adventure-id]");
    if (!body) {
      return null;
    }

    const adventureId = body.dataset.playAdventureId;
    const focusedEncounterId = body.dataset.playFocusedEncounterId || "";
    if (!adventureId) {
      return null;
    }

    const itemRecords = new Map();
    const encounterRecords = new Map();
    document.querySelectorAll("[data-play-item-record]").forEach((record) => {
      const kind = record.dataset.playKind;
      const id = record.dataset.playId;
      if ((kind !== "encounter" && kind !== "reference") || !id) {
        return;
      }
      const item = {
        kind,
        id,
        title: record.dataset.title || id,
        summary: record.dataset.summary || "",
        href: record.dataset.href || "/play",
      };
      itemRecords.set(`${kind}:${id}`, item);
      if (kind === "encounter") {
        encounterRecords.set(id, item);
      }
    });

    const pinsKey = `adventure-graph:play:${adventureId}:pins`;
    const recentKey = `adventure-graph:play:${adventureId}:recent-focus`;
    let pins = readStoredPins(pinsKey)
      .filter((pin) => itemRecords.has(`${pin.kind}:${pin.id}`))
      .slice(0, 16);
    writeStoredValue(pinsKey, JSON.stringify(pins));
    let recent = readStoredArray(recentKey).filter((id) => encounterRecords.has(id));
    if (focusedEncounterId && encounterRecords.has(focusedEncounterId)) {
      recent = [focusedEncounterId, ...recent.filter((id) => id !== focusedEncounterId)].slice(0, 12);
      writeStoredValue(recentKey, JSON.stringify(recent));
    }

    const pinButtons = Array.from(document.querySelectorAll("[data-play-pin-toggle]"));
    const pinPanel = document.querySelector("[data-play-pin-panel]");
    const pinList = document.querySelector("[data-play-pin-list]");
    const pinCount = document.querySelector("[data-play-pin-count]");
    const recentPanel = document.querySelector("[data-play-recent-panel]");
    const recentList = document.querySelector("[data-play-recent-list]");

    function pinKey(pin) {
      return `${pin.kind}:${pin.id}`;
    }

    function buttonPin(button) {
      const kind = button.dataset.playPinKind;
      const id = button.dataset.playPinId;
      if ((kind !== "encounter" && kind !== "reference") || !id) {
        return null;
      }
      return { kind, id };
    }

    function playLink(pin, className, removable = false) {
      const record = itemRecords.get(pinKey(pin));
      if (!record) {
        return null;
      }
      const row = document.createElement("div");
      row.className = className;
      const link = document.createElement("a");
      link.href = record.href;
      const strong = document.createElement("strong");
      strong.textContent = record.title;
      const small = document.createElement("small");
      const kindLabel = record.kind === "reference" ? "Reference" : "Encounter";
      small.textContent = record.summary ? `${kindLabel} · ${record.summary}` : kindLabel;
      link.append(strong, small);
      row.append(link);
      if (removable) {
        const button = document.createElement("button");
        button.type = "button";
        button.setAttribute("aria-label", `Unpin ${record.title}`);
        button.textContent = "×";
        button.addEventListener("click", () => {
          pins = pins.filter((value) => pinKey(value) !== pinKey(pin));
          writeStoredValue(pinsKey, JSON.stringify(pins));
          renderPins();
        });
        row.append(button);
      }
      return row;
    }

    function renderPins() {
      if (pinList) {
        pinList.replaceChildren();
        for (const pin of pins) {
          const row = playLink(pin, "play-pin-row", true);
          if (row) {
            pinList.append(row);
          }
        }
      }
      if (pinPanel) {
        pinPanel.hidden = pins.length === 0;
      }
      if (pinCount) {
        pinCount.textContent = String(pins.length);
      }
      for (const button of pinButtons) {
        const pin = buttonPin(button);
        if (!pin) {
          continue;
        }
        const pinned = pins.some((value) => pinKey(value) === pinKey(pin));
        button.setAttribute("aria-pressed", String(pinned));
        const noun = pin.kind === "reference" ? "reference" : "encounter";
        button.textContent = pinned ? `Unpin ${noun}` : `Pin ${noun}`;
      }
    }

    function renderRecent() {
      if (recentList) {
        recentList.replaceChildren();
        for (const id of recent) {
          const row = playLink({ kind: "encounter", id }, "play-recent-row");
          if (row) {
            if (id === focusedEncounterId) {
              row.classList.add("current");
            }
            recentList.append(row);
          }
        }
      }
      if (recentPanel) {
        recentPanel.hidden = recent.length === 0;
      }
    }

    for (const button of pinButtons) {
      const pin = buttonPin(button);
      if (!pin || !itemRecords.has(pinKey(pin))) {
        continue;
      }
      button.addEventListener("click", () => {
        if (pins.some((value) => pinKey(value) === pinKey(pin))) {
          pins = pins.filter((value) => pinKey(value) !== pinKey(pin));
        } else {
          pins = [pin, ...pins.filter((value) => pinKey(value) !== pinKey(pin))].slice(0, 16);
        }
        writeStoredValue(pinsKey, JSON.stringify(pins));
        renderPins();
      });
    }
    renderPins();
    renderRecent();

    const search = document.querySelector("[data-play-search]");
    const searchStatus = document.querySelector("[data-play-search-status]");
    const searchEntries = Array.from(document.querySelectorAll("[data-play-search-entry]"));

    function applyPlaySearch() {
      if (!search) {
        return;
      }
      const query = search.value.trim().toLocaleLowerCase();
      let visible = 0;
      for (const entry of searchEntries) {
        const matches = query.length > 0 && (entry.dataset.searchText || "").includes(query);
        entry.hidden = !matches;
        if (matches) {
          visible += 1;
        }
      }
      if (searchStatus) {
        searchStatus.textContent = query
          ? `${visible} matching item${visible === 1 ? "" : "s"}`
          : "Type to search the adventure.";
      }
    }

    search?.addEventListener("input", applyPlaySearch);
    const encounterPinButton = pinButtons.find(
      (button) =>
        button.dataset.playPinKind === "encounter" &&
        button.dataset.playPinId === focusedEncounterId,
    );
    return { pinButton: encounterPinButton || null, search, applyPlaySearch };
  }

  function initializePlayMode(sharedChrome) {
    const body = document.querySelector(".play-body");
    if (!body) {
      return;
    }

    const adventureId = body.dataset.playAdventureId;
    const focusedEncounterId = body.dataset.playFocusedEncounterId;
    if (!adventureId || !focusedEncounterId) {
      return;
    }

    const scrollRestoreKey = `adventure-graph:play:${adventureId}:scroll-return`;
    const pinButton = sharedChrome?.pinButton || null;
    const search = sharedChrome?.search || null;
    const applyPlaySearch = sharedChrome?.applyPlaySearch || (() => {});

    function writePlayScrollReturn() {
      const sections = {};
      document.querySelectorAll("[data-play-encounter-section-scroll]").forEach((content) => {
        const sectionName = content.dataset.playEncounterSectionScroll;
        if (sectionName) {
          sections[sectionName] = content.scrollTop || 0;
        }
      });
      const values = {
        focusedEncounterId,
        sections,
        route: document.querySelector(".play-route-rail")?.scrollTop || 0,
        utility: document.querySelector(".play-utility-rail")?.scrollTop || 0,
        page: window.scrollY || 0,
      };
      try {
        sessionStorage.setItem(scrollRestoreKey, JSON.stringify(values));
      } catch (_error) {
        // Scroll restoration is a convenience; canonical play state is server-side.
      }
    }

    function restorePlayScrollReturn() {
      let stored = null;
      try {
        stored = sessionStorage.getItem(scrollRestoreKey);
        sessionStorage.removeItem(scrollRestoreKey);
      } catch (_error) {
        return;
      }
      if (!stored) {
        return;
      }
      try {
        const values = JSON.parse(stored);
        if (!values || values.focusedEncounterId !== focusedEncounterId) {
          return;
        }
        window.requestAnimationFrame(() => {
          window.requestAnimationFrame(() => {
            const route = document.querySelector(".play-route-rail");
            const utility = document.querySelector(".play-utility-rail");
            const sections = values.sections && typeof values.sections === "object"
              ? values.sections
              : {};
            document.querySelectorAll("[data-play-encounter-section-scroll]").forEach((content) => {
              const sectionName = content.dataset.playEncounterSectionScroll;
              if (sectionName && Object.prototype.hasOwnProperty.call(sections, sectionName)) {
                content.scrollTop = Number(sections[sectionName]) || 0;
              }
            });
            if (route) route.scrollTop = Number(values.route) || 0;
            if (utility) utility.scrollTop = Number(values.utility) || 0;
            window.scrollTo({ top: Number(values.page) || 0, behavior: "auto" });
          });
        });
      } catch (_error) {
        // Ignore malformed browser-local scroll state.
      }
    }

    const notebook = document.querySelector("[data-play-notebook]");
    const notebookStatus = document.querySelector("[data-play-notebook-status]");
    const clearDraftVisit = body.dataset.playClearDraftVisit;
    if (clearDraftVisit) {
      removeStoredValue(`adventure-graph:play:${adventureId}:visit:${clearDraftVisit}:notebook`);
    }
    if (notebook) {
      const visitNumber = notebook.dataset.playVisitNumber;
      const notebookKey = `adventure-graph:play:${adventureId}:visit:${visitNumber}:notebook`;
      const submitted = notebook.dataset.playSubmitted === "1";
      const stored = readStoredValue(notebookKey);
      if (!submitted && stored !== null) {
        notebook.value = stored;
      } else if (submitted) {
        writeStoredValue(notebookKey, notebook.value);
      }
      const updateNotebookStatus = () => {
        if (notebookStatus) {
          notebookStatus.textContent = notebook.value
            ? "Draft kept in this browser"
            : "Empty notebook draft";
        }
      };
      updateNotebookStatus();
      notebook.addEventListener("input", () => {
        writeStoredValue(notebookKey, notebook.value);
        updateNotebookStatus();
      });
      document.querySelectorAll("[data-play-transition-form]").forEach((form) => {
        form.addEventListener("submit", () => {
          const note = form.querySelector("[data-play-transition-note]");
          if (note) {
            note.value = notebook.value;
          }
        });
      });
    }


    document.querySelectorAll("[data-play-transition-form]").forEach((form) => {
      const destination = form.querySelector("[data-play-transition-destination]");
      const submit = form.querySelector("[data-play-transition-submit]");
      const summary = form.querySelector("[data-play-transition-summary]");
      if (!destination) {
        return;
      }
      const revelationChecks = Array.from(
        form.querySelectorAll('input[name="established_revelation_id"]'),
      );
      const outcomeChecks = Array.from(form.querySelectorAll("[data-play-outcome]"));

      function selectedCount(name) {
        return form.querySelectorAll(`input[name="${name}"]:checked`).length;
      }

      function pluralized(count, singular, plural) {
        return `${count} ${count === 1 ? singular : plural}`;
      }

      function joinSummaryParts(parts) {
        if (parts.length === 1) {
          return parts[0];
        }
        if (parts.length === 2) {
          return `${parts[0]} and ${parts[1]}`;
        }
        return `${parts.slice(0, -1).join(", ")}, and ${parts[parts.length - 1]}`;
      }

      function pendingTransitionSummary() {
        const foundCount = selectedCount("spotted_clue_id");
        const missedCount = selectedCount("missed_clue_id");
        const revelationCount = selectedCount("established_revelation_id");
        const recordedOutcomeCount = foundCount + missedCount + revelationCount;
        const mixedClueBatch =
          foundCount > 0 && missedCount > 0 && foundCount + missedCount >= 3;
        const manyRevelations = revelationCount >= 3;
        const largeUpdate = recordedOutcomeCount >= 5;
        const bundledMove = Boolean(destination.value) && recordedOutcomeCount >= 3;
        if (!mixedClueBatch && !manyRevelations && !largeUpdate && !bundledMove) {
          return "";
        }

        const parts = [];
        if (foundCount) {
          parts.push(`${pluralized(foundCount, "lead", "leads")} found`);
        }
        if (missedCount) {
          parts.push(`${pluralized(missedCount, "lead", "leads")} missed`);
        }
        if (revelationCount) {
          parts.push(
            `${pluralized(revelationCount, "revelation", "revelations")} established`,
          );
        }
        if (destination.value) {
          const destinationTitle = destination.selectedOptions[0]?.dataset.encounterTitle;
          parts.push(`a move to ${destinationTitle || destination.value}`);
        }
        return `This will record: ${joinSummaryParts(parts)}.`;
      }

      function updateTransitionControls() {
        const selected = new Set(
          revelationChecks.filter((input) => input.checked).map((input) => input.value),
        );
        for (const option of destination.options) {
          const requirements = (option.dataset.requiresRevelations || "")
            .split(",")
            .filter(Boolean);
          if (!requirements.length) {
            continue;
          }
          option.disabled = !requirements.some((identifier) => selected.has(identifier));
        }
        if (destination.selectedOptions[0]?.disabled) {
          destination.value = "";
        }
        if (submit) {
          submit.textContent = destination.value
            ? "Save visit and move"
            : "Save outcomes without moving";
        }
        if (summary) {
          const message = pendingTransitionSummary();
          summary.textContent = message;
          summary.hidden = !message;
        }
      }

      outcomeChecks.forEach((input) => {
        input.addEventListener("change", () => {
          if (input.checked) {
            const row = input.closest(".play-transition-row");
            row?.querySelectorAll("[data-play-outcome]").forEach((other) => {
              if (other !== input) {
                other.checked = false;
              }
            });
          }
          updateTransitionControls();
        });
      });
      revelationChecks.forEach((input) => {
        input.addEventListener("change", updateTransitionControls);
      });
      destination.addEventListener("change", updateTransitionControls);
      updateTransitionControls();
    });

    const preserveScrollActions = new Set([
      "/play/clue/found",
      "/play/clue/missed",
      "/play/revelation/establish",
      "/play/revelation/foreclose",
      "/play/revelation/reopen",
      "/play/note",
      "/play/dice/roll",
      "/play/dice/record",
      "/play/unlock",
    ]);
    document.querySelectorAll('form[method="post"]').forEach((form) => {
      const action = new URL(form.action, window.location.href).pathname;
      if (preserveScrollActions.has(action)) {
        form.addEventListener("submit", writePlayScrollReturn);
      }
    });
    restorePlayScrollReturn();

    const diceRecentKey = `adventure-graph:play:${adventureId}:dice-recents`;
    const diceExpression = document.querySelector("[data-play-dice-expression]");
    const diceLabel = document.querySelector("[data-play-dice-label]");
    const diceRecentList = document.querySelector("[data-play-dice-recents]");
    const diceResult = document.querySelector("[data-play-dice-result]");

    function readDiceRecents() {
      const stored = readStoredValue(diceRecentKey);
      if (!stored) {
        return [];
      }
      try {
        const parsed = JSON.parse(stored);
        if (!Array.isArray(parsed)) {
          return [];
        }
        return parsed
          .filter(
            (entry) =>
              entry &&
              typeof entry === "object" &&
              typeof entry.expression === "string" &&
              typeof entry.label === "string",
          )
          .slice(0, 12);
      } catch (_error) {
        removeStoredValue(diceRecentKey);
        return [];
      }
    }

    let diceRecents = readDiceRecents();
    if (diceResult) {
      const expression = diceResult.dataset.expression || "";
      const label = diceResult.dataset.label || "";
      if (expression) {
        diceRecents = [
          { expression, label },
          ...diceRecents.filter(
            (entry) => entry.expression !== expression || entry.label !== label,
          ),
        ].slice(0, 12);
        writeStoredValue(diceRecentKey, JSON.stringify(diceRecents));
      }
    }

    function renderDiceRecents() {
      if (!diceRecentList) {
        return;
      }
      diceRecentList.replaceChildren();
      if (diceRecents.length === 0) {
        const empty = document.createElement("p");
        empty.className = "play-empty";
        empty.textContent = "Recent expressions stay in this browser.";
        diceRecentList.append(empty);
        return;
      }
      const heading = document.createElement("small");
      heading.textContent = "Recent rolls";
      diceRecentList.append(heading);
      for (const recentRoll of diceRecents) {
        const button = document.createElement("button");
        button.type = "button";
        const expression = document.createElement("strong");
        expression.textContent = recentRoll.expression;
        const label = document.createElement("span");
        label.textContent = recentRoll.label || "Unlabelled";
        button.append(expression, label);
        button.addEventListener("click", () => {
          if (diceExpression) {
            diceExpression.value = recentRoll.expression;
            diceExpression.focus();
            diceExpression.select();
          }
          if (diceLabel) {
            diceLabel.value = recentRoll.label;
          }
        });
        diceRecentList.append(button);
      }
    }

    const insertDice = document.querySelector("[data-play-dice-insert]");
    if (insertDice) {
      if (!notebook) {
        insertDice.disabled = true;
        insertDice.title = "Enter an encounter before inserting rolls in its notebook.";
      } else {
        insertDice.addEventListener("click", () => {
          const addition = diceResult?.dataset.notebookText || "";
          if (!addition) {
            return;
          }
          const separator = notebook.value.trim() ? "\n" : "";
          notebook.value = `${notebook.value}${separator}${addition}`;
          notebook.dispatchEvent(new Event("input", { bubbles: true }));
          notebook.focus();
        });
      }
    }
    renderDiceRecents();

    const drawerButtons = Array.from(document.querySelectorAll("[data-play-drawer-toggle]"));
    const drawers = new Map();
    document.querySelectorAll("[data-play-drawer]").forEach((drawer) => {
      drawers.set(drawer.dataset.playDrawer, drawer);
    });
    const scrim = document.querySelector("[data-play-drawer-close]");
    const mobileDrawerMedia = window.matchMedia("(max-width: 1000px)");
    let activeDrawerButton = null;

    function firstDrawerControl(drawer) {
      return drawer.querySelector(
        'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), ' +
          'select:not([disabled]), summary, [tabindex]:not([tabindex="-1"])',
      );
    }

    function synchronizeDrawerAccessibility() {
      const mobile = mobileDrawerMedia.matches;
      let anyOpen = false;
      for (const drawer of drawers.values()) {
        const open = mobile && drawer.classList.contains("is-open");
        drawer.inert = mobile && !open;
        if (mobile) {
          drawer.setAttribute("aria-hidden", String(!open));
        } else {
          drawer.removeAttribute("aria-hidden");
        }
        anyOpen ||= open;
      }
      if (scrim) {
        scrim.hidden = !anyOpen;
      }
      document.body.classList.toggle("has-play-drawer", anyOpen);
    }

    function closeDrawers({ restoreFocus = true } = {}) {
      const buttonToRestore = activeDrawerButton;
      activeDrawerButton = null;
      for (const drawer of drawers.values()) {
        drawer.classList.remove("is-open");
      }
      for (const button of drawerButtons) {
        button.setAttribute("aria-expanded", "false");
      }
      synchronizeDrawerAccessibility();
      if (restoreFocus && buttonToRestore) {
        window.requestAnimationFrame(() => buttonToRestore.focus({ preventScroll: true }));
      }
    }

    for (const button of drawerButtons) {
      button.addEventListener("click", () => {
        const name = button.dataset.playDrawerToggle;
        const drawer = drawers.get(name);
        if (!drawer || !mobileDrawerMedia.matches) {
          return;
        }
        const opening = !drawer.classList.contains("is-open");
        closeDrawers({ restoreFocus: false });
        if (opening) {
          drawer.classList.add("is-open");
          button.setAttribute("aria-expanded", "true");
          activeDrawerButton = button;
          synchronizeDrawerAccessibility();
          window.requestAnimationFrame(() => {
            firstDrawerControl(drawer)?.focus({ preventScroll: true });
          });
        } else {
          button.focus({ preventScroll: true });
        }
      });
    }
    if (scrim) {
      scrim.addEventListener("click", () => closeDrawers());
    }
    const handleDrawerBreakpoint = () => closeDrawers({ restoreFocus: false });
    if (typeof mobileDrawerMedia.addEventListener === "function") {
      mobileDrawerMedia.addEventListener("change", handleDrawerBreakpoint);
    } else {
      mobileDrawerMedia.addListener(handleDrawerBreakpoint);
    }
    synchronizeDrawerAccessibility();

    const routeLinks = Array.from(document.querySelectorAll("[data-play-route-link]"));

    function lastRouteIndex(predicate) {
      for (let index = routeLinks.length - 1; index >= 0; index -= 1) {
        if (predicate(routeLinks[index])) {
          return index;
        }
      }
      return -1;
    }

    const focusedRouteIndex = lastRouteIndex((link) => link.dataset.encounterId === focusedEncounterId);
    const currentVisitIndex = lastRouteIndex((link) => link.classList.contains("current"));
    const routeCursorIndex =
      focusedRouteIndex >= 0
        ? focusedRouteIndex
        : currentVisitIndex >= 0
          ? currentVisitIndex
          : Math.max(0, routeLinks.length - 1);

    function navigateRoute(offset) {
      if (routeLinks.length === 0) {
        return;
      }
      const next = Math.min(routeLinks.length - 1, Math.max(0, routeCursorIndex + offset));
      window.location.assign(routeLinks[next].href);
    }

    document.addEventListener("keydown", (event) => {
      const active = document.activeElement;
      const interacting = active?.matches(
        "input, textarea, select, button, a[href], summary, [contenteditable='true'], [role='button']",
      );
      if (event.key === "Escape") {
        if (search && search.value) {
          event.preventDefault();
          search.value = "";
          applyPlaySearch();
          search.focus();
        } else {
          closeDrawers();
        }
        return;
      }
      if (interacting || event.ctrlKey || event.metaKey || event.altKey) {
        return;
      }
      if (event.key === "/") {
        event.preventDefault();
        search?.focus();
      } else if (event.key.toLocaleLowerCase() === "p") {
        event.preventDefault();
        pinButton?.click();
      } else if (event.key.toLocaleLowerCase() === "g") {
        const current = document.querySelector("[data-play-current-link]");
        if (current) {
          event.preventDefault();
          window.location.assign(current.href);
        }
      } else if (event.key === "[") {
        event.preventDefault();
        navigateRoute(-1);
      } else if (event.key === "]") {
        event.preventDefault();
        navigateRoute(1);
      }
    });
  }

  function initializeAdventureCatalogFilters() {
    const catalog = document.querySelector("[data-adventure-catalog]");
    if (!catalog) {
      return;
    }
    const cards = Array.from(catalog.querySelectorAll("[data-adventure-card]"));
    const search = catalog.querySelector("[data-adventure-filter-search]");
    const genre = catalog.querySelector("[data-adventure-filter-genre]");
    const system = catalog.querySelector("[data-adventure-filter-system]");
    const setting = catalog.querySelector("[data-adventure-filter-setting]");
    const party = catalog.querySelector("[data-adventure-filter-party]");
    const level = catalog.querySelector("[data-adventure-filter-level]");
    const combat = catalog.querySelector("[data-adventure-filter-combat]");
    const clear = catalog.querySelector("[data-adventure-filter-clear]");
    const count = catalog.querySelector("[data-adventure-filter-count]");
    const empty = catalog.querySelector("[data-adventure-filter-empty]");

    function includesFacet(card, attribute, value) {
      if (!value) {
        return true;
      }
      return (card.dataset[attribute] || "").split("|").includes(value);
    }

    function withinRange(card, minimumAttribute, maximumAttribute, rawValue) {
      if (!rawValue) {
        return true;
      }
      const value = Number(rawValue);
      if (!Number.isInteger(value) || value < 1) {
        return true;
      }
      const minimumRaw = card.dataset[minimumAttribute] || "";
      const maximumRaw = card.dataset[maximumAttribute] || "";
      if (!minimumRaw && !maximumRaw) {
        return false;
      }
      const minimum = minimumRaw ? Number(minimumRaw) : Number.NEGATIVE_INFINITY;
      const maximum = maximumRaw ? Number(maximumRaw) : Number.POSITIVE_INFINITY;
      return minimum <= value && value <= maximum;
    }

    function applyFilters() {
      const query = (search?.value || "").trim().toLocaleLowerCase();
      let visible = 0;
      for (const card of cards) {
        const matches =
          (!query || (card.dataset.search || "").includes(query)) &&
          includesFacet(card, "genres", genre?.value || "") &&
          includesFacet(card, "systems", system?.value || "") &&
          includesFacet(card, "settings", setting?.value || "") &&
          withinRange(card, "partyMin", "partyMax", party?.value || "") &&
          withinRange(card, "levelMin", "levelMax", level?.value || "") &&
          (!(combat?.value) || card.dataset.combat === combat.value);
        card.hidden = !matches;
        if (matches) {
          visible += 1;
        }
      }
      if (count) {
        count.textContent = `${visible} of ${cards.length} projects`;
      }
      if (empty) {
        empty.hidden = visible !== 0;
      }
    }

    for (const control of [search, genre, system, setting, party, level, combat]) {
      control?.addEventListener(control === search ? "input" : "change", applyFilters);
      if (control === party || control === level) {
        control?.addEventListener("input", applyFilters);
      }
    }
    clear?.addEventListener("click", () => {
      for (const control of [search, genre, system, setting, party, level, combat]) {
        if (control) {
          control.value = "";
        }
      }
      applyFilters();
      search?.focus();
    });
    applyFilters();
  }

  document.addEventListener("DOMContentLoaded", () => {
    initializeThemeToggle();
    clearCommittedDraft();
    initializeEditableSurfaces();
    initializeAuthoringForm();
    initializeDisclosures();
    initializeNavigationFilter();
    initializeAdventureCatalogFilters();
    initializeEncounterGraphs();
    initializePrintButtons();
    const playChrome = initializePlaySharedChrome();
    initializePlayMode(playChrome);
  });
})();
