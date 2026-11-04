
## Estrutura do projeto

```text
G10-SentinelHome/
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   └── schemas.py
│   ├── data/
│   └── requirements.txt
├── frontend/
│   ├── css/
│   ├── js/
│   └── index.html
├── tests/
├── docs/
├── .github/workflows/
├── iniciar.bat
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## Endpoints principais

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/` | Status da API |
| GET | `/api/health` | Saúde da API |
| GET | `/api/risk` | Análise Fuzzy |
| GET | `/api/devices/` | Listar dispositivos |
| POST | `/api/devices/` | Cadastrar dispositivo |
| PATCH | `/api/devices/{id}` | Atualizar dispositivo |
| DELETE | `/api/devices/{id}` | Excluir dispositivo |
| GET | `/api/alerts/` | Listar alertas |
| POST | `/api/alerts/` | Criar alerta |
| PATCH | `/api/alerts/{id}` | Atualizar alerta |
| DELETE | `/api/alerts/{id}` | Excluir alerta |
| GET | `/api/analytics/summary` | Indicadores gerais |
| GET | `/api/analytics/severity` | Alertas por severidade |
| GET | `/api/analytics/timeline` | Histórico temporal |
| POST | `/api/network/analyze` | Analisar captura PCAP |

## Segurança e limitações

O projeto é uma ferramenta acadêmica de monitoramento e análise. O resultado Fuzzy é uma estimativa heurística e não uma confirmação de ataque.

A análise PCAP depende dos arquivos fornecidos pelo operador. Captura ao vivo, autenticação, autorização e bloqueio de tráfego não estão implementados nesta versão.
