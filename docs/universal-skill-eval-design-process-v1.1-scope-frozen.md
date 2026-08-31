# 《通用 Skill Eval Design Process v1.1（Scope-Frozen）》

Status: Scope-Frozen
Version: v1.1
Date: 2026-08-20

## 1. v1.1 项目边界

### 1.1 本版本要解决什么

v1.1 定义一条覆盖约 80%～90% 常规 Skill Eval 场景的通用主路径：

```text
输入 Target Skill
↓
Agent 理解 Skill
↓
Agent 设计可验证的 Benchmark / Eval Definition
↓
执行最低结构合法性检查
↓
冻结 Benchmark Definition
↓
开发者通过 CLI 执行
↓
生成多维 Metric、Overall Score、Gate Result 和完整证据链
```

本版本解决以下问题：

1. 如何把一个 Target Skill 的要求转化为可验证的 `Requirement`。
2. 如何把 Requirement 转化为具有明确成功、失败条件的 `Contract`。
3. 如何根据风险和重要程度设计 `Test Case` 与最低覆盖。
4. 如何为 Case 准备输入、Fixture 和运行环境。
5. 如何提前确定每个判断所需要的 `Evidence`。
6. 如何把结果验证和工作流验证放入同一套 Contract 驱动体系。
7. 如何选择 deterministic、rubric-based 或 mixed Grader。
8. 如何从 Grader Result 聚合多个 Metric。
9. 如何通过 Rubric、Weight 和 Gate 表达质量、重要程度与硬性约束。
10. 如何在同一 Benchmark 下比较 Baseline 与 Candidate。
11. 如何在执行前判断 Eval Definition 是否最低可执行、结构合法。
12. 如何冻结评测设计，避免执行后根据结果临时改变评分规则。
13. 如何执行 Case、保存 Episode、收集证据并生成 Scorecard。
14. 如何保留：

```text
Requirement
→ Contract
→ Test Case
→ Episode
→ Evidence
→ Grader Result
→ Metric Result
→ Gate Result
→ Scorecard
```

的完整可追溯链。

### 1.2 本版本不解决什么

v1.1 不试图证明一套 Eval 在科学意义上是“优秀 Benchmark”。

本版本不包含：

- Eval Quality Score
- Meta-Eval
- 多 Agent Benchmark 审查
- Benchmark Quality Scoring
- Empirical Benchmark Validation
- Human Alignment Validation
- Sensitivity / Specificity 分析
- Automatic Eval Optimization
- 自动证明 Case 具有充分代表性
- 自动证明 Rubric 与人类判断完全一致
- 自动证明 Benchmark 不存在偏差
- 通用 Concept Model 的完整设计
- Pydantic Schema
- YAML / JSON Schema
- CLI 命令与参数
- Runner 实现
- Grader Runtime 实现
- 文件目录结构
- SKILL.md
- 完整 Framework 架构

本版本只定义：

> 一套从 Target Skill 到 Frozen Benchmark Definition，再到可追溯评估结果的通用设计与执行流程。

### 1.3 Scope-Frozen 原则

v1.1 遵守以下收缩原则：

1. 不为每个设计活动创建独立的重量级概念。
2. 只有进入核心依赖链的对象才作为核心 Artifact。
3. Risk Analysis 是设计动作，不是独立大型子系统。
4. Pilot、Independent Review、Unseen Regression 不进入 Core v1。
5. Eval Design Validation 只判断最低可执行性和结构合法性。
6. Workflow Compliance 使用与 Outcome Eval 相同的 Contract、Case、Evidence、Grader、Metric、Gate 体系。
7. Framework 必须支持多维 Metric。
8. Framework 默认支持生成加权 Overall Score，但 Benchmark 可以明确关闭它。
9. Overall Score 不能替代 Metric Scorecard、Gate Result、Case Result 和 Evidence。
10. 所有评分政策必须在正式执行前冻结。

## 2. 压缩后的两阶段通用主流程

### 2.1 总流程图

```text
┌──────────────────────────────────────────────────────────────┐
│ Part 1：Agent Design                                        │
│                                                              │
│ Target Skill                                                 │
│   ↓                                                          │
│ 1. Skill Understanding & Scope                               │
│   ↓                                                          │
│ 2. Requirement Extraction                                    │
│   ↓                                                          │
│ 3. Contract, Criticality & Failure Modes                      │
│   ↓                                                          │
│ 4. Risk-driven Case Matrix & Coverage                         │
│   ↓                                                          │
│ 5. Input, Fixture & Environment Design                        │
│   ↓                                                          │
│ 6. Evidence & Workflow Trace Design                           │
│   ↓                                                          │
│ 7. Grader & Assertion Design                                  │
│   ↓                                                          │
│ 8. Metric, Rubric, Weight, Gate & Baseline Design             │
│   ↓                                                          │
│ 9. Eval Design Validation                                     │
│   ├── INVALID → 返回 Part 1 修正                              │
│   └── VALID                                                   │
│         ↓                                                    │
│ 10. Freeze Benchmark / Eval Definition                        │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ Part 2：CLI Execution                                       │
│                                                              │
│ Frozen Benchmark Definition                                  │
│   ↓                                                          │
│ 11. Create Run & Prepare Environment                          │
│   ↓                                                          │
│ 12. Execute Cases & Produce Episodes                          │
│   ↓                                                          │
│ 13. Collect, Qualify & Preserve Evidence                      │
│   ↓                                                          │
│ 14. Grade, Aggregate, Apply Gates & Generate Scorecard        │
│                                                              │
│ 输出：                                                       │
│ - Case Results                                               │
│ - Grader Results                                             │
│ - Outcome Metrics                                            │
│ - Workflow Metrics                                           │
│ - Baseline Comparison                                        │
│ - Weighted Overall Score（默认开启，可关闭）                  │
│ - Gate Status                                                │
│ - Evidence / Trace                                           │
│ - Failure Reasons                                            │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 真实依赖关系，而不是机械线性关系

这 14 个阶段存在一条主依赖链，但 Part 1 不是完全单向的瀑布流程。

以下反馈是允许且必要的：

```text
Contract Design
    ↔ Case Design
    ↔ Evidence Design
    ↔ Grader Design
    ↔ Metric Design
```

例如：

- 如果一个 Contract 无法找到可靠 Evidence，需要回到 Contract，重新明确可观察成功条件。
- 如果 Grader 需要的 Evidence 无法产生，需要修改 Evidence Producer、Case 或 Grader。
- 如果一个 Metric 没有足够的 Grader Result 支撑，需要重新设计 Metric 或补充 Case。
- 如果 Critical Contract 的风险无法被现有 Case 覆盖，需要增加 Case 或改变 Case Strategy。
- 如果 Baseline 无法在相同条件下运行，需要调整比较范围，而不是执行后强行比较。

但是，一旦进入第 10 阶段并冻结 Benchmark Definition，正式 Run 不得再反向修改评分规则。

如果执行后发现 Eval 设计问题，应当：

```text
保留原 Run
↓
修订 Benchmark Definition
↓
形成新的 Benchmark Version
↓
创建新的 Run
```

不能直接覆盖旧结果。

## 3. 步骤 1 → 步骤 14

# 第 1 部分：Agent Design

## 步骤 1：Skill Understanding & 范围

**分类：Mandatory**

### 输入

- Target Skill
- `SKILL.md`
- Skill 引用的 references
- scripts
- assets
- validator
- tool requirements
- workflow requirements
- output requirements
- 用户补充要求
- 项目约束
- 接口约束
- 可用运行环境信息

### 目标

理解被测 Skill 实际声明了什么、依赖什么、应该产出什么，以及本次 Eval 的范围是什么。

本阶段既要理解功能，也要识别执行约束，不能只阅读最终输出描述。

### Agent 要回答的问题

- Target Skill 的入口是什么？
- 它接受什么输入？
- 它应该产生什么输出？
- 它声明了哪些成功能力？
- 它要求读取哪些资源？
- 它要求使用哪些工具？
- 它是否要求特定步骤顺序？
- 它是否要求产生中间 Artifact？
- 它是否要求执行 validator？
- 它是否规定停止、重试、取消或用户授权行为？
- 它是否明确禁止某些操作？
- 哪些内容是 Skill 本身声明的？
- 哪些内容来自用户？
- 哪些内容来自项目或接口约束？
- 哪些依赖能够在 Eval 环境中准备？
- 哪些内容明确不进入本次 Eval 范围？
- 当前证据只支持静态理解，还是已经存在可复用的运行事实？

### 关键规则

`Evaluation Charter`、`Skill Identity`、`Source Inventory` 不再作为三个独立顶层阶段。

它们被收缩为本阶段中的设计活动：

- 确认被测对象
- 确认来源
- 确认范围
- 确认依赖
- 确认不在范围内的内容

### 输出

- 被测 Skill 的明确边界
- Skill 能力与工作流的理解记录
- Requirement 候选来源
- Eval 范围与非目标
- 依赖资源清单
- 已知环境前置条件
- 已知的不确定项

这些内容可以作为 Part 1 工作记录，最终必要信息进入 Frozen Benchmark Definition；不要求为每一项创建独立重量级 Artifact。

### 下游依赖

- Requirement Extraction
- Contract Design
- Input / Fixture / Environment 设计
- Workflow Compliance Design

## 步骤 2：Requirement Extraction

**分类：Mandatory**

### 输入

- Skill Understanding
- Skill 文件与相关资源
- 用户要求
- 项目约束
- 接口约束
- 其他明确来源

### 目标

将自然语言描述、工作流约束和输出要求整理为可追溯的 `Requirement`。

v1.1 只保留 `Requirement` 作为核心概念，不再把 `Claim` 作为独立一等概念。

### Requirement 来源

每条 Requirement 必须能够说明来源属于：

- `skill`
- `user`
- `project`
- `interface`
- `other`

这里规定的是来源分类方法，不规定具体 Schema。

### Agent 要回答的问题

- 这条要求来自哪里？
- 它是明确要求，还是 Agent 的推断？
- 如果是推断，是否有足够依据保留为 Requirement？
- 这条 Requirement 描述的是结果，还是执行过程？
- 它是否能够被观察和验证？
- 它是否包含多个不同责任，需要后续拆分？
- 它是否只是背景信息，而不是可评估要求？
- 它是否与其他 Requirement 重复或冲突？
- 如果不同来源发生冲突，应以什么范围或优先级处理？
- 这条 Requirement 是否属于本次 Eval 范围？

### 关键规则

- 不得把所有 Skill 文档内容机械转换成 Requirement。
- 不得把 Agent 自己期望的行为伪装成 Skill Requirement。
- 无法确认来源的内容应标记为不确定，而不是伪装成已确认事实。
- Requirement 可以描述 Outcome，也可以描述 Workflow。
- Requirement 本身不必直接可评分，但必须能在下一阶段被转化为可验证 Contract；否则需要收缩、澄清或排除。

### 输出

- Requirement 集合
- 每条 Requirement 的来源
- Requirement 的范围状态
- Outcome / Workflow 方向的初步分类
- Requirement 之间的重复、冲突或不确定项记录

### 下游依赖

- Contract Design
- Coverage 检查
- Eval Design Validation
- 最终 Requirement → Result 追溯链

## 步骤 3：Contract, Criticality & 失败模式

**分类：Mandatory**

### 输入

- Requirement
- Skill 范围
- 已知约束
- 已知风险与历史失败
- 工作流要求

### 目标

将 Requirement 转化为可观察、可验证、可产生明确通过或失败判断的 Contract。

Contract 是 Eval 的核心验证单元。

### Agent 要回答的问题

- 这条 Requirement 是否已经足够可验证？
- 一条 Requirement 是否包含多个独立责任？
- 是否需要拆成多个 Contract？
- 多条 Requirement 是否可以由同一个 Contract 共同验证？
- 什么条件代表 Contract 成功？
- 什么条件代表 Contract 失败？
- 成功与失败能否通过实际 Evidence 区分？
- 该 Contract 约束的是结果还是工作流？
- 该 Contract 的重要程度是什么？
- 失败会造成普通质量下降，还是使 Skill 结果不可接受？
- 可能出现哪些 Failure Mode？
- 哪些 Failure Mode 需要后续单独 Case？
- 该 Contract 是否可能进入 Gate？
- 如果进入 Gate，原因是否是业务或安全上的硬约束，而不是单纯“比较重要”？

### Criticality 的作用

Criticality 是 Contract 的必要设计判断，用于影响：

- Case 数量
- Case 风险类型
- Coverage 要求
- Evidence 强度
- Grader 严格程度
- 是否考虑 Gate

Criticality 不等于 Gate。

一个 Contract 可以很重要但仍然只影响 Metric；Gate 必须有明确的不可接受失败语义。

### Risk Analysis 的位置

v1.1 不把 Risk Analysis 建模为独立大型 Artifact。

Risk Analysis 作为本阶段和下一阶段的内部设计动作，其结果分布在：

- Contract Criticality
- Failure Modes
- Case Strategy
- Coverage
- Evidence 要求
- Gate 判断

### 输出

- 可验证 Contract
- Requirement → Contract 映射
- Contract 的成功条件
- Contract 的失败条件
- Contract Criticality
- 主要 Failure Modes
- Outcome Contract 或 Workflow Contract 的适用方向
- Gate 候选，而不是最终 Gate

### 下游依赖

- Test Case Design
- Coverage Design
- Evidence Design
- Grader Design
- Gate Design
- Eval Design Validation

## 步骤 4：Risk-driven Case Matrix & Coverage

**分类：Mandatory**

### 输入

- Contract
- Criticality
- Failure Modes
- 可用输入空间
- 运行成本与环境限制

### 目标

为 Contract 设计能够暴露真实失败风险的 Test Case，并建立 Contract 与 Case 之间的覆盖关系。

### Agent 要回答的问题

- 每个 Contract 至少需要多少个 Case？
- 一个 Case 是否能同时验证多个 Contract？
- 如果可以，是否仍然能够清楚定位失败原因？
- 一个 Contract 是否需要多个 Case？
- 多个 Case 是简单输入变化，还是覆盖不同风险？
- 哪些 Failure Mode 值得形成独立 Case？
- 是否需要：

  - happy path
  - negative
  - boundary
  - variation
  - failure
  - adversarial

- 哪些类型与本 Skill 无关，不应机械加入？
- Critical Contract 是否只由一个过于理想化的 Case 支撑？
- Case 是否包含足够明确的输入、执行条件和预期观察？
- Case 是否可重复执行？
- Case 是否可能因为环境问题产生误判？
- Case 的预期结果能否由后续 Evidence 和 Grader 验证？
- 工作流要求是否需要独立 Workflow Case？
- 是否存在一个结果正确但过程违规的 Case？
- 是否存在过程看似正确但最终结果错误的 Case？

### Coverage 原则

v1.1 不规定所有 Contract 必须拥有固定数量的 Case。

最低原则是：

1. 每个进入范围的 Contract 必须有合法 Case 支撑。
2. Critical Contract 必须满足 Benchmark 声明的最低覆盖政策。
3. Case 数量由风险、输入变化和 Failure Mode 决定。
4. 不要求每个 Contract 机械拥有所有 Case 类型。
5. 一个 Contract 可以由多个 Case 支撑。
6. 一个 Case 可以覆盖多个 Contract，但必须保留可解释的映射。
7. Coverage 只能说明“设计上有 Case 覆盖”，不能自动证明 Benchmark 具有科学代表性。

### 输出

- Test Case 集合
- Contract → Case 映射
- Case Strategy
- Case 风险类型
- Coverage 状态
- Critical Contract 的覆盖结果
- 仍未覆盖的 Failure Mode
- 因环境或成本暂时不覆盖的范围

### 下游依赖

- Fixture / Input Design
- Evidence Design
- Grader Design
- Coverage Validation
- Execution

## 步骤 5：Input, Fixture & Environment Design

**分类：核心阶段 Mandatory；具体 Fixture 为 Conditional**

### 输入

- Test Case
- Case 执行条件
- Target Skill 输入要求
- 工具与环境依赖
- 可复现性要求

### 目标

确保每个 Case 有明确、可准备、可重复使用的输入与运行条件。

### Agent 要回答的问题

- Case 的输入是什么？
- 输入是静态数据、临时生成数据、用户交互，还是外部系统状态？
- 输入是否需要被固定？
- 是否需要 Fixture 才能保证可重复性？
- Fixture 应该包含什么，排除什么？
- Fixture 是否可能泄漏预期答案？
- Fixture 是否只验证理想输入？
- 是否需要多个输入变体？
- 环境中必须具备哪些工具、权限、设备、服务或依赖？
- 哪些前置条件必须在 Run 前验证？
- 环境前置条件失败时，应标记为环境不可执行，还是 Contract Failure？
- Case 之间是否需要隔离？
- Case 是否会改变外部状态？
- 状态变化如何恢复或记录？
- 是否需要用户授权才能执行某些动作？
- 是否需要控制时间、随机性或网络条件？

### Mandatory 与 Conditional 的边界

所有 Case 都必须声明输入和执行前置条件。

但不是所有 Case 都必须拥有独立 Fixture。

Fixture 在以下情况下需要：

- 需要固定输入以保证重复执行；
- 需要准备文件、资源或状态；
- 需要隔离外部依赖；
- 需要比较 Baseline 与 Candidate；
- 需要防止输入漂移；
- 需要复现特定 Failure Mode。

对于简单纯文本 Skill，输入本身可能已经足够，不需要额外 Fixture。

### 输出

- Case Input
- 必要 Fixture
- 环境前置条件
- 状态准备要求
- 隔离与恢复要求
- 权限与用户授权要求
- 环境失败的分类规则

### 下游依赖

- Evidence Producer
- Run Preparation
- Case Execution
- Baseline Comparison

## 步骤 6：Evidence & Workflow Trace Design

**分类：Evidence 为 Mandatory；Workflow Trace 为 Conditional**

### 输入

- Contract
- Test Case
- Case Input / Fixture
- 成功与失败条件
- Workflow Requirements
- 环境与工具能力

### 目标

在执行前确定：

> 要判断一个 Contract 是否满足，必须产生什么可审查证据？

Evidence Design 必须先于正式执行完成，不能看到结果后再临时选择有利证据。

### Agent 要回答的问题

- 每个 Contract 需要什么 Evidence？
- Evidence 由谁或什么产生？
- Evidence 在执行前、执行中还是执行后产生？
- Evidence 是最终输出、中间 Artifact、日志、状态、截图、结构化结果、Tool Trace，还是人工观察？
- Evidence 是否足以区分成功与失败？
- Evidence 是否能够证明负面事实，例如“未执行禁止操作”？
- Evidence 是否完整，还是只保留摘要？
- Evidence 是否需要保留原始版本？
- Evidence 是否可能被后处理覆盖？
- Evidence 与具体 Run、Episode、Case 如何对应？
- Grader 能否稳定读取该 Evidence？
- Evidence 缺失应被视为：

  - Case Failure
  - Evidence Failure
  - Environment Failure
  - Not Executed
  - Unknown

- Workflow Contract 需要观察哪些过程信息？
- 是否需要 Tool Trace？
- 是否需要步骤顺序？
- 是否需要用户授权记录？
- 是否需要中间 Artifact？
- 是否需要 validator 结果？
- 是否需要停止、重试、取消的状态变化记录？

### Workflow Trace 的适用条件

当 Contract 只约束最终结果时，不强制生成完整 Workflow Trace。

当 Skill 明确要求以下任一内容时，应设计对应 Trace 或过程 Evidence：

- Required Steps
- Required Tool Usage
- Forbidden Actions
- Step Ordering
- User Authorization
- Intermediate Artifact
- Validator Execution
- State Transition
- Stop / Retry / Cancel 行为

### 输出

- Contract / Case 所需 Evidence
- Evidence Producer
- Evidence 产生时机
- Evidence 完整性与资格要求
- Workflow Trace 要求
- Evidence 缺失分类
- Evidence → Grader 的消费关系候选

### 下游依赖

- Grader Design
- Workflow Grader
- Eval Design Validation
- Episode Execution
- Evidence Preservation

## 步骤 7：Grader & Assertion Design

**分类：Mandatory**

### 输入

- Contract
- Test Case
- Expected Assertion
- Evidence 要求
- Workflow Trace 要求
- Failure Modes

### 目标

为每个可评分判断设计明确的 Grader，并确保 Grader 实际能够消费已经声明的 Evidence。

### Agent 要回答的问题

- 这个判断能否通过 deterministic code 完成？
- 是否存在明确、稳定、可重复的断言？
- 是否需要容差？
- 是否存在多个合法输出？
- 如果输出质量具有主观性，是否需要 Rubric-based Grader？
- 是否需要 Human 或 LLM 判断？
- 主观 Grader 的判断维度是否清楚？
- 是否应使用 Mixed Grader？
- Grader 消费哪些 Evidence？
- Evidence 格式与 Grader 是否兼容？
- Evidence 缺失时 Grader 应如何处理？
- Grader 是判断单一 Contract，还是多个 Contract？
- 一个 Grader 失败后能否定位具体 Failure Reason？
- Grader 能否区分：

  - Skill Failure
  - Workflow Failure
  - Evidence Failure
  - Environment Failure
  - Grader Error

- 是否存在由被测 Agent 自己声明“通过”的自评分问题？
- Grader 是否会意外使用不应看到的预期答案？
- Grader 输出能否被后续 Metric 聚合？

### Grader 选择原则

#### 技术主题：Deterministic Grader

适用于：

- 结构合法性
- 精确字段
- 文件存在性
- validator 结果
- 状态变化
- 工具调用记录
- 步骤顺序
- 禁止行为检测
- 可计算数值
- 明确成功条件

#### 技术主题：Rubric-based Grader

适用于：

- 表达质量
- 视觉质量
- 解释完整性
- 风格一致性
- 用户体验
- 多个合法答案之间的质量差异

#### 技术主题：Mixed Grader

适用于同时包含硬约束与质量判断的结果。

例如：

```text
结构合法性 → deterministic
内容质量   → rubric-based
```

### 关键规则

- 客观可判定内容优先使用 deterministic Grader。
- 主观质量不能伪装成确定性断言。
- Human / LLM Rubric 不是所有 Skill 的必需能力。
- 每个 Grader 必须声明所消费的 Evidence。
- Grader 不得依赖未声明或无法产生的 Evidence。
- Grader Result 必须保留判断结果和 Failure Reason。
- Workflow Grader 与 Outcome Grader 使用相同的 Grader 接口思想，不建立第二套独立 Framework。

### 输出

- Grader
- Expected Assertion
- Evidence → Grader 映射
- Grader Result 类型与失败分类要求
- Deterministic / Rubric-based / Mixed 的选择
- Workflow Grader

### 下游依赖

- Metric Design
- Rubric Design
- Gate Design
- Eval Design Validation
- Part 2 Grading

## 步骤 8：Metric, Rubric, Weight, Gate & 基线 Design

**分类：核心阶段 Mandatory；各组成项按适用性启用**

本阶段统一设计结果聚合与比较政策。它们相互依赖，因此不再拆成多个重量级顶层阶段。

### 技术主题：8.1 Metric Design

**实例化状态：Mandatory，且必须是多维 Metric**

#### 输入

- Contract
- Case
- Grader
- Grader Result
- Outcome / Workflow 评估方向

#### Agent 要回答的问题

- 需要报告哪些独立能力维度？
- 每个 Metric 由哪些 Grader Result 支撑？
- Metric 是 Case-level、Contract-level 还是跨 Case 聚合？
- Metric 的分母是什么？
- 未执行 Case 如何处理？
- Evidence 缺失是否进入失败分母？
- 不适用 Case 是否排除？
- Metric 是否混合了不应混合的不同能力？
- Workflow Compliance 是否需要独立 Metric？
- 是否需要保留样本数量和 Case 分布？
- Metric 是否能定位弱点，而不只是产生一个总分？

#### 输出

- 多维 Metric
- Grader → Metric 映射
- 聚合规则
- 样本计数规则
- 未执行、不适用、错误状态的处理规则

### 技术主题：8.2 Rubric Design

**实例化状态：Conditional**

#### 适用条件

- 质量不能通过简单断言判断；
- 存在多个合法输出；
- 需要判断程度，而不是简单 Pass / Fail；
- 需要 Human 或 LLM Grader；
- 需要把多个细粒度质量判断映射为分数。

#### Agent 要回答的问题

- Rubric 的每个等级代表什么可观察差异？
- 不同评分者是否能理解并重复使用？
- Rubric 是否直接基于 Evidence？
- Rubric 是否混合了多个无法区分的维度？
- 是否需要保留每个维度的子评分？
- Rubric 分数如何进入 Metric？
- Rubric 是否会掩盖硬性 Contract Failure？

#### 输出

- Rubric
- 等级或评分维度
- Rubric → Metric 映射
- 评分依据

### 技术主题：8.3 Weight & Overall Score Design

**实例化状态：Framework 默认支持并默认启用；Benchmark 可以关闭**

#### Agent 要回答的问题

- 是否需要 Overall Score？
- 如果需要，哪些 Metric 进入 Overall Score？
- 每个 Metric 的 Weight 是多少？
- 权重是否反映该 Skill 的实际目标？
- Workflow Metric 是否进入 Overall Score？
- 某些 Metric 是否只展示、不参与 Overall？
- 权重总和是否合法？
- 缺失 Metric 如何处理？
- Gate Failure 是否改变 Overall Score，还是单独决定接受状态？
- 是否存在“高总分掩盖关键失败”的风险？

#### 固定政策

Framework 默认支持并默认生成：

```text
Weighted Overall Score
```

但 Benchmark 可以在冻结前明确设置：

```text
overall_score_enabled = false
```

这是行为规则，不是本版本的 Schema 设计。

即使启用 Overall Score，最终结果仍然必须保留：

- 每个独立 Metric
- Metric 样本数量
- 每个 Case Result
- 每个 Grader Result
- Gate Result
- Evidence Trace
- Failure Reason

Overall Score 只是汇总视图，不能代替多维 Scorecard。

#### 输出

- Overall Score 是否启用
- Metric Weight
- Metric → Overall Score 映射
- Overall Score 聚合政策

### 技术主题：8.4 Gate Design

**实例化状态：Conditional；Framework Core 必须支持**

#### 适用条件

Gate 用于表达：

> 即使总体分数较高，某个关键失败仍然使结果不可接受。

适用于：

- 安全要求
- 数据完整性
- 用户授权
- 禁止操作
- 不可恢复的破坏性行为
- 必须产生的关键 Artifact
- 必须执行的 validator
- 核心功能完全失败
- 明确的发布或接受底线

#### Agent 要回答的问题

- 哪些失败不能只通过扣分处理？
- Gate 引用 Contract、Grader Result 还是 Metric？
- Gate 阈值是什么？
- Gate Failure 的语义是什么？
- Gate 是否有足够 Evidence 支撑？
- Gate 是否会因环境不可用而错误触发？
- Gate 是否与 Criticality 混淆？
- Gate 是否能够被一个高 Overall Score 掩盖？

#### 关键规则

- Critical Contract 不自动成为 Gate。
- Gate 必须引用合法 Metric、Contract Result 或 Grader Result。
- Gate 规则必须在执行前冻结。
- Gate Result 与 Overall Score 并列展示。
- Gate Failure 不删除其他 Metric 和 Case Result。
- 是否通过 Gate 与 Overall Score 是两个不同问题。

#### 输出

- Gate
- Gate 引用
- Gate 阈值
- Gate Failure 语义
- Gate Result 的展示政策

### 8.5 基线 Design

**实例化状态：Conditional；Framework Core 必须支持**

#### 适用条件

Baseline 在以下情况下有价值：

- 需要比较 Skill v1 与 Skill v2；
- 需要比较 Candidate Skill 与现有方案；
- 需要判断新 Skill 是否真的改善结果；
- 绝对分数难以解释；
- 需要观察 Metric Improvement 或 Regression。

#### Agent 要回答的问题

- Baseline 是什么？
- Baseline 是否能运行相同 Case？
- Baseline 与 Candidate 是否使用相同 Fixture、环境和 Grader？
- Baseline 是否在相同 Benchmark Definition 下运行？
- 哪些 Metric 可以合法比较？
- Baseline 缺失时是否仍能产生 Candidate 的绝对结果？
- Baseline 是否已冻结，还是需要在本次 Run 中重新执行？
- 差异来自 Skill，还是来自环境、输入或 Grader 变化？

#### 关键规则

- Baseline 不是所有 Skill Eval 的必需对象。
- 第一个版本只要求支持：

```text
Baseline vs Candidate
```

在同一 Frozen Benchmark Definition 下进行比较。

- Unseen Regression 不属于 Core v1。
- Baseline 和 Candidate 必须使用可比条件。
- 不可比结果不得伪装成 Improvement 或 Regression。

#### 输出

- Baseline 是否启用
- Baseline 对象
- 可比较 Metric
- 比较条件
- Improvement / Regression 的计算政策

### 本阶段整体输出

- 多维 Metric
- Conditional Rubric
- Weight
- Overall Score 政策
- Conditional Gate
- Conditional Baseline
- 完整聚合与比较政策

### 下游依赖

- Eval Design Validation
- Freeze
- Part 2 Grading
- Scorecard Generation

## 步骤 9：Eval Design 验证

**分类：Mandatory**

### 输入

Part 1 当前形成的 Benchmark / Eval Definition，包括：

- Requirement
- Contract
- Criticality
- Test Case
- Coverage
- Input / Fixture / Environment
- Evidence
- Workflow Trace
- Grader
- Metric
- Rubric
- Weight
- Gate
- Baseline

### 目标

只判断：

> 这份 Eval Definition 是否达到最低可执行和结构合法要求？

### 必须检查的问题

- ID 是否唯一？
- 所有引用是否存在？
- 每条进入范围的 Requirement 是否有必要 Contract？
- Contract 是否能够追溯到 Requirement？
- Critical Contract 是否具有符合最低政策的 Case？
- Case 是否引用合法 Contract？
- Coverage 是否满足 Benchmark 声明的最低要求？
- Case 所需 Input 是否能够准备？
- Fixture 引用是否存在？
- 环境前置条件是否声明？
- 每个必要 Evidence 是否存在 Producer？
- Workflow Trace 是否能够产生所需过程 Evidence？
- Grader 要求的 Evidence 是否能够产生？
- Grader 引用的 Evidence 是否合法？
- Metric 是否具有合法 Grader Result 来源？
- Rubric 是否有合法消费方和评分依据？
- Weight 是否合法？
- Overall Score 启用时，参与聚合的 Metric 与权重是否完整？
- Gate 是否引用合法 Metric、Contract Result 或 Grader Result？
- Baseline 比较是否使用可比 Case 与 Metric？
- 是否存在执行前尚未明确的关键判断规则？

### 输出

只能输出：

```text
VALID
```

或：

```text
INVALID
+ Validation Errors
```

### 明确禁止的输出

本阶段不输出：

- Eval Quality Score
- Benchmark Quality Score
- “该 Eval 是优秀 Benchmark”的结论
- Case 代表性科学评分
- Human Alignment 评分
- Sensitivity / Specificity 评分
- Meta-Eval 结果

### 下游依赖

- `VALID` → 冻结 Benchmark Definition
- `INVALID` → 返回 Part 1 对应阶段修正

## 步骤 10：Freeze Benchmark / Eval Definition

**分类：Mandatory**

### 输入

- 通过最低设计验证的 Eval Definition
- 全部 Case、Evidence、Grader 与评分政策
- Baseline 与环境政策
- Validation Result = VALID

### 目标

在正式执行前冻结评测设计，建立“设计阶段”和“执行阶段”的边界。

### Agent / Framework 要回答的问题

- 当前 Definition 是否已经通过 Validation？
- 所有评分规则是否已经明确？
- Case 是否已经确定？
- Evidence 要求是否已经确定？
- Grader 是否已经确定？
- Metric、Rubric、Weight、Gate 是否已经确定？
- Baseline 比较政策是否已经确定？
- Overall Score 是否启用？
- 是否还存在必须由执行结果决定的评分规则？
- 如何区分当前 Definition 与未来修订版本？

### 冻结规则

冻结后，正式 Run 不得修改：

- Requirement
- Contract
- Criticality
- Case
- Coverage Policy
- Expected Assertion
- Evidence Requirement
- Grader
- Metric
- Rubric
- Weight
- Gate
- Baseline Comparison Policy
- Overall Score Policy

执行后发现问题可以形成新的 Definition，但不得覆盖旧 Definition 或旧 Run。

### 输出

```text
Frozen Benchmark / Eval Definition
```

它是 Part 2 CLI Execution 的权威输入。

### 下游依赖

- Run Creation
- Baseline Execution
- Candidate Execution
- Result Traceability
- Version Comparison

# 第 2 部分：CLI Execution

Part 2 在本版本中只定义执行方法，不设计 CLI 命令、参数、文件结构或 Runtime 架构。

## 步骤 11：Create Run & Prepare Environment

**分类：Mandatory**

### 输入

- Frozen Benchmark Definition
- Candidate Skill
- Conditional Baseline
- Case Inputs
- Fixtures
- 环境前置条件
- 权限与授权条件

### 目标

为一次正式执行建立独立 Run，并确认执行环境满足最低前置条件。

### CLI / Framework 要解决的问题

- 使用的是哪一个 Frozen Benchmark Definition？
- 执行对象是哪个 Candidate？
- 是否执行 Baseline？
- Case、Grader、Metric 和 Gate 是否与被冻结版本一致？
- Input 与 Fixture 是否可用？
- 所需工具、权限、依赖和服务是否可用？
- 是否获得必要的用户授权？
- Case 是否需要状态隔离？
- 环境前置检查失败时，应如何分类？
- 是否存在会污染后续 Case 的历史状态？
- Run 是否能够与其他 Run 区分？
- 是否能够保留本次执行的实际环境信息？

### 关键规则

- Run 必须引用 Frozen Definition。
- 环境失败不能自动等同于 Skill Failure。
- 环境可用也不能自动证明 Skill Contract 通过。
- Baseline 与 Candidate 比较必须尽量使用相同条件。
- 任何执行期偏差必须记录，不能静默忽略。

### 输出

- Run
- 实际执行对象
- 实际环境记录
- 可执行 Case 集合
- 环境前置检查结果
- Baseline / Candidate 执行计划
- Not Executable 或可执行状态

### 下游依赖

- Episode Execution
- Evidence Qualification
- Scorecard 中的运行上下文

## 步骤 12：Execute Cases & Produce Episodes

**分类：Mandatory**

### 输入

- Run
- Frozen Test Cases
- Candidate Skill
- Conditional Baseline
- Inputs
- Fixtures
- 环境状态
- Workflow Trace 要求

### 目标

按照 Frozen Definition 逐个执行 Case，并为每次 Case 执行生成可评分记录单元。

在 v1.1 中，`Episode` 的操作性含义是：

> 某个 Case 在某个 Run 中针对某个被测对象的一次实际执行记录。

这里不进一步设计 Episode Schema。

### CLI / Framework 要解决的问题

- 当前执行的是哪个 Case？
- 当前被测对象是 Candidate 还是 Baseline？
- 实际输入与冻结输入是否一致？
- Case 是否完整执行？
- 是否发生重试？
- 是否发生取消或停止？
- 是否需要用户交互？
- 是否按要求获取用户授权？
- 是否产生必要中间 Artifact？
- 是否执行必要 validator？
- 是否调用所需工具？
- 是否发生禁止操作？
- 执行顺序是否能够保留？
- 实际结果与运行状态是否完整保存？
- Case 未完成的原因是什么？
- 同一个 Case 的多次尝试如何区分？

### 关键规则

- Case Execution 负责产生原始输出、Artifact 和 Trace，不负责自行宣布最终得分。
- 被测 Skill 的自我报告不能直接作为权威 Grader Result。
- 失败 Episode 必须保留，不得只保留成功结果。
- 重试记录不能覆盖第一次失败。
- Baseline 和 Candidate 的 Episode 必须能够区分。
- 实际执行偏离冻结 Case 时必须记录偏差。

### 输出

- Episode
- Raw Output
- Intermediate Artifact
- Tool Trace
- Workflow Trace
- Validator Result
- Execution Status
- Retry / Stop / Cancel 记录
- 实际输入与环境上下文
- 原始 Failure Information

### 下游依赖

- Evidence Collection
- Outcome Grader
- Workflow Grader
- Case Result
- Baseline Comparison

## 步骤 13：Collect, Qualify & Preserve Evidence

**分类：Mandatory**

### 输入

- Episode
- Raw Output
- Artifact
- Tool Trace
- Workflow Trace
- Validator Result
- Frozen Evidence Requirements

### 目标

把执行中产生的原始信息整理为能够被 Grader 合法消费的 Evidence，并保存其与 Run、Episode、Case、Contract 的关系。

### CLI / Framework 要解决的问题

- 每项 Evidence 来自哪个 Episode？
- Evidence 是否由声明的 Producer 产生？
- Evidence 是否完整？
- Evidence 是否被截断？
- Evidence 是否经过转换或后处理？
- 原始 Evidence 是否仍然保留？
- Evidence 是否满足 Grader 的输入要求？
- Evidence 是否能够证明对应 Contract？
- Evidence 是否只是一段摘要，而不是完整证明？
- Evidence 是否与实际 Tool Trace 一致？
- Evidence 是否与实际 Artifact 一致？
- Evidence 是否来自正确的 Candidate 或 Baseline？
- Evidence 缺失属于什么失败类型？
- Evidence 是否包含敏感信息，需要安全处理？
- 是否能够从最终结果回溯到原始 Evidence？

### Evidence Qualification 原则

应区分：

- Evidence 存在
- Evidence 完整
- Evidence 与 Episode 对应
- Evidence 可被 Grader 消费
- Evidence 足以支持判断

仅有一个文件路径或摘要，不必然代表完整 Evidence。

### 输出

- Outcome Evidence
- Workflow Evidence
- Qualified Evidence
- Incomplete / Missing Evidence 状态
- Evidence 与 Episode / Case / Contract 映射
- Evidence Provenance
- 原始 Artifact 与 Trace 的保留结果

### 下游依赖

- Grader Execution
- Failure Classification
- Metric Aggregation
- Scorecard
- Evidence Traceability

## 步骤 14：Grade, Aggregate, Apply Gates & Generate Scorecard

**分类：Mandatory**

### 输入

- Frozen Graders
- Qualified Evidence
- Episode
- Test Case
- Contract
- Metric
- Rubric
- Weight
- Gate
- Conditional Baseline
- Overall Score Policy

### 目标

依次完成：

```text
Evidence
↓
Grader Result
↓
Case / Contract Result
↓
Metric Result
↓
Rubric Aggregation
↓
Weight Aggregation
↓
Gate Evaluation
↓
Baseline Comparison
↓
Scorecard
↓
Overall Score
```

### CLI / Framework 要解决的问题

- 每个 Grader 是否获得了所需 Evidence？
- Grader 是否正常完成？
- Grader Error 与 Skill Failure 是否被区分？
- 每个 Case 验证了哪些 Contract？
- 一个 Case 部分通过时如何记录？
- Contract 在多个 Case 中的结果如何聚合？
- 每个 Metric 使用了哪些 Grader Result？
- Metric 的分母和样本数是多少？
- Not Executed、Not Applicable、Environment Failure 如何处理？
- Rubric 评分是否保留维度明细？
- Weight 是否使用冻结值？
- Overall Score 是否启用？
- Gate 引用是否能够实际计算？
- Gate Failure 是否正确反映不可接受失败？
- Baseline 与 Candidate 是否可比？
- Improvement / Regression 是否来自相同条件？
- 最终结果能否追溯到原始 Evidence？
- 是否保留所有 Failure Reason？

### 结果聚合顺序

#### 1. 技术主题：Grader Result

每个 Grader 基于声明的 Evidence 产生判断。

#### 2. 技术主题：Case / Contract Result

把 Grader Result 关联回 Case 与 Contract。

#### 3. 技术主题：Metric Result

按冻结规则聚合多个 Grader Result，并保留：

- Metric Value
- Sample Count
- Included Cases
- Excluded Cases
- Failure Distribution

#### 4. 技术主题：Rubric Aggregation

仅在适用时执行，并保留子维度评分。

#### 5. 技术主题：Weighted Overall Score

默认启用。

如果 Benchmark 在冻结前关闭 Overall Score，则不生成总体分数，但仍生成所有 Metric 与 Scorecard。

#### 6. 技术主题：Gate Evaluation

Gate 独立判断。

即使 Gate Failure，仍然保留并计算其他可计算 Metric；不得只输出一个失败状态。

#### 7. 基线 Comparison

仅比较可比 Metric，并输出：

- Improvement
- Regression
- No Material Change
- Not Comparable

#### 8. 字段或协议值：Scorecard

Scorecard 是权威结果视图，必须至少能够展示：

- Outcome Metrics
- Workflow Metrics
- Overall Score 或 Disabled 状态
- Gate Status
- Case Results
- Contract Results
- Grader Results
- Sample Counts
- Evidence
- Workflow Trace
- Baseline Comparison
- Failure Reasons
- Environment / Execution Exceptions

### 输出

- Grader Results
- Case Results
- Contract Results
- Outcome Metrics
- Workflow Metrics
- Rubric Results
- Weighted Overall Score，或明确 Disabled
- Gate Results
- Baseline Comparison
- Scorecard
- Failure Reasons
- 完整 Evidence Trace

### 最终追溯关系

```text
Requirement
↓
Contract
↓
Test Case
↓
Run / Episode
↓
Evidence / Workflow Trace
↓
Grader Result
↓
Case / Contract Result
↓
Metric Result
↓
Weight / Gate
↓
Overall Score / Scorecard
```

## 4. 三条评估线如何嵌入同一主流程

## 技术主题：4.1 A. Outcome Eval

Outcome Eval 回答：

> Skill 做出来的结果怎么样？

### 主链

```text
Outcome Requirement
↓
Outcome Contract
↓
Test Case
↓
Input / Fixture
↓
Execution Episode
↓
Outcome Evidence
↓
Outcome Grader
↓
Outcome Metric
↓
Rubric / Weight
↓
Optional Gate
↓
Scorecard / Overall Score
```

### 主要评估内容

可能包括但不限于：

- Correctness
- Task Success
- Output Quality
- Robustness
- Efficiency
- Baseline Improvement
- Skill 专属能力 Metrics

Framework 不规定所有 Skill 必须使用这些固定 Metric，也不规定固定权重。

Agent 根据 Target Skill 生成实际 Metric。

## 技术主题：4.2 B. Workflow Compliance Eval

Workflow Compliance 回答：

> Skill 是否按照要求的方式执行？

Workflow Compliance 不建立第二套 Eval Framework，而是使用相同的核心链。

### 主链

```text
Workflow Requirement
↓
Workflow Contract
↓
Workflow Case
↓
Execution Episode
↓
Workflow Trace / Process Evidence
↓
Workflow Grader
↓
Workflow Metric
↓
Optional Weight
↓
Optional Gate
↓
Scorecard
```

### 可验证内容

- Required Steps
- Required Tool Usage
- Forbidden Actions
- Step Ordering
- User Authorization
- Intermediate Artifact
- Validator Execution
- State Transition
- Stop Behavior
- Retry Behavior
- Cancel Behavior

### 与 Outcome Eval 的共享部分

两条线共享：

- Requirement
- Contract
- Criticality
- Case
- Coverage
- Evidence
- Grader
- Metric
- Rubric
- Weight
- Gate
- Run
- Episode
- Scorecard

主要差异只是所观察 Evidence 的类型：

```text
Outcome Eval    → 更关注结果 Artifact 和最终状态
Workflow Eval   → 更关注 Tool Trace、步骤、授权和中间状态
```

一个 Case 可以同时产生 Outcome Evidence 和 Workflow Evidence。

一个最终结果可能出现：

```text
Outcome PASS
Workflow FAIL
```

也可能出现：

```text
Outcome FAIL
Workflow PASS
```

这两个结果必须分别保留，不能互相覆盖。

## 4.3 C. Eval Design 验证

Eval Design Validation 回答：

> 这份 Eval Definition 是否达到最低可执行和结构合法要求？

它位于 Part 1 的末端、Freeze 之前。

### 验证链

```text
Draft Eval Definition
↓
ID / Reference / Coverage / Evidence / Grader / Metric / Weight / Gate Validation
↓
VALID
或
INVALID + Validation Errors
```

### 与另外两条线的区别

Outcome Eval 和 Workflow Compliance Eval 评估的是：

```text
Target Skill
```

Eval Design Validation 检查的是：

```text
Eval Definition
```

因此：

- Eval Design Validation 不进入 Skill Overall Score。
- `VALID` 不代表 Benchmark 是高质量 Benchmark。
- `INVALID` 只表示 Definition 当前不能安全、完整地执行。
- 它不输出百分制质量评分。
- 它不判断人类是否认可这套 Benchmark。
- 它不自动评估 Case 是否具有科学代表性。

## 4.4 三条线的统一关系

```text
                 ┌──────────────────────────────┐
                 │ Eval Design Validation       │
                 │ 检查 Definition 能否执行      │
                 └──────────────┬───────────────┘
                                │ VALID
                                ▼
                    Frozen Benchmark Definition
                                │
                 ┌──────────────┴───────────────┐
                 ▼                              ▼
        Outcome Eval                   Workflow Compliance
        评估结果质量                    评估执行方式
                 │                              │
                 └──────────────┬───────────────┘
                                ▼
                     Multi-dimensional Scorecard
                                │
                 ┌──────────────┴───────────────┐
                 ▼                              ▼
          Weighted Overall                Gate Status
          默认支持，可关闭                 独立硬约束
```

## 5. Core v1 能力清单

这里的“Core 能力”表示 Framework 主路径必须能够支持，并不表示每一个 Benchmark 都必须实例化所有对象。

| Core 能力 | Framework 是否必须支持 | 每个 Benchmark 是否必须实际使用 | 说明 |
|---|---:|---:|---|
| Skill Understanding | 是 | 是 | 必须完整理解被测 Skill 与范围 |
| Requirement | 是 | 是 | 统一核心需求概念，不保留独立 Claim |
| Requirement Source | 是 | 是 | 区分 skill、user、project、interface、other |
| Contract | 是 | 是 | Requirement 的可验证表达 |
| Criticality | 是 | 是 | 驱动覆盖、Evidence 强度和 Gate 候选 |
| Failure Modes | 是 | 是 | 作为 Contract 和 Case 设计判断 |
| Test Case | 是 | 是 | Contract 必须有 Case 支撑 |
| Coverage | 是 | 是 | 至少检查 Requirement、Contract 和 Critical Contract 覆盖 |
| Input | 是 | 是 | 每个 Case 必须有明确输入 |
| Fixture | 是 | 否，Conditional | 需要可重复、隔离或固定状态时使用 |
| Environment Requirement | 是 | 是 | 必须声明最低执行前置条件 |
| Evidence | 是 | 是 | Grader 的直接输入 |
| Evidence Producer | 是 | 是 | 必须说明 Evidence 如何产生 |
| Workflow Trace | 是 | 否，Conditional | 存在过程 Contract 时使用 |
| Grader | 是 | 是 | 支持 deterministic、rubric-based、mixed |
| Workflow Grader | 是 | 否，Conditional | 存在 Workflow Contract 时使用 |
| Metric | 是 | 是 | 必须产生多个有诊断价值的维度 |
| Rubric | 是 | 否，Conditional | 主观或分级质量判断时使用 |
| Weight | 是 | 否，Conditional | Overall Score 启用时使用 |
| Overall Score | 是 | 默认启用，可关闭 | 不能替代多维 Scorecard |
| Gate | 是 | 否，Conditional | 存在不可接受失败时使用 |
| Baseline | 是 | 否，Conditional | 需要 Candidate 比较时使用 |
| Eval Design Validation | 是 | 是 | 只检查最低可执行性和结构合法性 |
| Freeze | 是 | 是 | 执行前冻结 Benchmark Definition |
| Run | 是 | 是 | 一次正式执行上下文 |
| Episode | 是 | 是 | Case 在 Run 中的一次实际执行记录 |
| Grader Result | 是 | 是 | 保留判断和失败原因 |
| Metric Result | 是 | 是 | 保留值、样本数和来源 |
| Gate Result | 是 | 有 Gate 时必须 | 与 Overall Score 并列 |
| Scorecard | 是 | 是 | 权威多维结果视图 |
| Evidence Traceability | 是 | 是 | 从 Result 回溯到原始 Evidence |

### Core 中的 Mandatory / Conditional 边界

#### 所有常规 Eval 都必须存在

- Skill Understanding
- Requirement
- Contract
- Criticality
- Test Case
- Coverage
- Input
- Environment Requirement
- Evidence
- Grader
- Multi-dimensional Metric
- Eval Design Validation
- Freeze
- Run
- Episode
- Scorecard
- Evidence Traceability

#### Framework 必须支持，但具体 Benchmark 按条件启用

- Fixture
- Workflow Trace
- Workflow Grader
- Rubric
- Weight
- Gate
- Baseline

#### Overall Score 的特殊规则

- Framework 默认支持；
- Benchmark 默认生成；
- Benchmark 可以在执行前明确关闭；
- 即使关闭，Metric、Case Result、Gate Result 和 Evidence 仍然必须保留。

## 6. 技术主题：Advanced / Future Work

以下能力不进入 v1.1 Core 主路径。

## 技术主题：6.1 Pilot / Calibration

**分类：Optional / Advanced**

建议在以下情况下使用：

- 新 Grader；
- 新 Rubric；
- Human / LLM 主观评分；
- 高误报或高漏报风险；
- 复杂 Evidence Producer；
- 复杂 Workflow Trace；
- 高成本或高风险正式执行。

它的目的可以包括：

- 检查 Evidence 是否真的能够产生；
- 检查 Grader 是否误判；
- 检查 Rubric 是否可理解；
- 检查环境准备是否可重复；
- 在正式冻结前发现明显设计问题。

v1.1 不实现独立 Pilot System，也不把 Pilot 设为第一次 Eval Design 的强制阶段。

## 技术主题：6.2 Independent Review

**分类：Optional / Advanced**

适用于：

- 正式验收；
- 高风险 Skill；
- 大量主观 Rubric；
- 外部发布；
- 需要评测者与执行者角色分离；
- 需要独立证据复核。

Independent Review 不属于 Core Execution Chain，不要求每次常规 Eval 都执行。

## 技术主题：6.3 Unseen Regression

**分类：Optional / Advanced / Future Extension**

用于：

- 保留未参与开发调试的新 Case；
- 检查 Candidate 是否只针对已知 Case 过拟合；
- 进行更严格版本回归。

Core v1 只要求：

```text
Baseline vs Candidate
```

在同一套 Frozen Benchmark 上进行比较。

Unseen Regression 留待后续单独设计。

## 6.4 其他 Future Work

- 多 Agent Benchmark 审查
- Meta-Eval
- Benchmark Quality Score
- Empirical Benchmark Validation
- Human Alignment Validation
- Sensitivity / Specificity
- Inter-rater Reliability
- Automatic Eval Optimization
- 自动生成最优 Case
- 自动证明 Coverage 充分
- 自动调整 Metric Weight
- 自动发现 Benchmark 偏差
- 自动优化 Grader
- 跨 Benchmark 标准化 Overall Score
- 大规模统计显著性分析

这些能力不应反向扩大 v1.1 Core。

## 7. 技术主题：Framework Rules vs Agent Generated Eval Content

## 7.1 区分原则

Framework 负责规定：

> 一套 Eval 必须具备什么关系、声明什么依赖、满足什么最低合法性。

Agent 负责根据 Target Skill 生成：

> 具体评什么、怎么测、用什么证据、如何评分、什么失败不可接受。

Framework 不能把某个具体 Skill 的质量标准硬编码成所有 Skill 的规则。

## 7.2 对照表

| 领域 | Framework 固定规则 | Agent Generated Eval Content |
|---|---|---|
| Skill Scope | 必须明确被测对象与范围 | 具体 Skill、版本、入口、非目标 |
| Requirement | 统一使用 Requirement；必须有来源 | 具体 Requirement 内容 |
| Requirement Source | 来源必须可区分 | 某条 Requirement 来自 skill、user、project、interface 或 other |
| Contract | Requirement 必须转化为可验证 Contract | 具体成功与失败条件 |
| Criticality | 每个 Contract 必须进行重要性判断 | 某个 Contract 是高、普通或低关键性 |
| Failure Modes | Case 设计必须考虑真实失败风险 | 该 Skill 具体可能如何失败 |
| Test Case | Contract 必须有 Case 支撑 | 具体输入、场景和预期行为 |
| Coverage | 必须声明最低覆盖政策；Critical Contract 必须满足政策 | 某 Contract 需要几个 Case、覆盖哪些风险 |
| Fixture | Framework 支持受控 Fixture | 具体文件、数据、状态或环境 |
| Evidence | 每个 Grader 必须声明消费什么 Evidence | 具体日志、输出、Artifact、Trace |
| Evidence Producer | 必须存在合法 Evidence Producer | 具体由脚本、工具、执行过程或人工观察产生 |
| Workflow | Workflow Requirement 使用同一 Contract 链 | 具体 required step、tool、ordering、authorization |
| Grader | Grader 必须有合法 Evidence 输入 | 具体断言、判断逻辑或 Rubric |
| Deterministic Grading | 客观判断优先 deterministic | 具体字段、阈值、validator、结构断言 |
| Rubric | 主观评分必须声明维度和依据 | 具体质量等级与描述 |
| Metric | 每个 Metric 必须有合法 Grader Result 来源 | 具体 Correctness、Quality 或 Skill-specific Metric |
| Weight | Weight 必须在执行前冻结且合法 | 具体 Metric 权重 |
| Overall Score | 默认支持并默认启用；可明确关闭 | 是否关闭、哪些 Metric 参与 |
| Gate | Gate 必须引用合法结果且执行前冻结 | 哪些失败进入 Gate、阈值是多少 |
| Baseline | 比较必须使用可比条件 | 选择哪个 Baseline、比较哪些 Metric |
| Validation | 只输出 VALID 或 INVALID + errors | 修复具体 Definition 错误 |
| Freeze | 正式执行前必须冻结设计 | 当前 Benchmark 的具体冻结内容 |
| Run | Run 必须引用 Frozen Definition | 当前 Candidate、Baseline 与环境 |
| Episode | 每次 Case 执行必须可追踪 | 具体执行输出、Trace、状态 |
| Scorecard | 必须保留多维结果、Gate 和 Evidence | 该 Skill 的实际分数与失败模式 |

## 7.3 Framework 不应固定的内容

Framework 不应统一规定：

- 所有 Skill 的 Correctness 权重；
- 所有 Skill 的 Robustness 权重；
- 所有 Skill 的 Efficiency 权重；
- 所有 Skill 都必须有相同 Metric；
- 所有 Contract 都必须有相同 Case 数；
- 所有 Skill 都必须使用 Fixture；
- 所有 Skill 都必须有 Baseline；
- 所有 Skill 都必须使用 Human / LLM Rubric；
- 所有 Skill 都必须有 Gate；
- 所有 Workflow Metric 都必须进入 Overall Score；
- 所有 Quality Metric 都使用同一阈值；
- 所有失败都算 Skill Failure；
- 所有 Benchmark 都必须运行 Pilot；
- 所有结果都必须经过 Independent Review。

这些内容必须由 Agent 根据 Target Skill、风险、成本和实际可观察证据进行设计。

## 8. 相比 v1 的主要变化

## 8.1 删除或合并的顶层概念

### Requirement / Claim 统一

v1 中可能并列出现的：

```text
Requirement / Claim
```

在 v1.1 中统一为：

```text
Requirement
```

不同来源通过 Requirement Source 区分：

- skill
- user
- project
- interface
- other

`Claim` 不再作为 Core 一等概念。

### Evaluation Charter 被合并

`Evaluation Charter` 不再作为独立大型阶段。

其有效内容被吸收到：

```text
Step 1：Skill Understanding & Scope
```

包括：

- 被测对象
- Eval 范围
- 非目标
- 来源
- 环境边界

### Skill Identity / Source Inventory 被合并

它们不再单独形成顶层阶段，而是作为 Skill Understanding 的内部工作。

Framework 仍要求知道评的是谁、Requirement 来自哪里，但不为此增加额外主流程层级。

### Risk Analysis 被降为设计动作

Risk Analysis 不再作为独立大型 Artifact 或子系统。

它的结果进入：

- Contract Criticality
- Failure Modes
- Case Strategy
- Coverage
- Evidence Strength
- Gate 判断

## 8.2 主流程被压缩

v1 中较多的细分步骤被压缩为 14 个核心阶段：

```text
Part 1：10 个 Agent Design 阶段
Part 2：4 个 CLI Execution 阶段
```

压缩重点包括：

- Charter、Identity、Inventory 合并到 Skill Understanding；
- Risk Analysis 合并到 Contract 和 Case Design；
- Metric、Rubric、Weight、Gate、Baseline 合并为评分与比较政策阶段；
- Part 2 中执行、证据、评分与报告保留逻辑分层，但不扩展 Runtime 架构。

## 8.3 被降级的能力

以下能力从潜在主路径中移出：

### 技术主题：Pilot / Calibration

从常规必需步骤降为：

```text
Optional / Advanced
```

### 技术主题：Independent Review

从 Core Execution Chain 移出，降为：

```text
Optional / Advanced
```

### 技术主题：Unseen Regression

从第一次 Eval Design 的要求移出，降为：

```text
Optional / Advanced / Future Extension
```

Core v1 只保留同一 Benchmark 下的 Baseline vs Candidate。

## 8.4 被强化的能力

### Overall Score 被明确为默认能力

v1.1 明确：

- 多维 Metric 是 Mandatory；
- Framework 默认支持 Weighted Overall Score；
- Benchmark 默认生成 Overall Score；
- Benchmark 可以在执行前明确关闭；
- Overall Score 不能替代 Metric Scorecard；
- Overall Score 不能掩盖 Gate Failure；
- Overall Score 必须能够追溯到参与聚合的 Metric 和 Weight。

### Workflow Compliance 正式进入统一主链

Workflow Compliance 不再被视为外置附加系统。

它被明确纳入：

```text
Workflow Requirement
→ Workflow Contract
→ Workflow Case
→ Workflow Trace / Evidence
→ Workflow Grader
→ Workflow Metric
→ Optional Weight / Gate
→ Scorecard
```

### Eval Design Validation 被严格收缩

v1.1 将其限制为：

```text
Minimum Executability
+
Structural Legality
```

它只输出：

```text
VALID
```

或：

```text
INVALID + Validation Errors
```

不输出 Eval Quality Score，也不发展成 Meta-Eval。

### Freeze 被强化为 Part 1 与 Part 2 的正式边界

v1.1 明确规定：

- Case、Evidence、Grader、Metric、Weight、Gate 必须在执行前冻结；
- 执行后不能通过修改 Benchmark 让当前结果通过；
- 设计修订必须形成新的 Definition 和新的 Run；
- 历史失败与历史 Evidence 必须保留。

### 证据链被强化

最终权威结果必须能够恢复：

```text
Requirement
→ Contract
→ Test Case
→ Run
→ Episode
→ Evidence
→ Grader Result
→ Metric Result
→ Gate Result
→ Scorecard
```

不能只输出一个总分。

## 8.5 从旧人工 Eval 保留的方法

v1.1 保留了旧人工 Eval 中已经被真实流程证明有价值的方法：

- 先完整理解 Skill，再设计 Case；
- 从 Requirement 转化为可验证 Contract；
- 通过 Criticality 和 Failure Mode 决定 Case 覆盖；
- 一个 Contract 可以由多个 Case 支撑；
- 正式执行前验证最低环境前置条件；
- 使用受控输入和 Fixture 提高可重复性；
- 对客观结果优先使用 deterministic Grader；
- 对主观质量保留 Rubric-based 判断；
- 把 Outcome Evidence 与 Workflow Trace 都作为可评分证据；
- 区分预期步骤、禁止行为、工具调用、顺序、授权和中间 Artifact；
- 保留失败 Evidence，而不是只保存成功结果；
- 将 Baseline 与 Candidate 放在相同评测条件下比较；
- 使用 Gate 表达不可被高总分掩盖的关键失败；
- 冻结评分规则，防止执行后改变验收标准；
- 区分 Skill Failure、Environment Failure、Evidence Failure 与 Grader Error；
- 保留可复核的结果报告和证据链；
- 不把未完成、不可执行或证据不足错误报告为 PASS。

## 8.6 从旧人工 Eval 删除的项目特有设计

v1.1 不保留任何特定项目、平台、Case 编号、设备、脚本或数据场景。

被删除的是具体实现内容，例如：

- 特定 Skill 名称；
- 特定平台组合；
- 特定工具命令；
- 特定 Case 编号；
- 特定设备；
- 特定 Fixture；
- 特定页面、记录或代理场景；
- 特定 validator 数量；
- 特定目录；
- 特定评分阈值；
- 特定结果文件格式。

被保留的是它们背后的通用方法，例如：

```text
具体工具健康检查
→ 抽象为运行前置条件验证
```

```text
具体设备状态准备
→ 抽象为 Environment / Fixture Design
```

```text
具体命令调用验证
→ 抽象为 Required Tool Usage Contract
```

```text
具体禁止操作检查
→ 抽象为 Forbidden Action Contract
```

```text
具体运行记录
→ 抽象为 Episode + Workflow Trace
```

```text
具体脚本断言
→ 抽象为 Deterministic Grader
```

```text
具体人工质量判断
→ 抽象为 Rubric-based Grader
```

```text
具体版本对比
→ 抽象为 Frozen Benchmark 下的 Baseline vs Candidate
```

## 8.7 v1.1 最终冻结结论

v1.1 的 Core 主路径冻结为：

```text
Part 1：Agent Design

Skill Understanding
→ Requirement
→ Contract / Criticality / Failure Modes
→ Case Matrix / Coverage
→ Input / Fixture / Environment
→ Evidence / Workflow Trace
→ Grader
→ Metric / Rubric / Weight / Gate / Baseline
→ Eval Design Validation
→ Freeze Benchmark Definition
```

```text
Part 2：CLI Execution

Create Run
→ Prepare Environment
→ Execute Cases
→ Produce Episodes
→ Collect Evidence / Trace
→ Run Graders
→ Aggregate Metrics
→ Apply Rubric / Weight / Gates
→ Compare Baseline
→ Generate Scorecard / Overall Score
```

本版到此停止。
