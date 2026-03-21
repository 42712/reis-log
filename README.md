# 🚚 Reis Log — LeitorRota

> App PWA para leitura de CEP de pacotes via câmera e identificação de rota de entrega.  
> Desenvolvido para uso interno da **Reis Log Transporte e Logística**.

---

## 📋 Índice

1. [Funcionalidades](#funcionalidades)
2. [Estrutura dos arquivos](#estrutura)
3. [Deploy no GitHub Pages](#github-pages)
4. [Deploy no Netlify](#netlify)
5. [Criar ícone na tela do celular](#pwa-icone)
6. [Painel Admin](#admin)
7. [Adicionar/Importar CEPs](#ceps)
8. [Configurações do app](#configuracoes)
9. [Trocar senha master](#senha)
10. [Histórico de versões](#versoes)

---

## ✅ Funcionalidades <a name="funcionalidades"></a>

| Função | Descrição |
|--------|-----------|
| 📷 Câmera | Abre câmera traseira e escaneia em tempo real |
| 🔲 QR Code | Lê QR Codes de pacotes |
| |||||| Código de Barras | Lê Code 128, EAN, Interleaved 2of5 |
| 🔍 Busca manual | Digite o CEP para consultar |
| 🔊 Voz | Fala a rota automaticamente ao escanear |
| 📳 Vibração | Vibração háptica ao encontrar rota |
| ⚡ Lanterna | Ativa flash do celular em ambientes escuros |
| 🕓 Histórico | Últimas 50 consultas com data/hora |
| ⚙️ Configurações | Câmera, voz, velocidade, tom, vibração |
| 🔒 Admin protegido | Painel admin com senha master |
| ➕ Add manual | Adicionar CEPs individualmente no app |
| 📥 Importar | Importar planilha .xlsx ou .csv |
| ⬇️ Exportar | Baixar CSV com toda a base ativa |
| 📱 PWA | Funciona como app nativo, ícone na tela |
| 🌐 Offline | Funciona sem internet após carregado |

**Base embutida:** 13.078 CEPs — Goiânia/GO

---

## 📁 Estrutura dos arquivos <a name="estrutura"></a>

```
reis-log/
├── index.html      ← App completo (banco de CEPs embutido)
├── manifest.json   ← Configuração PWA (nome, ícone, cor)
├── sw.js           ← Service Worker (cache offline)
├── icon.svg        ← Ícone do app
└── README.md       ← Este arquivo
```

> ⚠️ **Todos os 4 arquivos precisam estar na mesma pasta.**  
> O `index.html` já contém os 13k CEPs — não precisa de servidor nem banco de dados.

---

## 🚀 Deploy no GitHub Pages <a name="github-pages"></a>

### Passo 1 — Criar conta no GitHub
Acesse [github.com](https://github.com) e crie uma conta gratuita (se ainda não tiver).

### Passo 2 — Criar repositório
1. Clique em **"New repository"** (botão verde no canto superior direito)
2. Preencha:
   - **Repository name:** `reis-log` (ou qualquer nome sem espaços)
   - **Visibility:** ✅ **Public** (obrigatório para GitHub Pages gratuito)
   - Deixe as demais opções desmarcadas
3. Clique em **"Create repository"**

### Passo 3 — Fazer upload dos arquivos
1. Na página do repositório recém-criado, clique em **"uploading an existing file"**
2. Arraste os **4 arquivos** de uma vez:
   - `index.html`
   - `manifest.json`
   - `sw.js`
   - `icon.svg`
3. No campo **"Commit changes"**, escreva: `Primeiro deploy`
4. Clique em **"Commit changes"** (botão verde)

### Passo 4 — Ativar GitHub Pages
1. No repositório, clique em **"Settings"** (aba no topo)
2. No menu lateral esquerdo, clique em **"Pages"**
3. Em **"Source"**, selecione:
   - Branch: **`main`**
   - Folder: **`/ (root)`**
4. Clique em **"Save"**

### Passo 5 — Acessar o app
- Aguarde **2 a 5 minutos**
- A URL do seu app será:
  ```
  https://SEU-USUARIO.github.io/reis-log/
  ```
- Exemplo: `https://joao123.github.io/reis-log/`

> ✅ Essa URL funciona para sempre, é gratuita e pode ser compartilhada com toda a equipe!

### Atualizar o app no futuro
1. Acesse o repositório no GitHub
2. Clique no arquivo que deseja atualizar (ex: `index.html`)
3. Clique no ícone de lápis ✏️
4. Faça a alteração e clique **"Commit changes"**
5. O app será atualizado automaticamente em ~1 minuto

---

## 🌐 Deploy no Netlify (alternativa — mais rápido) <a name="netlify"></a>

O Netlify é mais simples que o GitHub para quem não quer lidar com Git.

### Opção A — Upload direto (mais fácil)
1. Acesse [app.netlify.com](https://app.netlify.com)
2. Crie uma conta gratuita com e-mail
3. Na tela inicial, localize o quadro **"Deploy manually"**
4. **Arraste a pasta com os 4 arquivos** direto para esse quadro
5. Pronto! Em segundos você receberá uma URL como:
   ```
   https://nome-aleatorio-123.netlify.app
   ```

### Personalizar a URL no Netlify
1. Acesse o painel do site criado
2. Clique em **"Site configuration"** → **"Site details"**
3. Clique em **"Change site name"**
4. Digite: `reis-log` (ou o nome que preferir)
5. Sua URL vira: `https://reis-log.netlify.app`

### Opção B — Via GitHub (recomendado para atualizações automáticas)
1. Faça os passos do GitHub Pages (Passo 1 a 4 acima)
2. No Netlify, clique em **"Add new site"** → **"Import an existing project"**
3. Selecione **"GitHub"** e autorize
4. Escolha o repositório `reis-log`
5. Em **"Build settings"** deixe tudo em branco
6. Clique **"Deploy site"**

> ✅ Agora toda vez que você atualizar o repositório no GitHub,  
> o Netlify atualiza o app automaticamente em segundos!

---

## 📲 Criar ícone na tela do celular (PWA) <a name="pwa-icone"></a>

Depois de acessar o link do app pelo celular:

### Android (Chrome — recomendado)
1. Abra a URL no **Chrome**
2. Toque no menu **⋮** (três pontos, canto superior direito)
3. Toque em **"Adicionar à tela inicial"**
4. Confirme o nome e toque **"Adicionar"**
5. O ícone aparece na tela inicial como um app!

### iPhone / iPad (Safari — obrigatório)
1. Abra a URL no **Safari** (não funciona no Chrome do iPhone)
2. Toque no botão **Compartilhar** (quadrado com seta para cima)
3. Role a lista e toque em **"Adicionar à Tela de Início"**
4. Confirme o nome e toque **"Adicionar"**
5. O ícone aparece na tela inicial!

> 🔥 Após adicionar, o app abre **sem barra do navegador**, igual a um app nativo instalado.

---

## ⚙️ Painel Admin <a name="admin"></a>

O painel admin é protegido por senha master.

- Acesse pela aba **"⚙️ Admin"** na barra inferior
- **Senha master padrão:** `rota202601`
- Ao entrar, você permanece autenticado até tocar em **"Sair do painel admin"**
- Toda ação destrutiva (resetar base) exige confirmação da senha E confirmação adicional

---

## ➕ Adicionar e Importar CEPs <a name="ceps"></a>

### Adicionar manualmente
1. Entre no painel **Admin**
2. Na seção **"Adicionar CEP manual"**:
   - Digite o CEP no campo (formato: `00000-000`)
   - Digite o número da Rota
   - Toque em **"+ ADD"**
3. O CEP aparece como tag (toque para remover se errar)
4. Adicione quantos quiser antes de salvar
5. Toque em **"💾 SALVAR ADIÇÕES"**

> Os CEPs ficam salvos no armazenamento local do celular.  
> Se limpar os dados do navegador, os adicionados manualmente são perdidos.  
> Use a função **Exportar CSV** para fazer backup periódico.

### Importar planilha Excel ou CSV
1. Entre no painel **Admin**
2. Na seção **"📥 Importar Excel / CSV"**, toque na área de upload
3. Selecione o arquivo `.xlsx` ou `.csv`
4. O arquivo deve ter **duas colunas**: `CEP` e `ROTA` (com cabeçalho)

**Exemplo de formato CSV aceito:**
```
CEP,ROTA
74080-010,119
74083-005,053
74085-120,047
```

**Exemplo de formato Excel aceito:**

| CEP | ROTA |
|-----|------|
| 74080-010 | 119 |
| 74083-005 | 053 |

> ✅ CEPs com ou sem traço são aceitos automaticamente.

### Exportar base
- No Admin → **"⬇️ EXPORTAR CSV"**
- Baixa um arquivo `base_cep_rota.csv` com todos os CEPs (originais + adicionados)
- Use para backup ou para atualizar a base no futuro

### Resetar base
- No Admin → **"🗑️ RESETAR BASE"**
- Remove apenas os CEPs adicionados manualmente/importados
- A base original (13.078 CEPs) é sempre preservada
- Requer confirmação de senha master + confirmação adicional

---

## ⚙️ Configurações do app <a name="configuracoes"></a>

Acesse pelas configurações (ícone ⚙️ no header — toque para abrir/fechar).

| Configuração | Opções |
|---|---|
| Câmera traseira | Ativa/desativa câmera traseira (recomendado: ativado) |
| Alta resolução | 1280×720 — melhor leitura, mais bateria |
| Pausa após leitura | 2s / 3s / 5s / 8s entre escaneamentos |
| Falar rota automaticamente | Diz a rota ao escanear |
| Vibrar ao encontrar | Vibração háptica |
| Velocidade da fala | Slider: lenta → muito rápida |
| Tom da voz | Slider: grave → aguda |
| Voz selecionada | Vozes PT-BR disponíveis no dispositivo |
| Histórico automático | Salvar consultas |
| Limpar campo após busca | Apaga CEP digitado após consultar |

---

## 🔑 Trocar senha master <a name="senha"></a>

### Pelo app (recomendado)
1. Abra as **Configurações** (⚙️ no header)
2. Role até **"🔑 Segurança"**
3. Toque em **"🔑 ALTERAR SENHA MASTER"**
4. Confirme a senha atual → digite a nova senha

### Direto no código (se esquecer a senha)
1. Abra o arquivo `index.html` em qualquer editor de texto (Bloco de Notas, VS Code, etc.)
2. Use **Ctrl+F** para buscar: `rota202601`
3. Substitua pela nova senha desejada
4. Salve e faça upload novamente para o GitHub/Netlify

---

## 📦 Histórico de versões <a name="versoes"></a>

| Versão | Data | O que mudou |
|--------|------|-------------|
| v2.1 | Mar/2026 | Logo Reis Log, marca d'água, engrenagem toggle, rota em fonte grande, senha `rota202601` |
| v2.0 | Mar/2026 | PWA completo, painel admin, importação Excel, service worker, configurações |
| v1.0 | Mar/2026 | Versão inicial: câmera, leitura de código, consulta CEP, voz, histórico |

---

## 🆘 Problemas comuns

| Problema | Solução |
|----------|---------|
| Câmera não abre | Verifique se o navegador tem permissão de câmera nas configurações do celular |
| App não vira ícone | No iPhone use Safari. No Android use Chrome |
| CEP não encontrado | O CEP pode não estar na base. Adicione pelo painel Admin |
| Voz não funciona | Verifique se o volume está ligado. Teste em Configurações → "▶ TESTAR VOZ" |
| Service worker erro | Acesse pelo HTTPS (GitHub Pages e Netlify já usam HTTPS automaticamente) |
| App desatualizado | Force atualização: segure o ícone → "Remover" → acesse o link e adicione de novo |

---

*Reis Log Transporte e Logística — Sistema interno de triagem de rotas*  
*Desenvolvido com tecnologia PWA — funciona offline após o primeiro acesso*
