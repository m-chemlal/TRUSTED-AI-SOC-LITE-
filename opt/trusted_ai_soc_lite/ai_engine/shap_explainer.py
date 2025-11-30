"""Utilities to generate SHAP explanations (with graceful fallbacks)."""
from __future__ import annotations

from typing import Sequence

try:  # pragma: no cover - optional dependency
    import shap  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - shap absent in CI
    shap = None  # type: ignore


def explain_with_shap(
    model: object,
    feature_vectors: Sequence[Sequence[float]],
    feature_names: Sequence[str],
    *,
    top_k: int = 5,
) -> list[list[dict[str, float]]] | None:
    """Return the top-K SHAP contributors per host.

    When the SHAP library is unavailable (or fails at runtime) the function
    returns ``None`` so that the IA pipeline can continue without interruption.
    """

    if shap is None or model is None or not feature_vectors:
        return None

    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(feature_vectors)
    except Exception:  # noqa: BLE001 - propagate as graceful fallback
        return None

    if isinstance(shap_values, list):
        shap_values = shap_values[-1]

    payload: list[list[dict[str, float]]] = []
    for row in shap_values:
        pairs = sorted(
            zip(feature_names, row), key=lambda item: abs(item[1]), reverse=True
        )
        payload.append(
            [
                {"feature": name, "impact": float(round(value, 4))}
                for name, value in pairs[:top_k]
            ]
        )
    return payload


__all__ = ["explain_with_shap"]
