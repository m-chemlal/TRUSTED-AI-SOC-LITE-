"""Thin wrapper around LIME with defensive fallbacks."""
from __future__ import annotations

from typing import Sequence

try:  # pragma: no cover - optional dependency
    import numpy as np
except ModuleNotFoundError:  # pragma: no cover
    np = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from lime.lime_tabular import LimeTabularExplainer  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    LimeTabularExplainer = None  # type: ignore


def explain_with_lime(
    model: object,
    feature_vectors: Sequence[Sequence[float]],
    feature_names: Sequence[str],
    *,
    top_k: int = 5,
) -> list[list[dict[str, float]] | None] | None:
    """Return LIME explanations per host or ``None`` if unavailable."""

    if LimeTabularExplainer is None or model is None or np is None or not feature_vectors:
        return None

    try:
        background = np.array(feature_vectors)
        explainer = LimeTabularExplainer(
            background,
            feature_names=list(feature_names),
            discretize_continuous=False,
        )
    except Exception:  # noqa: BLE001
        return None

    def predict_fn(samples: np.ndarray):  # type: ignore[override]
        try:
            return model.predict_proba(samples)
        except Exception:  # noqa: BLE001
            return np.zeros((samples.shape[0], 2))

    payload: list[list[dict[str, float]] | None] = []
    for vector in feature_vectors:
        try:
            explanation = explainer.explain_instance(
                np.array(vector), predict_fn, num_features=min(top_k, len(feature_names))
            )
            contribution = [
                {"feature": name, "weight": float(round(weight, 4))}
                for name, weight in explanation.as_list()
            ]
            payload.append(contribution[:top_k])
        except Exception:  # noqa: BLE001
            payload.append(None)
    return payload


__all__ = ["explain_with_lime"]
