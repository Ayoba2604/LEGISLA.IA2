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
const responseMode = document.getElementById('response-mode');
const sourceFilter = document.getElementById('source-filter');
const attachedDocuments = document.getElementById('attached-documents');
const sessionTokenEndpoint = document.querySelector('meta[name="legisla-session-token-url"]')?.content?.trim();

const IA_STATUS_INTERVAL_MS = 30000;
const messagesDiv = document.getElementById('messages');
const inputText = document.getElementById('input-text');
const sendBtn = document.getElementById('send-btn');
const promptChips = document.querySelectorAll('.prompt-chip');
const uploadInput = document.getElementById('pdf-input');

const attachedDocumentIds = [];
let userSessionToken = null;

function buildApiBaseUrl() {
    const metaBase = document.querySelector('meta[name="legisla-api-base-url"]')?.content?.trim();
    const storageBase = window.localStorage.getItem('legisla.apiBaseUrl');
    if (metaBase) return metaBase;
    if (storageBase) return storageBase;

    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
    const host = window.location.hostname || 'localhost';
    return `${protocol}//${host}:8000`;
}

const API_BASE_URL = buildApiBaseUrl();

async function loadSessionToken() {
    if (!sessionTokenEndpoint) return null;

    try {
        const response = await fetch(sessionTokenEndpoint, {
            method: 'GET',
            credentials: 'same-origin'
        });

        if (!response.ok) {
            userSessionToken = null;
            return null;
        }

        const payload = await response.json();
        userSessionToken = payload.token || null;
        return userSessionToken;
    } catch (error) {
        userSessionToken = null;
        return null;
    }
}

function buildAuthHeaders(initialHeaders = {}) {
    const headers = { ...initialHeaders };
    if (userSessionToken) {
        headers['X-Legisla-User-Token'] = userSessionToken;
    }
    return headers;
}

function escapeHtml(value) {
    return (value || '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}

function setSidebarState(isOpen) {
    if (!sidebar || !openSidebar || !body) return;
    sidebar.classList.toggle('closed', !isOpen);
    body.classList.toggle('sidebar-open', isOpen);
    openSidebar.classList.toggle('hidden', isOpen);
    if (!isOpen && settingsPopover) settingsPopover.hidden = true;
}

function setIaStatus(isOnline, label) {
    if (!iaStatusDot || !iaStatusText) return;
    iaStatusDot.classList.toggle('offline', !isOnline);
    iaStatusText.textContent = label || (isOnline ? 'Online' : 'Offline');
}

function addUserMessage(text) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', 'user-message');
    msgDiv.textContent = text;
    messagesDiv.appendChild(msgDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function addSystemNotice(text) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', 'system-message');
    msgDiv.textContent = text;
    messagesDiv.appendChild(msgDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function renderAssistantResponse(payload) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', 'bot-message', 'assistant-card');

    const confidenceClass = (payload.confidence_level || 'low').toLowerCase();
    const alerts = [];
    if (payload.requires_human_escalation === true) {
        alerts.push(`
            <section class="assistant-alert human-review">
                <strong>ATENCAO: Esta consulta exige revisao por advogado qualificado antes de qualquer acao.</strong>
                <span>Ha risco juridico relevante, urgencia processual ou suporte insuficiente para uso autonomo da resposta.</span>
            </section>
        `);
    }
    if (payload.sufficient_support === false) {
        alerts.push(`
            <section class="assistant-alert support-gap">
                <strong>A IA nao encontrou fontes suficientes para sustentar esta resposta com seguranca.</strong>
                <span>Use a resposta apenas como triagem inicial e confirme a base normativa antes de agir.</span>
            </section>
        `);
    } else if (confidenceClass === 'low') {
        alerts.push(`
            <section class="assistant-alert low-confidence">
                <strong>Confianca baixa.</strong>
                <span>Os sinais de recuperacao e verificacao sugerem necessidade de revisao humana ou complemento documental.</span>
            </section>
        `);
    }
    const sourcesHtml = (payload.fontes_consultadas || [])
        .map((source) => {
            const meta = [];
            if (source.reference_label) meta.push(escapeHtml(source.reference_label));
            if (source.metadata?.tribunal) meta.push(escapeHtml(source.metadata.tribunal));
            return `
                <li class="source-item">
                    <div class="source-title">${escapeHtml(source.title || 'Fonte sem titulo')}</div>
                    <div class="source-meta">${meta.join(' | ')}</div>
                    <blockquote>${escapeHtml(source.quote || '')}</blockquote>
                </li>
            `;
        })
        .join('');

    const limitationsHtml = (payload.limites || [])
        .map((item) => `<li>${escapeHtml(item)}</li>`)
        .join('');

    const stepsHtml = (payload.proximos_passos || [])
        .map((item) => `<li>${escapeHtml(item)}</li>`)
        .join('');

    const citationsHtml = (payload.citacoes || [])
        .map((item) => `<li>${escapeHtml(item)}</li>`)
        .join('');

    msgDiv.innerHTML = `
        <div class="assistant-header">
            <span class="answer-mode">${payload.mode === 'technical' ? 'Modo tecnico' : 'Modo leigo'}</span>
            <span class="confidence-badge ${confidenceClass}">
                Confianca ${Math.round((payload.confidence_score || 0) * 100)}%
            </span>
        </div>
        ${alerts.join('')}
        <section class="assistant-section">
            <h3>Resposta objetiva</h3>
            <p>${escapeHtml(payload.resposta_objetiva || payload.resposta || 'Sem resposta no momento.')}</p>
        </section>
        <section class="assistant-section">
            <h3>Fundamentacao juridica</h3>
            <p>${escapeHtml(payload.fundamentacao_juridica || 'Nao informado.')}</p>
        </section>
        <section class="assistant-section">
            <h3>Citacoes</h3>
            <ul class="assistant-list">${citationsHtml || '<li>Nenhuma citacao estruturada.</li>'}</ul>
        </section>
        <section class="assistant-section">
            <h3>Fontes consultadas</h3>
            <ul class="source-list">${sourcesHtml || '<li class="source-item">Nenhuma fonte listada.</li>'}</ul>
        </section>
        <section class="assistant-grid">
            <div class="assistant-section warning">
                <h3>Limites da resposta</h3>
                <ul class="assistant-list">${limitationsHtml || '<li>Sem limites adicionais informados.</li>'}</ul>
            </div>
            <div class="assistant-section">
                <h3>Proximos passos</h3>
                <ul class="assistant-list">${stepsHtml || '<li>Sem proximos passos informados.</li>'}</ul>
            </div>
        </section>
    `;

    if (payload.debug) {
        const debugDetails = document.createElement('details');
        debugDetails.classList.add('debug-panel');
        debugDetails.innerHTML = `
            <summary>Debug</summary>
            <pre>${escapeHtml(JSON.stringify(payload.debug, null, 2))}</pre>
        `;
        msgDiv.appendChild(debugDetails);
    }

    messagesDiv.appendChild(msgDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function renderAttachedDocuments() {
    if (!attachedDocuments) return;
    if (!attachedDocumentIds.length) {
        attachedDocuments.innerHTML = '<span class="attached-label">Nenhum documento anexado</span>';
        return;
    }

    attachedDocuments.innerHTML = attachedDocumentIds
        .map((documentId) => `<span class="attached-chip">${escapeHtml(documentId)}</span>`)
        .join('');
}

async function checkIaStatus() {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    try {
        const res = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            signal: controller.signal
        });
        setIaStatus(res.ok, res.ok ? 'Online' : 'Instavel');
    } catch (err) {
        setIaStatus(false, 'Offline');
    } finally {
        clearTimeout(timeoutId);
    }
}

async function uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/api/v1/ingestion/upload`, {
        method: 'POST',
        headers: buildAuthHeaders(),
        body: formData
    });

    if (!response.ok) {
        const errorPayload = await response.json().catch(() => ({ detail: 'Falha no upload.' }));
        throw new Error(errorPayload.detail || 'Falha no upload.');
    }

    const data = await response.json();
    attachedDocumentIds.push(data.source_id);
    renderAttachedDocuments();
    addSystemNotice(`Documento anexado: ${file.name}`);
}

function showTyping() {
    const typingMsg = document.createElement('div');
    typingMsg.classList.add('message', 'bot-message');
    typingMsg.textContent = 'Analisando fontes e montando resposta...';
    messagesDiv.appendChild(typingMsg);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return typingMsg;
}

async function enviarPergunta() {
    const texto = inputText?.value.trim();
    if (!texto) return;

    addUserMessage(texto);
    inputText.value = '';
    const typingMsg = showTyping();

    const bodyPayload = {
        question: texto,
        mode: responseMode?.value || 'friendly',
        source_filters: sourceFilter?.value ? [sourceFilter.value] : [],
        user_document_ids: attachedDocumentIds,
        debug: new URLSearchParams(window.location.search).get('debug') === '1'
    };

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/chat/query`, {
            method: 'POST',
            headers: buildAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(bodyPayload)
        });

        if (!response.ok) {
            const errorPayload = await response.json().catch(() => ({ detail: 'Erro ao consultar a IA.' }));
            throw new Error(errorPayload.detail || 'Erro ao consultar a IA.');
        }

        const data = await response.json();
        typingMsg.remove();
        setIaStatus(true, 'Online');
        renderAssistantResponse(data);
    } catch (err) {
        typingMsg.remove();
        setIaStatus(false, 'Offline');
        addSystemNotice(`Erro: ${err.message}`);
    }
}

function novaConversa() {
    if (!messagesDiv) return;
    messagesDiv.innerHTML = '';
}

if (openSidebar && sidebar) {
    openSidebar.onclick = () => setSidebarState(true);
}

if (closeSidebar && sidebar && openSidebar) {
    closeSidebar.onclick = () => setSidebarState(false);
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

if (sendBtn) {
    sendBtn.addEventListener('click', enviarPergunta);
}

if (inputText) {
    inputText.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') enviarPergunta();
    });
}

if (uploadInput) {
    uploadInput.addEventListener('change', async (event) => {
        const file = event.target.files?.[0];
        if (!file) return;

        try {
            await uploadDocument(file);
        } catch (error) {
            addSystemNotice(`Erro no upload: ${error.message}`);
        } finally {
            uploadInput.value = '';
        }
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

window.addEventListener('DOMContentLoaded', async () => {
    await loadSessionToken();
    setSidebarState(window.innerWidth > 1024);
    if (settingsPopover) settingsPopover.hidden = true;
    syncThemeOptions();
    renderAttachedDocuments();
    checkIaStatus();
    setInterval(checkIaStatus, IA_STATUS_INTERVAL_MS);

    const params = new URLSearchParams(window.location.search);
    const question = params.get('q');
    const mode = params.get('mode');

    if (mode && responseMode) {
        responseMode.value = mode;
    }

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
