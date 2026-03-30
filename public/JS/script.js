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
const welcomeScreen = document.getElementById('welcome-screen');

const API_BASE_URL = window.LEGISLA_API_BASE_URL
    || localStorage.getItem('legisla_api_base_url')
    || `${window.location.protocol === 'https:' ? 'https:' : 'http:'}//${window.location.hostname || '127.0.0.1'}:8000`;
const CHAT_ENDPOINTS = ['/api/v1/chat/query', '/perguntar'];
const IA_STATUS_INTERVAL_MS = 30000;

const messagesDiv = document.getElementById('messages');
const inputText = document.getElementById('input-text');
const sendBtn = document.getElementById('send-btn');
const promptChips = document.querySelectorAll('.prompt-card');
const pdfInput = document.getElementById('pdf-input');
const pdfPreview = document.getElementById('pdf-preview');
const pdfFilename = document.getElementById('pdf-filename');
const pdfRemove = document.getElementById('pdf-remove');

let arquivoPdf = null;

// --- Welcome screen ---

function hideWelcome() {
    if (welcomeScreen) {
        welcomeScreen.style.display = 'none';
    }
}

function showWelcome() {
    if (welcomeScreen) {
        welcomeScreen.style.display = '';
    }
}

// --- Sidebar ---

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

// --- Auto-resize textarea ---

function autoResize() {
    if (!inputText) return;
    inputText.style.height = 'auto';
    inputText.style.height = Math.min(inputText.scrollHeight, 150) + 'px';
}

if (inputText) {
    inputText.addEventListener('input', autoResize);
}

// --- Markdown & typing ---

function parseMd(text) {
    let h = text
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/^### (.+)$/gm, '<h4>$1</h4>')
        .replace(/^## (.+)$/gm, '<h3>$1</h3>')
        .replace(/^# (.+)$/gm, '<h2>$1</h2>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`(.+?)`/g, '<code>$1</code>')
        .replace(/^[-*] (.+)$/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
        .replace(/^---$/gm, '<hr>')
        .replace(/\n/g, '<br>');
    return h;
}

function createMessageRow(text, fromUser = true) {
    const row = document.createElement('div');
    row.classList.add('message-row', fromUser ? 'user' : 'bot');

    const avatar = document.createElement('div');
    avatar.classList.add('msg-avatar', fromUser ? 'user' : 'bot');
    avatar.innerHTML = fromUser
        ? '<i class="bi bi-person-fill"></i>'
        : '<i class="bi bi-stars"></i>';

    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', fromUser ? 'user-message' : 'bot-message');

    row.appendChild(avatar);
    row.appendChild(msgDiv);

    return { row, msgDiv };
}

function addMessage(text, fromUser = true) {
    if (!messagesDiv) return;
    hideWelcome();

    const { row, msgDiv } = createMessageRow(text, fromUser);

    if (fromUser) {
        msgDiv.textContent = text;
        messagesDiv.appendChild(row);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        return;
    }

    msgDiv.innerHTML = '';
    messagesDiv.appendChild(row);
    typeWriter(msgDiv, text);
}

function addPdfMessage(filename, promptText) {
    if (!messagesDiv) return;
    hideWelcome();

    const { row, msgDiv } = createMessageRow('', true);
    msgDiv.classList.add('pdf-msg');

    const card = document.createElement('div');
    card.classList.add('pdf-card');
    card.innerHTML =
        '<i class="bi bi-file-earmark-pdf-fill"></i>' +
        '<div class="pdf-card-info">' +
            '<span class="pdf-card-name">' + filename.replace(/</g, '&lt;') + '</span>' +
            '<span class="pdf-card-label">PDF anexado</span>' +
        '</div>';
    msgDiv.appendChild(card);

    if (promptText) {
        const txt = document.createElement('p');
        txt.classList.add('pdf-msg-text');
        txt.textContent = promptText;
        msgDiv.appendChild(txt);
    }

    messagesDiv.appendChild(row);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function typeWriter(el, text, speed = 12) {
    let i = 0;
    const raw = text;

    function tick() {
        if (i <= raw.length) {
            el.innerHTML = parseMd(raw.slice(0, i));
            i++;
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            requestAnimationFrame(() => setTimeout(tick, speed));
        }
    }
    tick();
}

function showTyping() {
    hideWelcome();
    const row = document.createElement('div');
    row.classList.add('message-row', 'bot');

    const avatar = document.createElement('div');
    avatar.classList.add('msg-avatar', 'bot');
    avatar.innerHTML = '<i class="bi bi-stars"></i>';

    const typingMsg = document.createElement('div');
    typingMsg.classList.add('message', 'bot-message', 'typing-indicator');
    typingMsg.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';

    row.appendChild(avatar);
    row.appendChild(typingMsg);
    messagesDiv.appendChild(row);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return row;
}

// --- PDF attach ---

function mostrarPdfPreview(file) {
    arquivoPdf = file;
    if (pdfFilename) pdfFilename.textContent = file.name;
    if (pdfPreview) pdfPreview.hidden = false;
}

function removerPdf() {
    arquivoPdf = null;
    if (pdfInput) pdfInput.value = '';
    if (pdfPreview) pdfPreview.hidden = true;
    if (pdfFilename) pdfFilename.textContent = '';
}

if (pdfInput) {
    pdfInput.addEventListener('change', () => {
        if (pdfInput.files.length) {
            mostrarPdfPreview(pdfInput.files[0]);
        }
    });
}

if (pdfRemove) {
    pdfRemove.addEventListener('click', removerPdf);
}

// --- Status IA ---

function setIaStatus(isOnline, label) {
    if (!iaStatusDot || !iaStatusText) return;
    iaStatusDot.classList.toggle('offline', !isOnline);
    iaStatusText.textContent = label || (isOnline ? 'Online' : 'Offline');
}

async function checkIaStatus() {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    try {
        const res = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            signal: controller.signal
        });
        setIaStatus(res.ok, res.ok ? 'Online' : 'Offline');
    } catch (err) {
        setIaStatus(false, 'Offline');
    } finally {
        clearTimeout(timeoutId);
    }
}

// --- API calls ---

async function lerRespostaJson(res) {
    const contentType = res.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
        const text = await res.text();
        return { detail: text };
    }
    return res.json();
}

async function enviarPerguntaParaBackend(payload) {
    let lastError = null;

    for (const endpoint of CHAT_ENDPOINTS) {
        try {
            const res = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await lerRespostaJson(res);
            if (res.status === 404) {
                lastError = new Error(`Endpoint indisponivel: ${endpoint}`);
                continue;
            }

            if (!res.ok) {
                throw new Error(data.detail || data.erro || data.mensagem || `Erro HTTP ${res.status}`);
            }

            return data;
        } catch (err) {
            lastError = err;
        }
    }

    throw lastError || new Error('Nenhum endpoint de chat disponivel.');
}

// --- Enviar PDF com prompt ---

async function enviarPdfComPrompt(file, prompt) {
    const formData = new FormData();
    formData.append('file', file);
    if (prompt) formData.append('prompt', prompt);

    const res = await fetch(`${API_BASE_URL}/resumir_pdf`, {
        method: 'POST',
        body: formData
    });

    const data = await lerRespostaJson(res);

    if (!res.ok) {
        throw new Error(data.detail || 'Erro ao processar PDF');
    }

    return data;
}

// --- Enviar mensagem principal ---

function isYoutubeUrl(text) {
    return /(?:youtube\.com\/watch\?v=|youtu\.be\/)[A-Za-z0-9_-]{11}/.test(text);
}

async function enviarPergunta() {
    if (!inputText) return;

    const texto = inputText.value.trim();
    const temPdf = !!arquivoPdf;

    if (!texto && !temPdf) return;

    // Montar mensagem do usuario
    if (temPdf) {
        addPdfMessage(arquivoPdf.name, texto);
    } else {
        addMessage(texto, true);
    }

    inputText.value = '';
    autoResize();
    const pdfFile = arquivoPdf;
    removerPdf();

    // YouTube
    if (!temPdf && isYoutubeUrl(texto)) {
        await resumirVideo(texto);
        return;
    }

    const typingRow = showTyping();

    try {
        let data;

        if (pdfFile) {
            data = await enviarPdfComPrompt(pdfFile, texto);
            setIaStatus(true, 'Online');
            typingRow.remove();
            addMessage(data.resumo || 'Nao foi possivel gerar o resumo.', false);
        } else {
            data = await enviarPerguntaParaBackend({ texto });
            setIaStatus(true, 'Online');
            typingRow.remove();
            addMessage(data.resposta || 'Sem resposta no momento.', false);
        }
    } catch (err) {
        setIaStatus(false, 'Offline');
        typingRow.remove();
        addMessage('Erro: ' + err.message, false);
    }
}

async function resumirVideo(url) {
    const typingRow = showTyping();

    try {
        const res = await fetch(`${API_BASE_URL}/resumir_video`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ link: url })
        });

        const data = await lerRespostaJson(res);
        setIaStatus(true, 'Online');
        typingRow.remove();

        if (!res.ok) {
            addMessage('Erro ao resumir video: ' + (data.detail || 'Erro desconhecido'), false);
            return;
        }

        addMessage(data.resumo || 'Nao foi possivel gerar o resumo.', false);
    } catch (err) {
        setIaStatus(false, 'Offline');
        typingRow.remove();
        addMessage('Erro ao resumir video: ' + err.message, false);
    }
}

// --- Settings ---

function novaConversa() {
    if (!messagesDiv) return;
    // Remove everything except welcome screen
    const children = Array.from(messagesDiv.children);
    children.forEach(child => {
        if (child.id !== 'welcome-screen') child.remove();
    });
    showWelcome();
    removerPdf();
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

settingsThemeOptions.forEach((opt) => {
    opt.addEventListener('click', () => {
        if (!themeToggle) return;
        themeToggle.checked = opt.dataset.theme === 'dark';
        themeToggle.dispatchEvent(new Event('change', { bubbles: true }));
        syncThemeOptions();
        if (settingsPopover) settingsPopover.hidden = true;
    });
});

// --- Event listeners ---

if (sendBtn) {
    sendBtn.addEventListener('click', enviarPergunta);
}

if (inputText) {
    inputText.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            enviarPergunta();
        }
    });
}

promptChips.forEach((chip) => {
    chip.addEventListener('click', () => {
        const prompt = chip.getAttribute('data-prompt') || '';
        if (!inputText) return;
        inputText.value = prompt;
        inputText.focus();
        autoResize();
    });
});

// --- Init ---

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
