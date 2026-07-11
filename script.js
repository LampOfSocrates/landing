// Footer year
document.getElementById("year").textContent = new Date().getFullYear();

// ---------- Theme toggle ----------
(function () {
  var root = document.documentElement;
  var btn = document.getElementById("theme-toggle");
  if (!btn) return;

  function apply(theme) {
    root.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
    btn.setAttribute("aria-pressed", theme === "light" ? "true" : "false");
  }

  btn.addEventListener("click", function () {
    var current = root.getAttribute("data-theme") || "dark";
    apply(current === "dark" ? "light" : "dark");
  });
})();

// ---------- Last-commit badges ----------
(function () {
  var cards = document.querySelectorAll(".card[data-repo]");
  if (!cards.length) return;

  var rtf = (typeof Intl !== "undefined" && Intl.RelativeTimeFormat)
    ? new Intl.RelativeTimeFormat("en", { numeric: "auto" })
    : null;

  function relativeTime(then) {
    var diffSec = Math.round((then - Date.now()) / 1000); // negative for past
    var abs = Math.abs(diffSec);
    var units = [
      ["year",   60 * 60 * 24 * 365],
      ["month",  60 * 60 * 24 * 30],
      ["week",   60 * 60 * 24 * 7],
      ["day",    60 * 60 * 24],
      ["hour",   60 * 60],
      ["minute", 60],
    ];
    for (var i = 0; i < units.length; i++) {
      var unit = units[i][0];
      var sec  = units[i][1];
      if (abs >= sec || unit === "minute") {
        var n = Math.round(diffSec / sec);
        if (rtf) return rtf.format(n, unit);
        return Math.abs(n) + " " + unit + (Math.abs(n) === 1 ? "" : "s") + " ago";
      }
    }
    return "just now";
  }

  function injectMeta(card, text, opts) {
    opts = opts || {};
    var meta = document.createElement("p");
    meta.className = "card-meta" + (opts.muted ? " card-meta--muted" : "");
    meta.textContent = text;
    var actions = card.querySelector(".card-actions");
    if (actions) {
      card.querySelector(".card-body").insertBefore(meta, actions);
    } else {
      card.querySelector(".card-body").appendChild(meta);
    }
  }

  // Parse "last page" out of GitHub's Link header.
  // With per_page=1 the total page count == total commit count.
  function commitCountFromLinkHeader(link) {
    if (!link) return null;
    var m = link.match(/[?&]page=(\d+)[^>]*>;\s*rel="last"/);
    return m ? parseInt(m[1], 10) : null;
  }

  // Unauthenticated GitHub API allows 60 req/hr per IP and each load costs
  // one request per card — cache results so reloads don't re-spend the quota.
  var CACHE_TTL = 30 * 60 * 1000;

  function readCache(repo) {
    try {
      var raw = localStorage.getItem("commitCache:" + repo);
      return raw ? JSON.parse(raw) : null;
    } catch (e) { return null; }
  }

  function writeCache(repo, entry) {
    try { localStorage.setItem("commitCache:" + repo, JSON.stringify(entry)); } catch (e) {}
  }

  function renderCommit(card, dateStr, count) {
    var when = new Date(dateStr).getTime();
    card.dataset.commitTs = String(when);
    // Highly active: last commit within 14 days → amber in list view.
    if (Date.now() - when <= 14 * 24 * 60 * 60 * 1000) {
      card.classList.add("card--hot");
    }
    var existing = card.querySelector(".card-meta");
    if (existing) {
      existing.classList.remove("card-meta--muted");
      existing.innerHTML =
        '<span class="card-meta-dot" aria-hidden="true"></span>' +
        'Updated <time datetime="' + dateStr + '">' + relativeTime(when) + '</time>' +
        '<span class="card-meta-sep">·</span>' +
        '<span class="card-meta-commits">' + count + ' commit' + (count === 1 ? '' : 's') + '</span>';
    }
    document.dispatchEvent(new CustomEvent("cards:commit-loaded"));
  }

  function renderError(card, message) {
    // Unknown commit time → sort to the bottom under "Recent".
    if (!card.dataset.commitTs) card.dataset.commitTs = "0";
    document.dispatchEvent(new CustomEvent("cards:commit-loaded"));
    var existing = card.querySelector(".card-meta");
    if (!existing) return;
    existing.classList.add("card-meta--muted");
    existing.textContent = message;
  }

  cards.forEach(function (card) {
    var repo = card.getAttribute("data-repo");
    // Show a placeholder so layout doesn't jump on slow networks
    injectMeta(card, "Loading commit info…", { muted: true });

    var cached = readCache(repo);
    if (cached && Date.now() - cached.at < CACHE_TTL) {
      if (cached.notFound) {
        renderError(card, "Private repo · commit info hidden");
      } else {
        renderCommit(card, cached.dateStr, cached.count);
      }
      return;
    }

    fetch("https://api.github.com/repos/" + repo + "/commits?per_page=1", {
      headers: { "Accept": "application/vnd.github+json" }
    })
      .then(function (r) {
        if (r.status === 404) throw new Error("not-found");
        if (r.status === 403) throw new Error("rate-limited");
        if (!r.ok) throw new Error("http-" + r.status);
        var count = commitCountFromLinkHeader(r.headers.get("Link"));
        return r.json().then(function (data) { return { data: data, count: count }; });
      })
      .then(function (res) {
        var commit = Array.isArray(res.data) && res.data[0];
        if (!commit) throw new Error("empty");
        var dateStr = commit.commit && commit.commit.committer && commit.commit.committer.date;
        if (!dateStr) throw new Error("no-date");
        // res.count is null when there's a single page (1 commit) — Link header is absent in that case.
        var count = res.count == null ? 1 : res.count;
        writeCache(repo, { dateStr: dateStr, count: count, at: Date.now() });
        renderCommit(card, dateStr, count);
      })
      .catch(function (err) {
        if (err.message === "not-found") {
          // 404s burn quota too — cache them as well.
          writeCache(repo, { notFound: true, at: Date.now() });
          renderError(card, "Private repo · commit info hidden");
        } else if (cached && !cached.notFound) {
          // Stale-if-error: an expired cache entry beats no data.
          renderCommit(card, cached.dateStr, cached.count);
        } else if (err.message === "rate-limited") {
          renderError(card, "GitHub rate-limited — refresh later");
        } else {
          renderError(card, "Commit info unavailable");
        }
      });
  });
})();

// ---------- Sort cards (recent / name) ----------
(function () {
  var grid = document.getElementById("projects");
  // Scope to [data-sort]: the view-toggle buttons share the .sort-btn class for styling.
  var buttons = document.querySelectorAll(".sort-btn[data-sort]");
  if (!grid || !buttons.length) return;

  function cardName(card) {
    var t = card.querySelector(".card-title");
    return (t ? t.textContent : card.getAttribute("data-repo") || "").trim().toLowerCase();
  }

  function cardTime(card) {
    var ts = parseInt(card.dataset.commitTs, 10);
    return isNaN(ts) ? -1 : ts; // not loaded yet / unavailable → bottom for "recent"
  }

  function sortCards(mode) {
    var cards = Array.prototype.slice.call(grid.querySelectorAll(".card"));
    cards.sort(function (a, b) {
      if (mode === "name") return cardName(a).localeCompare(cardName(b));
      var diff = cardTime(b) - cardTime(a); // recent first
      return diff !== 0 ? diff : cardName(a).localeCompare(cardName(b));
    });
    cards.forEach(function (c) { grid.appendChild(c); });
  }

  function setMode(mode) {
    if (mode !== "name") mode = "recent"; // guard against stale/invalid stored values
    buttons.forEach(function (b) {
      var on = b.getAttribute("data-sort") === mode;
      b.classList.toggle("is-active", on);
      b.setAttribute("aria-pressed", on ? "true" : "false");
    });
    localStorage.setItem("sortMode", mode);
    sortCards(mode);
  }

  buttons.forEach(function (b) {
    b.addEventListener("click", function () { setMode(b.getAttribute("data-sort")); });
  });

  // Commit times arrive asynchronously — keep re-sorting while "recent" is active.
  document.addEventListener("cards:commit-loaded", function () {
    if ((localStorage.getItem("sortMode") || "recent") === "recent") sortCards("recent");
  });

  setMode(localStorage.getItem("sortMode") || "recent");
})();

// ---------- View toggle (cards / list) ----------
(function () {
  var grid = document.getElementById("projects");
  var buttons = document.querySelectorAll(".view-btn");
  if (!grid || !buttons.length) return;

  function setView(mode) {
    if (mode !== "list") mode = "cards";
    grid.classList.toggle("projects--list", mode === "list");
    buttons.forEach(function (b) {
      var on = b.getAttribute("data-view") === mode;
      b.classList.toggle("is-active", on);
      b.setAttribute("aria-pressed", on ? "true" : "false");
    });
    localStorage.setItem("viewMode", mode);
  }

  buttons.forEach(function (b) {
    b.addEventListener("click", function () { setView(b.getAttribute("data-view")); });
  });

  setView(localStorage.getItem("viewMode") || "cards");
})();
