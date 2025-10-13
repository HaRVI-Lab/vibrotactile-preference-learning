# 音频偏好学习系统说明 / Audio Preference Learning Overview

## 中文说明
### 功能概览
- **高斯过程偏好建模**：支持成对比较、处理不确定度权重，并利用信息增益选择下一组查询。
- **音频信号工具链**：根据振幅、频率、密度、梯度四个参数生成音频，可试听、保存及提取特征。
- **侧边栏界面**：通过 Tkinter 展示 A/B 音频、记录交互、查看日志与波形。
- **自动导出数据**：每次会话结束后，自动在 `data/YYYYMMDD_编号/` 下生成 `session.json` 与 `log.txt`，便于后续分析。

### 使用指南
1. 安装依赖（示例）：
   ```bash
   pip install numpy scipy matplotlib pygame sounddevice
   ```
   仅浏览界面时，可不安装播放相关库。
2. 启动界面：
   ```bash
   python run_user_study_ui.py   # 用户实验模式
   python run_auto_test_ui.py    # 自动测试模式
   ```
   若已设置 `PYTHONPATH=src`，也可运行 `python -m preference_learning.interface.ui_study`。
3. 点击 **Begin** 开始会话：
   - **User Study**：试听 A/B 音频，选择偏好并给出 1–5 的不确定度等级。
   - **Auto Test**：系统根据真值函数自动迭代更新。
4. **Stop** 暂停会话，**Reset** 重置为初始状态。

### 目录结构
```
.
├── run_user_study_ui.py        # 用户实验入口
├── run_auto_test_ui.py         # 自动测试入口
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
            └── ui_study.py       # 统一 UI（支持两种模式）
```

### 模块说明
- `run_user_study_ui.py` / `run_auto_test_ui.py`：入口脚本，会自动将 `src` 加入 `PYTHONPATH` 并启动对应模式。
- `preference_learning.audio`：音频生成与播放逻辑。
- `preference_learning.gp`：高斯过程核心与音频参数化扩展。
- `preference_learning.interface.session`：维护会话状态、记录指标并导出结果。
- `preference_learning.interface.ui_study`：唯一的 Tkinter 图形界面，实现用户实验与自动测试。

## English Guide
### Features
- **GP preference learning** with uncertainty weighting and information-gain query selection.
- **Audio synthesis** utilities to generate, normalise, and analyse four-parameter signals.
- **Unified sidebar UI** built with Tkinter for controlling sessions, previewing waveforms, and reviewing logs.
- **Automatic export**: after each run, results are saved to `data/YYYYMMDD_<index>/session.json` and `log.txt`.

### Quick Start
1. Install dependencies:
   ```bash
   pip install numpy scipy matplotlib pygame sounddevice
   ```
   Audio libraries are optional if you only need the UI.
2. Launch either mode:
   ```bash
   python run_user_study_ui.py   # user study workflow
   python run_auto_test_ui.py    # automated testing workflow
   ```
   Alternatively run `python -m preference_learning.interface.ui_study` when `PYTHONPATH=src` is set.
3. Press **Begin** to start:
   - **User Study** – listen to A/B clips, choose a preference, and rate certainty (1–5).
   - **Auto Test** – the system simulates responses using the selected ground-truth function.
4. Use **Stop** to pause and **Reset** to restart a fresh session.

### Project Layout
```
.
├── run_user_study_ui.py        # entry point for manual study
├── run_auto_test_ui.py         # entry point for automated test
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
            └── ui_study.py
```

### Modules
- `run_user_study_ui.py` / `run_auto_test_ui.py` – launcher scripts that set up `PYTHONPATH` and start the UI.
- `preference_learning.audio` – audio synthesis, playback, and feature helpers.
- `preference_learning.gp` – Gaussian-process core and audio-specific wrapper.
- `preference_learning.interface.session` – session controller, metrics, and export pipeline.
- `preference_learning.interface.ui_study` – the only Tkinter UI used going forward.
