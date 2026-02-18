import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.model import MODEL_LOADED, SEQ_LENGTH, predict_from_prices, predict_from_ticker
from app.monitoring import (
    log_prediction,
    track_request,
)
from app.schemas import (
    HealthResponse,
    PredictionRequest,
    PredictionResponse,
    TickerPredictionRequest,
)

# Configurações de logging estruturado
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: D401
    logger.info("API starting up – model_loaded=%s seq_length=%d", MODEL_LOADED, SEQ_LENGTH)
    yield
    logger.info("API shutting down.")


# Configurações da API
app = FastAPI(
    title="LSTM Stock Price Predictor",
    description=(
        "API RESTful para previsão de preços de ações usando um modelo de "
        "deep learning LSTM treinado com dados do ITUB4 (Itaú Unibanco)."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware: logging de cada requisição com latência
@app.middleware("http")
async def count_requests(request: Request, call_next):
    start    = time.perf_counter()
    response = await call_next(request)
    elapsed  = time.perf_counter() - start
    logger.debug(
        "%s %s → %d (%.3fs)", request.method, request.url.path,
        response.status_code, elapsed,
    )
    return response


# Rotas
@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness / readiness probe",
    tags=["Infraestrutura"],
)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy" if MODEL_LOADED else "degraded",
        model_loaded=MODEL_LOADED,
        model_version="1.0.0",
        seq_length=SEQ_LENGTH,
    )


@app.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Previsão a partir de preços históricos fornecidos pelo usuário",
    tags=["Predição"],
)
def predict(request: PredictionRequest) -> PredictionResponse:
    """
    Recebe uma lista de **preços de fechamento históricos** (mínimo 60 valores)
    e retorna a previsão dos próximos `days_ahead` dias úteis.
    """
    if not MODEL_LOADED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modelo não carregado. Verifique os artefatos do modelo.",
        )

    t0 = time.perf_counter()
    try:
        with track_request("/predict"):
            result = predict_from_prices(request.prices, request.days_ahead)
    except Exception as exc:
        logger.exception("Prediction error on /predict")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    log_prediction(
        endpoint="/predict",
        ticker=None,
        days_ahead=request.days_ahead,
        predicted_prices=result["predicted_prices"],
        latency_s=time.perf_counter() - t0,
    )
    return PredictionResponse(**result)


@app.post(
    "/predict/ticker",
    response_model=PredictionResponse,
    summary="Previsão por ticker (Yahoo Finance)",
    tags=["Predição"],
)
def predict_by_ticker(request: TickerPredictionRequest) -> PredictionResponse:
    """
    Busca automaticamente os preços históricos recentes do ticker informado
    via **Yahoo Finance** e retorna a previsão dos próximos `days_ahead` dias.

    Exemplos de tickers: `ITUB4.SA`, `PETR4.SA`, `AAPL`, `MSFT`.
    """
    if not MODEL_LOADED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modelo não carregado. Verifique os artefatos do modelo.",
        )

    t0 = time.perf_counter()
    try:
        with track_request("/predict/ticker"):
            result = predict_from_ticker(request.ticker, request.days_ahead)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Prediction error on /predict/ticker")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    log_prediction(
        endpoint="/predict/ticker",
        ticker=request.ticker,
        days_ahead=request.days_ahead,
        predicted_prices=result["predicted_prices"],
        latency_s=time.perf_counter() - t0,
    )
    return PredictionResponse(**result)

