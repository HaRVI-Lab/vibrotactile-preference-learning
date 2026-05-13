<div align="center">

# Vibrotactile Preference Learning

### Uncertainty-Aware Preference Learning for Personalized Vibration Feedback

**ACM UMAP 2026**

Rongtao Zhang, Xin Zhu, Masoume Pourebadi Khotbehsara, Warren Dao, Erdem Biyik, Heather Culbertson

University of Southern California

[![Project Page](https://img.shields.io/badge/Project-Page-2f6f9f?style=for-the-badge)](https://isanshi.github.io/publication/vpl)
[![arXiv](https://img.shields.io/badge/arXiv-2604.20210-b31b1b?style=for-the-badge)](https://arxiv.org/abs/2604.20210)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey?style=for-the-badge)](https://creativecommons.org/licenses/by/4.0/)

[English](README.md) | [中文](README_zh-CN.md)

</div>

<p align="center">
  <img src="teaser_fig.jpg" alt="Vibrotactile Preference Learning teaser" width="82%">
</p>

## Overview

**Vibrotactile Preference Learning (VPL)** is an interactive framework for personalizing vibration feedback from pairwise user preferences.

Instead of asking users to give absolute satisfaction scores, VPL learns a user-specific vibrotactile utility function from simple A/B comparisons. The system combines:

- Gaussian-process-based preference learning
- expected-information-gain query selection
- confidence-aware weighting from user-reported uncertainty
- an interactive vibrotactile interface implemented with Xbox controller feedback

In our ACM UMAP 2026 study, VPL learns individualized vibration preferences within a 40-comparison interaction budget while keeping the experience comfortable and low workload.

## System

<p align="center">
  <img src="image2.png" alt="VPL interaction example" width="76%">
</p>

The user is repeatedly shown two candidate vibration signals. After choosing the preferred signal and reporting confidence, the model updates its posterior preference estimate and selects the next informative comparison.

The stimulus space is parameterized by four vibrotactile dimensions:

| Parameter | Description |
| --- | --- |
| `intensity` | Overall vibration strength |
| `texture` | Frequency-like tactile texture |
| `rhythm` | Temporal pulse structure |
| `grain` | Fine-grained vibration variation |

## Repository Contents

```text
.
├── run_user_study_ui.py      # Interactive pairwise preference-learning UI
├── run_auto_test_ui.py       # Automatic simulated evaluation mode
├── run_study.py              # Full study pipeline with final favorite-signal capture
├── xbox_control.py           # Standalone preferred-signal tuning tool
├── requirements.txt
└── src/preference_learning/
    ├── audio/                # Vibrotactile/audio signal generation
    ├── gp/                   # Gaussian process preference modeling
    ├── interface/            # UI and interaction logic
    └── evaluation.py         # Evaluation and analysis utilities
```

## Installation

This codebase requires Python 3.8 or newer.

```bash
git clone https://github.com/HaRVI-Lab/vibrotactile-preference-learning.git
cd vibrotactile-preference-learning

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

System requirements:

- Python 3.8+
- Tkinter support
- PortAudio-compatible audio output for `sounddevice`
- Optional Xbox controller for full interaction and favorite-signal capture

## Quick Start

### Interactive user-study interface

```bash
python run_user_study_ui.py
```

This starts the main VPL interface. The default study configuration uses a 40-query budget.

### Full study pipeline

```bash
python run_study.py
```

This runs the preference-learning session and then opens the favorite-signal recorder. The final preferred signal is saved as `favorite_signal.json` in the session folder.

### Automatic simulated evaluation

```bash
python run_auto_test_ui.py --iters 40 --gt center
python run_auto_test_ui.py --iters 40 --gt bimodal --seed 0
```

Useful arguments:

| Argument | Description |
| --- | --- |
| `--iters` | Number of preference queries |
| `--gt` | Simulated ground-truth preference type: `center`, `offset`, `bimodal`, or `ridge` |
| `--seed` | Random seed |
| `--ranges` | JSON string or path specifying parameter bounds |
| `--plot-res` | Resolution for visualization |
| `--plot-every` | Plot update frequency |

### Favorite-signal tuning

```bash
python xbox_control.py
```

## Controller Controls

| Input | Action |
| --- | --- |
| D-pad / left stick | Move UI focus |
| `A` | Play candidate A |
| `B` | Play candidate B |
| `X` | Activate focused button |
| `Start` | Start the session |

## Outputs

Completed sessions are saved under:

```text
data/YYYYMMDD_<index>/
```

Typical outputs include:

| File | Description |
| --- | --- |
| `session.json` | Structured log of queries, choices, confidence labels, model state, and final recommendation |
| `log.txt` | Human-readable session log |
| `favorite_signal.json` | Final preferred vibration signal recorded after the study |

`session.json` includes final recommendations, posterior summaries, information-gain histories, and automatic-evaluation metrics when available.

## Citation

If you use this code in academic work, please cite:

```bibtex
@misc{zhang2026vibrotactilepreferencelearninguncertaintyaware,
      title={Vibrotactile Preference Learning: Uncertainty-Aware Preference Learning for Personalized Vibration Feedback}, 
      author={Rongtao Zhang and Xin Zhu and Masoume Pourebadi Khotbehsara and Warren Dao and Erdem Bıyık and Heather Culbertson},
      year={2026},
      eprint={2604.20210},
      archivePrefix={arXiv},
      primaryClass={cs.HC},
      url={https://arxiv.org/abs/2604.20210}, 
}
```

## License

This repository is released under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).

## Acknowledgements

This project was developed at the University of Southern California as part of research on personalized haptic interaction and preference-based learning.

This codebase references content from the [UUPL repository](https://github.com/capy8ra/UUPL).
