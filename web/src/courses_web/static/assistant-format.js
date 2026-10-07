(function () {
  "use strict";

  function isPortalTarget(target) {
    return target.charAt(0) === "/" && target.indexOf("//") === -1;
  }

  function renderInline(text) {
    var span = document.createElement("span");
    var pattern = /(\*\*([^*]+)\*\*|`([^`]+)`|\[([^\]]+)\]\(\s*([^)\s]+)\s*\))/g;
    var last = 0;
    var match;
    while ((match = pattern.exec(text)) !== null) {
      if (match.index > last) {
        span.appendChild(document.createTextNode(text.slice(last, match.index)));
      }
      if (match[2] !== undefined) {
        var strong = document.createElement("strong");
        strong.textContent = match[2];
        span.appendChild(strong);
      } else if (match[3] !== undefined) {
        var code = document.createElement("code");
        code.className = "chat-code-inline";
        code.textContent = match[3];
        span.appendChild(code);
      } else if (isPortalTarget(match[5].trim())) {
        var link = document.createElement("a");
        link.className = "chat-link";
        link.href = match[5].trim();
        link.textContent = match[4];
        span.appendChild(link);
      } else {
        span.appendChild(document.createTextNode(match[0]));
      }
      last = match.index + match[0].length;
    }
    if (last < text.length) {
      span.appendChild(document.createTextNode(text.slice(last)));
    }
    return span;
  }

  function renderAssistantAnswer(text) {
    var value = text || "";
    var frag = document.createDocumentFragment();
    var pattern = /```([^\n`]*)\n?([\s\S]*?)```/g;
    var last = 0;
    var match;
    while ((match = pattern.exec(value)) !== null) {
      if (match.index > last) {
        frag.appendChild(renderInline(value.slice(last, match.index)));
      }
      var pre = document.createElement("pre");
      pre.className = "chat-code";
      var code = document.createElement("code");
      var lang = match[1].trim();
      if (lang) code.className = "lang-" + lang;
      code.textContent = match[2].replace(/\n$/, "");
      pre.appendChild(code);
      frag.appendChild(pre);
      last = match.index + match[0].length;
    }
    if (last < value.length) {
      frag.appendChild(renderInline(value.slice(last)));
    }
    return frag;
  }

  window.renderAssistantAnswer = renderAssistantAnswer;
})();
