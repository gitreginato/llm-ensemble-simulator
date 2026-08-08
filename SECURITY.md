# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| latest  | sim       |

## Reporting a Vulnerability

Não abra issue pública para vulnerabilidades. Envie email descrevendo o problema, passos para reproduzir e impacto estimado. Resposta em até 72 horas.

## Security Measures

### API Keys
- Nunca hardcodadas no código. Sempre via `.env` (gitignored).
- Cada adapter (Ollama, Cline, Kilocode, Devin) lê suas próprias credenciais de variáveis de ambiente.
- Nunca logar API keys, tokens, ou respostas completas de LLM em produção.

### Rate Limiting
- Cada source tem rate limit independente para evitar bloqueio cascata.
- Backoff exponencial em caso de 429 ou timeout.

### Dados
- Personas sintéticas são geradas com seed fixo para reprodutibilidade.
- Não usa dados pessoais reais. Dataset de calibração (142 personas) é anonimizado.
- Resultados de simulação não contêm PII.

### Dependencies
- Todas as dependências pinadas em `requirements.txt`.
- Rodar `pip-audit` regularmente.
