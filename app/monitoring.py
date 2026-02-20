import logging
import time
from contextlib import contextmanager
from typing import Generator

logger = logging.getLogger(__name__)


@contextmanager
def track_request(endpoint: str) -> Generator[None, None, None]:
    """Gerenciador de contexto para medir a latência de cada
    requisição e emitir um log estruturado."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.debug("endpoint=%s latency=%.4fs", endpoint, elapsed)


def log_prediction(
    *,
    endpoint: str,
    ticker: str | None,
    days_ahead: int,
    predicted_prices: list[float],
    latency_s: float,
) -> None:
    """Emite uma linha de log estruturada após cada previsão."""
    logger.info(
        "prediction | endpoint=%s ticker=%s days_ahead=%d prices=%s latency_ms=%.1f",  # noqa: E501
        endpoint,
        ticker or "N/A",
        days_ahead,
        [round(p, 4) for p in predicted_prices],
        latency_s * 1000,
    )
