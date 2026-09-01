# 《Agent Skill 基准概念模型 v0.1》

Version: v0.1
状态：已批准进入 Schema 设计（Approved for Schema Design）
Date: 2026-08-21

> v0.1 是进入第一批 Schema 设计前的当前 Concept Model Baseline。

> [!IMPORTANT]
> **文档角色：基础概念模型与历史设计基线。** 本文冻结核心对象的概念边界，但不是当前 `skill-eval` CLI 的 capability contract，也不覆盖后续 `BenchmarkDefinitionV03`、Runtime/Result 实现或当前 Audit 状态。当前操作入口见根 `README.md`、`SKILL.md` 与 `references/`；当前状态权威见 `docs/audit-status-v0.1.md`。

## 1. 一句话定义 Benchmark

> Agent Skill Benchmark 是一套在执行前冻结的“任务要求、测试样本、证据要求和评分规则”，以及使用这些规则对一个被测对象（通常为 Skill）进行实际运行、收集证据、计算多维结果的完整评估单位。

用更简单的话说：

```text
Benchmark Definition
= 考什么 + 怎么考 + 需要什么证据 + 怎么评分

Run
= 拿这套规则对一个明确的 Subject 真正执行一次

Scorecard
= 这次执行最后得到的多维结果和证据链
```

Benchmark 不是单个 Test Case，也不是一个总分。

一个完整 Benchmark 必须能够解释：

```text
为什么评
→ Requirement

具体要验证什么
→ Contract

用什么场景验证
→ Test Case

执行时实际发生了什么
→ Run / Episode

产生了什么
→ Artifact / Evidence

如何判断
→ Grader Specification / Grader Result

如何聚合
→ Metric Specification / Metric Result

是否触发硬性失败
→ Gate Specification / Gate Result

最终结果是什么
→ Scorecard
```

## 2. 三阶段总图

```text
┌──────────────────────────────────────────────────────┐
│ A. Benchmark Definition                             │
│                                                      │
│ 在执行前由 Agent Designer 设计并冻结                 │
│                                                      │
│ Benchmark Definition                                 │
│ ├── Requirement                                      │
│ ├── Contract                                         │
│ ├── Test Case                                        │
│ ├── Evidence Specification                           │
│ ├── Grader Specification                             │
│ ├── Metric Specification                             │
│ └── Gate Specification（Conditional）                │
└──────────────────────────┬───────────────────────────┘
                           │ Freeze
                           ▼
┌──────────────────────────────────────────────────────┐
│ B. Runtime                                          │
│                                                      │
│ Run = 一个 Frozen Definition + 一个 Subject         │
│       + 一次完整执行                                  │
│                                                      │
│ Run                                                  │
│ ├── Subject（外部引用，且只有一个）                   │
│ └── Episode                                          │
│     ├── Raw Output / Execution State                 │
│     ├── Artifact（Conditional）                      │
│     ├── Execution Trace / Tool Trace                 │
│     └── Evidence                                     │
└──────────────────────────┬───────────────────────────┘
                           │ Grade & Aggregate
                           ▼
┌──────────────────────────────────────────────────────┐
│ C. Result                                           │
│                                                      │
│ Grader Result                                        │
│      ↓                                               │
│ Metric Result                                        │
│      ↓                                               │
│ Gate Result（Conditional）                           │
│      ↓                                               │
│ Scorecard                                            │
│ ├── Case Summary                                     │
│ ├── Contract Summary                                 │
│ ├── Metric Results                                   │
│ ├── Overall Score                                    │
│ ├── Gate Status                                      │
│ └── Evidence Trace                                   │
└──────────────────────────────────────────────────────┘
```

不同 Subject 的比较不发生在单个 Run 内部，而发生在两个兼容 Run 的 Result 之间：

```text
Frozen Benchmark Definition B1
        │
        ├── Run A
        │   ├── Subject = Skill v1 / Baseline implementation
        │   └── Scorecard A
        │
        └── Run B
            ├── Subject = Skill v2 / Candidate
            └── Scorecard B

Scorecard A / Metric Results A
                vs
Scorecard B / Metric Results B
                ↓
派生比较视图
```

比较过程不新增 `Comparison`、`Comparison Run` 或 `Comparison Result` 一等对象。

## 3. 最终保留的一等核心对象

v0.1 继续保留 16 个一等对象，数量和分类与 v0 相同。

### 3.1 Benchmark Definition 层：8 个

1. Benchmark Definition
2. Requirement
3. Contract
4. Test Case
5. Evidence Specification
6. Grader Specification
7. Metric Specification
8. Gate Specification

### 3.2 Runtime 层：4 个

9. Run
10. Episode
11. Artifact
12. Evidence

### 3.3 Result 层：4 个

13. Grader Result
14. Metric Result
15. Gate Result
16. Scorecard

### 3.4 数量控制结论

没有为以下概念单独建立一等对象：

- Workflow Requirement
- Workflow Contract
- Workflow Case
- Workflow Metric
- Input Specification
- Fixture Specification
- Benchmark Policy
- Coverage Policy
- Risk Analysis
- Criticality
- Failure Mode
- Rubric
- Weight
- Subject
- Baseline
- Candidate
- Comparison
- Comparison Policy
- Comparison Result
- Baseline Result
- Subject Result
- Execution Trace
- Tool Trace
- Observation
- Rubric Result
- Case Result
- Contract Result
- Overall Score

这些概念并没有被删除，而是：

- 作为某个核心对象的类型；
- 作为某个核心对象的组成内容；
- 作为聚合政策；
- 作为外部对象引用；
- 作为 Scorecard 或上层比较流程中的派生视图。

## 4. 每个核心对象的中文解释

# A. 技术主题：Benchmark Definition

## 4.1 基准定义

### 中文名称

基准定义

### 英文名称

Benchmark Definition

### 它是什么

一套已经设计完成并在正式执行前冻结的 Skill 评估规则集合。

它相当于：

```text
考试卷
+
评分规则
+
证据要求
+
聚合与比较政策
```

在 v0.1 中，不额外建立一个独立的 `Benchmark` 对象和另一个 `Benchmark Definition` 对象；二者合并为同一个顶层对象，简称 Benchmark。

### 为什么需要它

如果没有 Benchmark Definition，Requirement、Case、Grader、Metric 和 Gate 就会成为一组没有共同边界的零散定义。

它负责说明：

- 当前评的是哪一套规则；
- 规则属于哪个版本；
- 哪些对象共同构成这套 Benchmark；
- 哪些执行、聚合和比较政策已经冻结；
- Run 使用的是哪一个权威定义。

### 属于哪个阶段

```text
Definition
```

### 谁产生它

```text
Agent Designer
```

必要时由 Human 审核、确认或补充约束。

### 谁使用它

- Eval Design Validator
- CLI / Execution Framework
- Grader
- Metric Aggregator
- Gate Evaluator
- Scorecard Generator
- Human Reviewer

### 它与哪些对象直接关联

Benchmark Definition 直接包含或引用：

- Requirement
- Contract
- Test Case
- Evidence Specification
- Grader Specification
- Metric Specification
- Gate Specification
- Benchmark-level Policy

每个 Run 必须引用一个已经冻结的 Benchmark Definition。

同一个 Benchmark Definition 可以产生多个 Run，每个 Run 只对应一个 Subject。

### 技术主题：Mandatory / Conditional / Optional

```text
Mandatory
```

### 是否应该成为一等对象

```text
是
```

它是 Definition 层的顶层容器，也是版本、冻结状态和 Run 引用的共同边界。

## 4.2 需求

### 中文名称

需求

### 英文名称

Requirement

### 它是什么

从 Skill、用户、项目、接口或其他合法来源提取出来的一条评估要求。

Requirement 回答：

> 为什么要评这一项？

它可以描述最终结果要求，也可以描述工作流、工具、授权、禁止行为、中间产物或输出质量要求。

### 为什么需要它

如果直接从 Skill 文档跳到 Test Case，就会失去 Case 的来源、Contract 的依据，以及 Requirement 覆盖是否完整的追溯能力。

### 属于哪个阶段

```text
Definition
```

### 谁产生它

```text
Agent Designer
```

### 谁使用它

- Contract Designer
- Coverage Validator
- Human Reviewer
- Scorecard Traceability

### 它与哪些对象直接关联

- 属于一个 Benchmark Definition；
- 可以关联一个或多个 Contract；
- 一个 Contract 也可以同时追溯到多个 Requirement。

### 技术主题：Mandatory / Conditional / Optional

```text
Mandatory
```

### 是否应该成为一等对象

```text
是
```

Requirement 具有独立来源、独立身份和多对多追溯关系，不能只作为 Contract 中的一段说明文字。

## 4.3 契约

### 中文名称

契约

### 英文名称

Contract

### 它是什么

对一个或多个 Requirement 的可验证表达。

Contract 回答：

> 到底要观察什么，什么算成功，什么算失败？

Contract 可以约束 Outcome、Workflow，或同时涉及结果和过程。Workflow Contract 不建立独立对象类别，只是 Contract 的一种评估方向。

### 为什么需要它

Requirement 可能太宽、包含多个责任或没有明确成功条件。Contract 把它收缩成可由 Case、Evidence 和 Grader 验证的责任单元。

### 属于哪个阶段

```text
Definition
```

### 谁产生它

```text
Agent Designer
```

### 谁使用它

- Test Case Designer
- Evidence Designer
- Grader Designer
- Coverage Validator
- Gate Designer
- Scorecard Generator
- Human Reviewer

### 它与哪些对象直接关联

- 关联一个或多个 Requirement；
- 被一个或多个 Test Case 覆盖；
- 关联一个或多个 Evidence Specification；
- 被一个或多个 Grader Specification 评价；
- Runtime 中通过 Contract-specific Grader Result 体现实际判断；
- 可以与 Grader Specification 一起成为 Gate Specification 的 Definition-level 引用目标。

### 技术主题：Mandatory / Conditional / Optional

```text
Mandatory
```

### 是否应该成为一等对象

```text
是
```

Contract 是 Requirement 与实际可评分执行之间的核心桥梁。Criticality、Failure Modes、成功条件和失败条件属于 Contract 的设计内容，不另建顶层对象。

## 4.4 测试用例

### 中文名称

测试用例

### 英文名称

Test Case

### 它是什么

在 Benchmark Definition 中提前设计的一道可执行评测题。

它描述给 Subject 什么输入、在什么前置条件下执行、验证哪些 Contract、需要产生哪些输出或 Evidence，以及是否需要重复执行。

### 为什么需要它

Contract 说明需要验证的责任，Test Case 则把责任转换成真正可以执行和重复使用的 Benchmark Sample。

### 属于哪个阶段

```text
Definition
```

### 谁产生它

```text
Agent Designer
```

### 谁使用它

- CLI / Execution Framework
- Episode Creator
- Evidence Collector
- Grader
- Metric Aggregator
- Coverage Validator
- Human Reviewer

### 它与哪些对象直接关联

- 属于一个 Benchmark Definition；
- 覆盖一个或多个 Contract；
- 使用零个或多个 Evidence Specification；
- 可以关联多个 Grader Specification；
- 在一个或多个 Run 中产生零个或多个 Episode；
- 输入、简单 Fixture 和环境前置条件属于 Test Case 的组成内容。

### 技术主题：Mandatory / Conditional / Optional

```text
Mandatory
```

### 是否应该成为一等对象

```text
是
```

Test Case 可以在多个 Run 中重复执行，也可以在一个 Run 中重复多次，不能被 Episode 取代。

## 4.5 证据规格

### 中文名称

证据规格

### 英文名称

Evidence Specification

### 它是什么

Definition 阶段对“执行时必须产生或取得什么证据”的预先声明。

它回答：

> 为了让 Grader 判断某个 Contract，Runtime 应提供什么来源、什么类型和什么完整程度的证据？

### 为什么需要它

如果 Evidence 只在 Runtime 中临时决定，就可能出现执行完成但无法评分、Grader 输入无法产生或看到结果后选择有利证据的问题。

Evidence Specification 是 Definition 与 Runtime 之间的正式接口。

### 属于哪个阶段

```text
Definition
```

### 谁产生它

```text
Agent Designer
```

### 谁使用它

- Eval Design Validator
- CLI / Execution Framework
- Evidence Collector
- Grader
- Human Reviewer

### 它与哪些对象直接关联

- 服务于一个或多个 Contract；
- 可以被一个或多个 Test Case 使用；
- 可以被一个或多个 Grader Specification 声明为输入；
- Runtime 中由 Episode、Artifact、输出或 Trace 产生实际 Evidence。

### 技术主题：Mandatory / Conditional / Optional

```text
Mandatory
```

### 是否应该成为一等对象

```text
是
```

它具有跨 Case、跨 Contract 和跨 Grader 复用的可能，也是 Design Validation 检查 Evidence Compatibility 的关键连接点。

## 4.6 评分器规格

### 中文名称

评分器规格

### 英文名称

Grader Specification

### 它是什么

对“如何根据实际 Evidence 作出一次判断”的预先定义。

它说明评分方法，不是实际评分结果。它可以代表 deterministic、validator-based、rubric-based、Human、LLM 或 mixed judgment。

### 为什么需要它

Grader Specification 冻结消费哪些 Evidence、判断哪些 Contract、使用什么方法，以及什么算通过、失败或无法判断。

### 属于哪个阶段

```text
Definition
```

### 谁产生它

```text
Agent Designer
```

### 谁使用它

- Eval Design Validator
- Grading Engine
- Human / LLM Grader
- Metric Aggregator
- Gate Evaluator
- Human Reviewer

### 它与哪些对象直接关联

- 评价一个或多个 Contract；
- 声明消费一个或多个 Evidence Specification；
- 可以用于一个或多个 Test Case；
- 每次实际评分产生 Grader Result；
- 可以与 Contract 一起被 Gate Specification 引用；
- 其 Grader Result 可以进入一个或多个 Metric Result。

### 技术主题：Mandatory / Conditional / Optional

```text
Mandatory
```

### 是否应该成为一等对象

```text
是
```

Grader Specification 需要独立 Evidence 依赖和独立结果实例。Rubric 是其使用的评分政策，不另建一等对象。

## 4.7 指标规格

### 中文名称

指标规格

### 英文名称

Metric Specification

### 它是什么

对“如何把多个 Episode 产生的多个 Grader Result 聚合成一个能力指标”的预先定义。

它回答：

> 哪些实际测量共同代表这个能力，以及应该如何汇总？

### 为什么需要它

Benchmark 评价的是 Skill 的能力，而不是某一个 Case 是否碰巧通过。

Metric Specification 必须支持：

```text
多个 Test Cases
+
多个 Episodes
+
多个 Grader Results
→
一个 Metric Result
```

### 属于哪个阶段

```text
Definition
```

### 谁产生它

```text
Agent Designer
```

### 谁使用它

- Eval Design Validator
- Metric Aggregator
- Gate Evaluator
- Scorecard Generator
- Run-to-Run 比较
- Human Reviewer

### 它与哪些对象直接关联

- 由一个或多个 Grader Specification 的未来结果支撑；
- 可以跨多个 Test Case 聚合；
- 在每个 Run 中为该 Run 唯一 Subject 产生 Metric Result；
- 可以参与 Overall Score；
- 可以被 Gate Specification 在 Definition 阶段引用；
- 两个兼容 Run 的对应 Metric Result 可以被比较。

### 技术主题：Mandatory / Conditional / Optional

```text
Mandatory
```

### 是否应该成为一等对象

```text
是
```

Metric 具有独立能力含义、独立聚合规则和独立结果。Weight 属于 Metric 与 Overall Aggregation Policy 之间的关系，不另建对象。

## 4.8 硬门规格

### 中文名称

硬门规格

### 英文名称

Gate Specification

### 它是什么

在 Benchmark Definition 冻结时，对“哪些关键失败无论总体分数多高都不可接受”的预先定义。

Gate Specification 只描述未来应如何找到相关实际结果并作出硬门判断，本身不包含任何未来 Run 的 Result。

### 为什么需要它

如果只有加权分数，严重失败可能被其他高分抵消。Gate 保证安全、授权、禁止行为和核心功能等关键失败不会被 Overall Score 掩盖。

### 属于哪个阶段

```text
Definition
```

### 谁产生它

```text
Agent Designer
```

高风险场景可能需要 Human 确认。

### 谁使用它

- Eval Design Validator
- Gate Evaluator
- Scorecard Generator
- Human Reviewer

### 它与哪些对象直接关联

Gate Specification 在 Definition 阶段只能引用已经存在的 Definition 对象或预定义执行状态条件，例如：

- Metric Specification；
- Grader Specification 与 Contract 的组合；
- 合法的预定义执行状态条件。

它不能在 Definition 阶段引用未来才产生的 Metric Result 或 Grader Result。

正式 Run 后，Gate Evaluator 根据 Gate Specification 定位该 Run 中对应的实际 Grader Result、Metric Result 或执行状态，计算 Gate Result。

### 技术主题：Mandatory / Conditional / Optional

```text
Conditional
```

### 是否应该成为一等对象

```text
是，但为 Conditional 一等对象
```

Gate 需要独立身份、Definition-level 引用、判断规则和运行后结果，不能只作为 Metric 的布尔属性。

# B. 字段或协议值：Runtime

## 4.9 运行

### 中文名称

运行

### 英文名称

Run

### 它是什么

使用一个已经冻结的 Benchmark Definition，对一个明确的被测对象执行一次完整 Benchmark 所形成的 Runtime 顶层容器。

正式定义为：

```text
Run
= Frozen Benchmark Definition
+ Subject
+ Execution Context
+ Episodes
+ Results
```

其中，一个 Run 中只有一个 Subject。

Subject 可以是：

- Skill v1；
- Skill v2；
- 不使用 Skill 的 baseline implementation；
- 另一个可比较方案。

Subject 只是外部被测对象引用，不新增为一等对象。

### 为什么需要它

同一套 Benchmark 可以对不同 Subject 或同一 Subject 的不同执行分别产生 Run：

```text
Benchmark B1 + Skill v1 + 一次执行 → Run A
Benchmark B1 + Skill v2 + 一次执行 → Run B
```

如果没有 Run，不同执行的 Episode、环境、Evidence 和 Result 会混在一起。

### 属于哪个阶段

```text
Runtime
```

### 谁产生它

```text
CLI / Execution Framework
```

### 谁使用它

- Episode Creator
- Evidence Collector
- Grader
- Metric Aggregator
- Gate Evaluator
- Scorecard Generator
- Human Reviewer

### 它与哪些对象直接关联

- 引用一个 Frozen Benchmark Definition；
- 引用且只引用一个 Subject；
- 包含零个或多个 Episode；
- 产生零个或多个 Grader Result；
- 产生适用的 Metric Result；
- 产生 Conditional Gate Result；
- 最终产生一个 Scorecard。

Baseline 或 Candidate 不作为同一 Run 中的第二个 Subject。比较时分别建立两个 Run。

### 技术主题：Mandatory / Conditional / Optional

```text
Mandatory
```

### 是否应该成为一等对象

```text
是
```

Run 是一个 Benchmark、一个 Subject、一次完整执行和该次结果共同所属的顶层运行边界。

## 4.10 执行单元

### 中文名称

执行单元

### 英文名称

Episode

### 它是什么

某个 Test Case 在某个 Run 中，针对该 Run 唯一 Subject 的一次实际执行或执行尝试。

### 为什么需要它

Test Case 是提前设计的题，Episode 是某次真正作答的过程。

同一个 Test Case 可以在不同 Run 中执行，也可以在同一个 Run 中重复执行、失败后重试、因环境阻塞或因用户取消而终止。

### 属于哪个阶段

```text
Runtime
```

### 谁产生它

```text
CLI / Execution Framework
```

### 谁使用它

- Evidence Collector
- Grader
- Metric Aggregator
- Scorecard Generator
- Human Reviewer

### 它与哪些对象直接关联

每个 Episode：

- 属于一个 Run；
- 对应一个 Test Case；
- 自动继承该 Run 唯一 Subject；
- 表示一次执行或执行尝试；
- 可以产生零个或多个 Artifact；
- 可以产生零个或多个 Evidence；
- 可以产生零个或多个 Grader Result；
- 可以包含 Execution Trace、Tool Trace 和状态变化。

### 技术主题：Mandatory / Conditional / Optional

```text
Mandatory for scheduled execution
```

某个 Test Case 在某个 Run 中仍可能有零个 Episode，例如未调度、不适用或 Run 在调度前整体终止。

如果 Case 已进入执行尝试但被前置条件阻塞，建议产生一个 BLOCKED Episode，保留阻塞事实。

### 是否应该成为一等对象

```text
是
```

Episode 是重复执行、失败重试和运行证据追溯的基本单位。

## 4.11 运行产物

### 中文名称

运行产物

### 英文名称

Artifact

### 它是什么

Episode 在执行过程中产生或捕获的可持久化输出物，例如文件、结构化输出、截图、日志、validator 报告、中间产物或持久化 Trace。

### 为什么需要它

Artifact 与 Evidence 不是同一个概念。Artifact 表示实际产生了什么；只有其中被选取、资格确认并用于证明 Contract 的内容才成为 Evidence 的来源。

### 属于哪个阶段

```text
Runtime
```

### 谁产生它

- Subject
- CLI / Execution Framework
- Validator
- Tooling
- Environment Capture

### 谁使用它

- Evidence Collector
- Grader
- Human Reviewer
- Scorecard Traceability

### 它与哪些对象直接关联

- 通常由一个 Episode 产生或捕获；
- 可以成为零个或多个 Evidence 的来源；
- 可以被 Workflow Evidence 和 Outcome Evidence 共同引用。

### 技术主题：Mandatory / Conditional / Optional

```text
Conditional
```

### 是否应该成为一等对象

```text
是，但为 Conditional 一等对象
```

简单 Eval 可以没有独立 Artifact，但复杂 Eval 需要独立保存其来源、完整性和生命周期。

## 4.12 证据

### 中文名称

证据

### 英文名称

Evidence

### 它是什么

从某次 Episode 的输出、Artifact、Trace、状态或观察中取得，并经过资格确认、可被 Grader 用于判断 Contract 的信息。

Evidence 不是整个 Episode，也不等于所有 Runtime Artifact，而是从实际执行事实中选取并确认可以用于评分的部分。

### 为什么需要它

Evidence 明确实际观察到了什么、来自哪个 Episode、是否完整、是否满足 Evidence Specification，以及能否被 Grader 合法消费。

### 属于哪个阶段

```text
Runtime
```

### 谁产生它

```text
Evidence Collector / Execution Framework
```

### 谁使用它

- Deterministic Grader
- Human Grader
- LLM Grader
- Workflow Grader
- Human Reviewer
- Scorecard Traceability

### 它与哪些对象直接关联

- 满足一个或多个 Evidence Specification；
- 来源于一个 Episode；
- 可以来源于零个或多个 Artifact；
- 也可以直接来源于 Episode 输出、状态或 Trace；
- 可以被一个或多个 Grader Result 消费；
- 可以服务于 Outcome Contract、Workflow Contract 或两者共享。

### 技术主题：Mandatory / Conditional / Optional

```text
Mandatory for gradable execution
```

### 是否应该成为一等对象

```text
是
```

Evidence 是 Runtime 事实与评分判断之间的正式桥梁。

# C. 字段或协议值：Result

## 4.13 评分器结果

### 中文名称

评分器结果

### 英文名称

Grader Result

### 它是什么

某个 Grader Specification 在某次 Run 中，基于某个 Episode 的一组 Evidence 作出的一次可追溯判断。

它是本 Concept Model 中最小的可聚合测量单元。

### 为什么需要它

Grader Specification 只是“怎么判”，Grader Result 才是这一次实际判出了什么。

它必须在概念上保留判断对象、Evidence、Episode、Contract、实际判断、失败原因、无法判断原因和 Grader 自身错误状态。

### 属于哪个阶段

```text
Result
```

### 谁产生它

- Deterministic Grader
- Human Grader
- LLM Grader
- Mixed Grader

### 谁使用它

- Metric Aggregator
- Gate Evaluator
- Scorecard Generator
- Human Reviewer

### 它与哪些对象直接关联

每个 Grader Result：

- 引用一个 Grader Specification；
- 属于一个 Run；
- 通常对应一个 Episode；
- 消费一个或多个 Evidence；
- 必须明确其判断的 Contract；
- 可以被一个或多个 Metric Result 使用；
- 可以由 Gate Evaluator 按 Gate Specification 的 Definition-level 引用定位并使用。

### 技术主题：Mandatory / Conditional / Optional

```text
Mandatory for each applicable grading operation
```

### 是否应该成为一等对象

```text
是
```

Grader Result 同时承担候选 Observation 的职责，因此不新增 Observation 对象。

## 4.14 指标结果

### 中文名称

指标结果

### 英文名称

Metric Result

### 它是什么

某个 Metric Specification 在一次 Run 中，根据多个有效 Grader Result 聚合出来的该 Run 唯一 Subject 的实际能力指标。

### 为什么需要它

一个 Case 的一次结果不能代表稳定能力。Metric Result 必须能够表达实际得分、样本数量、有效观察、blocked、not run、insufficient evidence、included cases 和比较兼容性等信息。

这些是概念要求，本轮不设计字段。

### 属于哪个阶段

```text
Result
```

### 谁产生它

```text
Metric Aggregator
```

### 谁使用它

- Gate Evaluator
- Overall Score Aggregator
- Scorecard Generator
- Run-to-Run 比较
- Human Reviewer

### 它与哪些对象直接关联

- 对应一个 Metric Specification；
- 属于一个 Run；
- 评价该 Run 唯一 Subject；
- 聚合零个或多个 Grader Result；
- 通常覆盖多个 Test Case 和 Episode；
- 可以由 Gate Evaluator按 Gate Specification 定位并使用；
- 可以参与 Overall Score；
- 可以与另一个兼容 Run 的同类 Metric Result 比较。

即使没有足够有效观察，也应形成明确状态，而不是让该 Metric 静默消失。

### 技术主题：Mandatory / Conditional / Optional

```text
Mandatory
```

### 是否应该成为一等对象

```text
是
```

Metric Result 是 Benchmark 从单次判断上升到能力评估的关键结果对象。

## 4.15 硬门结果

### 中文名称

硬门结果

### 英文名称

Gate Result

### 它是什么

Gate Evaluator 根据某个 Gate Specification 和本次 Run 中与其 Definition-level 引用相对应的实际 Result，计算出的通过、失败或无法判断结果。

### 为什么需要它

Gate Result 回答这次 Run 是否真正触发硬性失败，并且必须与 Overall Score 分开存在。

### 属于哪个阶段

```text
Result
```

### 谁产生它

```text
Gate Evaluator
```

### 谁使用它

- Scorecard Generator
- Acceptance Decision
- Human Reviewer
- Run-to-Run 比较

### 它与哪些对象直接关联

- 引用一个 Gate Specification；
- 属于一个 Run；
- 根据 Gate Specification 引用的 Metric Specification，定位本次 Run 对应的 Metric Result；
- 或根据 Gate Specification 引用的 Grader Specification 与 Contract，定位本次 Run 对应的 Grader Result；
- 或使用 Gate Specification 声明的预定义执行状态条件；
- 进入该 Run 的 Scorecard；
- 影响 Gate Status，但不删除其他 Metric Result。

### 技术主题：Mandatory / Conditional / Optional

```text
Conditional
```

### 是否应该成为一等对象

```text
是，但为 Conditional 一等对象
```

Gate 有独立状态、依据和失败原因，不能只作为 Scorecard 中一个无来源的布尔值。

## 4.16 评估记分卡

### 中文名称

评估记分卡

### 英文名称

Scorecard

### 它是什么

一次 Run、一个 Subject 的权威、多维、可追溯结果汇总。

Scorecard 不是简单总分，而是该 Run 完整结果的入口。

### 为什么需要它

Scorecard 把 Episodes、Evidence、Grader Results、Metric Results 和 Gate Results 组织成可理解结果，同时保留回到原始 Evidence 的能力。

### 属于哪个阶段

```text
Result
```

### 谁产生它

```text
Framework / Scorecard Generator
```

### 谁使用它

- Developer
- Skill Author
- Human Reviewer
- Acceptance Decision
- Run-to-Run 比较
- 后续版本优化流程

### 它与哪些对象直接关联

Scorecard：

- 属于一个 Run；
- 引用该 Run 使用的 Frozen Benchmark Definition；
- 表示该 Run 唯一 Subject；
- 汇总全部 Metric Result；
- 汇总全部 Gate Result；
- 提供 Case Summary；
- 提供 Contract Summary；
- 提供 Overall Score 或明确 Disabled；
- 保留到 Grader Result、Episode 和 Evidence 的追溯入口。

Candidate vs Baseline 或 Skill v1 vs Skill v2 的比较由两个兼容 Run 的 Scorecard / Metric Results 派生，不在单个 Scorecard 内假设存在第二个 Subject。

### 技术主题：Mandatory / Conditional / Optional

```text
Mandatory for finalized or terminated Run
```

### 是否应该成为一等对象

```text
是
```

Scorecard 是 Result 层的顶层结果对象。

## 5. 对象关系图

### 5.1 Definition 到 Result 的完整关系

```text
Benchmark Definition
│
├── Requirement
│      N
│      ↕
│      N
│   Contract
│      N
│      ↕
│      N
│   Test Case
│
├── Evidence Specification
│      N
│      ↕
│      N
│   Grader Specification
│
├── Metric Specification
│
└── Gate Specification（Conditional）
       ├── references Metric Specification
       ├── or Grader Specification + Contract
       └── or predefined execution-state condition
             │
             │ Freeze
             ▼
Run
├── Frozen Benchmark Definition（exactly one）
├── Subject（exactly one external reference）
└── Episode
      ├── Test Case
      ├── Execution / Tool Trace
      ├── Artifact
      │      │
      │      └──────────┐
      └── Evidence ◄────┘
             │
             │ consumed by
             ▼
       Grader Result
             │
             │ many observations
             ▼
       Metric Result
             │
             ├──────────────┐
             │              │
             ▼              ▼
       Gate Evaluator  Overall Aggregation
             │              │
             ▼              ▼
       Gate Result      Overall Score
             │              │
             └──────┬───────┘
                    ▼
                Scorecard
                    ├── Case Summary
                    ├── Contract Summary
                    └── Evidence Trace
```

Definition 中的 Gate Specification 不引用 Result。运行后 Gate Evaluator 才根据其 Definition-level 引用定位本次 Run 的实际 Result。

### 5.2 Run 与 Run 的比较关系

```text
Frozen Benchmark Definition B1
        │
        ├── Run 001
        │   ├── Subject = Skill v1
        │   ├── Episodes 001
        │   ├── Metric Results 001
        │   ├── Gate Results 001
        │   └── Scorecard 001
        │
        └── Run 002
            ├── Subject = Skill v2
            ├── Episodes 002
            ├── Metric Results 002
            ├── Gate Results 002
            └── Scorecard 002

Run 001 Result
        vs
Run 002 Result
        ↓
派生比较：
- Metric Improvement / Regression
- Overall Score Difference
- Gate Status Difference
- Failure Mode Difference
- Sample / Execution Difference
```

比较的基本单位是两个兼容 Run 的 Result，而不是一个 Run 内的两个 Subject。

### 技术主题：5.3 Requirement → Contract

```text
Requirement N ↔ N Contract
```

一个 Requirement 可以拆成多个 Contract；一个 Contract 也可以承接多个来源 Requirement。Contract 必须保留全部来源关系。

在有效 Benchmark 中：

- 每个进入范围的 Requirement 至少关联一个 Contract；
- 每个 Contract 至少关联一个 Requirement。

### 技术主题：5.4 Contract ↔ Test Case

```text
Contract N ↔ N Test Case
```

一个 Contract 必须支持多个风险类型的 Case；一个 Case 也可以验证多个 Contract。

多 Contract Case 不能只记录模糊的 `Case FAIL`。每个 Grader Result 必须明确评价哪个 Contract、使用哪些 Evidence，以及对该 Contract 的具体判断。

### 技术主题：5.5 Test Case → Episode

```text
Test Case 1 → 0..N Episodes
```

同一个 Test Case 可以：

- 在多个 Run 中执行；
- 在同一个 Run 中重复多次；
- 因明确 retry 产生多个 Episode；
- 在某个 Run 中未调度或不适用，因此产生零个 Episode。

不同 Subject 的同一 Case 必须存在于不同 Run 中：

```text
TC001
├── Run A / Subject Skill v1
│   ├── Episode E001
│   └── Episode E002
└── Run B / Subject Skill v2
    ├── Episode E003
    └── Episode E004
```

如果 Case 已进入执行尝试但被前置条件阻塞，建议形成 BLOCKED Episode；具体状态表达留到 Schema 阶段。

### 技术主题：5.6 Episode → Artifact / Evidence

```text
Episode 1 → 0..N Artifacts
Episode 1 → 0..N Evidence
Artifact 1 → 0..N Evidence
```

Evidence 不是 Episode 本身。

```text
Episode
├── 实际执行状态
├── Raw Output
├── Artifact
├── Execution Trace
└── Tool Trace
        ↓
从中选择并确认可用于评分的内容
        ↓
Evidence
```

### 技术主题：5.7 Evidence ↔ Grader

Definition 层：

```text
Evidence Specification N ↔ N Grader Specification
```

Runtime / Result 层：

```text
Evidence N ↔ N Grader Result
```

一个 Grader 可以消费多个 Evidence；一个 Evidence 也可以被多个 Grader 复用。复用不意味着自动适用于所有判断，每个 Grader Specification 都必须明确其 Evidence 依赖。

### 技术主题：5.8 Grader Result → Metric Result

```text
Grader Result N ↔ N Metric Result
```

主要聚合方向是：

```text
Metric Result 1 ← N Grader Results
```

一个 Metric Result 应由多个 Test Case、Episode 和 Grader Result 支撑。一个 Grader Result 也可以按冻结的 Metric Specification 被多个 Metric 使用，但不能在执行后临时重复计分。

### 技术主题：5.9 Gate Specification → Gate Result

Definition 层：

```text
Gate Specification
        ├── references Metric Specification
        ├── or Grader Specification + Contract
        └── or predefined execution-state condition
```

Result 层：

```text
Metric Specification
        ↓ produces for this Run
Metric Result
        ↓
Gate Evaluator
```

或：

```text
Grader Specification + Contract
        ↓ produces for this Run
Contract-specific Grader Result
        ↓
Gate Evaluator
```

最终：

```text
Gate Evaluator
        ↓
Gate Result
        ↓
Scorecard
```

### 5.10 Scorecard 与跨 Run 比较

```text
Run 1 → 0..1 finalized Scorecard
```

一个 Scorecard 只总结一个 Run、一个 Subject。

跨版本或 Baseline/Candidate 比较使用：

```text
Scorecard A / Metric Results A
                vs
Scorecard B / Metric Results B
```

比较输出是派生视图，不新增权威一等 Result。

## 6. 基数关系

### 6.1 Definition 层

| 关系 | 基数 | 解释 |
|---|---:|---|
| Benchmark Definition → Requirement | 1 → 1..N | 一套 Benchmark 至少有一个 Requirement |
| Benchmark Definition → Contract | 1 → 1..N | 至少有一个可验证 Contract |
| Benchmark Definition → Test Case | 1 → 1..N | 至少有一个可执行 Case |
| Benchmark Definition → Evidence Specification | 1 → 1..N | 至少有一项证据要求 |
| Benchmark Definition → Grader Specification | 1 → 1..N | 至少有一个评分方法 |
| Benchmark Definition → Metric Specification | 1 → 1..N | 至少有一个 Metric；实际应支持多维 Metric |
| Benchmark Definition → Gate Specification | 1 → 0..N | Gate 按需要存在 |
| Requirement ↔ Contract | N ↔ N | Requirement 可拆分，Contract 可承接多个来源 |
| Contract ↔ Test Case | N ↔ N | 一个 Contract 多 Case，一个 Case 可测多个 Contract |
| Contract ↔ Evidence Specification | N ↔ N | Contract 可以需要多种 Evidence，一种 Evidence 也可支持多个 Contract |
| Test Case ↔ Evidence Specification | N ↔ N | Case 可以产生多种 Evidence，同一种规格可以被多个 Case 使用 |
| Grader Specification ↔ Evidence Specification | N ↔ N | Grader 可消费多份 Evidence，一份 Evidence 可被多个 Grader 使用 |
| Grader Specification ↔ Metric Specification | N ↔ N | Metric 聚合多个 Grader 的未来结果，一个 Grader 可支持多个 Metric |
| Gate Specification ↔ Metric Specification | N ↔ N | Gate 在 Definition 中可以引用一个或多个 Metric Specification |
| Gate Specification ↔ Grader Specification + Contract | N ↔ N | Gate 可以定义为对特定 Grader 与 Contract 判断的硬约束 |

### 6.2 Runtime 层

| 关系 | 基数 | 解释 |
|---|---:|---|
| Benchmark Definition → Run | 1 → 0..N | 同一冻结定义可执行多次 |
| Run → Benchmark Definition | N → 1 | 每个 Run 只使用一个 Frozen Definition |
| Run → Subject | 1 → 1 | 每个 Run 只评估一个外部 Subject 引用 |
| Subject → Run | 1 → 0..N | 同一外部 Subject 可被重复评估；Subject 不是核心对象 |
| Run → Episode | 1 → 0..N | Run 可能在调度前终止，也可能执行很多 Episode |
| Test Case → Episode | 1 → 0..N | Case 可不执行、重复执行或在不同 Run 中执行 |
| Episode → Test Case | N → 1 | 每个 Episode 必须来自一个明确 Case |
| Episode → Run | N → 1 | 每个 Episode 只属于一个 Run |
| Episode → Subject | N → 1 via Run | Episode 继承所属 Run 的唯一 Subject |
| Episode → Artifact | 1 → 0..N | 简单 Episode 可以没有独立 Artifact |
| Episode → Evidence | 1 → 0..N | 失败或阻塞 Episode 可能没有足够 Evidence |
| Artifact → Evidence | 1 → 0..N | Artifact 不一定被评分，也可能支持多份 Evidence |
| Evidence → Artifact | N → 0..N | Evidence 可以直接来自输出或 Trace，也可以组合多个 Artifact |
| Evidence → Episode | N → 1 | 每份 Runtime Evidence 必须追溯到一个 Episode |

### 6.3 Result 层

| 关系 | 基数 | 解释 |
|---|---:|---|
| Grader Specification → Grader Result | 1 → 0..N | 每次适用评分可产生结果 |
| Episode → Grader Result | 1 → 0..N | 一个 Episode 可由多个 Grader 评价 |
| Evidence ↔ Grader Result | N ↔ N | 一个结果消费多份 Evidence；Evidence 可被多个结果复用 |
| Metric Specification → Metric Result | 1 → 0..N | 每个适用 Run 产生该 Run Subject 的结果 |
| Grader Result ↔ Metric Result | N ↔ N | Metric 聚合多个观察，一个观察可支持多个 Metric |
| Gate Specification → Gate Result | 1 → 0..N | 每个适用 Run 产生结果 |
| Gate Result → Metric Result | N → 0..N | Gate Evaluator 可按 Gate Specification 定位本次 Run 的 Metric Results |
| Gate Result → Grader Result | N → 0..N | Gate Evaluator 可按 Grader Specification + Contract 定位实际 Grader Results |
| Run → Scorecard | 1 → 0..1 | 执行中可以没有最终 Scorecard；结束后应有一个 |
| Scorecard → Metric Result | 1 → 1..N | Scorecard 保留所有适用 Metric |
| Scorecard → Gate Result | 1 → 0..N | 没有 Gate 时为空 |
| Scorecard → Grader Result | 1 → 0..N | 可以直接包含或追溯到全部评分结果 |
| Compatible Run ↔ Compatible Run | N ↔ N | Result 可进行派生比较，但不创建 Comparison 一等对象 |

## 7. Definition / Runtime / Result 对照表

| 提前冻结的 Definition | Runtime 实际发生 | Result 实际得到 |
|---|---|---|
| Benchmark Definition | Run：一个 Definition + 一个 Subject + 一次执行 | Scorecard：一个 Run、一个 Subject 的结果 |
| Requirement | 不产生同名 Runtime 对象 | 通过 Scorecard 追溯满足情况 |
| Contract | Episode 中实际表现 | 由 Contract-specific Grader Results 派生 Contract Summary |
| Test Case | Episode | 由 Episode 与 Grader Results 派生 Case Summary |
| Case Input / Fixture 内容 | Episode 使用的实际输入与环境 | 执行偏差和适用性摘要 |
| Evidence Specification | Evidence | Evidence 充分性与 Grader Result |
| Grader Specification | Grader 实际执行 | Grader Result |
| Metric Specification | 聚合过程 | Metric Result |
| Rubric，作为 Grader Specification 的政策 | Human / LLM / Mixed 评分过程 | Grader Result 中的 Rubric 明细 |
| Gate Specification：引用 Metric Specification 或 Grader Specification + Contract | Gate Evaluator 定位本次 Run 的实际 Results | Gate Result |
| Comparison Policy，作为 Benchmark Policy | 分别执行 Run A 与 Run B | 两个兼容 Run Result 的派生比较视图 |
| Overall Aggregation Policy | 单个 Run 内的 Overall 聚合 | 该 Run Scorecard 中的 Overall Score |
| Coverage Policy，作为 Benchmark Policy | 实际 Case / Episode 覆盖 | Scorecard 中的样本与覆盖摘要 |

核心边界始终是：

```text
Definition
= 未来应该怎么执行和判断

Runtime / Result
= 这一次实际上发生了什么、算出了什么
```

必须严格区分：

```text
Test Case              vs Episode
Evidence Specification vs Evidence
Grader Specification   vs Grader Result
Metric Specification   vs Metric Result
Gate Specification     vs Gate Result
Benchmark Definition   vs Run
```

## 8. 被合并或删除的候选概念

### 8.1 Workflow 对象体系

```text
Workflow Requirement
→ Requirement 的一种类型

Workflow Contract
→ Contract 的一种类型

Workflow Case
→ Test Case 的一种评估方向

Workflow Metric
→ Metric Specification 的一种评估方向
```

Outcome 与 Workflow 共用同一主链，不建立平行对象体系。

### 技术主题：8.2 Input Specification

```text
Input Specification
→ Test Case 的组成内容
```

输入本身不在 Core v0.1 中成为一等对象。

### 技术主题：8.3 Fixture

```text
简单 Fixture
→ Test Case Input / Setup 的组成部分

复杂可复用 Fixture
→ 可被 Test Case 引用的定义资源
```

Fixture 不进入 Core 一等对象集合。

### 技术主题：8.4 Benchmark Policy / Coverage Policy

```text
Benchmark Policy
→ Benchmark Definition 的组成部分

Coverage Policy
→ Benchmark Policy 的组成部分
```

它们承载规则，不单独形成核心实体。

### 8.5 风险分析 / Criticality / Failure Mode

```text
Risk Analysis
→ Definition 设计动作

Criticality
→ Contract 的设计内容

Failure Mode
→ Contract 与 Test Case 的设计信息
```

三者均不建立一等对象。

### 技术主题：8.6 Execution Trace / Tool Trace

```text
Execution Trace
Tool Trace
→ Episode 的组成部分
```

如果 Trace 被持久化成独立文件，它可以成为 Artifact；其中被 Grader 使用的部分可以成为 Evidence。

### 技术主题：8.7 Rubric / Rubric Result

```text
Rubric
→ Grader Specification 使用的评分政策

Rubric Result
→ Grader Result 的组成内容
```

不新增独立对象。

### 技术主题：8.8 Weight / Overall Score

```text
Weight
→ Overall Aggregation Policy 的组成部分

Overall Score
→ Scorecard 中的汇总值
```

二者均不具有独立权威 Evidence，不成为一等对象。

### 8.9 Subject / Candidate / 基线

```text
Subject
→ Run 所评估的一个外部对象引用

Candidate
Baseline
→ Subject 在特定比较语境下扮演的角色
```

一个 Run 只有一个 Subject。Candidate 和 Baseline 必须分别执行为独立 Run，不能作为同一 Run 中的两个 Subject。

Subject、Candidate、Baseline 均不新增为当前核心对象，也不在本轮设计其 Schema。

### 技术主题：8.10 Comparison / Comparison Result

```text
Comparison Policy
→ Benchmark Definition 的组成部分

Comparison
→ 两个兼容 Run Result 之间的上层计算过程

Comparison Result
Baseline Comparison Result
Subject Result
→ Scorecard 组合展示或上层比较流程中的派生视图
```

不新增 `Comparison`、`Comparison Run`、`Comparison Result`、`Baseline Result` 或 `Subject Result` 一等对象。

### 技术主题：8.11 Observation

```text
Observation
→ 不新增
```

`Grader Result` 已经表示某个 Grader 针对某个 Episode、Contract 和一组 Evidence 产生的一次可聚合测量，因此它承担 Observation 职责。

### 技术主题：8.12 Case Result

```text
Case Result
→ Scorecard 中的派生 Case Summary
```

Case 可以有多个 Episode、多个 Grader Result，并且可能同时验证多个 Contract。简单 Case PASS / FAIL 容易掩盖部分失败，因此不提升为权威一等 Result。

### 技术主题：8.13 Contract Result

```text
Contract Result
→ Scorecard 中的派生 Contract Summary
```

Contract Summary 由 Contract、Cases、Episodes 和 Contract-specific Grader Results 派生。

后续 Schema 阶段可以为了查询、报告、缓存或审计决定是否物化 Case Summary 与 Contract Summary；即使保存，它们也不是新的权威判断来源。

权威事实仍然是：

```text
Episode
+ Evidence
+ Grader Result
+ Metric Result
```

## 9. Benchmark Metric 如何由多个 Case 支撑

### 9.1 为什么不能单 Case = 一个能力分数

一个 Test Case 只是输入空间中的一个样本。

即使某个 Case PASS，也只证明在这个具体输入、这次具体环境和这次具体 Run 中，相关 Contract 得到了满足。

因此：

```text
TC001 PASS
≠ Correctness = 100

TC001 PASS
≠ Robustness = 100

TC001 PASS
≠ 整个 Skill PASS
```

### 9.2 多样本主链

在一个 Run 中：

```text
Metric Specification
        ↑
        │ declares included observations
        │
Test Case 1 → Episode 1 → Evidence 1 → Grader Result 1
Test Case 2 → Episode 2 → Evidence 2 → Grader Result 2
Test Case 3 → Episode 3 → Evidence 3 → Grader Result 3
Test Case 4 → Episode 4 → Evidence 4 → Grader Result 4
Test Case 5 → Episode 5 → Evidence 5 → Grader Result 5
                                                   │
                                                   ▼
                                             Metric Result
```

所有 Episode 都针对该 Run 唯一 Subject。

Metric Result 的权威输入是多个 Grader Result，而不是一个 Case 的总体状态。

### 9.3 Grader Result 作为 Observation

v0.1 的最小聚合单位继续是：

```text
Grader Result
```

它表达：

```text
哪个 Run
+ 哪个 Subject（通过 Run）
+ 哪个 Episode
+ 哪个 Test Case
+ 哪个 Contract
+ 哪个 Grader Specification
+ 消费了哪些 Evidence
+ 得到了什么判断
```

因此不新增 Observation。

### 9.4 Metric Result 必须保留的概念信息

Metric Result 不能只保留：

```text
score = 84
```

它还必须能够说明：

- 计划使用了多少 Case；
- 实际产生了多少 Episode；
- 有多少有效 Grader Result；
- 有多少观察被纳入或排除；
- 有多少 BLOCKED；
- 有多少 NOT RUN；
- 有多少因为 Evidence 不足无法判断；
- 包含了哪些 Cases；
- 是否达到最低有效样本要求；
- 是否能够与另一个 Run 合法比较。

本轮只确认这些信息在概念上必须存在，不设计字段或数据结构。

### 9.5 重复执行不是简单增加分母

如果一个 Case 在同一 Run 中重复三次：

```text
TC001
→ E001
→ E002
→ E003
```

会产生多个 Grader Result，但它们是否等权进入 Metric，必须由冻结的 Metric Specification 和 Benchmark Policy 决定。

不能默认重复一百次就自动获得一百个独立 Benchmark Samples。

### 9.6 Baseline 与 Candidate 先分别形成 Run Result

正确关系是：

```text
Baseline Run
├── Subject = baseline implementation
├── Episodes
├── Grader Results
├── Metric Results
└── Scorecard

Candidate Run
├── Subject = candidate Skill
├── Episodes
├── Grader Results
├── Metric Results
└── Scorecard
```

然后：

```text
Baseline Run Result
        vs
Candidate Run Result
```

比较：

- 对应 Metric Results；
- Overall Score；
- Gate Status；
- Failure Modes；
- Sample / execution differences。

不同 Run 的 Grader Results 不能混入同一个 Metric Result 后再计算差异。

### 9.7 Evidence 不足不能自动按失败或零分处理

Metric Result 必须区分：

```text
FAIL
BLOCKED
NOT RUN
INSUFFICIENT EVIDENCE
NOT APPLICABLE
GRADER ERROR
ENVIRONMENT FAILURE
```

是否把某类无效观察计入分母，必须由 Metric Specification 在执行前确定。

## 10. 当前仍未解决的问题

以下问题留给下一阶段 Schema 设计决定，不重新打开 Concept Model Scope。

### 10.1 对象身份与版本引用

需要决定：

- 各一等对象如何拥有稳定身份；
- Frozen Benchmark Definition 如何标识版本；
- Run 如何精确引用某个冻结版本；
- Definition 修订后如何保留历史引用。

### 10.2 Subject 外部引用

Concept Model 已冻结：

```text
Run 1 → 1 Subject
```

Schema 阶段需要决定：

- 如何引用外部 Subject；
- 如何区分 Skill 版本、baseline implementation 和其他方案；
- 如何记录 Subject 身份与版本；
- 如何保证一个 Run 只对应一个 Subject。

Subject 不升级为核心一等对象。

### 10.3 Run 兼容性与 Run-to-Run Comparison

比较已经冻结为：

```text
Run vs Run
```

Schema 阶段需要决定：

- 两个 Run 在什么条件下兼容；
- 是否必须引用完全相同的 Frozen Benchmark Definition；
- 环境、Case、重复次数或样本差异如何影响可比性；
- 比较结果如何作为派生视图呈现；
- 如何表达 Not Comparable。

不新增 Comparison 一等对象。

### 10.4 Grader Result 的原子程度

需要决定：

- 一个 Grader Result 是否只允许判断一个 Contract；
- 还是允许一次 Grader 执行包含多个 Contract-specific 子判断；
- Metric 如何引用其中的特定判断。

无论如何，不能退化为只有一个模糊的 Case PASS / FAIL。

### 10.5 BLOCKED Episode 的创建边界

需要精确定义：

- Case 在什么阶段算已经产生 Episode；
- 前置检查失败是否创建 Episode；
- Run 级阻塞与 Episode 级阻塞如何区分；
- 未调度、Not Applicable、Not Run 和 Blocked 如何区分。

### 10.6 Artifact 与 Evidence 的引用方式

需要决定：

- Evidence 保存内容、引用还是两者；
- 如何引用 Artifact 的全部或部分；
- 原始 Artifact 的完整性如何确认；
- Evidence 后处理如何保留来源；
- 大文件、截图、日志和 Trace 如何表示。

### 10.7 Evidence 资格状态

需要定义统一状态来区分 available、complete、incomplete、missing、corrupted、incompatible、redacted 和 insufficient。

### 10.8 重复 Episode 的聚合政策

需要决定：

- 重复执行是否等权；
- retry 是否进入正式样本；
- 第一次失败和第二次成功如何同时保留；
- 稳定性 Metric 如何利用重复执行；
- 普通 Metric 如何避免重复样本过度计权。

### 10.9 Metric 的有效样本政策

需要决定：

- 最低有效观察数如何表达；
- BLOCKED、NOT RUN 和 Evidence 不足如何处理；
- 某些 Case 是否有不同权重；
- 多个 Grader Result 如何去重；
- 一个 Grader Result 被多个 Metric 使用时如何避免意外重复计分。

### 10.10 Case Summary 与 Contract Summary 的物化方式

v0.1 继续将 Case Result 和 Contract Result 定义为 Scorecard 派生视图，而不是一等对象。

Schema 阶段需要判断是否为了查询、报告、缓存或审计而物化；即使物化，它们仍然不是新的权威判断来源。

### 10.11 Gate Definition-level 引用表达

Concept Model 已冻结：

```text
Gate Specification
→ Metric Specification

or

Gate Specification
→ Grader Specification + Contract

or

Gate Specification
→ predefined execution-state condition
```

Schema 阶段需要决定：

- 如何表达这些 Definition-level 引用；
- 如何验证引用合法性；
- Gate Evaluator 如何定位本次 Run 对应的实际 Result；
- 多个结果满足或缺失时如何计算 Gate Result。

Gate Specification 不能引用未来的 Metric Result 或 Grader Result。

### 10.12 Overall Score 的精度与缺失处理

需要决定：

- Weight 合法范围和总和规则；
- Metric 不可计算时是否重新归一化；
- Gate Failure 是否只改变接受状态；
- Overall Score Disabled 如何表示；
- 两个兼容 Run 的 Overall Score 如何比较。

### 10.13 生命周期状态

下一阶段需要确定 Benchmark Definition、Run、Episode、Evidence、Grader Result、Metric Result 和 Scorecard 的生命周期状态，但 Concept Model v0.1 不预先设计状态枚举。

## 11. v0.1 冻结修订摘要

v0.1 不增加、不删除任何核心一等对象，只冻结以下三处边界修订。

### 11.1 Run → 单 Subject

```text
一个 Run
= 一个 Frozen Benchmark Definition
+ 一个 Subject
+ 一次完整执行
```

Subject 是外部被测对象引用，不成为第 17 个核心对象。

### 技术主题：11.2 Comparison → Run vs Run

```text
Baseline Run Result
        vs
Candidate Run Result
```

比较不再发生于一个 Run 内的两个 Subject，也不新增 Comparison Result 一等对象。

### 技术主题：11.3 Gate Specification → Definition-level references

```text
Gate Specification
→ Metric Specification

or

Gate Specification
→ Grader Specification + Contract

or

Gate Specification
→ predefined execution-state condition
```

运行后 Gate Evaluator 才使用这些引用定位本次 Run 的实际 Metric Result、Grader Result 或执行状态，计算 Gate Result。

Concept Model v0.1 到此冻结，作为进入第一批 Schema 设计前的当前 Concept Model Baseline。它不是 `Final Forever`，未来仍可通过新的版本演进。
