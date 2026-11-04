// Mentors carousel: prev/next buttons scroll by one card; buttons disable at the ends.
document.addEventListener("DOMContentLoaded", function () {
  var list = document.querySelector("[data-mentors]");
  var prev = document.querySelector("[data-mentors-prev]");
  var next = document.querySelector("[data-mentors-next]");
  if (!list || !prev || !next) return;

  function step() {
    var card = list.querySelector(".mentor");
    if (!card) return list.clientWidth;
    var gap = parseFloat(getComputedStyle(list).columnGap) || 0;
    return card.getBoundingClientRect().width + gap;
  }

  function update() {
    var max = list.scrollWidth - list.clientWidth - 1;
    prev.disabled = list.scrollLeft <= 1;
    next.disabled = list.scrollLeft >= max;
  }

  prev.addEventListener("click", function () { list.scrollBy({ left: -step(), behavior: "smooth" }); });
  next.addEventListener("click", function () { list.scrollBy({ left: step(), behavior: "smooth" }); });
  list.addEventListener("scroll", update, { passive: true });
  window.addEventListener("resize", update);
  update();
});
