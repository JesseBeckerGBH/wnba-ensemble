#!/usr/bin/env python3
"""
node_wnba_engine/model/export_onnx.py

Export the trained WNBA ensemble models (moneyline + totals) from their
scikit-learn ``.pkl`` artifacts to portable ONNX graphs.

Each model is a:

    CalibratedClassifierCV( isotonic )            <- probability calibration
      └─ StackingClassifier
            ├─ LogisticRegression (scaled)        <- base
            ├─ XGBClassifier                      <- base
            ├─ LightGBM LGBMClassifier            <- base
            └─ LogisticRegression  (meta-learner)

skl2onnx handles the StackingClassifier + isotonic calibration; the XGBoost and
LightGBM base learners need their onnxmltools converters registered first
(skl2onnx does not ship them by default).

IMPORTANT — what ONNX does and does NOT cover:
    The .onnx graph is ONLY the feature-vector -> probability forward pass.
    Everything in predict.py that BUILDS the vector (DuckDB feature lookups,
    home-minus-away differentials, NaN imputation from ``col_medians`` in the
    JSON sidecar) is NOT in the graph. Whatever runtime loads the .onnx must
    reproduce that feature engineering itself. The JSON sidecar (feature order
    + medians) is therefore part of the deploy artifact, alongside the .onnx.

Usage:
    python model/export_onnx.py                 # export moneyline + totals
    python model/export_onnx.py --target moneyline
    python model/export_onnx.py --tolerance 1e-4

Outputs (next to the .pkl, same version stem):
    model/artifacts/wnba_moneyline_v_<ts>_moneyline.onnx
    model/artifacts/wnba_totals_v_<ts>_totals.onnx

Install the export toolchain first:
    pip install -r requirements-onnx.txt
"""

from __future__ import annotations

import argparse
import pathlib
import sys

import numpy as np

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from model.stack_train import load_latest_model, MODEL_DIR  # noqa: E402


def _register_boosted_converters() -> None:
    """Teach skl2onnx how to convert XGBoost + LightGBM estimators."""
    from skl2onnx import update_registered_converter
    from skl2onnx.common.shape_calculator import (
        calculate_linear_classifier_output_shapes,
    )
    from onnxmltools.convert.xgboost.operator_converters.XGBoost import (
        convert_xgboost,
    )
    from onnxmltools.convert.lightgbm.operator_converters.LightGbm import (
        convert_lightgbm,
    )
    from xgboost import XGBClassifier
    from lightgbm import LGBMClassifier

    update_registered_converter(
        XGBClassifier,
        "XGBoostXGBClassifier",
        calculate_linear_classifier_output_shapes,
        convert_xgboost,
        options={"nocl": [True, False], "zipmap": [True, False, "columns"]},
    )
    update_registered_converter(
        LGBMClassifier,
        "LightGbmLGBMClassifier",
        calculate_linear_classifier_output_shapes,
        convert_lightgbm,
        options={"nocl": [True, False], "zipmap": [True, False, "columns"]},
    )


def export_target(target: str, tolerance: float) -> pathlib.Path:
    """Convert the latest model for ``target`` to ONNX and verify parity."""
    from skl2onnx import convert_sklearn
    from skl2onnx.common.data_types import FloatTensorType
    import onnxruntime as ort

    meta = load_latest_model(target)
    model = meta["model"]
    feature_cols = meta["feature_cols"]
    n_features = len(feature_cols)
    pkl_path = pathlib.Path(meta["model_path"])
    onnx_path = pkl_path.with_suffix(".onnx")

    print(f"\n[{target}] version={meta['version']}  features={n_features}")
    print(f"  source: {pkl_path.name}")

    initial_types = [("input", FloatTensorType([None, n_features]))]
    onx = convert_sklearn(
        model,
        initial_types=initial_types,
        # emit a plain probability tensor (no ZipMap dict) so any runtime,
        # including the Rust `ort` crate or Node, can read column 1 directly.
        options={id(model): {"zipmap": False}},
        # The tree ensembles (XGBoost/LightGBM) and isotonic calibration emit
        # ops in the 'ai.onnx.ml' domain; pin it to opset 3, which is what the
        # onnxmltools/skl2onnx converters target, while keeping the standard
        # 'ai.onnx' domain modern.
        target_opset={"": 17, "ai.onnx.ml": 3},
    )
    onnx_path.write_bytes(onx.SerializeToString())
    print(f"  wrote:  {onnx_path.name}  ({onnx_path.stat().st_size / 1024:.0f} KB)")

    # ── Parity check: sklearn vs onnxruntime on representative inputs ──────────
    rng = np.random.default_rng(42)
    medians = np.array(meta["col_medians"], dtype=np.float32)
    samples = np.vstack(
        [
            np.tile(medians, (1, 1)),                       # the imputation row
            medians + rng.normal(0, 1, (16, n_features)),   # jittered around it
            rng.normal(0, 3, (16, n_features)),             # broad random
        ]
    ).astype(np.float32)

    sk_probs = model.predict_proba(samples)[:, 1]

    sess = ort.InferenceSession(
        onnx_path.as_posix(), providers=["CPUExecutionProvider"]
    )
    input_name = sess.get_inputs()[0].name
    # output[1] is the probabilities tensor when zipmap=False
    prob_output = sess.get_outputs()[1].name
    onnx_probs = sess.run([prob_output], {input_name: samples})[0]
    onnx_probs = np.asarray(onnx_probs)[:, 1]

    max_diff = float(np.max(np.abs(sk_probs - onnx_probs)))
    status = "OK" if max_diff <= tolerance else "FAIL"
    print(f"  parity: max|Δprob| = {max_diff:.2e}  (tol {tolerance:.0e}) -> {status}")
    if max_diff > tolerance:
        raise SystemExit(
            f"[{target}] ONNX parity check FAILED (max diff {max_diff:.2e} "
            f"> tol {tolerance:.0e}). The .onnx was written but does not match "
            f"the sklearn model — do not deploy it."
        )
    return onnx_path


def main() -> None:
    p = argparse.ArgumentParser(description="Export WNBA models to ONNX")
    p.add_argument(
        "--target",
        choices=["moneyline", "totals", "all"],
        default="all",
        help="Which model to export (default: all)",
    )
    p.add_argument(
        "--tolerance",
        type=float,
        default=1e-4,
        help="Max allowed |Δprob| between sklearn and ONNX (default: 1e-4)",
    )
    args = p.parse_args()

    print(f"[onnx] artifacts dir: {MODEL_DIR}")
    try:
        _register_boosted_converters()
    except ImportError as e:
        raise SystemExit(
            f"Missing ONNX export dependency: {e}\n"
            f"Install with: pip install -r requirements-onnx.txt"
        )

    targets = ["moneyline", "totals"] if args.target == "all" else [args.target]
    written = []
    for t in targets:
        try:
            written.append(export_target(t, args.tolerance))
        except FileNotFoundError as e:
            print(f"[{t}] SKIP: {e}")

    if written:
        print("\n[done] exported:")
        for w in written:
            print(f"  {w}")
    else:
        print("\n[done] nothing exported (no trained models found).")


if __name__ == "__main__":
    main()
