from typing import List, Optional
from pydantic import BaseModel, Field


# Requisições
class PredictionRequest(BaseModel):

    prices: List[float] = Field(
        ...,
        min_length=60,
        description="Preços de fechamento diários históricos (mínimo 60 valores, o mais recente por último).",  # noqa: E501
        examples=[[30.5, 31.0, 30.8]],  # abreviado para legibilidade
    )
    days_ahead: int = Field(
        default=1,
        ge=1,
        le=30,
        description="Número de dias úteis futuros a prever.",
    )


class TickerPredictionRequest(BaseModel):

    ticker: str = Field(
        ...,
        description="Símbolo do ticker reconhecido pelo Yahoo Finance (ex.: ITUB4.SA, AAPL).",  # noqa: E501
        examples=["ITUB4.SA"],
    )
    days_ahead: int = Field(
        default=1,
        ge=1,
        le=30,
        description="Número de dias úteis futuros a prever.",
    )


# Respostas
class PredictionResponse(BaseModel):
    """Payload de resposta unificado para todos os endpoints de previsão."""

    ticker: Optional[str] = Field(
        None, description="Símbolo do ticker (quando disponível)."
    )
    predicted_prices: List[float] = Field(
        ..., description="Preços de fechamento previstos em BRL."
    )
    days_ahead: int = Field(..., description="Número de dias previstos.")
    last_known_price: float = Field(
        ..., description="Último preço de fechamento observado."
    )
    model_version: str = Field(
        default="1.0.0", description="Versão do modelo implantado."
    )


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str
    seq_length: int
