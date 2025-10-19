# 触觉偏好学习系统 / Haptic Preference Learning Toolkit

English README: [README.md](README.md)

![UI Demo](image.png)

## 快速上手
1. 克隆仓库：
   ```bash
   git clone https://github.com/iSanshi/haptic-preference-learning.git
   cd haptic-preference-learning
   ```
2. 建议使用虚拟环境（可选）：
   
3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

4. 启动界面：
   ```bash
   python run_user_study_ui.py   # 用户实验流程
   python run_auto_test_ui.py    # 自动测试流程
   ```

5. 点击 **Begin** 开始。用户实验模式需手动选择 A/B 音频并给出 1–5 的不确定度等级；自动测试模式由系统自动迭代。
6. 会话完成后，数据会导出到 `data/YYYYMMDD_序号/` 下的 `session.json` 与 `log.txt`。

## 目录结构
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
