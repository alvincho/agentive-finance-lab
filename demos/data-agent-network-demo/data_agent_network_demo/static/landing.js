(function () {
  "use strict";

  var tabs = Array.from(document.querySelectorAll('[role="tab"]'));
  var panels = Array.from(document.querySelectorAll('[role="tabpanel"]'));
  var disclosures = Array.from(document.querySelectorAll(".guide-tree__toggle"));
  var demoTree = document.querySelector("[data-demo-tree]");
  var aliases = {
    frameworks: "prompits",
    demo: "demos",
    "single-source": "demos",
    "multiple-sources": "demos-multiple",
    "real-data": "demos-real",
  };

  function isDemoPanel(panelId) {
    return panelId === "demos" || panelId === "demos-multiple" || panelId === "demos-real";
  }

  function tabForPanel(panelId) {
    return tabs.find(function (tab) {
      return tab.getAttribute("aria-controls") === panelId;
    });
  }

  function panelIdFromHash() {
    var rawId = window.location.hash.replace(/^#/, "");
    var decodedId;
    try {
      decodedId = decodeURIComponent(rawId);
    } catch (_error) {
      decodedId = rawId;
    }
    return aliases[decodedId] || decodedId;
  }

  function setDisclosure(toggle, expanded) {
    var children = document.getElementById(toggle.getAttribute("aria-controls"));
    toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
    if (children) {
      children.hidden = !expanded;
    }
  }

  function revealDemoPath() {
    disclosures.forEach(function (toggle) {
      setDisclosure(toggle, true);
    });
  }

  function activateTab(tab, options) {
    if (!tab) {
      return;
    }

    var settings = options || {};
    var panelId = tab.getAttribute("aria-controls");

    if (isDemoPanel(panelId)) {
      revealDemoPath();
    }
    if (demoTree) {
      demoTree.classList.toggle("is-active", isDemoPanel(panelId));
    }

    tabs.forEach(function (candidate) {
      var selected = candidate === tab;
      candidate.setAttribute("aria-selected", selected ? "true" : "false");
      candidate.setAttribute("tabindex", selected ? "0" : "-1");
    });

    panels.forEach(function (panel) {
      panel.hidden = panel.id !== panelId;
    });

    if (settings.focus) {
      tab.focus();
    }

    if (settings.updateHistory && window.location.hash !== "#" + panelId) {
      window.history.pushState(null, "", "#" + panelId);
    }

    if (settings.revealPanel) {
      window.requestAnimationFrame(function () {
        var panel = document.getElementById(panelId);
        var header = document.querySelector(".site-header");
        if (!panel) {
          return;
        }
        var headerHeight = header ? header.getBoundingClientRect().height : 0;
        var targetTop = window.scrollY + panel.getBoundingClientRect().top - headerHeight - 14;
        var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        window.scrollTo({
          top: Math.max(0, targetTop),
          behavior: reduceMotion ? "auto" : "smooth",
        });
      });
    }
  }

  disclosures.forEach(function (toggle) {
    toggle.addEventListener("click", function () {
      setDisclosure(toggle, toggle.getAttribute("aria-expanded") !== "true");
    });
  });

  tabs.forEach(function (tab, index) {
    tab.addEventListener("click", function () {
      activateTab(tab, { focus: true, updateHistory: true, revealPanel: true });
    });

    tab.addEventListener("keydown", function (event) {
      var nextIndex = null;

      if (event.key === "ArrowDown" || event.key === "ArrowRight") {
        nextIndex = (index + 1) % tabs.length;
      } else if (event.key === "ArrowUp" || event.key === "ArrowLeft") {
        nextIndex = (index - 1 + tabs.length) % tabs.length;
      } else if (event.key === "Home") {
        nextIndex = 0;
      } else if (event.key === "End") {
        nextIndex = tabs.length - 1;
      }

      if (nextIndex === null) {
        return;
      }

      event.preventDefault();
      activateTab(tabs[nextIndex], {
        focus: true,
        updateHistory: true,
        revealPanel: true,
      });
    });
  });

  window.addEventListener("hashchange", function () {
    activateTab(tabForPanel(panelIdFromHash()) || tabs[0], {
      focus: false,
      updateHistory: false,
      revealPanel: true,
    });
  });

  if (window.location.protocol === "file:") {
    var fileNote = document.querySelector("#file-note");
    if (fileNote) {
      fileNote.hidden = false;
    }
    document.querySelectorAll("[data-demo-link]").forEach(function (link) {
      link.href = "http://127.0.0.1:8000" + (link.dataset.demoRoute || "/demos/data-agent-network/");
    });
    document.querySelectorAll("img[data-file-src]").forEach(function (image) {
      image.src = image.dataset.fileSrc;
    });
    document.querySelectorAll("[data-file-href]").forEach(function (link) {
      link.href = link.dataset.fileHref;
    });
    var wordmark = document.querySelector(".wordmark");
    if (wordmark) {
      wordmark.href = "./index.html";
    }
  }

  activateTab(tabForPanel(panelIdFromHash()) || tabs[0], {
    focus: false,
    updateHistory: false,
    revealPanel: Boolean(window.location.hash),
  });
})();
