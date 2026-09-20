document.addEventListener("DOMContentLoaded", function () {
  // ---- Mobile main navigation toggle ---------------------------------
  var navToggle = document.querySelector(".nav-toggle");
  var navMenu = document.querySelector(".nav-menu");

  if (navToggle && navMenu) {
    navToggle.addEventListener("click", function () {
      var isOpen = navMenu.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });

    // Close the mobile menu whenever a plain nav link is clicked.
    navMenu.querySelectorAll("a.nav-link").forEach(function (link) {
      link.addEventListener("click", function () {
        navMenu.classList.remove("is-open");
        navToggle.setAttribute("aria-expanded", "false");
      });
    });

    // Portals dropdown toggle on touch/mobile (tap instead of hover).
    document.querySelectorAll(".nav-dropdown > .nav-dropdown-toggle").forEach(function (toggle) {
      toggle.addEventListener("click", function (e) {
        if (window.innerWidth <= 900) {
          e.preventDefault();
          toggle.closest(".nav-dropdown").classList.toggle("is-open");
        }
      });
    });
  }

  // ---- Dashboard sidebar toggle (chairman/coach/transfer portals) ---
  var dashToggle = document.querySelector(".mobile-dash-toggle");
  var dashSidebar = document.querySelector(".dash-sidebar");
  if (dashToggle && dashSidebar) {
    dashToggle.addEventListener("click", function () {
      dashSidebar.classList.toggle("is-open");
    });
  }

  // ---- Smooth scroll for same-page anchor links -----------------
  document.querySelectorAll('a[href^="#"]').forEach(function (link) {
    link.addEventListener("click", function (e) {
      var targetId = link.getAttribute("href");
      if (targetId.length > 1) {
        var target = document.querySelector(targetId);
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }
    });
  });

  // ---- Flash messages: dismiss button + auto-fade ------------------
  document.querySelectorAll(".flash-message").forEach(function (msg) {
    var closeBtn = msg.querySelector("button");
    if (closeBtn) {
      closeBtn.addEventListener("click", function () {
        msg.remove();
      });
    }
    setTimeout(function () {
      if (msg && msg.parentNode) {
        msg.style.transition = "opacity 300ms ease";
        msg.style.opacity = "0";
        setTimeout(function () { msg.remove(); }, 300);
      }
    }, 6000);
  });

  // ---- Simple client-side "required file selected" hint for photo
  // uploads. This is a UX nicety only - the server always re-validates.
  document.querySelectorAll('input[type="file"]').forEach(function (input) {
    input.addEventListener("change", function () {
      var label = document.querySelector('[data-file-label-for="' + input.id + '"]');
      if (label && input.files && input.files.length > 0) {
        label.textContent = input.files[0].name;
      }
    });
  });
});
