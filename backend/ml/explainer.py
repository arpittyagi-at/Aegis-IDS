"""Feature attribution explanation engine.

This module provides explain_prediction(predictor, feature_dict) -> dict
with two modes:
  - SHAP (if available)
  - Fallback using feature importances

The output is a dict mapping feature_name -> {value, shap, direction}
"""

from __future__ import annotations

import logging
from typing import Any, Dict

import numpy as np


_SHAP_EXPLAINERS: dict[str, Any] = {}


def _build_feature_vector(predictor, feature_dict: dict) -> np.ndarray:
    """Build the feature vector used by the predictor (before scaling)."""
    # Use predictor's full feature list (same as training)
    features = getattr(predictor, "all_feature_names", None)
    if features is None:
        # fallback to predictor.feature_names if all_feature_names isn't present
        features = getattr(predictor, "feature_names", [])

    vec = [float(feature_dict.get(f, 0.0) or 0.0) for f in features]
    arr = np.array(vec, dtype=float).reshape(1, -1)
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    return arr, features


def explain_prediction(predictor, feature_dict: dict) -> Dict[str, Dict[str, Any]]:
    """Return the top-5 feature attributions for a single prediction."""
    import warnings
    import pandas as pd

    arr, features = _build_feature_vector(predictor, feature_dict)

    # Apply selector and scaler in the same order as predictor.predict()
    # Use DataFrame so sklearn doesn't complain about feature names
    arr_df = pd.DataFrame(arr, columns=features)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            selected = predictor.selector.transform(arr_df)
            scaled = predictor.scaler.transform(selected)
    except Exception as e:
        raise RuntimeError("Failed to apply selector/scaler on input") from e

    # Compute base probability (zero vector) for fallback
    try:
        zero_scaled = np.zeros_like(scaled)
        base_prob = float(predictor.model.predict_proba(zero_scaled)[0][1])
    except Exception:
        base_prob = 0.0

    # Attempt SHAP mode
    try:
        import shap  # type: ignore

        explainer = _SHAP_EXPLAINERS.get(predictor.dataset)
        if explainer is None:
            explainer = shap.TreeExplainer(predictor.model)
            _SHAP_EXPLAINERS[predictor.dataset] = explainer

        shap_values = explainer.shap_values(scaled)

        # shap_values can be:
        #   - list of 2 arrays (one per class): shape [n_classes][n_samples, n_features]
        #   - single ndarray of shape (n_samples, n_features, n_classes)  (newer shap)
        #   - single ndarray of shape (n_samples, n_features)  (binary shorthand)
        # We always want class 1 = attack
        if isinstance(shap_values, list):
            # Classic format: list[0] = class 0, list[1] = class 1
            shap_arr = np.array(shap_values[-1])   # last entry = attack class
        else:
            sv = np.array(shap_values)
            if sv.ndim == 3:
                # shape (n_samples, n_features, n_classes)
                shap_arr = sv[:, :, 1]
            else:
                # shape (n_samples, n_features) — already attack direction for binary RF
                shap_arr = sv

        # Ensure single-sample row
        shap_row = shap_arr[0] if shap_arr.ndim == 2 else shap_arr

        # Get top 5 features by abs(shap)
        top_idx = np.argsort(np.abs(shap_row))[::-1][:5]

        out: Dict[str, Dict[str, Any]] = {}
        for idx in top_idx:
            fname = predictor.feature_names[idx]
            raw_val = float(feature_dict.get(fname, 0.0) or 0.0)
            shap_val = float(shap_row[idx])
            out[fname] = {
                "value": raw_val,
                "shap": shap_val,
                "direction": "attack" if shap_val > 0 else "normal",
            }
        return out

    except Exception as e:
        logging.debug("SHAP explanation failed, falling back to feature importance: %s", e)

    # Fallback mode: feature importances
    try:
        importances = np.array(getattr(predictor.model, "feature_importances_", []))
        if importances.size == 0:
            raise AttributeError("Model has no feature_importances_")

        # Compute attributions
        prob = float(predictor.model.predict_proba(scaled)[0][1])
        diff = prob - base_prob

        # Effective scaled values (after selector) for each selected feature
        scaled_vals = scaled[0] if scaled.ndim == 2 else scaled

        attributions = importances * np.sign(scaled_vals) * diff

        top_idx = np.argsort(np.abs(attributions))[::-1][:5]

        out: Dict[str, Dict[str, Any]] = {}
        for idx in top_idx:
            fname = predictor.feature_names[idx]
            raw_val = float(feature_dict.get(fname, 0.0) or 0.0)
            attr = float(attributions[idx])
            out[fname] = {
                "value": raw_val,
                "shap": attr,
                "direction": "attack" if attr > 0 else "normal",
            }
        return out
    except Exception as e:
        raise RuntimeError("Failed to explain prediction") from e
