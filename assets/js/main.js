/* =====================================================================
   Thompson Law STL — site behavior
   Lightweight, dependency-free. Everything degrades gracefully with
   JS disabled (nav links still work, FAQ uses <details> fallback).
   ===================================================================== */
(function () {
  "use strict";
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---- Mobile nav ---- */
  var header = document.querySelector(".header");
  var toggle = document.querySelector(".nav-toggle");
  if (toggle && header) {
    toggle.addEventListener("click", function () {
      var open = header.classList.toggle("nav-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    // Close menu when a link is tapped
    header.querySelectorAll(".mobile-menu a").forEach(function (a) {
      a.addEventListener("click", function () {
        header.classList.remove("nav-open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  /* ---- Sticky header shadow ---- */
  if (header) {
    var onScroll = function () {
      header.classList.toggle("scrolled", window.scrollY > 8);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ---- FAQ accordion (accessible, animated) ---- */
  document.querySelectorAll(".faq-q").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var expanded = btn.getAttribute("aria-expanded") === "true";
      // Close siblings within the same .faq group for a clean accordion
      var group = btn.closest(".faq");
      if (group && !expanded) {
        group.querySelectorAll('.faq-q[aria-expanded="true"]').forEach(function (other) {
          if (other !== btn) other.setAttribute("aria-expanded", "false");
        });
      }
      btn.setAttribute("aria-expanded", expanded ? "false" : "true");
    });
  });

  /* ---- Reveal on scroll ---- */
  var revealEls = document.querySelectorAll(".reveal");
  if (revealEls.length && !reduceMotion && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add("in");
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("in"); });
  }

  /* ---- Current year in footers ---- */
  document.querySelectorAll("[data-year]").forEach(function (el) {
    el.textContent = new Date().getFullYear();
  });

  /* =====================================================================
     Intake assistant — guided flow (Pillar 04: Conversion Systems)
     A zero-backend qualifier: engages instantly, narrows the matter,
     then routes the visitor to call or request a free consultation.
     ===================================================================== */
  var fab = document.getElementById("intakeFab");
  var panel = document.getElementById("intakePanel");
  if (fab && panel) {
    var body = panel.querySelector(".intake-body");
    var closeBtn = panel.querySelector(".intake-close");
    var started = false;

    var PHONE = "314-650-8520";
    var PHONE_HREF = "tel:+13146508520";

    // Decision tree. Each node: bot line + option buttons -> next node id.
    var TREE = {
      start: {
        bot: "Hi, I'm here to help. Thompson Law offers free, no-obligation consultations — what happened?",
        opts: [
          { t: "Car or truck accident", go: "injured" },
          { t: "Motorcycle accident", go: "injured" },
          { t: "Slip, fall or dog bite", go: "injured" },
          { t: "Workplace injury", go: "injured" },
          { t: "Lost a loved one", go: "wd" },
          { t: "Something else", go: "other" }
        ]
      },
      injured: {
        bot: "I'm sorry that happened. Were you or a family member injured?",
        opts: [
          { t: "Yes, there were injuries", go: "recent" },
          { t: "Not sure yet", go: "recent" },
          { t: "Mostly property damage", go: "recent" }
        ]
      },
      wd: {
        bot: "I'm very sorry for your loss. These cases are time-sensitive, and we handle them with care. When did it happen?",
        opts: [
          { t: "Within the last year", go: "handoff" },
          { t: "More than a year ago", go: "handoff" }
        ]
      },
      other: {
        bot: "No problem — Tyler reviews every situation personally. The fastest way to get answers is a quick, free call.",
        opts: [{ t: "Okay, what's next?", go: "handoff" }]
      },
      recent: {
        bot: "Got it. Have you already given a recorded statement to the insurance company?",
        opts: [
          { t: "No, not yet", go: "good" },
          { t: "Yes, I have", go: "good" }
        ]
      },
      good: {
        bot: "Thanks — that's exactly the kind of detail Tyler will want to walk through with you. There's no fee unless he wins your case.",
        opts: [{ t: "Great, let's talk", go: "handoff" }]
      }
    };

    function el(tag, cls, html) {
      var n = document.createElement(tag);
      if (cls) n.className = cls;
      if (html != null) n.innerHTML = html;
      return n;
    }
    var BOT_AV = '<span class="bot-av"><svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="4" y="7" width="16" height="11" rx="3" stroke="currentColor" stroke-width="1.6"/><path d="M9 18v2M15 18v2M8 22h8M12 4v3M12 4h0" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><circle cx="9.5" cy="12" r="1" fill="currentColor"/><circle cx="14.5" cy="12" r="1" fill="currentColor"/></svg></span>';

    function scroll() { body.scrollTop = body.scrollHeight; }

    function botSay(text, cb) {
      var typing = el("div", "msg", BOT_AV + '<span class="bubble">…</span>');
      body.appendChild(typing);
      scroll();
      setTimeout(function () {
        typing.querySelector(".bubble").textContent = text;
        scroll();
        if (cb) cb();
      }, reduceMotion ? 60 : 480);
    }

    function showOpts(opts) {
      var wrap = el("div", "opts");
      opts.forEach(function (o) {
        var b = el("button", "opt", o.t);
        b.type = "button";
        b.addEventListener("click", function () {
          // echo user's choice
          body.appendChild(el("div", "msg", '<span class="bubble user">' + o.t + "</span>"));
          wrap.remove();
          scroll();
          go(o.go);
        });
        wrap.appendChild(b);
      });
      body.appendChild(wrap);
      scroll();
    }

    function go(id) {
      if (id === "handoff") return handoff();
      var node = TREE[id];
      botSay(node.bot, function () { showOpts(node.opts); });
    }

    function handoff() {
      botSay("Here's the quickest way to get started — Tyler personally answers:", function () {
        var box = el("div", "", "");
        box.style.cssText = "display:flex;flex-direction:column;gap:10px;padding-left:39px";
        box.innerHTML =
          '<a class="btn btn-primary btn-block" href="' + PHONE_HREF + '">' +
            '<svg viewBox="0 0 24 24" fill="none"><path d="M6.6 10.8a15 15 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.24 11 11 0 0 0 3.5.56 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.3a1 1 0 0 1 1 1 11 11 0 0 0 .56 3.5 1 1 0 0 1-.24 1z" fill="currentColor"/></svg>' +
            'Call ' + PHONE + '</a>' +
          '<a class="btn btn-outline btn-block" href="contact.html">Request a free consultation</a>';
        body.appendChild(box);
        scroll();
      });
    }

    function open() {
      panel.classList.add("open");
      fab.style.display = "none";
      panel.setAttribute("aria-hidden", "false");
      if (!started) { started = true; go("start"); }
      if (closeBtn) closeBtn.focus();
    }
    function close() {
      panel.classList.remove("open");
      fab.style.display = "inline-flex";
      panel.setAttribute("aria-hidden", "true");
      fab.focus();
    }
    fab.addEventListener("click", open);
    if (closeBtn) closeBtn.addEventListener("click", close);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && panel.classList.contains("open")) close();
    });
  }

  /* ---- Contact / hero form: graceful mailto fallback ---- */
  document.querySelectorAll("form[data-intake]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      // If no real endpoint is configured, fall back to a prefilled email
      if (form.getAttribute("action") && form.getAttribute("action").indexOf("http") === 0) return;
      e.preventDefault();
      var fd = new FormData(form);
      var name = (fd.get("name") || "").toString();
      var phone = (fd.get("phone") || "").toString();
      var email = (fd.get("email") || "").toString();
      var msg = (fd.get("message") || "").toString();
      var subject = encodeURIComponent("Free consultation request — " + (name || "Website"));
      var bodyText = encodeURIComponent(
        "Name: " + name + "\nPhone: " + phone + "\nEmail: " + email + "\n\n" + msg
      );
      window.location.href = "mailto:tyler@thompsonlawstl.com?subject=" + subject + "&body=" + bodyText;
      var note = form.querySelector("[data-form-note]");
      if (note) {
        note.textContent = "Opening your email app… or call 314-650-8520 for an immediate response.";
        note.style.color = "var(--green)";
      }
    });
  });
})();
