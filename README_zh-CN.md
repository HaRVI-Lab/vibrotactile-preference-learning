<div align="center">

# Vibrotactile Preference Learning

### 面向个性化振动反馈的、结合不确定性的偏好学习

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

## 项目概述

**Vibrotactile Preference Learning (VPL)** 是一个通过用户成对偏好来个性化振动反馈的交互式框架。

VPL 不要求用户给出绝对满意度评分，而是通过简单的 A/B 比较学习用户特定的振动触觉效用函数。系统结合了：

- 基于高斯过程的偏好学习
- 基于期望信息增益的查询选择
- 来自用户自报不确定度的置信度感知权重
- 基于 Xbox 控制器振动反馈实现的交互式振动触觉界面

在我们的 ACM UMAP 2026 研究中，VPL 能够在 40 次比较的交互预算内学习个体化振动偏好，同时保持舒适、低负担的用户体验。

## 系统

<p align="center">
  <img src="image2.png" alt="VPL interaction example" width="76%">
</p>

<p align="center">
  <img src="image1.png" alt="VPL user interface and selection workflow" width="76%">
</p>

系统会反复向用户呈现两个候选振动信号。用户选择更偏好的信号并报告置信度后，模型更新其后验偏好估计，并选择下一组信息量较高的比较。

刺激空间由四个振动触觉维度参数化：

| 参数 | 描述 |
| --- | --- |
| `intensity` | 整体振动强度 |
| `texture` | 类似频率的触觉纹理 |
| `rhythm` | 时间脉冲结构 |
| `grain` | 细粒度振动变化 |

## 仓库内容

```text
.
├── run_user_study_ui.py      # 交互式成对偏好学习界面
├── run_auto_test_ui.py       # 自动化模拟评估模式
├── run_study.py              # 包含最终偏好信号采集的完整实验流程
├── xbox_control.py           # 独立的偏好信号调节工具
├── requirements.txt
└── src/preference_learning/
    ├── audio/                # 振动触觉/音频信号生成
    ├── gp/                   # 高斯过程偏好建模
    ├── interface/            # UI 与交互逻辑
    └── evaluation.py         # 评估与分析工具
```

## 安装

本代码库需要 Python 3.8 或更新版本。

```bash
git clone https://github.com/HaRVI-Lab/vibrotactile-preference-learning.git
cd vibrotactile-preference-learning

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

系统要求：

- Python 3.8+
- Tkinter 支持
- 可供 `sounddevice` 使用的 PortAudio 兼容音频输出
- 可选：Xbox 控制器，用于完整交互和最终偏好信号采集

## 快速开始

### 交互式用户实验界面

```bash
python run_user_study_ui.py
```

该命令会启动主 VPL 界面。默认实验配置使用 40 次查询预算。

### 完整实验流程

```bash
python run_study.py
```

该命令会先运行偏好学习实验，然后打开最终偏好信号记录器。最终偏好的信号会以 `favorite_signal.json` 保存到会话文件夹中。

### 自动化模拟评估

```bash
python run_auto_test_ui.py --iters 40 --gt center
python run_auto_test_ui.py --iters 40 --gt bimodal --seed 0
```

常用参数：

| 参数 | 描述 |
| --- | --- |
| `--iters` | 偏好查询次数 |
| `--gt` | 模拟地面真值偏好类型：`center`、`offset`、`bimodal` 或 `ridge` |
| `--seed` | 随机种子 |
| `--ranges` | 指定参数边界的 JSON 字符串或文件路径 |
| `--plot-res` | 可视化分辨率 |
| `--plot-every` | 图像更新频率 |

### 偏好信号调节

```bash
python xbox_control.py
```

## 手柄控制

| 输入 | 操作 |
| --- | --- |
| 方向键 / 左摇杆 | 移动 UI 焦点 |
| `A` | 播放候选 A |
| `B` | 播放候选 B |
| `X` | 激活当前焦点按钮 |
| `Start` | 开始实验 |

## 输出

完成的实验会话会保存到：

```text
data/YYYYMMDD_<index>/
```

典型输出包括：

| 文件 | 描述 |
| --- | --- |
| `session.json` | 查询、选择、置信度标签、模型状态和最终推荐的结构化日志 |
| `log.txt` | 便于阅读的会话日志 |
| `favorite_signal.json` | 实验后记录的最终偏好振动信号 |

`session.json` 包含最终推荐、后验摘要、信息增益历史，以及可用时的自动化评估指标。

## 引用

如果你在学术工作中使用本代码，请引用：

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

## 许可证

本仓库采用 [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/) 许可发布。

## 致谢

本项目在 University of Southern California 开发，是个性化触觉交互与基于偏好的学习研究的一部分。

本代码参考了 [UUPL 代码库](https://github.com/capy8ra/UUPL) 的内容。
