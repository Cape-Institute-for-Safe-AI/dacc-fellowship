// CISAI site header — nav collapse + hamburger toggle, copied from
// cisai.co assets/js/main.js so the header behaves the same here.
document.addEventListener("DOMContentLoaded", function () {
  var header = document.querySelector(".site-header");
  var inner = document.querySelector(".site-header__inner");
  var logo = document.querySelector(".logo-link");
  var toggle = document.getElementById("nav-toggle");
  var nav = document.getElementById("site-nav");

  // Collapse the nav into the hamburger menu based on measured overflow
  // (i.e. as soon as the tabs would actually start being pushed off
  // screen), rather than a guessed, fixed viewport breakpoint.
  function updateNavCollapse() {
    if (!header || !inner || !logo || !nav) return;

    // Measure against the uncollapsed (full desktop) layout first.
    header.classList.remove("nav-collapsed");
    document.body.classList.remove("nav-collapsed");

    var available = inner.clientWidth;
    var needed = logo.getBoundingClientRect().width + nav.scrollWidth;

    if (needed > available) {
      header.classList.add("nav-collapsed");
      document.body.classList.add("nav-collapsed");
    }
  }

  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var isOpen = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });

    nav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  updateNavCollapse();

  // Only re-evaluate on width changes (mobile address-bar show/hide fires
  // resize with the same width and would flash the menu open).
  var lastWidth = window.innerWidth;
  window.addEventListener("resize", function () {
    var currentWidth = window.innerWidth;
    if (currentWidth !== lastWidth) {
      lastWidth = currentWidth;
      updateNavCollapse();
    }
  });

  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(updateNavCollapse);
  }
});
