(function () {
  document.querySelectorAll(".step-form").forEach(function (form) {
    var type = form.querySelector("[data-step-type]");
    var choices = form.querySelector("[data-choice-fields]");
    var answer = form.querySelector("[data-answer-field]");
    if (!type || !choices || !answer) return;
    function refresh() {
      choices.classList.toggle("hidden", type.value !== "choice");
      answer.classList.toggle("hidden", type.value !== "string" && type.value !== "number");
    }
    type.addEventListener("change", refresh);
    refresh();
  });
}());
