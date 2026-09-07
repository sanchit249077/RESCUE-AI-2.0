# ML Layer — RescueAI

The MVP starts with a transparent weighted risk engine so the prototype is explainable.

Recommended production path:

1. Build a labelled landslide inventory for NER.
2. Join each event/non-event sample with:
   - 24h / 72h / 7d rainfall
   - slope/aspect/elevation
   - geology/soil
   - land-cover change
   - distance to drainage/roads
   - historical susceptibility
3. Train a baseline model (Random Forest / XGBoost).
4. Compare against rainfall-only baselines.
5. Calibrate probability and report precision/recall, ROC-AUC and false-alarm rate.
6. Perform district-wise and temporal validation to avoid leakage.

Do not report synthetic demo performance as real accuracy.
