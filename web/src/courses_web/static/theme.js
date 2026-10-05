(function () {
  var KEY = "theme";

  function current() {
    return document.documentElement.dataset.theme || "dark";
  }

  function label(el, theme) {
    el.textContent = theme === "light" ? "Тёмная" : "Светлая";
    el.setAttribute("aria-pressed", theme === "light" ? "true" : "false");
  }

  function apply(theme) {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem(KEY, theme);
    } catch (e) {}
    document.querySelectorAll("[data-theme-toggle]").forEach(function (el) {
      label(el, theme);
    });
  }

  function toggle() {
    apply(current() === "dark" ? "light" : "dark");
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-theme-toggle]").forEach(function (el) {
      el.addEventListener("click", toggle);
      label(el, current());
    });
  });

  window.toggleTheme = toggle;
})();
