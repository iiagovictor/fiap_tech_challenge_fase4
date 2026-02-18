# models/

Esta pasta contém os artefatos do modelo treinado:

| Arquivo | Descrição |
|---------|-----------|
| `lstm_stock_model.h5` | Modelo LSTM treinado (Keras / TensorFlow) |
| `scaler.pkl` | `MinMaxScaler` serializado com joblib |

## Como gerar os artefatos

Execute todas as células do notebook [`pre-work.ipynb`](../pre-work.ipynb).  
Os arquivos serão salvos automaticamente **nesta pasta** (`models/`).

## Git LFS

Os arquivos `.h5` e `.pkl` são rastreados via **Git LFS** (ver `.gitattributes`).  
Certifique-se de ter o LFS instalado antes de fazer push:

```bash
git lfs install
git lfs track "*.h5" "*.pkl"
git add .gitattributes models/
git commit -m "chore: add model artefacts via LFS"
git push
```

## Fluxo de deploy

A esteira CI/CD (**deploy_aws.yml**) faz o upload automático para S3:

```
models/lstm_stock_model.h5  →  s3://<bucket>/models/lstm_stock_model.h5
models/scaler.pkl            →  s3://<bucket>/models/scaler.pkl
```

O container ECS carrega os artefatos do S3 na memória durante a inicialização.
