// "Read more" toggles on track cards: expands the panel in place.
(function () {
  document.querySelectorAll('[data-track-toggle]').forEach(function (btn) {
    var panel = document.getElementById(btn.getAttribute('aria-controls'));
    var label = btn.querySelector('[data-label]');
    if (!panel) return;
    btn.addEventListener('click', function () {
      var open = btn.getAttribute('aria-expanded') === 'true';
      btn.setAttribute('aria-expanded', String(!open));
      panel.classList.toggle('is-open', !open);
      label.textContent = open ? 'Read more' : 'Read less';
    });
  });
})();
