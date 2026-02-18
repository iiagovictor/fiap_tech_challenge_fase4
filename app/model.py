import logging
import os
import tempfile
from typing import Any, Dict

import boto3
import joblib
import numpy as np
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model  # type: ignore

logger = logging.getLogger(__name__)

# Variáveis de ambiente
S3_BUCKET     = os.getenv("S3_BUCKET")          # definido em produção (variável de ambiente ECS)
MODEL_S3_KEY  = os.getenv("MODEL_S3_KEY", "models/lstm_stock_model.h5")
SCALER_S3_KEY = os.getenv("SCALER_S3_KEY", "models/scaler.pkl")
MODEL_PATH    = os.getenv("MODEL_PATH", "models/lstm_stock_model.h5")
SCALER_PATH   = os.getenv("SCALER_PATH", "models/scaler.pkl")
AWS_REGION    = os.getenv("AWS_REGION", "us-east-1")


def _load_from_s3():
    """Carrega os artefatos do modelo a partir do bucket S3."""
    logger.info("Carregando artefatos do bucket S3 '%s'...", S3_BUCKET)
    s3 = boto3.client("s3", region_name=AWS_REGION)

    with tempfile.TemporaryDirectory() as tmp:
        model_path  = os.path.join(tmp, "model.h5")
        scaler_path = os.path.join(tmp, "scaler.pkl")

        s3.download_file(S3_BUCKET, MODEL_S3_KEY,  model_path)
        s3.download_file(S3_BUCKET, SCALER_S3_KEY, scaler_path)

        # Carrega na memória antes que o diretório temporário seja removido
        model  = load_model(model_path)
        scaler = joblib.load(scaler_path)

    logger.info("Artefatos carregados do S3 na memória.")
    return model, scaler


def _load_from_disk():
    """Carrega os artefatos do modelo a partir do disco local (modo desenvolvimento)."""
    logger.info("Carregando artefatos do disco: %s, %s", MODEL_PATH, SCALER_PATH)
    model  = load_model(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    return model, scaler


# Carrega os artefatos UMA VEZ na inicialização — mantidos na memória do processo
try:
    if S3_BUCKET:
        _model, _scaler = _load_from_s3()
    else:
        _model, _scaler = _load_from_disk()

    SEQ_LENGTH: int = int(_model.input_shape[1])
    MODEL_LOADED = True
    logger.info("Modelo pronto (seq_length=%d)", SEQ_LENGTH)
except Exception as exc:
    _model       = None  # type: ignore[assignment]
    _scaler      = None  # type: ignore[assignment]
    SEQ_LENGTH   = 60
    MODEL_LOADED = False
    logger.error("Falha ao carregar modelo / scaler: %s", exc)


# Funções auxiliares públicas

def _check_loaded() -> None:
    if not MODEL_LOADED:
        raise RuntimeError(
            "Modelo ou scaler não carregado. "
            f"Verifique se '{MODEL_PATH}' e '{SCALER_PATH}' existem."
        )


def predict_from_prices(prices: list[float], days_ahead: int = 1) -> Dict[str, Any]:
    """
    Prevê preços de fechamento futuros a partir de uma lista de preços históricos.

    Parâmetros
    ----------
    prices:     Lista de preços de fechamento históricos (tamanho ≥ SEQ_LENGTH).
    days_ahead: Número de dias a prever (previsão recursiva multi-step).

    Retorno
    -------
    Dicionário compatível com PredictionResponse.
    """
    _check_loaded()

    arr = np.array(prices, dtype=np.float32).reshape(-1, 1)
    scaled = _scaler.transform(arr)

    predictions: list[float] = []
    current_seq = scaled[-SEQ_LENGTH:].reshape(1, SEQ_LENGTH, 1)

    for _ in range(days_ahead):
        pred_scaled = _model.predict(current_seq, verbose=0)          # shape (1,1)
        pred_price  = float(_scaler.inverse_transform(pred_scaled)[0, 0])
        predictions.append(pred_price)
        # Desloca a janela um passo à frente
        current_seq = np.append(
            current_seq[:, 1:, :],
            pred_scaled.reshape(1, 1, 1),
            axis=1,
        )

    return {
        "predicted_prices": predictions,
        "days_ahead": days_ahead,
        "last_known_price": float(prices[-1]),
        "model_version": "1.0.0",
    }


def predict_from_ticker(ticker: str, days_ahead: int = 1) -> Dict[str, Any]:
    """
    Busca dados históricos recentes do Yahoo Finance e realiza a previsão.

    Parâmetros
    ----------
    ticker:     Símbolo do ticker no Yahoo Finance (ex.: 'ITUB4.SA').
    days_ahead: Número de dias a prever.
    """
    _check_loaded()

    stock = yf.Ticker(ticker)
    hist  = stock.history(period="6mo")

    if hist.empty:
        raise ValueError(f"Nenhum dado histórico encontrado para o ticker '{ticker}'.")

    prices = hist["Close"].dropna().tolist()

    if len(prices) < SEQ_LENGTH:
        raise ValueError(
            f"O ticker '{ticker}' possui apenas {len(prices)} pontos de dados; "
            f"são necessários pelo menos {SEQ_LENGTH}."
        )

    # Ajusta um scaler sobre os preços do próprio ticker para garantir
    # normalização correta independente da faixa de preço do ativo.
    arr = np.array(prices, dtype=np.float32).reshape(-1, 1)
    ticker_scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = ticker_scaler.fit_transform(arr)

    predictions: list[float] = []
    current_seq = scaled[-SEQ_LENGTH:].reshape(1, SEQ_LENGTH, 1)

    for _ in range(days_ahead):
        pred_scaled = _model.predict(current_seq, verbose=0)  # shape (1, 1)
        pred_price  = float(ticker_scaler.inverse_transform(pred_scaled)[0, 0])
        predictions.append(pred_price)
        # Desloca a janela um passo à frente
        current_seq = np.append(
            current_seq[:, 1:, :],
            pred_scaled.reshape(1, 1, 1),
            axis=1,
        )

    return {
        "ticker": ticker,
        "predicted_prices": predictions,
        "days_ahead": days_ahead,
        "last_known_price": float(prices[-1]),
        "model_version": "1.0.0",
    }

