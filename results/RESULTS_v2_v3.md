# JevTraffic v2 / v3 实验结果（SUMO · SingleTSCBaselines）

任务：SingleTSCBaselines（SUMO + TransSimHub），12 个真实路口 × easy/normal 两种路网 × 5 种需求模式，每 5 s 决策一次，1000 s 一个 episode。
指标：ATT 平均通行时间（秒，越低越好），由 SUMO tripinfo 计算；特种车辆单独统计 timeLoss。完整表格见 [sumo/summary.md](sumo/summary.md)，由 `scripts/analyze_sumo.py` 生成；逐次运行的 JSON 只保存在服务器上。

- 训练路口（9 个）：北京 ×6、天津、成都 ×2。**留出路口**：France_Massy、SouthKorea_Songdo、Hongkong_YMT。**留出需求模式**：random_perturbation。
- 分组：seen = 训练路口 × 4 种训练模式；pattern = 训练路口 × 留出模式；junction = 留出路口 × 全部模式。
- 事件：none；官方 `event_1`；两组随机事件 `random:1/2`（1 组事故封道 + 1–3 辆特种车）。
- 规则基线和 UniTSA 跑 3 个 SUMO 种子，Jev 跑种子 0。按场景配对后，约 1% 以内的差异应视为噪声。

## v2：MaxPressure 蒸馏的 7B Jev + 上下文智能体 + 特殊事件

**E1/E2 无事件**（ATT / 相对 MaxPressure）

| 控制器 | seen | pattern | junction |
|---|---|---|---|
| MaxPressure | 39.2 | 39.2 | 53.9 |
| FixTime | 41.6 / +7.9% | 42.1 / +8.5% | 52.5 / +0.3% |
| Qwen2.5-7B 零样本 | 45.8 / +16.5% | 48.4 / +23.7% | 58.5 / +7.3% |
| Jev 7B（`sumo-distill`） | 39.5 / +0.4% | 39.9 / +1.7% | 52.3 / −2.9% |
| Jev 7B（CityFlow adapter 起步，`sumo-distill-fromcf`） | 39.5 / +0.3% | 39.8 / +1.3% | 51.5 / −4.1% |

**E3 上下文智能体**（留出路口）：触发式 (`triggered`) 只在 1.2–1.9% 的步上额外调用一次 Jev，每步 73–103 ms。每步都调用 (`always`) 时为 258–340 ms，而 ATT 没有更好（`event_1` 下分别为 55.0 和 54.8）。

**E4 特殊事件**：250/250 辆特种车被识别，特种车 timeLoss 从 30–31 s 降到 15.4 s（`event_1`），从 24–25 s 降到 13.8 s（随机事件）。可观测封道的检出数：规则检测器 160/198，Jev（触发式）123/194，Jev（每步）148/195。随机事件下误报 14–15 次（每步调用时 23 次）。

**E5 长期记忆 + 周期微调**（3 个留出路口，各 14 个模拟日）：共享模型已经优于 MaxPressure（−0.7% / −7.2% / −8.0%）。daily、weekly、auto 训练出的路口 LoRA 在回放验证日上都没有带来提升，所以**一次都没有部署**，4 种策略结果相同。`auto` 只花 400–700 s 训练，不存参数，是合理的默认值。

## v3：UniTSA 作教师，小 Jev 学生

UniTSA（IEEE TVT 2024）：PPO + 运动 token Transformer，动作为保持/切换。我们训练了一个跨 9 个训练路口的**通用模型**（2M 步，79 分钟），在留出路口上各训练一个**从零开始**的模型，并在 6 个路口上从通用模型出发做**逐路口微调**（各 300k 步）。训练配置见 [unitsa/](unitsa/)。

**UniTSA 通用模型零样本**：无事件时为 38.0 / −1.9%、38.5 / −0.8%、50.1 / −5.1%（seen / pattern / junction）。它在所有分组上都优于 MaxPressure 和 v2 Jev，唯一的例外是 Hongkong_YMT（41.6，MaxPressure 为 39.0，v2 Jev 为 36.5）。

**学生**：Qwen2.5-0.5B / 1.5B + LoRA，回答“保持还是切换？”，用教师的动作概率做软蒸馏（6.5 万条），同时训练特殊事件问题。`compact` 状态约 220 token，`full` 约 320 token。

离线与教师的一致率：验证集约 87%，留出模式约 86%，留出路口 73–77%。

**相对 UniTSA 通用模型的 ATT（按场景配对，负值 = 比 UniTSA 好）**

| 控制器 | 无事件 seen | 无事件 junction | event_1 seen | 随机事件 junction | 在线一致率 | ms/决策 |
|---|---|---|---|---|---|---|
| UniTSA 逐路口微调 | −3.8% | −2.7% | −4.7% | −2.4% | – | 8.6（CPU） |
| UniTSA 逐路口从零训练 | – | +0.4% | – | +0.8% | – | 7.1（CPU） |
| MaxPressure | +2.9% | +7.0% | +1.7% | +7.1% | – | – |
| v2 Jev 7B | +3.4% | +3.8% | +2.5% | +3.5% | – | 117 |
| 学生 0.5B compact | +0.1% | +0.4% | −1.6% | +0.2% | 0.83 | 33 |
| 学生 0.5B full | +0.1% | −1.4% | +0.2% | −1.1% | 0.83 | 33 |
| 学生 1.5B compact | −0.2% | −1.5% | +0.6% | −1.6% | 0.83 | 37 |

**学生 + 事件预案**（特种车 timeLoss，秒）

| 控制器 | event_1 | 随机事件 | 封道检出 |
|---|---|---|---|
| UniTSA（无预案） | 30.8 | 21.7 | – |
| 学生 0.5B compact | 19.0 | 15.2 | 73/221 |
| 学生 0.5B full | 19.6 | 15.0 | 168/218 |
| 学生 1.5B compact | 19.7 | 15.8 | 115/206 |
| v2 Jev 7B | 15.3 | 13.8 | 123/194 |

**推理开销**（训练后的学生，compact 状态，[sumo/bench/](sumo/bench/)）

| 模型 | 设备 | batch 1 | batch 8（每决策） | 显存 |
|---|---|---|---|---|
| UniTSA（0.33M actor 参数） | CPU 单线程 | 3.6–8.6 ms | – | – |
| 0.5B，CUDA graphs（`--compile`） | GPU | **4.6 ms** | **2.5 ms** | 1.3 GB |
| 0.5B，普通推理 | GPU | 17.3 ms | 3.2 ms | 1.2 GB |
| 1.5B，CUDA graphs | GPU | 7.6 ms | 6.0 ms | 4.2 GB |
| 0.5B | CPU 8 线程 | 229 ms | 236 ms | – |
| v2 Jev 7B | GPU | 73–117 ms | 33–45 ms | 14.6 GB |

编译后的概率与普通推理最多相差 0.02（0.5B），尚未用编译模式做完整的在线评测。

## 结论

1. UniTSA 是更强的教师：零样本优于 MaxPressure 1–5%，在 SouthKorea_Songdo 上逐路口微调后优于 MaxPressure 18.7%。
2. 0.5B 学生在 ATT 上与 UniTSA 通用模型持平（±1.5%），GPU + CUDA graphs 下单次决策 4.6 ms，与 UniTSA 的 CPU 开销同一量级。它比 7B 快 15–25 倍，显存少约 11 倍。CPU 上不可用。
3. 特殊事件是 Jev 相对 UniTSA 的增量：特种车延误下降约 30–40%，而总 ATT 不变。识别封道需要 full 状态。
4. 学生仍落后 UniTSA 逐路口微调 2–4%。下一步：逐路口微调学生，或用仿真结果（反事实 rollout）作训练信号，超越模仿上限。
