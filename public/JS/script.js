/* ======================
   SIDEBAR
====================== */

const sidebar = document.getElementById("sidebar");
const openSidebar = document.getElementById("open-sidebar");
const closeSidebar = document.getElementById("close-sidebar");

openSidebar.onclick = () => {
    sidebar.classList.remove("closed");
    openSidebar.style.display = "none";
};

closeSidebar.onclick = () => {
    sidebar.classList.add("closed");
    openSidebar.style.display = "block";
};

/* ======================
   CHAT
====================== */

const messagesDiv = document.getElementById('messages');
const inputText = document.getElementById('input-text');
const sendBtn = document.getElementById('send-btn');


function addMessage(text, fromUser = true) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', fromUser ? 'user-message' : 'bot-message');
    msgDiv.textContent = text;
    messagesDiv.appendChild(msgDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function novaConversa() {
    messagesDiv.innerHTML = "";
}

/* Enviar pergunta */
async function enviarPergunta() {
    const texto = inputText.value.trim();
    if (!texto) return;

    addMessage(texto, true);
    inputText.value = '';

    const typingMsg = showTyping();

    try {
        const res = await fetch("http://127.0.0.1:8000/perguntar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ texto })
        });

        const data = await res.json();
        typingMsg.remove();

        addMessage(data.resposta || "Sem resposta.", false);

    } catch (err) {
        typingMsg.remove();
        addMessage("Erro: " + err.message, false);
    }
}

function showTyping() {
    const typingMsg = document.createElement('div');
    typingMsg.classList.add('message', 'bot-message');
    typingMsg.textContent = 'Digitando...';
    messagesDiv.appendChild(typingMsg);
    return typingMsg;
}

sendBtn.addEventListener('click', enviarPergunta);

inputText.addEventListener('keydown', e => {
    if (e.key === 'Enter') enviarPergunta();
});
