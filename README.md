# haptic-preference-learning

[中文版](README_zh-CN.md)
Personalizing haptic feedback is difficult because users struggle to assign absolute satisfaction scores. We introduce a preference-based method that infers a user’s latent utility surface from binary pairwise comparisons (A/B choices). A Gaussian Process (GP) preference model encodes smoothness and posterior uncertainty over the stimulus space, while an active query policy selects comparisons by maximizing expected information gain. We incorporate self-reported response uncertainty as per-comparison weights to down-weight ambiguous judgments. By emphasizing relative rather than absolute evaluations, the system mitigates rating fatigue and drift and avoids forcing users to map tactile sensations onto a numeric scale. In simulation with synthetic ground-truth preferences, the method accurately recovers preference maps and optima, achieving higher sample efficiency than uniform/query-agnostic sampling. We also release an open-source framework for interactive preference search over haptic signals.
Contributions.
(i) A binary, preference-driven learning approach to haptic personalization that reduces user fatigue and rating drift;
(ii) An interaction loop that weights comparisons by user-reported uncertainty to improve search efficiency;
(iii) An open-source, extensible code framework for interactive preference search over haptic signals.
![UI Demo](image.png)

## Quick Start
1. Clone the repo:
   ```bash
   git clone https://github.com/iSanshi/haptic-preference-learning.git
   cd haptic-preference-learning
   ```
2. (Optional) create a virtual environment:

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Launch the UI:
   ```bash
   python run_user_study_ui.py   # manual study workflow
   python run_auto_test_ui.py    # automated testing workflow
   ```

5. Press **Begin** in the UI. In user mode you manually pick A/B clips and rate certainty (1–5); in auto-test mode the system simulates preferences via a ground-truth function.
6. When a session completes, results are exported to `data/YYYYMMDD_<index>/session.json` and `log.txt`.

## Project Layout
```
.
├── requirements.txt
├── README.md
├── README.zh-CN.md
├── run_user_study_ui.py
├── run_auto_test_ui.py
├── tutorial
    ├── gp_interactive_Chinese.html
    └── gp_interactive_English.html
└── src
    └── preference_learning
        ├── __init__.py
        ├── audio
        │   ├── generator.py
        │   └── signal.py
        ├── gp
        │   ├── audio_gp.py
        │   ├── gaussian_process.py
        │   └── math_utils.py
        └── interface
            ├── __init__.py
            ├── session.py
            ├── ui_study.py
            └── logo/
```
