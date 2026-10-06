(function () {
  var step = window.STEP || {};
  var courseId = window.COURSE_ID;

  function jsonHeaders() {
    return { "Content-Type": "application/json", Accept: "application/json" };
  }

  function showResult(text, ok) {
    var el = document.getElementById("answer-result");
    if (!el) return;
    el.textContent = text;
    el.classList.remove("hidden");
    el.classList.toggle("ok", !!ok);
    el.classList.toggle("bad", !ok);
  }

  function buildAnswer(form) {
    if (form.dataset.input === "true") {
      return form.answer.value;
    }
    var checked = Array.prototype.slice
      .call(form.querySelectorAll('input[name="choice"]:checked'))
      .map(function (i) { return Number(i.value); });
    return checked;
  }

  var form = document.getElementById("answer-form");
  if (form) {
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      var resp = await fetch(
        "/api/v1/courses/" + courseId + "/steps/" + step.id + "/answer",
        { method: "POST", headers: jsonHeaders(), credentials: "same-origin",
          body: JSON.stringify({ answer: buildAnswer(form) }) }
      );
      if (resp.status === 401) {
        window.location.href = "/login";
        return;
      }
      var data = await resp.json();
      if (!data.is_correct && data.correct_answer !== undefined && data.correct_answer !== null) {
        showResult("Неверно. Правильный ответ: " + JSON.stringify(data.correct_answer), false);
      } else if (data.is_correct) {
        showResult("Верно!", true);
      } else {
        showResult("Ответ сохранён.", false);
      }
    });
  }

  var completeForm = document.getElementById("complete-form");
  if (completeForm) {
    completeForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      var resp = await fetch(
        "/api/v1/courses/" + courseId + "/steps/" + step.id + "/answer",
        { method: "POST", headers: jsonHeaders(), credentials: "same-origin",
          body: JSON.stringify({ answer: null }) }
      );
      if (resp.status === 401) { window.location.href = "/login"; return; }
      showResult("Отмечено выполненным.", true);
    });
  }

  var widget = document.querySelector(".assistant");
  if (widget) {
    var toggle = document.getElementById("assistant-toggle");
    var drawer = document.getElementById("assistant-drawer");
    var closeBtn = document.getElementById("assistant-close");
    var log = document.getElementById("chat-log");
    var chatForm = document.getElementById("chat-form");
    var chatInput = document.getElementById("chat-input");
    var courseId = parseInt(widget.dataset.courseId, 10) || null;
    var sessionId = null;

    function openPanel() {
      drawer.classList.add("open");
      drawer.setAttribute("aria-hidden", "false");
      toggle.setAttribute("aria-expanded", "true");
      chatInput.focus();
    }

    function closePanel() {
      drawer.classList.remove("open");
      drawer.setAttribute("aria-hidden", "true");
      toggle.setAttribute("aria-expanded", "false");
    }

    toggle.addEventListener("click", function () {
      if (drawer.classList.contains("open")) closePanel();
      else openPanel();
    });
    closeBtn.addEventListener("click", closePanel);

    function append(role, text) {
      var div = document.createElement("div");
      div.className = "chat-msg " + role;
      div.textContent = text;
      log.appendChild(div);
      log.scrollTop = log.scrollHeight;
      return div;
    }

    async function ensureSession() {
      if (sessionId) return sessionId;
      if (!courseId) return null;
      var resp = await fetch("/api/v1/chat/sessions", {
        method: "POST", headers: jsonHeaders(), credentials: "same-origin",
        body: JSON.stringify({ course_id: courseId }),
      });
      if (resp.status === 401) { window.location.href = "/login"; return null; }
      if (!resp.ok) return null;
      var data = await resp.json();
      sessionId = data.id;
      return sessionId;
    }

    chatForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      var question = chatInput.value.trim();
      if (!question) return;
      chatInput.value = "";
      append("user", question);
      var placeholder = append("assistant", "…");
      var sid = await ensureSession();
      if (!sid) { placeholder.textContent = "Не удалось создать сессию."; return; }
      var resp = await fetch("/api/v1/chat/sessions/" + sid + "/ask", {
        method: "POST", headers: jsonHeaders(), credentials: "same-origin",
        body: JSON.stringify({ question: question }),
      });
      if (!resp.ok) { placeholder.textContent = "Ошибка постановки вопроса."; return; }
      var job = await resp.json();
      poll(job.job_id, placeholder);
    });

    async function poll(jobId, node) {
      for (var i = 0; i < 120; i++) {
        await new Promise(function (r) { setTimeout(r, 1000); });
        var resp = await fetch("/api/v1/jobs/" + jobId, { headers: { Accept: "application/json" } });
        if (!resp.ok) continue;
        var data = await resp.json();
        if (data.status === "done") { node.textContent = data.answer || ""; return; }
        if (data.status === "failed") { node.textContent = "Ошибка: " + (data.error || "неизвестно"); return; }
      }
      node.textContent = "Превышено время ожидания ответа.";
    }
  }
})();
