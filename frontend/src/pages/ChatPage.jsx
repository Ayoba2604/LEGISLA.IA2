import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { sendQuestion, sendPdf, sendVideoUrl, checkHealth } from '../lib/chatApi'
import { useAuth } from '../lib/auth'
import { getUserInitials } from '../lib/profile'
import { useThemePreference } from '../lib/theme'
import '../styles/chat.css'

const PROMPTS = [
  { icon: 'bi bi-briefcase', title: 'Atestado no trabalho', text: 'Posso faltar ao trabalho com atestado?' },
  { icon: 'bi bi-bag-check', title: 'Compra com defeito', text: 'Quais sao meus direitos?' },
  { icon: 'bi bi-people', title: 'Pensao alimenticia', text: 'Como funciona no Brasil?' },
  { icon: 'bi bi-shield-check', title: 'Demissao sem justa causa', text: 'Quais sao meus direitos?' },
  { icon: 'bi bi-file-earmark-text', title: 'Divorcio', text: 'Como funciona o processo?' },
  { icon: 'bi bi-house', title: 'Direito de vizinhanca', text: 'Barulho excessivo, o que fazer?' },
]

const STATUS_INTERVAL = 30_000
const TYPE_SPEED = 12 // ms per character
const AUTO_SCROLL_THRESHOLD = 64
const CHAT_STORAGE_VERSION = 1
const MAX_STORED_CONVERSATIONS = 12
const MAX_STORED_MESSAGES = 80

function normalizeText(text = '') {
  return String(text).replace(/\s+/g, ' ').trim()
}

function truncateText(text, maxLength) {
  const normalized = normalizeText(text)
  if (!normalized) return ''
  if (normalized.length <= maxLength) return normalized
  return `${normalized.slice(0, Math.max(0, maxLength - 3))}...`
}

function getMessageSummary(message) {
  const text = normalizeText(message?.text)
  if (text) return text
  if (message?.pdf) return `PDF: ${message.pdf}`
  return ''
}

function sanitizeMessages(messages) {
  return messages
    .filter((message) => !message.dots)
    .map(({ id, text, fromUser, pdf }) => ({
      id: String(id),
      text: typeof text === 'string' ? text : '',
      fromUser: Boolean(fromUser),
      ...(pdf ? { pdf } : {}),
    }))
    .filter((message) => message.text || message.pdf)
}

function hydrateStoredMessages(messages) {
  if (!Array.isArray(messages)) return []

  return messages.map((message, index) => ({
    id: message?.id || `stored_${index}`,
    text: typeof message?.text === 'string' ? message.text : '',
    fromUser: Boolean(message?.fromUser),
    ...(message?.pdf ? { pdf: message.pdf } : {}),
    isTyping: false,
  }))
}

function buildConversationTitle(messages) {
  const firstUserMessage = messages.find((message) => message.fromUser && getMessageSummary(message))
  return truncateText(getMessageSummary(firstUserMessage), 44) || 'Nova conversa'
}

function buildConversationPreview(messages) {
  const lastMessage = [...messages].reverse().find((message) => getMessageSummary(message))
  if (!lastMessage) return 'Sem mensagens ainda'

  return `${lastMessage.fromUser ? 'Voce' : 'IA'}: ${truncateText(getMessageSummary(lastMessage), 56)}`
}

function buildConversationStorageKey(userId) {
  return `legisla.chat.v${CHAT_STORAGE_VERSION}:${userId || 'guest'}`
}

function sortConversations(conversations) {
  return [...conversations]
    .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
    .slice(0, MAX_STORED_CONVERSATIONS)
}

function createConversation(seedText = '') {
  const now = new Date().toISOString()
  const summary = truncateText(seedText, 44)

  return {
    id: `conv_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    title: summary || 'Nova conversa',
    preview: summary ? `Voce: ${truncateText(seedText, 56)}` : 'Sem mensagens ainda',
    createdAt: now,
    updatedAt: now,
    messages: [],
  }
}

function readStoredConversations(storageKey) {
  if (typeof window === 'undefined' || !storageKey) return []

  try {
    const raw = window.localStorage.getItem(storageKey)
    if (!raw) return []

    const parsed = JSON.parse(raw)
    const conversations = Array.isArray(parsed)
      ? parsed
      : Array.isArray(parsed?.conversations)
        ? parsed.conversations
        : []

    return sortConversations(
      conversations
        .filter((conversation) => conversation && typeof conversation.id === 'string')
        .map((conversation) => ({
          id: conversation.id,
          title: conversation.title || 'Nova conversa',
          preview: conversation.preview || 'Sem mensagens ainda',
          createdAt: conversation.createdAt || new Date().toISOString(),
          updatedAt: conversation.updatedAt || conversation.createdAt || new Date().toISOString(),
          messages: sanitizeMessages(Array.isArray(conversation.messages) ? conversation.messages : []),
        })),
    )
  } catch {
    return []
  }
}

function formatConversationTime(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''

  const now = new Date()
  const sameDay = date.toDateString() === now.toDateString()

  return sameDay
    ? date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
    : date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
}

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
    .replace(/\n/g, '<br>')
  return h
}

function isYoutubeUrl(text) {
  return /(?:youtube\.com\/watch\?v=|youtu\.be\/)[A-Za-z0-9_-]{11}/.test(text)
}

/* ---------- Typewriter component ---------- */
function TypewriterText({ fullText, onDone, scrollFn }) {
  const [charIndex, setCharIndex] = useState(0)
  const rafRef = useRef(null)
  const lastTimeRef = useRef(0)

  useEffect(() => {
    if (charIndex >= fullText.length) {
      onDone?.()
      return
    }

    const step = (timestamp) => {
      if (!lastTimeRef.current) lastTimeRef.current = timestamp
      const elapsed = timestamp - lastTimeRef.current

      if (elapsed >= TYPE_SPEED) {
        // advance multiple chars if frame was slow
        const chars = Math.max(1, Math.floor(elapsed / TYPE_SPEED))
        setCharIndex((prev) => Math.min(prev + chars, fullText.length))
        lastTimeRef.current = timestamp
        scrollFn?.()
      }

      rafRef.current = requestAnimationFrame(step)
    }

    rafRef.current = requestAnimationFrame(step)
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [charIndex, fullText, onDone, scrollFn])

  const visible = fullText.slice(0, charIndex)

  return (
    <>
      <span dangerouslySetInnerHTML={{ __html: parseMd(visible) }} />
      {charIndex < fullText.length && <span className="typewriter-cursor" />}
    </>
  )
}

export default function ChatPage() {
  const { user, loading } = useAuth()
  const [searchParams] = useSearchParams()
  const [messages, setMessages] = useState([])
  const [conversations, setConversations] = useState([])
  const [activeConversationId, setActiveConversationId] = useState(null)
  const [input, setInput] = useState('')
  const [pdfFile, setPdfFile] = useState(null)
  const [sending, setSending] = useState(false)
  const [online, setOnline] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth > 1024)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [theme, setTheme] = useThemePreference()

  const messagesRef = useRef(null)
  const inputRef = useRef(null)
  const pdfInputRef = useRef(null)
  const initialQuestionSent = useRef(false)
  const autoScrollRef = useRef(true)
  const storageKey = loading ? null : buildConversationStorageKey(user?.id)

  const isNearBottom = useCallback(() => {
    const container = messagesRef.current
    if (!container) return true

    const distanceToBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight

    return distanceToBottom <= AUTO_SCROLL_THRESHOLD
  }, [])

  const forceScrollBottom = useCallback(() => {
    const container = messagesRef.current
    if (!container) return
    container.scrollTop = container.scrollHeight
  }, [])

  const scrollBottom = useCallback(() => {
    if (!autoScrollRef.current) return
    forceScrollBottom()
  }, [forceScrollBottom])

  const enableAutoScroll = useCallback(() => {
    autoScrollRef.current = true
  }, [])

  const ensureActiveConversation = useCallback((seedText = '') => {
    if (activeConversationId) return activeConversationId

    const conversation = createConversation(seedText)
    setActiveConversationId(conversation.id)
    setConversations((prev) => sortConversations([conversation, ...prev]))
    return conversation.id
  }, [activeConversationId])

  const markTyped = useCallback((id) => {
    setMessages((prev) =>
      prev.map((m) => (m.id === id ? { ...m, isTyping: false } : m))
    )
  }, [])

  const addMsg = useCallback((text, fromUser) => {
    setMessages((prev) => [
      ...prev,
      { text, fromUser, id: Date.now() + Math.random(), isTyping: false },
    ])
  }, [])

  const addBotMsg = useCallback((text) => {
    const id = Date.now() + Math.random()
    setMessages((prev) => [...prev, { text, fromUser: false, id, isTyping: true }])
    return id
  }, [])

  const doSend = useCallback(async (texto, pdf) => {
    if (sending) return
    if (!texto && !pdf) return

    ensureActiveConversation(texto || pdf?.name || 'Nova conversa')
    enableAutoScroll()
    setSending(true)

    if (pdf) {
      setMessages((prev) => [
        ...prev,
        { text: texto, fromUser: true, pdf: pdf.name, id: Date.now() + Math.random() },
      ])
    } else {
      addMsg(texto, true)
    }

    setMessages((prev) => [...prev, { dots: true, id: 'dots' }])

    try {
      let data
      if (pdf) {
        data = await sendPdf(pdf, texto)
        setMessages((prev) => prev.filter((m) => !m.dots))
        addBotMsg(data.resumo || 'Nao foi possivel gerar o resumo.')
      } else if (isYoutubeUrl(texto)) {
        data = await sendVideoUrl(texto)
        setMessages((prev) => prev.filter((m) => !m.dots))
        addBotMsg(data.resumo || 'Nao foi possivel gerar o resumo.')
      } else {
        data = await sendQuestion(texto)
        setMessages((prev) => prev.filter((m) => !m.dots))
        addBotMsg(data.resposta || 'Sem resposta no momento.')
      }
      setOnline(true)
    } catch (err) {
      setMessages((prev) => prev.filter((m) => !m.dots))
      addMsg('Erro: ' + err.message, false)
      setOnline(false)
    } finally {
      setSending(false)
    }
  }, [sending, addMsg, addBotMsg, enableAutoScroll, ensureActiveConversation])

  const handleSend = useCallback(() => {
    const texto = input.trim()
    const pdf = pdfFile
    setInput('')
    setPdfFile(null)
    if (pdfInputRef.current) pdfInputRef.current.value = ''
    doSend(texto, pdf)
  }, [input, pdfFile, doSend])

  // Health check
  useEffect(() => {
    checkHealth().then(setOnline)
    const interval = setInterval(() => checkHealth().then(setOnline), STATUS_INTERVAL)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (!storageKey) return

    const storedConversations = readStoredConversations(storageKey)
    setConversations(storedConversations)

    if (storedConversations.length > 0) {
      setActiveConversationId(storedConversations[0].id)
      setMessages(hydrateStoredMessages(storedConversations[0].messages))
    } else {
      setActiveConversationId(null)
      setMessages([])
    }

    setInput('')
    setPdfFile(null)
    if (pdfInputRef.current) pdfInputRef.current.value = ''
  }, [storageKey])

  useEffect(() => {
    if (!storageKey || typeof window === 'undefined') return

    window.localStorage.setItem(
      storageKey,
      JSON.stringify({
        version: CHAT_STORAGE_VERSION,
        conversations,
      }),
    )
  }, [conversations, storageKey])

  useEffect(() => {
    const container = messagesRef.current
    if (!container) return

    const handleScroll = () => {
      autoScrollRef.current = isNearBottom()
    }

    handleScroll()
    container.addEventListener('scroll', handleScroll)
    return () => container.removeEventListener('scroll', handleScroll)
  }, [isNearBottom])

  // Scroll on new messages
  useEffect(scrollBottom, [messages, scrollBottom])

  useEffect(() => {
    if (!activeConversationId) return

    const storedMessages = sanitizeMessages(messages).slice(-MAX_STORED_MESSAGES)

    setConversations((prev) => {
      const currentConversation = prev.find((conversation) => conversation.id === activeConversationId)
      if (!currentConversation) return prev

      const currentPayload = JSON.stringify(currentConversation.messages || [])
      const nextPayload = JSON.stringify(storedMessages)
      if (currentPayload === nextPayload) return prev

      const updatedConversation = {
        ...currentConversation,
        title: buildConversationTitle(storedMessages),
        preview: buildConversationPreview(storedMessages),
        updatedAt: new Date().toISOString(),
        messages: storedMessages,
      }

      return sortConversations([
        updatedConversation,
        ...prev.filter((conversation) => conversation.id !== activeConversationId),
      ])
    })
  }, [messages, activeConversationId])

  // Sidebar responsive
  useEffect(() => {
    let lastDesktop = window.innerWidth > 1024
    const handler = () => {
      const isDesktop = window.innerWidth > 1024
      if (isDesktop !== lastDesktop) {
        setSidebarOpen(isDesktop)
        lastDesktop = isDesktop
      }
    }
    window.addEventListener('resize', handler)
    return () => window.removeEventListener('resize', handler)
  }, [])

  // Initial question from URL
  useEffect(() => {
    if (loading) return

    const q = searchParams.get('q')
    if (q && !initialQuestionSent.current) {
      initialQuestionSent.current = true
      setActiveConversationId(null)
      setMessages([])
      setPdfFile(null)
      if (pdfInputRef.current) pdfInputRef.current.value = ''
      setInput(q)
      setTimeout(() => doSend(q, null), 300)
    }
  }, [searchParams, doSend, loading])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleNewChat = useCallback(() => {
    enableAutoScroll()
    setActiveConversationId(null)
    setMessages([])
    setInput('')
    setPdfFile(null)
    if (pdfInputRef.current) pdfInputRef.current.value = ''
  }, [enableAutoScroll])

  const handleOpenConversation = useCallback((conversationId) => {
    const conversation = conversations.find((item) => item.id === conversationId)
    if (!conversation) return

    enableAutoScroll()
    setActiveConversationId(conversation.id)
    setMessages(hydrateStoredMessages(conversation.messages))
    setInput('')
    setPdfFile(null)
    if (pdfInputRef.current) pdfInputRef.current.value = ''
    requestAnimationFrame(() => {
      forceScrollBottom()
    })
  }, [conversations, enableAutoScroll, forceScrollBottom])

  const showWelcome = messages.length === 0
  const profileName = loading ? 'Carregando sessao' : user?.nome || 'Visitante'
  const profileRole = loading
    ? 'Sincronizando perfil'
    : user?.admin
      ? 'Administrador'
      : user
        ? 'Usuario autenticado'
        : 'Modo visitante'
  const profileInitials = getUserInitials(profileName)
  const chatsLabel = `${conversations.length} chat${conversations.length === 1 ? '' : 's'} salvo${conversations.length === 1 ? '' : 's'}`
  const aiStatusText = online === null
    ? 'Verificando disponibilidade'
    : online
      ? 'Pronta para responder'
      : 'Servico indisponivel agora'

  return (
    <div className="chat-layout">
      {!sidebarOpen && (
        <button
          className="floating-btn"
          onClick={() => setSidebarOpen(true)}
          aria-label="Abrir menu"
        >
          <i className="bi bi-layout-sidebar-inset"></i>
        </button>
      )}

      <aside className={`chat-sidebar${sidebarOpen ? '' : ' closed'}`}>
        <div className="sidebar-top">
          <div className="sidebar-brand">
            <img src="/favicon.svg" alt="Legisla.IA" className="brand-logo" />
            <div>
              <h2>Legisla.IA</h2>
              <span className="brand-tag">Assistente Juridico</span>
            </div>
          </div>
          {sidebarOpen && (
            <button className="close-sidebar-btn" onClick={() => setSidebarOpen(false)}>
              <i className="bi bi-x-lg"></i>
            </button>
          )}
        </div>

        <div className="sidebar-actions">
          <button onClick={handleNewChat}>
            <i className="bi bi-plus-lg"></i> Nova conversa
          </button>
        </div>

        <div className="sidebar-history">
          <small className="history-label">Conversas recentes</small>
          {conversations.length > 0 ? (
            <div className="history-list">
              {conversations.map((conversation) => (
                <button
                  key={conversation.id}
                  type="button"
                  className={`history-item${conversation.id === activeConversationId ? ' active' : ''}`}
                  onClick={() => handleOpenConversation(conversation.id)}
                >
                  <div className="history-item-top">
                    <strong>{conversation.title}</strong>
                    <span className="history-time">{formatConversationTime(conversation.updatedAt)}</span>
                  </div>
                  <span className="history-item-preview">{conversation.preview}</span>
                </button>
              ))}
            </div>
          ) : (
            <div className="history-empty">
              <i className="bi bi-chat-left-text"></i>
              <span>Nenhuma conversa ainda</span>
            </div>
          )}
        </div>

        <div className="sidebar-foot">
          <div className="sidebar-profile-card">
            {user?.fotoUrl ? (
              <img className="profile-avatar-image" src={user.fotoUrl} alt="" />
            ) : (
              <div className="profile-avatar">{profileInitials}</div>
            )}
            <div className="profile-copy">
              <strong>{profileName}</strong>
              <span>{profileRole}</span>
            </div>
          </div>

          <div className="profile-meta">
            <span className="profile-chip">{user?.id ? `ID ${user.id}` : 'Sessao local'}</span>
            <span className="profile-chip">{chatsLabel}</span>
            {user?.admin ? <span className="profile-chip accent">Admin</span> : null}
          </div>

          <div className="assistant-status-card">
            <div className="assistant-status-copy">
              <strong>Status da IA</strong>
              <span>{aiStatusText}</span>
            </div>
            <div className="status-bar">
              <span className={`status-dot${online === false ? ' offline' : ''}`}></span>
              <span>{online === null ? 'Verificando...' : online ? 'Online' : 'Offline'}</span>
            </div>
          </div>

          <button
            className="chat-config-toggle"
            onClick={(e) => { e.stopPropagation(); setSettingsOpen(!settingsOpen) }}
          >
            <span><i className="bi bi-gear"></i> Configuracoes</span>
            <i className={`bi ${settingsOpen ? 'bi-chevron-up' : 'bi-chevron-down'}`}></i>
          </button>

          {settingsOpen && (
            <div className="chat-settings-popover">
              <strong className="chat-settings-title">Preferencias rapidas</strong>
              <div className="chat-theme-options">
                <button
                  type="button"
                  className={`chat-settings-theme-option${theme === 'light' ? ' active' : ''}`}
                  onClick={() => { setTheme('light'); setSettingsOpen(false) }}
                >
                  <i className="bi bi-sun"></i> Claro
                </button>
                <button
                  type="button"
                  className={`chat-settings-theme-option${theme === 'dark' ? ' active' : ''}`}
                  onClick={() => { setTheme('dark'); setSettingsOpen(false) }}
                >
                  <i className="bi bi-moon-stars"></i> Escuro
                </button>
              </div>

              <div className="chat-settings-inline-section">
                <strong>Personalidade</strong>
                <span>Padrao</span>
              </div>

              <div className="chat-settings-inline-section">
                <strong>Outras opcoes</strong>
                <span>Mais ajustes em breve</span>
              </div>

              <Link
                to="/configuracoes?tab=preferencias"
                className="chat-settings-link-button"
                onClick={() => setSettingsOpen(false)}
              >
                <i className="bi bi-sliders"></i> Abrir configuracoes
              </Link>
            </div>
          )}

          <Link to="/" className="back-link">
            <i className="bi bi-arrow-left"></i> Voltar ao inicio
          </Link>
        </div>
      </aside>

      <main className="chat-main">
        <div className="chat-head">
          <div className="chat-head-left">
            <div className="chat-avatar-head-wrap">
              <img src="/favicon.svg" alt="Legisla.IA" className="chat-avatar-head" />
              <span className={`head-status-dot${online === false ? ' offline' : ''}`} />
            </div>
            <div>
              <h1>Assistente Juridico</h1>
              <p>Legisla.IA &mdash; linguagem simples, direito acessivel</p>
            </div>
          </div>
        </div>

        <div className="chat-messages" ref={messagesRef}>
          {showWelcome && (
            <div className="welcome-screen">
              <img src="/favicon.svg" alt="Legisla.IA" className="welcome-logo" />
              <h2>Ola! Sou o Legisla.IA</h2>
              <p>
                Seu assistente juridico com linguagem simples. Pergunte sobre direitos
                trabalhistas, do consumidor, familia e muito mais.
              </p>
              <div className="prompt-grid">
                {PROMPTS.map((p) => (
                  <button
                    key={p.title}
                    className="prompt-card"
                    onClick={() => {
                      const q = p.text.length > 30 ? p.text : `${p.title}: ${p.text}`
                      setInput(q)
                      inputRef.current?.focus()
                    }}
                  >
                    <i className={p.icon}></i>
                    <div>
                      <strong>{p.title}</strong>
                      <span>{p.text}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m) => {
            if (m.dots) {
              return (
                <div key={m.id} className="message-row bot">
                  <div className="msg-avatar bot"><i className="bi bi-stars"></i></div>
                  <div className="message bot-message typing-indicator">
                    <span className="dot"></span>
                    <span className="dot"></span>
                    <span className="dot"></span>
                  </div>
                </div>
              )
            }

            return (
              <div key={m.id} className={`message-row ${m.fromUser ? 'user' : 'bot'}`}>
                <div className={`msg-avatar ${m.fromUser ? 'user' : 'bot'}`}>
                  {m.fromUser ? (
                    user?.fotoUrl ? (
                      <img className="chat-message-avatar-image" src={user.fotoUrl} alt="" />
                    ) : (
                      <span className="chat-message-avatar-fallback">{profileInitials}</span>
                    )
                  ) : (
                    <i className="bi bi-stars"></i>
                  )}
                </div>
                <div className={`message ${m.fromUser ? 'user-message' : 'bot-message'}`}>
                  {m.pdf && (
                    <div className="pdf-card">
                      <i className="bi bi-file-earmark-pdf-fill"></i>
                      <div className="pdf-card-info">
                        <span className="pdf-card-name">{m.pdf}</span>
                        <span className="pdf-card-label">PDF anexado</span>
                      </div>
                    </div>
                  )}
                  {m.fromUser ? (
                    <span>{m.text}</span>
                  ) : m.isTyping ? (
                    <TypewriterText
                      fullText={m.text}
                      onDone={() => markTyped(m.id)}
                      scrollFn={scrollBottom}
                    />
                  ) : (
                    <span dangerouslySetInnerHTML={{ __html: parseMd(m.text) }} />
                  )}
                </div>
              </div>
            )
          })}
        </div>

        <div className="chat-input-area">
          {pdfFile && (
            <div className="pdf-preview">
              <i className="bi bi-file-earmark-pdf-fill"></i>
              <span>{pdfFile.name}</span>
              <button
                type="button"
                onClick={() => {
                  setPdfFile(null)
                  if (pdfInputRef.current) pdfInputRef.current.value = ''
                }}
              >
                <i className="bi bi-x-lg"></i>
              </button>
            </div>
          )}

          <div className="input-row">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Digite sua pergunta juridica..."
              rows={1}
              onInput={(e) => {
                e.target.style.height = 'auto'
                e.target.style.height = Math.min(e.target.scrollHeight, 150) + 'px'
              }}
            />
            <div className="input-actions">
              <label className="icon-btn" title="Anexar PDF">
                <i className="bi bi-paperclip"></i>
                <input
                  ref={pdfInputRef}
                  type="file"
                  accept="application/pdf"
                  style={{ display: 'none' }}
                  onChange={(e) => {
                    if (e.target.files.length) setPdfFile(e.target.files[0])
                  }}
                />
              </label>
              <button onClick={handleSend} title="Enviar" disabled={sending}>
                <i className="bi bi-arrow-up"></i>
              </button>
            </div>
          </div>
          <span className="input-hint">
            Legisla.IA pode cometer erros. Consulte sempre um advogado para orientacao profissional.
          </span>
        </div>
      </main>
    </div>
  )
}
