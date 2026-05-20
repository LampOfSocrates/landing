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

  cards.forEach(function (card) {
    var repo = card.getAttribute("data-repo");
    // Show a placeholder so layout doesn't jump on slow networks
    injectMeta(card, "Loading commit info…", { muted: true });

    fetch("https://api.github.com/repos/" + repo + "/commits?per_page=1", {
      headers: { "Accept": "application/vnd.github+json" }
    })
      .then(function (r) {
        if (r.status === 404) throw new Error("not-found");
        if (r.status === 403) throw new Error("rate-limited");
        if (!r.ok) throw new Error("http-" + r.status);
        return r.json();
      })
      .then(function (data) {
        var commit = Array.isArray(data) && data[0];
        if (!commit) throw new Error("empty");
        var dateStr = commit.commit && commit.commit.committer && commit.commit.committer.date;
        if (!dateStr) throw new Error("no-date");
        var when = new Date(dateStr).getTime();
        var msg  = (commit.commit.message || "").split("\n")[0];
        if (msg.length > 60) msg = msg.slice(0, 57) + "…";
        var existing = card.querySelector(".card-meta");
        if (existing) {
          existing.classList.remove("card-meta--muted");
          existing.innerHTML =
            '<span class="card-meta-dot" aria-hidden="true"></span>' +
            'Updated <time datetime="' + dateStr + '">' + relativeTime(when) + '</time>' +
            ' · <span class="card-meta-msg">' + escapeHtml(msg) + '</span>';
        }
      })
      .catch(function (err) {
        var existing = card.querySelector(".card-meta");
        if (!existing) return;
        existing.classList.add("card-meta--muted");
        if (err.message === "not-found") {
          existing.textContent = "Repo not public (yet)";
        } else if (err.message === "rate-limited") {
          existing.textContent = "GitHub rate-limited — refresh later";
        } else {
          existing.textContent = "Commit info unavailable";
        }
      });
  });

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
})();
