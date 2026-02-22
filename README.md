# 📈 LSTM Stock Price Predictor - FIAP Tech Challenge - Fase 4

API de previsão de preços de ações com modelo LSTM treinado no histórico do **ITUB4.SA (Itaú Unibanco)**.

---

## Stack

- **ML**: TensorFlow / Keras (LSTM)
- **API**: FastAPI + Uvicorn
- **Infra**: AWS ECS Fargate, ECR, S3, API Gateway
- **IaC**: Terraform
- **CI/CD**: GitHub Actions

---

## Como executar localmente

```bash
# Instalar dependências
pip install -r requirements.txt

# Iniciar a API
uvicorn app.main:app --reload
```

Ou com Docker:

```bash
docker compose up --build
```

> ⚠️ Execute os notebooks em `Notebooks/` para treinar o modelo e gerar `model.h5`, para deployar em produção.

---

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Status da API e do modelo |
| `POST` | `/predict` | Previsão a partir de preços históricos |
| `POST` | `/predict/ticker` | Previsão por ticker (ex: `ITUB4.SA`) |

Documentação interativa disponível em **`/docs`**.