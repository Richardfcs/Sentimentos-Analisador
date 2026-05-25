# 🧠 Analisador de Sentimentos com IA

Dashboard inteligente que analisa avaliações de clientes usando Inteligência Artificial, classificando sentimentos, emoções e extraindo pontos positivos e negativos de comentários textuais.

**Projeto Acadêmico — Programação 2026.1**

---

## 🚀 Como Executar

### Pré-requisitos

- Python 3.10 ou superior
- Conta no [OpenRouter](https://openrouter.ai/) (gratuito)

### Instalação

1. **Clone o repositório:**
   ```bash
   git clone <url-do-repositorio>
   cd Sentimentos-Analisador
   ```

2. **Crie e ative um ambiente virtual (recomendado):**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure a chave da API:**
   ```bash
   # Copie o arquivo de exemplo
   copy .env.example .env
   # Edite o .env e coloque sua chave do OpenRouter
   ```

### Execução

```bash
python app.py
```

Acesse: **http://localhost:5000**

---

## 📁 Estrutura do Projeto

```
Sentimentos-Analisador/
├── app.py                 # Servidor Flask principal
├── schemas.py             # Modelos Pydantic (validação)
├── ai_service.py          # Comunicação com OpenRouter
├── data_service.py        # Leitura de dados e estatísticas
├── avaliacoes.json        # Base simulada de avaliações
├── .env                   # Chave da API (não versionado)
├── .env.example           # Exemplo de configuração
├── requirements.txt       # Dependências Python
├── templates/
│   └── index.html         # Página do dashboard
└── static/
    ├── css/style.css      # Estilos (dark mode)
    └── js/dashboard.js    # Gráficos e filtros
```

## 🏗️ Arquitetura

```
avaliacoes.json → Flask lê → Pydantic valida → IA analisa comentários
→ Pydantic valida resposta → Backend calcula estatísticas → Frontend exibe dashboards
```

**Princípio:** A IA analisa texto. O Backend processa dados. O Frontend mostra dashboards.

## 🛠️ Tecnologias

| Camada     | Tecnologia |
|-----------|-----------|
| Backend    | Python + Flask |
| IA         | OpenRouter (LLaMA 3.1 8B) |
| Validação  | Pydantic v2 |
| Frontend   | HTML + CSS + JavaScript |
| Gráficos   | Chart.js |

## 📊 Dashboard

- Total de avaliações e média de estrelas
- Gráfico de pizza por sentimento
- Gráfico de barras por emoção
- Evolução temporal dos sentimentos
- Pontos positivos e negativos recorrentes
- Comentários representativos
- Filtros por data, sentimento e emoção

---

## 👥 Equipe

Projeto desenvolvido para a disciplina de Programação 2026.1.
