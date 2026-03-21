# 🚚 Reis Log — LeitorRota v3.0

App PWA de leitura de CEP por câmera com OCR via Google Gemini AI.

---

## 🔑 Como trocar a chave da API Gemini

### Passo 1 — Obter a chave (gratuito)
1. Acesse **aistudio.google.com**
2. Faça login com sua conta Google
3. Clique em **"Get API key"** → **"Create API key"**
4. Copie a chave (começa com `AIzaSy...`)

### Passo 2 — Colocar no app
1. Abra o arquivo `index.html` em qualquer editor de texto
2. Use **Ctrl+F** e busque por: `COLE_SUA_CHAVE_AQUI`
3. Você vai encontrar esta linha:
   ```
   const GEMINI_API_KEY = "AIzaSy_COLE_SUA_CHAVE_AQUI";
   ```
4. Substitua `AIzaSy_COLE_SUA_CHAVE_AQUI` pela sua chave real:
   ```
   const GEMINI_API_KEY = "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXX";
   ```
5. Salve o arquivo
6. Suba o `index.html` atualizado no GitHub/Netlify

### Limites gratuitos Gemini
- **1.500 requisições/dia** — gratuito, sem cartão
- Modelo: `gemini-2.0-flash` (rápido e preciso)
- Sem chave: usa Tesseract local (funciona offline)

---

## 🚀 Deploy GitHub Pages
1. Crie repositório público em github.com
2. Arraste os 4 arquivos: `index.html`, `manifest.json`, `sw.js`, `icon.svg`
3. Settings → Pages → Branch main → Save
4. URL: `https://SEU-USUARIO.github.io/REPO/`

## 🌐 Deploy Netlify
1. app.netlify.com → arraste a pasta com os 4 arquivos
2. Pronto em segundos

---

## 📲 Instalar no celular
- **Android:** ao abrir o link, aparece banner automático → toque **INSTALAR**
- **iPhone (Safari):** Compartilhar → Adicionar à Tela de Início

---

## 🔒 Painel Admin
- Aba **Admin** na barra inferior → senha: `rota202601`
- Adicionar CEPs manualmente ou importar `.xlsx`/`.csv`
- Exportar base completa em CSV

---

## 📁 Arquivos
| Arquivo | Função |
|---------|--------|
| `index.html` | App completo — **suba este para atualizar** |
| `manifest.json` | Config PWA (nome, ícone) |
| `sw.js` | Cache offline |
| `icon.svg` | Ícone do app |
