
## 📌 Visão geral

O **G10 SentinelHome** é um projeto acadêmico de segurança da informação
voltado ao monitoramento e à análise de redes domésticas. A aplicação
reúne informações sobre dispositivos conectados, permite realizar
descoberta de hosts na rede local, analisa arquivos de captura de
tráfego e utiliza lógica fuzzy para produzir uma classificação
heurística de risco.

A proposta é oferecer uma visão centralizada da rede por meio de uma
interface web, apoiada por uma API em Python. O sistema organiza dados
de dispositivos e alertas, apresenta indicadores e fornece recursos para
apoiar a investigação de eventos potencialmente suspeitos.

> **Objetivo:** apoiar a visibilidade da rede doméstica e a
> identificação de comportamentos que merecem investigação --- não
> substituir ferramentas profissionais de segurança, firewall ou
> sistemas SIEM.

## 🎯 Problema que o projeto aborda

Redes domésticas podem reunir computadores, celulares, televisores,
dispositivos IoT e outros equipamentos. Sem uma visão centralizada, pode
ser difícil responder a perguntas como:

-   Quais dispositivos foram identificados na rede?
-   Há algum equipamento desconhecido que precisa ser verificado?
-   O que uma captura de tráfego revela sobre a atividade observada?
-   Quais dispositivos ou eventos merecem maior atenção?
-   Como acompanhar alertas e indicadores ao longo do tempo?

O SentinelHome organiza essas informações em módulos integrados para
facilitar a observação e a análise.

## ✨ Funcionalidades

### 1. Descoberta de dispositivos por ARP

-   Executa descoberta de hosts em uma faixa de rede local informada
    pelo operador.
-   Utiliza ARP para identificar dispositivos que respondem na rede
    local.
-   Retorna informações de descoberta para apoiar o inventário de
    ativos.
-   Permite encaminhar os dispositivos encontrados para cadastro na
    aplicação.

### 2. Inventário e gerenciamento de dispositivos

-   Cadastro, consulta, atualização e remoção de dispositivos.
-   Persistência das informações em banco de dados.
-   Organização dos ativos para consulta pelo dashboard e pelos módulos
    de análise.

### 3. Análise de capturas de rede (PCAP/PCAPNG)

-   Recebe arquivos `.pcap` e `.pcapng` enviados pelo operador.
-   Processa a captura para extrair informações relevantes do tráfego.
-   Disponibiliza análise geral e análise associada aos dispositivos
    cadastrados.
-   Limita o tamanho do arquivo enviado a 20 MB nesta versão.

### 4. Motor de inferência fuzzy

-   Avalia variáveis relacionadas à atividade de rede, como pacotes,
    portas e tráfego.
-   Aplica lógica fuzzy para calcular um índice e classificar o nível de
    risco.
-   Permite realizar análise geral e análise vinculada aos dispositivos.

**Importante:** o resultado fuzzy é um indicador heurístico produzido
pelas regras e funções de pertinência do modelo. Não representa
probabilidade estatística, diagnóstico definitivo ou confirmação de
ataque.

### 5. Alertas e indicadores

-   Cadastro e gerenciamento de alertas.
-   Consulta de indicadores consolidados.
-   Agrupamento de alertas por severidade.
-   Visualização de histórico temporal para apoiar a análise.

### 6. Dashboard web

-   Interface para acompanhar os dados disponibilizados pela API.
-   Visualização centralizada de dispositivos, alertas e análises.
-   Componentes gráficos para facilitar a interpretação dos resultados.

> A disponibilidade e o nível de atualização dos dados dependem das
> operações executadas e das fontes de informação habilitadas na
> aplicação.

## 🧠 Áreas de conhecimento aplicadas

O projeto foi organizado para explorar conceitos de diferentes áreas da
Engenharia da Computação:

  -----------------------------------------------------------------------
  Área                                Aplicação no SentinelHome
  ----------------------------------- -----------------------------------
  **Open Source**                     Código versionado publicamente,
                                      licença MIT e diretrizes de
                                      contribuição.

  **Cloud Computing for Software      Base de aplicação separada entre
  Development**                       frontend e API, preparada para
                                      evoluir para implantação em
                                      ambiente de nuvem. A hospedagem em
                                      nuvem não faz parte da execução
                                      local documentada nesta versão.

  **Software Architecture & Design    Separação entre rotas, serviços,
  Patterns**                          modelos, schemas, persistência e
                                      interface.

  **Telecommunications & Network      Descoberta ARP, leitura de capturas
  Security**                          PCAP/PCAPNG e análise de
                                      informações de rede.

  **Computational Intelligence &      Inferência fuzzy para classificação
  Algorithm Optimization**            heurística de risco. Técnicas de
                                      otimização, como PSO, podem ser
                                      exploradas em etapas futuras; não
                                      são apresentadas aqui como recurso
                                      já integrado ao fluxo atual.
  -----------------------------------------------------------------------

## 🏗️ Arquitetura

A aplicação adota uma organização em camadas, separando a interface, a
API, as regras de negócio e a persistência.

``` mermaid
flowchart TB
    U[Operador] --> FE[Frontend Web]
    FE -->|HTTP / JSON| API[API FastAPI]
    API --> ROUTES[Rotas REST]
    ROUTES --> SERVICES[Camada de Serviços]
    SERVICES --> DISC[Descoberta ARP]
    SERVICES --> PCAP[Análise PCAP / PCAPNG]
    SERVICES --> FUZZY[Motor de Inferência Fuzzy]
    SERVICES --> RISK[Análise de Risco por Dispositivo]
    ROUTES --> DB[SQLAlchemy]
    DB --> SQL[(SQLite)]
    ROUTES --> ALERTS[Alertas e Analytics]
```

### Responsabilidade dos componentes

  -----------------------------------------------------------------------
  Componente                          Responsabilidade
  ----------------------------------- -----------------------------------
  **Frontend**                        Apresentar dashboard, formulários,
                                      tabelas e visualizações.

  **FastAPI**                         Expor os endpoints HTTP e coordenar
                                      as operações da aplicação.

  **Routes**                          Receber requisições, validar
                                      entradas e encaminhar chamadas aos
                                      serviços.

  **Services**                        Concentrar descoberta de rede,
                                      análise de capturas e lógica fuzzy.

  **SQLAlchemy**                      Fazer o mapeamento
                                      objeto-relacional e intermediar o
                                      acesso ao banco.

  **SQLite**                          Persistir dispositivos, alertas e
                                      demais registros da aplicação.
  -----------------------------------------------------------------------

## 🧰 Tecnologias utilizadas

### Backend

-   **Python 3.11+** --- linguagem principal.
-   **FastAPI** --- construção da API REST.
-   **Uvicorn** --- servidor ASGI para execução local.
-   **SQLAlchemy** --- persistência e mapeamento objeto-relacional.
-   **Pydantic** --- validação e estruturação de dados.
-   **Scapy** --- operações e análise de rede.
-   **NetworkX** --- recursos de representação e análise de estruturas
    de rede.
-   **scikit-fuzzy, NumPy e SciPy** --- operações numéricas e inferência
    fuzzy.
-   **python-multipart** --- recebimento de arquivos pela API.

### Frontend

-   HTML5
-   CSS3
-   JavaScript
-   Chart.js e Three.js para visualizações utilizadas na interface.

### Qualidade e desenvolvimento

-   pytest
-   HTTPX
-   Git e GitHub
-   Visual Studio Code

## 📂 Estrutura do projeto

``` text
G10-SentinelHome/
├── backend/
│   └── app/
│       ├── routes/
│       │   ├── devices.py
│       │   ├── alerts.py
│       │   └── analytics.py
│       ├── services/
│       │   ├── fuzzy_engine.py
│       │   ├── network_discovery.py
│       │   ├── network_monitor.py
│       │   └── risk_analyzer.py
│       ├── main.py
│       ├── database.py
│       ├── models.py
│       ├── schemas.py
│       └── requirements.txt
├── frontend/
│   ├── css/
│   ├── js/
│   └── index.html
├── tests/
├── docs/
├── .github/
│   └── workflows/
├── COMO_EXECUTAR.md
├── CONTRIBUTING.md
├── LICENSE
├── iniciar.bat
└── README.md
```

*Observação: arquivos auxiliares e subpastas podem evoluir conforme
novas funcionalidades forem incorporadas.*

## ⚙️ Instalação e execução

### Pré-requisitos

-   Windows, Linux ou macOS.
-   Python 3.11 ou superior.
-   Git.
-   Acesso à rede local e permissões adequadas para operações de
    descoberta ARP, quando esse recurso for utilizado.

### 1. Clonar o repositório

``` bash
git clone https://github.com/Gustavo499-max/G10-SentinelHome.git
cd G10-SentinelHome
```

### 2. Criar o ambiente virtual

**Windows (PowerShell ou CMD):**

``` bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux ou macOS:**

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar as dependências

``` bash
cd backend
pip install -r app/requirements.txt
```

### 4. Iniciar a API

Ainda dentro da pasta `backend`, execute:

``` bash
python -m uvicorn app.main:app --reload
```

Quando a inicialização for concluída, a API estará disponível em:

-   **API:** http://127.0.0.1:8000
-   **Documentação Swagger:** http://127.0.0.1:8000/docs
-   **Documentação ReDoc:** http://127.0.0.1:8000/redoc
-   **Health check:** http://127.0.0.1:8000/api/health

### 5. Abrir o frontend

Com a API em execução, abra uma segunda janela de terminal na raiz do
projeto e inicie um servidor local para os arquivos estáticos.

Uma opção é utilizar a extensão **Live Server** no Visual Studio Code:
abra `frontend/index.html` e selecione **Open with Live Server**.

A interface deve ser acessada pela origem local configurada no CORS da
API (por exemplo, `http://127.0.0.1:5500`).

> **Dica:** consulte também [`COMO_EXECUTAR.md`](COMO_EXECUTAR.md) para
> as instruções complementares do projeto.

## 🔌 Documentação da API

A documentação interativa gerada pelo FastAPI está disponível em `/docs`
enquanto o backend estiver em execução.

### Endpoints principais

  --------------------------------------------------------------------------------
  Método                  Endpoint                         Finalidade
  ----------------------- -------------------------------- -----------------------
  `GET`                   `/`                              Informações gerais e
                                                           status da aplicação.

  `GET`                   `/api/health`                    Verificação da API e
                                                           conexão com o banco.

  `GET`                   `/api/risk`                      Cálculo fuzzy geral a
                                                           partir dos parâmetros
                                                           informados.

  `GET`                   `/api/devices/`                  Listagem de
                                                           dispositivos.

  `POST`                  `/api/devices/`                  Cadastro de
                                                           dispositivo.

  `PATCH`                 `/api/devices/{id}`              Atualização de
                                                           dispositivo.

  `DELETE`                `/api/devices/{id}`              Remoção de dispositivo.

  `GET`                   `/api/alerts/`                   Listagem de alertas.

  `POST`                  `/api/alerts/`                   Criação de alerta.

  `PATCH`                 `/api/alerts/{id}`               Atualização de alerta.

  `DELETE`                `/api/alerts/{id}`               Remoção de alerta.

  `GET`                   `/api/analytics/summary`         Indicadores gerais.

  `GET`                   `/api/analytics/severity`        Indicadores por
                                                           severidade.

  `GET`                   `/api/analytics/timeline`        Histórico temporal.

  `POST`                  `/api/network/discover`          Descoberta de
                                                           dispositivos via ARP.

  `POST`                  `/api/network/analyze`           Análise de arquivo
                                                           PCAP/PCAPNG.

  `POST`                  `/api/network/analyze-devices`   Análise da captura
                                                           associada aos
                                                           dispositivos.
  --------------------------------------------------------------------------------

### Exemplos de requisição

**Verificar a saúde da aplicação:**

``` bash
curl http://127.0.0.1:8000/api/health
```

**Calcular um indicador fuzzy:**

``` bash
curl "http://127.0.0.1:8000/api/risk?packets=30&ports=20&traffic=25"
```

**Descobrir dispositivos em uma rede local autorizada:**

``` bash
curl -X POST "http://127.0.0.1:8000/api/network/discover?network=192.168.0.0/24&timeout=2"
```

Os parâmetros de rede devem ser ajustados para a faixa realmente
utilizada no ambiente de teste. A descoberta deve ser executada somente
em redes próprias ou com autorização explícita.

## 🧪 Testes

O projeto inclui estrutura de testes com `pytest`. Para executar os
testes a partir da raiz do repositório, com o ambiente virtual ativo:

``` bash
cd backend
python -m pytest ../tests -v
```

Se algum teste depender de configuração, arquivo de captura ou ambiente
específico, consulte os arquivos de teste e a documentação complementar
antes da execução.

## 🔐 Segurança, privacidade e limitações

O SentinelHome é um projeto acadêmico e experimental. Considere os
seguintes pontos antes de utilizá-lo:

-   Execute descoberta e análise de rede somente em ambientes próprios
    ou autorizados.
-   A descoberta ARP depende das características da rede local, da
    interface selecionada e das permissões do sistema operacional.
-   A análise de tráfego desta versão é baseada em arquivos PCAP/PCAPNG
    fornecidos pelo operador; isso não equivale a uma captura contínua
    de toda a rede.
-   A classificação fuzzy é heurística e deve ser interpretada como
    apoio à análise, não como confirmação de incidente.
-   A aplicação local documentada utiliza SQLite e não representa, por
    si só, uma implantação em nuvem ou ambiente de produção.
-   Autenticação, autorização, bloqueio automático de tráfego e
    integração com SIEM não devem ser considerados recursos disponíveis
    sem implementação e validação específicas.
-   Não envie capturas contendo dados pessoais, credenciais, tokens ou
    informações sensíveis para repositórios públicos.
-   Não publique bancos de dados reais, arquivos `.env`, capturas de
    tráfego ou inventários que revelem informações da rede.

## ☁️ Evolução para Cloud Computing

A arquitetura separada entre frontend, API e persistência cria uma base
para uma futura implantação em nuvem. Uma evolução possível inclui:

1.  Empacotar a API em um contêiner Docker.
2.  Utilizar um serviço de hospedagem para executar o backend.
3.  Migrar o banco local para um serviço gerenciado, após avaliar os
    requisitos de persistência e concorrência.
4.  Configurar variáveis de ambiente e gerenciamento seguro de segredos.
5.  Adicionar HTTPS, autenticação, autorização, logs centralizados e
    monitoramento.
6.  Automatizar testes e implantação por meio de pipeline CI/CD.

Esses itens representam possibilidades de evolução e não devem ser
interpretados como infraestrutura já configurada neste repositório.

## 🗺️ Roadmap

-   [x] API REST com FastAPI.
-   [x] Persistência com SQLAlchemy e SQLite.
-   [x] Gerenciamento de dispositivos e alertas.
-   [x] Indicadores e histórico analítico.
-   [x] Descoberta de dispositivos por ARP.
-   [x] Análise de capturas PCAP/PCAPNG.
-   [x] Motor de inferência fuzzy.
-   [ ] Ampliar cobertura e automação dos testes.
-   [ ] Evoluir documentação técnica e diagramas.
-   [ ] Planejar implantação em nuvem e pipeline CI/CD.
-   [ ] Avaliar integração com ferramentas SIEM.
-   [ ] Pesquisar técnicas de otimização, incluindo PSO, para
    experimentos comparativos com o modelo atual.

## 🤝 Contribuição

Contribuições são bem-vindas! Para propor melhorias:

1.  Faça um fork do repositório.
2.  Crie uma branch para sua alteração.
3.  Implemente e teste a mudança.
4.  Descreva claramente o que foi alterado.
5.  Abra um Pull Request.

Consulte [`CONTRIBUTING.md`](CONTRIBUTING.md) para conhecer as
diretrizes de contribuição.

## 📄 Licença

Este projeto está licenciado sob a **MIT License**. Consulte o arquivo
[`LICENSE`](LICENSE) para obter o texto completo.

## 👥 Projeto

**G10 SentinelHome**\
Projeto acadêmico de Engenharia da Computação.

-   Repositório: https://github.com/Gustavo499-max/G10-SentinelHome
-   Documentação da API (execução local): http://127.0.0.1:8000/docs

------------------------------------------------------------------------

::: {align="center"}
**G10 SentinelHome --- Visibilidade, análise e inteligência para redes
domésticas.**
:::
