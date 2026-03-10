const sidebar = document.getElementById('sidebar');
const body = document.body;
const openSidebar = document.getElementById('open-sidebar');
const closeSidebar = document.getElementById('close-sidebar');
const newChatBtn = document.getElementById('new-chat-btn');
const configBtn = document.getElementById('config-btn');
const settingsPopover = document.getElementById('settings-popover');
const settingsThemeOptions = document.querySelectorAll('.settings-theme-option');
const themeToggle = document.getElementById('toggle-theme');
const iaStatusDot = document.getElementById('ia-status-dot');
const iaStatusText = document.getElementById('ia-status-text');

const API_BASE_URL = 'http://192.168.1.63:8000';
const IA_STATUS_INTERVAL_MS = 30000;

const messagesDiv = document.getElementById('messages');
const inputText = document.getElementById('input-text');
const sendBtn = document.getElementById('send-btn');
const promptChips = document.querySelectorAll('.prompt-chip');

function setSidebarState(isOpen) {
    if (!sidebar || !openSidebar || !body) return;
    sidebar.classList.toggle('closed', !isOpen);
    body.classList.toggle('sidebar-open', isOpen);
    openSidebar.classList.toggle('hidden', isOpen);
    if (!isOpen && settingsPopover) settingsPopover.hidden = true;
}

if (openSidebar && sidebar) {
    openSidebar.onclick = () => setSidebarState(true);
}

if (closeSidebar && sidebar && openSidebar) {
    closeSidebar.onclick = () => setSidebarState(false);
}

function addMessage(text, fromUser = true) {
    if (!messagesDiv) return;
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', fromUser ? 'user-message' : 'bot-message');
    msgDiv.textContent = text;
    messagesDiv.appendChild(msgDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function novaConversa() {
    if (!messagesDiv) return;
    messagesDiv.innerHTML = '';
}

if (newChatBtn) {
    newChatBtn.addEventListener('click', novaConversa);
}

if (configBtn) {
    configBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (!settingsPopover) return;
        settingsPopover.hidden = !settingsPopover.hidden;
    });
}

function syncThemeOptions() {
    if (!themeToggle) return;
    settingsThemeOptions.forEach((opt) => {
        const isDark = opt.dataset.theme === 'dark';
        const active = isDark ? themeToggle.checked : !themeToggle.checked;
        opt.classList.toggle('active', active);
    });
}

function setIaStatus(isOnline, label) {
    if (!iaStatusDot || !iaStatusText) return;

    iaStatusDot.classList.toggle('offline', !isOnline);
    iaStatusText.textContent = label || (isOnline ? 'Online' : 'Offline');
}

async function checkIaStatus() {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    try {
        const res = await fetch(`${API_BASE_URL}/docs`, {
            method: 'GET',
            signal: controller.signal
        });

        setIaStatus(res.ok || res.status > 0, 'Online');
    } catch (err) {
        setIaStatus(false, 'Offline');
    } finally {
        clearTimeout(timeoutId);
    }
}

settingsThemeOptions.forEach((opt) => {
    opt.addEventListener('click', () => {
        if (!themeToggle) return;
        themeToggle.checked = opt.dataset.theme === 'dark';
        themeToggle.dispatchEvent(new Event('change', { bubbles: true }));
        syncThemeOptions();
        if (settingsPopover) settingsPopover.hidden = true;
    });
});

async function enviarPergunta() {
    if (!inputText) return;

    const texto = inputText.value.trim();
    if (!texto) return;

    addMessage(texto, true);
    inputText.value = '';

    const typingMsg = showTyping();

    try {
        const res = await fetch(`${API_BASE_URL}/perguntar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ texto })
        });

        setIaStatus(true, 'Online');
        const data = await res.json();
        typingMsg.remove();

        addMessage(data.resposta || 'Sem resposta no momento.', false);
    } catch (err) {
        setIaStatus(false, 'Offline');
        typingMsg.remove();
        addMessage('Erro: ' + err.message, false);
    }
}

function showTyping() {
    const typingMsg = document.createElement('div');
    typingMsg.classList.add('message', 'bot-message');
    typingMsg.textContent = 'Digitando...';
    messagesDiv.appendChild(typingMsg);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return typingMsg;
}

if (sendBtn) {
    sendBtn.addEventListener('click', enviarPergunta);
}

if (inputText) {
    inputText.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') enviarPergunta();
    });
}

promptChips.forEach((chip) => {
    chip.addEventListener('click', () => {
        const prompt = chip.getAttribute('data-prompt') || '';
        if (!inputText) return;
        inputText.value = prompt;
        inputText.focus();
    });
});

window.addEventListener('DOMContentLoaded', () => {
    setSidebarState(window.innerWidth > 1024);
    if (settingsPopover) settingsPopover.hidden = true;
    syncThemeOptions();
    checkIaStatus();
    setInterval(checkIaStatus, IA_STATUS_INTERVAL_MS);

    const params = new URLSearchParams(window.location.search);
    const question = params.get('q');

    if (question && inputText) {
        inputText.value = question;
        enviarPergunta();
    }
});

document.addEventListener('click', (e) => {
    if (!settingsPopover || settingsPopover.hidden) return;
    if (!settingsPopover.contains(e.target) && e.target !== configBtn && !configBtn?.contains(e.target)) {
        settingsPopover.hidden = true;
    }
});

let lastDesktopState = window.innerWidth > 1024;
window.addEventListener('resize', () => {
    const isDesktop = window.innerWidth > 1024;
    if (isDesktop !== lastDesktopState) {
        setSidebarState(isDesktop);
        lastDesktopState = isDesktop;
    }
});
