# G10 SentinelHome

## Como executar o projeto no VS Code

Este documento apresenta as instruções para instalar as dependências e executar o G10 SentinelHome localmente.

O projeto utiliza Python, FastAPI, SQLite, SQLAlchemy e HTML, CSS e JavaScript.

---

## 1. Pré-requisitos

Antes de iniciar, verifique se possui instalado:

- Python 3.10 ou superior.
- Visual Studio Code.
- Git.
- Navegador Google Chrome ou equivalente.

---

## 2. Abrir o projeto

Abra o Visual Studio Code e selecione a pasta principal:

`G10-SentinelHome`

Abra o terminal integrado utilizando:

`Ctrl + '`

Confira se o terminal está na pasta principal do projeto:

```bash
pwd
```

---

## 3. Executar o Backend

O backend é responsável pelo processamento das informações, comunicação com o banco de dados, gerenciamento de dispositivos, alertas e inteligência Fuzzy.

### 3.1 Entrar na pasta do backend

```bash
cd backend
```

### 3.2 Ativar o ambiente virtual

No Windows utilizando Git Bash:

```bash
source .venv/Scripts/activate
```

No Windows utilizando PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3.3 Instalar as dependências

Na primeira execução ou quando houver alterações nas dependências:

```bash
python -m pip install -r app/requirements.txt
```

### 3.4 Iniciar a API

```bash
python -m uvicorn app.main:app --reload
```

Se tudo estiver correto, o servidor ficará disponível em:

`http://127.0.0.1:8000`

Mantenha esse terminal aberto enquanto estiver utilizando o sistema.

---

## 4. Executar o Frontend

O frontend corresponde à interface visual do SentinelHome, desenvolvida com HTML, CSS e JavaScript.

Abra um segundo terminal no VS Code.

Certifique-se de estar na pasta principal do projeto.

Execute:

```bash
python -m http.server 5500 --directory frontend
```

O frontend ficará disponível em:

`http://127.0.0.1:5500`

Mantenha esse segundo terminal aberto.

---

## 5. Acessar o sistema

Depois de iniciar os dois servidores, utilize os seguintes endereços:

| Serviço | Endereço |
|---|---|
| Painel principal | http://127.0.0.1:5500 |
| Backend / API | http://127.0.0.1:8000 |
| Documentação interativa | http://127.0.0.1:8000/docs |
| Verificação de saúde | http://127.0.0.1:8000/api/health |

---

## 6. Banco de dados

O SentinelHome utiliza SQLite para armazenar informações localmente.

O banco está configurado para ser armazenado em:

`data/sentinelhome.db`

As informações que podem ser armazenadas incluem:

- Dispositivos cadastrados.
- Endereços IP e MAC.
- Tipos de dispositivos.
- Status dos equipamentos.
- Alertas registrados.
- Pontuações de risco.
- Datas de criação e resolução.

**Importante:** não exclua o arquivo `sentinelhome.db` durante o desenvolvimento, pois ele pode conter registros importantes.

---

## 7. Tecnologias utilizadas

| Tecnologia | Finalidade |
|---|---|
| Python | Linguagem principal do backend |
| FastAPI | Desenvolvimento da API REST |
| Uvicorn | Servidor de aplicação |
| SQLAlchemy | Mapeamento e comunicação com o banco |
| SQLite | Banco de dados local |
| Pydantic | Validação de dados |
| scikit-fuzzy | Motor de inferência Fuzzy |
| NumPy | Operações numéricas |
| SciPy | Recursos matemáticos e científicos |
| HTML | Estrutura das páginas |
| CSS | Estilização e identidade visual |
| JavaScript | Interatividade e integração com a API |
| Chart.js | Construção de gráficos |
| Three.js | Visualização tridimensional |
| pytest | Testes automatizados |
| Git | Controle de versão |
| GitHub | Hospedagem do código-fonte |

---

## 8. Problemas comuns

### Erro: No module named fastapi

Verifique se o ambiente virtual está ativado e instale as dependências:

```bash
python -m pip install -r app/requirements.txt
```

### Erro: No module named scipy

Instale as dependências novamente:

```bash
python -m pip install -r app/requirements.txt
```

### Erro: Address already in use

Significa que a porta utilizada já está ocupada.

Verifique se existe outro servidor rodando antes de iniciar uma nova instância.

### API desconectada no painel

Verifique se o backend está funcionando:

`http://127.0.0.1:8000/api/health`

### Página não encontrada

Confira se existe o arquivo:

`frontend/index.html`

Verifique também se o servidor frontend foi iniciado na pasta principal do projeto.

---

## 9. Encerrar a execução

Para parar os servidores, acesse cada terminal e pressione:

`Ctrl + C`

Depois, você pode fechar o VS Code normalmente.

---

## 10. Atualizar o projeto no GitHub

Após realizar alterações no código, utilize:

```bash
git status
git add .
git commit -m "Atualiza funcionalidades do SentinelHome"
git push origin main
```

Confira se as alterações foram enviadas corretamente ao repositório.

---

## 11. Estrutura geral do projeto

```text
G10-SentinelHome/
│
├── backend/
│   └── app/
│       ├── main.py
│       ├── database.py
│       ├── models.py
│       ├── routes/
│       └── services/
│
├── frontend/
│   ├── index.html
│   ├── css/
│   └── js/
│
├── data/
│   └── sentinelhome.db
│
├── tests/
│
├── README.md
├── COMO_EXECUTAR.md
└── LICENSE
```

*Observação: a estrutura acima é uma referência dos diretórios esperados; alguns arquivos e pastas podem variar conforme a evolução do projeto.*

---

## G10 SentinelHome

**Security Intelligence — Monitoramento Inteligente de Redes Domésticas**

Projeto acadêmico desenvolvido no curso de Engenharia da Computação — UNIFECAF.

Repositório: https://github.com/Gustavo499-max/G10-SentinelHome

