document.addEventListener('DOMContentLoaded', function () {
  const toggle = document.getElementById('navToggle');
  const links = document.getElementById('navLinks');
  if (toggle && links) {
    toggle.addEventListener('click', function () {
      links.classList.toggle('open');
    });
  }

  // Themes: dark (away) <-> gold only — auto every 12s + manual button
  const themes = ['dark', 'gold'];
  function applyTheme(next) {
    if (next === 'light') next = 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('jhapa-theme', next); } catch (e) {}
  }
  const themeBtn = document.getElementById('themeToggle');
  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      const cur = document.documentElement.getAttribute('data-theme') || 'dark';
      const idx = themes.indexOf(cur);
      applyTheme(themes[(idx + 1) % themes.length]);
    });
  }
  // Auto switch
  setInterval(function () {
    const cur = document.documentElement.getAttribute('data-theme') || 'dark';
    const idx = themes.indexOf(cur);
    applyTheme(themes[(idx + 1) % themes.length]);
  }, 12000);

  const chatToggle = document.getElementById('chatToggle');
  const chatPanel = document.getElementById('chatPanel');
  const chatMessages = document.getElementById('chatMessages');
  const chatInput = document.getElementById('chatInput');
  const chatSend = document.getElementById('chatSend');
  const chatQuick = document.getElementById('chatQuick');

  function appendMsg(text, who) {
    if (!chatMessages) return;
    const div = document.createElement('div');
    div.className = 'chat-msg ' + who;
    div.textContent = text;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function sendChat(msg) {
    msg = (msg || '').trim();
    if (!msg) return;
    appendMsg(msg, 'user');
    if (chatInput) chatInput.value = '';
    fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg })
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        appendMsg(data.reply || 'Jhapali is thinking…', 'bot');
      })
      .catch(function () {
        appendMsg('Jhapali temporarily offline.', 'bot');
      });
  }

  if (chatToggle && chatPanel) {
    chatToggle.addEventListener('click', function () {
      chatPanel.classList.toggle('open');
    });
  }
  if (chatSend) {
    chatSend.addEventListener('click', function () {
      sendChat(chatInput && chatInput.value);
    });
  }
  if (chatInput) {
    chatInput.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        sendChat(chatInput.value);
      }
    });
  }
  if (chatQuick) {
    chatQuick.querySelectorAll('button').forEach(function (btn) {
      btn.addEventListener('click', function () {
        sendChat(btn.getAttribute('data-msg') || btn.textContent);
      });
    });
  }
});
