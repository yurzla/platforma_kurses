(function () {
  var root = document.querySelector("[data-course-tabs]");
  if (!root) return;

  var tabs = Array.prototype.slice.call(root.querySelectorAll(".course-tab"));
  var panels = Array.prototype.slice.call(root.querySelectorAll("[data-panel]"));
  if (!tabs.length || !panels.length) return;

  function activate(name) {
    tabs.forEach(function (tab) {
      var on = tab.dataset.tab === name;
      tab.classList.toggle("active", on);
      tab.setAttribute("aria-selected", on ? "true" : "false");
    });
    panels.forEach(function (panel) {
      panel.classList.toggle("active", panel.dataset.panel === name);
    });
  }

  root.classList.add("tabs-ready");

  tabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      activate(tab.dataset.tab);
    });
  });

  var initial = root.querySelector(".course-tab.active");
  activate(initial ? initial.dataset.tab : tabs[0].dataset.tab);
})();
