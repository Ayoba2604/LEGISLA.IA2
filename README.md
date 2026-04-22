# LEGISLA.IA2

Plataforma de educacao juridica com interface web, autenticacao, painel administrativo e assistente de IA para consultas, resumos e analises juridicas.

## Visao geral

O sistema combina uma camada web tradicional em PHP com um frontend moderno em React e um backend de IA em Python/FastAPI.

## Tecnologias utilizadas

### Backend de IA

- Python 3.13
- FastAPI
- Uvicorn
- Pydantic
- Pydantic Settings
- Python Dotenv
- Python Multipart
- SQLAlchemy
- PyMySQL
- Passlib com bcrypt
- Email Validator

### IA e processamento de linguagem

- Google Gemini via `google-genai`
- spaCy
- Modelo `pt_core_news_sm` quando instalado
- `youtube-transcript-api` para transcricao e resumo de videos
- PyMuPDF para leitura e resumo de PDFs

### Frontend

- React 19
- React DOM
- React Router DOM
- TanStack React Query
- Vite
- ESLint

### Camada web e autenticacao

- PHP puro
- PHP Sessions
- API de autenticacao em PHP
- PDO para acesso a banco na camada PHP

### Banco de dados

- MySQL como banco principal
- SQLite como fallback local no backend da IA

### UI e assets

- Bootstrap Icons
- Bootstrap via CDN em partes legadas da interface

### Ambiente e execucao

- Node.js local embarcado no projeto
- npm
- PowerShell
- Batch (`.bat`)
- Ambiente Windows/WAMP

## Arquitetura do projeto

- `public/`: entrada principal da aplicacao PHP
- `app/`: controllers, models e views da camada PHP
- `frontend/`: aplicacao React compilada com Vite
- `IA/`: API FastAPI, servicos de IA, NLP e acesso a banco
- `routes/`: roteamento da camada PHP
- `venv/`: ambiente virtual Python do projeto

## Setup rapido no terminal

### 1. Instalar o Python

Se o Python 3.13 ainda nao estiver instalado no Windows:

```powershell
winget install --id Python.Python.3.13 -e --scope user --accept-source-agreements --accept-package-agreements
```

Feche e abra o terminal novamente depois da instalacao.

### 2. Criar o ambiente virtual

Na raiz do projeto:

```powershell
cd C:\wamp64\www8\LEGISLA.IA2-main
python -m venv venv
```

### 3. Ativar o venv

No PowerShell:

```powershell
cd C:\wamp64\www8\LEGISLA.IA2-main
Set-ExecutionPolicy -Scope Process Bypass
. .\venv\Scripts\Activate.ps1
python --version
```

No Prompt de Comando (`cmd`):

```cmd
cd /d C:\wamp64\www8\LEGISLA.IA2-main
venv\Scripts\activate.bat
python --version
```

### 4. Instalar as dependencias Python

Com o `venv` ativado:

```powershell
pip install -r requirements.txt
```

## Configuracao do .env

Crie o arquivo `.env` com base no exemplo:

```powershell
cd C:\wamp64\www8\LEGISLA.IA2-main
Copy-Item .env.example .env
notepad .env
```

Preencha pelo menos:

```env
GEMINI_API_KEY=SUA_CHAVE_AQUI
DB_DRIVER=sqlite
DB_NAME=UsuariosLegislaIA
```

Se quiser usar MySQL, ajuste tambem `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` e `DB_PASS`.

## Como ativar a IA

### Rodar backend da IA somente

```powershell
cd C:\wamp64\www8\LEGISLA.IA2-main\IA
..\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

API disponivel em:

```text
http://127.0.0.1:8000
```

### Rodar o projeto pelo script PowerShell

Antes, instale as dependencias do frontend:

```powershell
cd C:\wamp64\www8\LEGISLA.IA2-main\frontend
..\node-v24.14.1-win-x64\npm.cmd install
```

Depois execute:

```powershell
cd C:\wamp64\www8\LEGISLA.IA2-main
Set-ExecutionPolicy -Scope Process Bypass
.\iniciar-um-terminal.ps1
```

Esse script:

- gera o build do frontend
- sobe a API FastAPI
- serve a aplicacao em `http://127.0.0.1:8000`

## Resumo da stack

`PHP + React/Vite + Python/FastAPI + Gemini + spaCy + MySQL/SQLite`
