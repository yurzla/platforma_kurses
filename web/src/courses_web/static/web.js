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
    var historyPanel = document.getElementById("assistant-history");
    var historyList = document.getElementById("assistant-history-list");
    var backBtn = document.getElementById("assistant-back");

    function openPanel() {
      drawer.classList.add("open");
      drawer.setAttribute("aria-hidden", "false");
      toggle.setAttribute("aria-expanded", "true");
      chatInput.focus();
      refreshHistory();
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

    document.addEventListener("click", function (event) {
      if (!drawer.classList.contains("open")) return;
      if (widget.contains(event.target)) return;
      closePanel();
    });

    function append(role, text) {
      var div = document.createElement("div");
      div.className = "chat-msg " + role;
      if (role === "assistant" && window.renderAssistantAnswer) {
        div.appendChild(window.renderAssistantAnswer(text));
      } else {
        div.textContent = text;
      }
      log.appendChild(div);
      log.scrollTop = log.scrollHeight;
      return div;
    }

    function clearLog() {
      log.innerHTML = "";
    }

    function showChat() {
      if (historyPanel) historyPanel.classList.add("hidden");
      if (backBtn) backBtn.classList.remove("hidden");
      log.classList.remove("hidden");
    }

    async function refreshHistory() {
      if (!historyList) return;
      var url = "/assistant/history";
      if (courseId) url += "?course_id=" + courseId;
      var resp = await fetch(url, {
        headers: { Accept: "text/html" }, credentials: "same-origin",
      });
      if (resp.status === 401) { window.location.href = "/login"; return; }
      if (!resp.ok) return;
      historyList.innerHTML = await resp.text();
    }

    async function ensureSession() {
      if (sessionId) return sessionId;
      var payload = {};
      if (courseId) payload.course_id = courseId;
      var resp = await fetch("/api/v1/chat/sessions", {
        method: "POST", headers: jsonHeaders(), credentials: "same-origin",
        body: JSON.stringify(payload),
      });
      if (resp.status === 401) { window.location.href = "/login"; return null; }
      if (!resp.ok) return null;
      var data = await resp.json();
      sessionId = data.id;
      return sessionId;
    }

    async function loadSession(id) {
      var resp = await fetch("/api/v1/chat/sessions/" + id + "/messages?limit=50", {
        headers: { Accept: "application/json" }, credentials: "same-origin",
      });
      if (resp.status === 401) { window.location.href = "/login"; return; }
      if (!resp.ok) return;
      var messages = await resp.json();
      clearLog();
      messages.forEach(function (message) {
        append(message.role === "user" ? "user" : "assistant", message.content);
      });
      sessionId = id;
      showChat();
    }

    if (historyList) {
      historyList.addEventListener("click", function (event) {
        var btn = event.target.closest(".history-session");
        if (!btn) return;
        loadSession(parseInt(btn.dataset.sessionId, 10));
      });
    }

    if (backBtn) {
      backBtn.addEventListener("click", async function () {
        sessionId = null;
        clearLog();
        log.classList.add("hidden");
        backBtn.classList.add("hidden");
        if (historyPanel) historyPanel.classList.remove("hidden");
        await refreshHistory();
      });
    }

    chatForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      var question = chatInput.value.trim();
      if (!question) return;
      chatInput.value = "";
      showChat();
      append("user", question);
      var placeholder = append("assistant", "…");
      var sid = await ensureSession();
      if (!sid) {
        placeholder.textContent = "Не удалось создать сессию.";
        return;
      }
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
        if (data.status === "done") {
          var answer = data.answer || "";
          node.textContent = "";
          if (window.renderAssistantAnswer) node.appendChild(window.renderAssistantAnswer(answer));
          else node.textContent = answer;
          return;
        }
        if (data.status === "failed") { node.textContent = "Ошибка: " + (data.error || "неизвестно"); return; }
      }
      node.textContent = "Превышено время ожидания ответа.";
    }
  }
})();
