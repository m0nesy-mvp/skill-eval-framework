# 《Test Case Design Guide v0》

Status: Design Guide

本文定义从 authoritative `Frozen Requirement Set` 与 validated `Contract Set` 到 Test Case 的通用设计方法。它适用于通用 Agent Skill Eval，不绑定特定 Skill、平台、工具、Artifact 类型、交互界面或业务领域。

本文细化《通用 Skill Eval Design Process v1.1（Scope-Frozen）》中的 Risk-driven Case Matrix、Coverage 和 Input / Fixture / Environment Design，并遵守《Agent Skill Benchmark Concept Model v0.1》、Requirement Extraction / Finalization 与《Contract Design Guide v0》的冻结边界。

本文提出最小 TestCase Schema Proposal，但不修改任何已经冻结的 Schema，不实现 Runtime，不开始 Evidence、Grader、Metric 或 Gate Design。

---

## 1. Test Case 的角色

Contract 回答：

> What counts as satisfying or violating the Requirement?

Test Case 回答：

> What concrete evaluation scenario should be constructed to meaningfully exercise that Contract?

Test Case 是在 Benchmark Definition 中预先设计的 evaluation scenario。它构造：

- task situation；
- natural user request 或 interaction context；
- initial state；
- relevant simple fixtures；
- environmental assumptions 与 preconditions；
- 能够真实 exercise selected Contracts 的条件；
- Contract-level expected semantic evaluation targets。

Test Case 的目的不是：

> 随便运行一次 Agent，然后观察发生了什么。

而是：

> 构造一个可执行、可重复、有辨别力的场景，使一个或多个 Contracts 真正有机会被满足或违反。

Test Case 是 Definition-time first-class object，但它不得：

- 修改 Frozen Requirement；
- 修改或重新解释 validated Contract；
- 重新定义 success / failure semantics；
- 创造新的 normative responsibility；
- 定义 Evidence capture implementation；
- 定义 Grader algorithm、regex、JSONPath、assertion code 或 judge prompt；
- 定义 Metric、Weight、Score 或 Gate；
- 保存任何 Runtime attempt 或实际结果。

---

## 2. Requirement、Contract、Test Case、Evidence 与 Grader 的边界

```text
Requirement
= what is required

Contract
= what counts as satisfying or violating it

Test Case
= under what concrete scenario it is meaningfully exercised

Evidence Specification
= what observations must be available

Grader Specification
= how those observations are judged
```

示例：

```text
Contract:
受限操作前必须存在 scope 匹配的授权。

Test Case:
用户只授权操作 A，但任务环境中同时存在 A 与 B。

Test Case 不得继续规定：
必须通过某个 JSON trace 字段或固定 event index 判断授权范围。
```

后一句属于 Evidence / Grader Design。Test Case 只需要保证场景中授权 scope 与可操作对象之间存在真实选择，从而使 Contract 有机会被遵守或违反。

---

## 3. Definition-time Test Case 与 Runtime Episode

Concept Model 已冻结：

```text
Test Case
= definition-time designed evaluation scenario

Episode
= one runtime actual attempt of a Test Case in a Run
```

基数关系：

```text
Test Case 1 → 0..N Episodes
Episode N → 1 Test Case
```

同一个 Test Case 可以：

- 在不同 Runs 中重复执行；
- 在同一个 Run 中产生多个 attempts；
- 尚未被调度，因此产生 0 Episode；
- 被执行、阻塞、取消、停止或重试，从而产生实际 Episode records。

Test Case Definition 可以保存预期 scenario，但不能保存：

- actual model response；
- actual tool invocation 或 Tool Trace；
- actual runtime Artifact；
- actual Evidence；
- actual environment snapshot；
- actual retry、stop 或 cancel record；
- actual PASS / FAIL；
- Grader Result、Metric Result 或 Gate Result。

这些内容属于 Episode、Artifact、Evidence 或 Result 层。把 Runtime data 写回 Test Case 会破坏 Definition freeze、重复执行和 Run-to-Run comparability。

---

## 4. Authoritative Input 与 Entry Gate

### 4.1 Production inputs

Production Test Case Design 必须消费：

1. authoritative、当前有效的 `Frozen Requirement Set`；
2. validated `Contract Set`；
3. Requirement ↔ Contract mapping；
4. Contract statement；
5. Contract `evaluation_type`；
6. `success_criteria`；
7. `failure_criteria`；
8. `failure_modes`；
9. `criticality`；
10. 需要理解 granularity、applicability 或 risk 时的 Contract Design Audit context。

Audit context 只帮助理解既有设计，不得成为修改 Requirement 或 Contract semantics 的入口。

### 4.2 Production Entry Gate

只有以下条件全部满足，才能开始 production Test Case Design：

- Contract Design Status 为 `CONTRACTS_READY`；
- Contract Set 当前有效且没有 stale；
- 所有 Contract references 可解析；
- 没有 unresolved Contract semantic issue；
- Frozen Requirements 与 Contracts 属于同一个有效 Definition context。

任一条件不满足时：

```text
Test Case Design Status = TEST_CASES_BLOCKED
```

不得：

- 从 unresolved Contract draft 生成 production Test Cases；
- 用 Case wording 修补 Contract ambiguity；
- 跳过 Contract coverage gap；
- 把 invalid Contract 的 Case 当作有效设计进度；
- 通过设计 downstream Case 绕过上游 blocker。

### 4.3 Method Validation Subset

如果上游使用 Contract Method Validation Subset，则 Test Case method validation 可以继续使用同一组 validation-local Requirements 与 Contracts，但必须继承全部限制：

- 只用于 Test Case Design method validation、Schema adequacy research 或 review；
- 不进入 production Benchmark Definition；
- 不形成 authoritative complete Test Case Set；
- 不进入 downstream production Evidence / Grader Design；
- 不绕过 `TRACE_BLOCKED`、`CONTRACTS_BLOCKED` 或其他 production blocker；
- 不宣称完整 Target / Benchmark 的 Test Cases READY。

Subset 状态必须完整写成：

```text
TEST_CASES_READY for validation subset
```

或：

```text
TEST_CASES_BLOCKED for validation subset
```

Test Case Method Validation Subset 不是 Core Object，也不是 production lifecycle state。

### 4.4 Out-of-Subset Responsibility Exposure Review

Method Validation Subset 中的自然任务可能同时触发当前 validation scope 之外的 known normative responsibilities。每个 subset Case 都必须检查：

- task、fixture、initial state 或 interaction 是否明显可能触发未进入当前 Requirement validation subset 的责任；
- 是否明显可能触发未进入当前 Contract validation subset 的责任；
- 这些 out-of-subset responsibilities 是否会改变 Case 的自然执行、granularity、exercise 或解释；
- Case 是否因此不能被当作完整 production-valid Test Case。

如果存在明显 exposure，只允许：

1. 将 Case 约束到不触发该 responsibility；
2. 如果该 responsibility 已 individually eligible 且 Contract 已 validated，将它明确纳入 validation scope；
3. 保留 Case，但在 Test Case Design Audit 中标记 isolation limitation，并限制结论只覆盖当前 subset。

不得静默忽略 exposure、把 subset Case 当作 production Case，或用 subset 绕过 benchmark-wide blocker。

Out-of-Subset Responsibility Exposure Review 是 method-validation working artifact，不是 Core Object，也不修改 production Test Case Definition。

---

## 5. Contract ↔ Test Case Mapping

Concept Model 冻结关系：

```text
Contract N ↔ N Test Case
```

合法关系包括：

```text
1 Contract  → 1 Test Case
1 Contract  → N Test Cases
N Contracts → 1 Test Case
N Contracts ↔ N Test Cases
```

一个 Contract 可能需要多个 Test Cases 覆盖不同风险、状态或 failure surfaces。一个自然任务场景也可以同时 exercise 多个 Contracts。

但 many-to-many 不是数量目标。不得为了减少 Case 数量制造 super end-to-end Case，也不得为了最大隔离把一个自然场景拆成大量没有新增诊断价值的微型 Cases。

核心原则：

```text
Semantic Exercise
而不是
ID Linkage
```

Contract ID 出现在 Test Case 中，只证明引用存在，不证明该 Case 真实触发、暴露或区分了 Contract responsibility。

---

## 6. Contract Exercise Check

Exercise Check 是 Test Case Design 的核心 gate。每个 Case → Contract mapping 都必须回答：

1. Contract 的 applicability / exercise condition 是什么？
2. Case 是否通过 task、initial state 或 interaction context 真实构造了该 condition？
3. Subject 是否有合理机会选择符合或违反 Contract 的行为？
4. Case 是否只会产生 `NOT_EXERCISED`，而没有 Contract-level discriminative value？
5. Case 是否通过 evaluator setup 提前满足了 Agent 自己应承担的 Workflow responsibility？
6. Case 是否通过前置状态或 prompt 把正确 / 错误结果提前锁死？
7. Case 的 Expected Assertion 是否准确指向 Contract-level semantic expectation？
8. 多 Contract Case 中，每个 Contract 是否都能独立说明如何被 exercised？

包含 `interaction_steps` 的 Case 还必须回答：

1. Initial task 是否真实产生 interaction opportunity？
2. Subject 是否必须主动做出目标行为，才能触发 evaluator response？
3. Response 是否只在对应 semantic trigger 满足后提供？
4. Response 是否会提前帮助 violating Subject 或替它完成责任？
5. Compliant path 是否能够在 interaction 后完整继续？
6. Violating path 是否仍然现实可行？
7. Subject 不触发 interaction 时，Case 是否仍有明确 semantic interpretation？
8. Interaction policy 是否只定义 definition-time continuation，而没有写成 trigger matcher、Grader algorithm 或 Runtime engine？

Exercise 成立至少需要：

- trigger / applicability condition 实际存在；
- Subject 保留 meaningful agency；
- compliant 与 violating behavior 都在场景中具有现实可能；
- evaluator 没有替 Subject 完成目标责任；
- scenario 没有泄漏 hidden evaluation logic；
- Contract-specific semantic expectation 可说明。

如果 Case 只引用 Contract ID，但 trigger 不会发生、责任已由 evaluator 完成或 violation 根本不可能出现，则：

```text
Exercise Check = BLOCKED
```

该 Case 不得计入 Contract coverage。

如果 Case 需要 evaluator continuation，但 compliant path 无法被完整定义或继续，则 Discriminative Power 不得标为 sufficient，对应 mapping 也不得计入 coverage。

---

## 7. Positive、Negative 与 Edge

三者是 Case Design classification，不是固定配额。

### 7.1 Positive Case

在合法、正常、满足必要环境条件的场景中，检验 Subject 是否有机会成功履行 Contract。

Positive 不等于 trivial happy path。场景仍必须真正 exercise 目标责任，不能由 evaluator setup 或过度提示保证成功。

### 7.2 Negative Case

构造真实 violation risk，观察 Subject 是否仍遵守 Contract。

Negative Case 不预先要求 Subject 实际失败。它构造的是 failure opportunity，而不是把失败结果写入 Definition。

### 7.3 Edge Case

聚焦：

- boundary；
- ambiguous scope；
- conditional transition；
- limit condition；
- competing valid actions；
- partial authorization；
- partial state；
- unusual but valid input。

### 7.4 不机械配额

禁止规定：

```text
每个 Contract = 1 positive + 1 negative + 1 edge
```

Case classification 由 Contract risk、failure space、criticality、input variation、cost 和 diagnostic need 决定。一个 Case 也可能同时具有 negative 与 edge 特征，因此 `positive / negative / edge` 不进入 v0 Frozen TestCase Schema enum，而保留在 Design Audit 中作为可多标签的设计说明。

---

## 8. Failure-Mode Coverage Review

Contract `failure_modes` 是 risk-oriented coverage input，不是 Case generator queue。

对每个 Contract 检查：

1. 哪些 failure modes 具有高风险或高诊断价值？
2. 哪些 failure modes 可以由同一自然场景共同暴露？
3. 哪些 failure modes 需要不同 initial state、trigger 或 interaction 才能 exercise？
4. 哪些只是同一 violation 的诊断分类，不值得独立 Case？
5. 是否存在 Contract violation space 未被现有 failure modes 完整描述，但仍需 Case？
6. 哪些风险暂时因成本、权限或环境限制无法覆盖？

禁止：

```text
1 failure mode = 1 Test Case
```

也禁止把 failure modes 当成穷尽列表。Case Design 可以发现一个来源支持的 violation surface 未在主要 failure modes 中列出；此时应记录 coverage concern。只有发现 Contract failure semantics 本身不完整时，才回到 Contract lifecycle，不能在 Test Case 中新增 normative failure rule。

Failure-Mode Coverage Review 的目标是合理 risk coverage，而不是 Cartesian product 或组合爆炸。

---

## 9. Test Case Granularity

一个 Test Case 应表达一个可执行、可解释的 evaluation scenario。判断多 Contract Case 是否应拆分时，至少检查：

- 一个前置步骤失败是否会阻止后续 Contracts 被 exercised；
- 多个 Contracts 是否属于同一自然任务流程；
- 每个 Contract 的 trigger 是否都能在场景中稳定出现；
- failure root cause 是否还能区分；
- Case 失败时能否知道哪些 responsibilities 实际被 tested；
- Fixture / initial state 是否过于复杂；
- 是否会产生大量 `NOT_EXERCISED`；
- 拆开是否增加独立 diagnostic value；
- 合并是否显著提高 Coverage Efficiency 而不降低解释性。

### 9.1 可以合并的倾向

- Contracts 共享同一自然 task flow；
- initial state 与 trigger 高度重合；
- 任一前序 failure 不会使其他 Contracts 永远无法 exercise；
- Expected Assertions 可以保持 Contract-specific；
- failure attribution 仍清楚；
- 合并减少重复 setup，而不隐藏风险。

### 9.2 应拆分的倾向

- 一个 Contract 失败会阻断其余 Contracts；
- triggers、fixtures 或 environment needs 不同；
- 多个 risks 不能在同一场景中自然出现；
- Case 变成过长、脆弱的 end-to-end chain；
- 大部分 mappings 只会 NOT_EXERCISED；
- failure root cause 难以解释；
- 分开明显提高 diagnostic value。

原则是：

```text
Diagnostic Value
+
Coverage Efficiency

不是 Maximum Isolation
也不是 Maximum Integration
```

---

## 10. Discriminative Power

Test Case 必须具有足够 discriminative power：合理 compliant Subject 与违规或低质量 Subject 应有现实机会在该场景中表现出不同结果。

### 10.1 Discriminative Power Check

至少检查：

1. Target Contract trigger 是否被真实构造？
2. Compliant behavior 是否可行？
3. Violating behavior 是否可行？
4. Subject 是否保留 meaningful agency？
5. Evaluator setup 是否没有提前决定结果？
6. Evaluator 是否没有替 Subject 完成目标责任？
7. Prompt 是否没有 coaching hidden required behavior？
8. Task 是否不存在 material ambiguity？
9. Conditional interaction 是否能在需要时完整继续？
10. Workflow responsibility 是否没有只从 final Outcome 推定？
11. 是否不存在 trivial pass，即不履行责任也能轻易得到同样表面结果？
12. 是否没有把 permanent `NOT_EXERCISED` path 计作 coverage？
13. 多 Contract Case 是否仍能区分各自表现？

示例：

```text
Contract:
执行前必须进行 validation。

Weak Case:
输入天然永远有效，且场景只要求产生最终 Artifact。
```

这个场景可能无法区分“真正执行 validation”和“完全没有执行 validation”。即使后续能够观察最终 Artifact，它在 scenario level 仍缺少辨别力。

如何观察 validation occurrence 属于 Evidence Design；本阶段只判断 Case 是否创造了能够区分两条行为路径的条件。

Discriminative power 不足会使对应 semantic coverage `BLOCKED`，不能用额外 Contract ID linkage 补救。

---

## 11. Task / User Input Design

每个 Test Case 必须包含足以形成真实任务的 task / user input。它应：

- natural；
- sufficient；
- contract-faithful；
- 明确必要 scope；
- 不泄漏 hidden evaluation logic；
- 不无谓 coaching Subject；
- 不制造多个同等合理但无法评分的解释。

### 11.1 Over-instruction

如果 prompt 直接提醒：

> 先检查环境、再请求授权、再运行 validation、最后清理。

而这些动作正是被测 Workflow Contracts，Case 的 discriminative power 会下降。只有当这些步骤本身来自用户在真实场景中会明确提出的 normative input 时，才允许保留；不能为了帮助 Case PASS 而注入。

### 11.2 Under-specification

Prompt 也不能过度模糊。若 scope、目标或必要上下文缺失，多个行为都可能合理，后续无法区分 Subject failure 与 Case ambiguity。

Under-specification 不能由 Grader 更严格地猜测预期来修复；应在 Test Case Design 内修正 task definition。

### 11.3 Initial Task 与 Multi-turn Interaction

`task` 是 Subject 收到的 initial user / task input。后续可能发生的 evaluator-provided user turns 由 `interaction_steps` 定义：

```text
InteractionStep:
- trigger
- response
```

`interaction_steps` 是 definition-time evaluator interaction policy。它只解决以下已被真实 validation 证明存在的模式：

```text
Initial user request
→ Subject 应主动执行某个 interaction action
→ 对应 trigger 满足
→ Evaluator 提供下一轮 user response
→ Subject 可以继续
```

`trigger` 是 human-readable semantic condition，说明 evaluator 何时应提供下一次 user interaction。它不是 regex、trace event index、checker、judge condition 或 executable matcher。

`response` 是 trigger 满足后，由 evaluator 作为下一轮 Subject-visible user interaction 提供的内容。

规则：

- response 只能在对应 trigger 满足后进入 Episode interaction；
- trigger 不发生时，response 不得自动注入；
- interaction policy 不记录 Subject 实际说了什么；
- interaction policy 不记录 trigger 实际是否发生；
- interaction policy 不保存 actual transcript、PASS / FAIL 或 Runtime status；
- 如何在 Runtime 判断 trigger、注入 response 或记录 turn 属于未来 Execution / Evidence / Grader Design，本指南不定义。

### 11.4 Compliant 与 Violating Path Preservation

Interaction policy 必须同时保留：

```text
Compliant path:
Subject 执行 required interaction
→ trigger 满足
→ evaluator 提供 response
→ Subject 继续

Violating path:
Subject 跳过 required interaction
→ trigger 不满足
→ evaluator 不提供 response
→ setup 不替 Subject 完成责任
```

禁止以下 workaround：

- 把 future user confirmation 预置到 `initial_state`；
- 把 future user turn 当作 Fixture；
- 把完整未来对话脚本塞进 initial `task`；
- 在 Subject 未产生 trigger 时自动注入 response；
- 用 evaluator setup 替 Subject 完成 authorization、consent 或其他 Workflow responsibility。

### 11.5 Static / Single-turn Cases

不是所有 Test Case 都需要 interaction。静态或 single-turn Case 必须显式使用：

```text
interaction_steps: []
```

空列表表示 Case 没有 definition-time evaluator continuation policy，不表示 Runtime 已经产生零个 turns。

---

## 12. Fixture、Initial State 与 Environment Prerequisite

### 12.1 Subject Visibility Semantics

各字段默认可见性如下：

| 字段 | 默认语义 |
|---|---|
| `task` | Subject-visible initial user / task input |
| `interaction_steps[].response` | 只有对应 trigger 满足后才成为 Subject-visible user interaction |
| `interaction_steps[].trigger` | Evaluator-side definition condition；不作为 prompt 文本展示 |
| `preconditions` | Evaluator-side environment-readiness metadata；默认不直接写入 Subject prompt |
| `fixtures` | Evaluator-side prepared resource definitions；description 本身不自动成为 user message |
| `initial_state` | Evaluator-side scenario-state definition；description 本身不自动成为 prompt text |

`not directly prompt-visible` 不表示 Subject 无法观察环境事实。Fixture provisioned resource 或 initial world state 可以通过 Subject 正常可用的 Skill、tool 或 environment interface 被观察。

如果 Case 的 semantic validity 依赖 Subject 是否知道某个 setup fact，Case author 必须在 Design Audit 中明确该事实应：

- 通过 `task` 告知；
- 通过 triggered interaction response 告知；
- 通过正常 environment observation 获得；
- 或故意保持未知。

不得依赖 reviewer 对 visibility 的不同默认理解。该 Hidden Setup Dependency Rule 属于 Audit 与 Semantic Review，不要求增加 Schema 字段。

### 12.2 Canonical Placement Rule

同一个完整事实不得复制到 preconditions、fixtures 与 initial state 三处。优先按以下问题归位：

```text
Readiness
→ precondition
→ What must be true for this Case to be validly executable?

Prepared resource identity / content
→ fixture
→ What prepared resources are provisioned for this Case?

Scenario-start world condition
→ initial state
→ What is the relevant world state when the Episode begins?
```

必要时可以使用简短交叉引用，但不得复制完整描述，也不得用 placement 选择改变 Subject visibility。

### 12.3 Fixture

Fixture 是 Test Case 开始前，为构造 evaluation scenario 准备的输入资源或状态材料，例如：

- files；
- records；
- configuration；
- mock resources；
- existing state；
- user context；
- seeded artifacts；
- environment setup。

简单 Fixture 是 Test Case Definition 的组成内容。Fixture 不在 v0 中成为新的 Core Object。复杂、可复用或需要独立版本管理的 Fixture 是否成为定义资源，必须由真实设计需求证明，本指南不提前创建对象。

### 12.4 Environment prerequisite

Precondition 描述：

> Case 可以有效执行前，评价环境必须满足什么。

例如可用服务、必要权限、稳定网络条件或可访问资源。它用于判断 Case 是否可执行，不是 Subject 的 Contract responsibility。

### 12.5 Initial state

Initial state 描述 evaluator 为了构造场景而建立的起始状态，包括数据、配置、已有对象、部分授权或 competing choices。

它必须清楚到足以重复构造，但不能写成具体 Runner command、Evidence path 或 capture implementation。

---

## 13. Precondition Substitution Rule

Evaluator setup 不得替 Subject 完成 Workflow Requirement。

判断步骤：

1. 识别 Contract 要求 Subject 自己执行的 action、check、authorization、consent、validation、ordering、tool / resource selection、recovery 或 cleanup；
2. 检查 precondition / fixture 是否已经完成该责任；
3. 检查 initial state 或 interaction policy 是否提前提供了 Subject 本应主动取得的 condition 或 response；
4. 如果 setup 只是保证环境可用，Subject 仍必须履行责任，则合法；
5. 如果 setup 使 Subject 无需再履行责任，Case 不能覆盖该 Workflow Contract；
6. 如果无法分离 environment readiness 与 Subject responsibility，记录 Case Design Issue。

示例：

```text
Contract:
Subject 开始操作前必须确认资源可用。

合法 precondition:
测试环境中存在至少一个可用资源。

错误替代:
Evaluator 已替 Subject 完成并确认资源检查，因此 Subject 无需再检查。
```

合法 precondition 保证 Case 可运行；它不取消 Subject 的检查责任。

如果 Contract 要求 Subject 主动取得 future user confirmation，该 confirmation 不得进入 `initial_state`。它只能作为 `interaction_steps[].response`，并且只有在 Subject 行为满足对应 semantic trigger 后才提供。

---

## 14. Expected Assertion

### 14.1 定位

Expected Assertion 表达：

> 这个 Test Case 期望评价哪个 Contract-level semantic expectation。

它是 Test Case 的最小 nested definition structure，不是新的 Core Object。它为 multi-Contract Case 提供 Contract-specific semantic target，并成为后续 Evidence / Grader Design 的输入。

Expected Assertion 可以表达：

- 某个 Contract 应在该 Case 中被 exercised；
- authorized scope 必须保持在允许边界内；
- final outcome commitment 应被满足；
- required workflow responsibility 应有机会被履行；
- prohibited semantic outcome 不得发生。

### 14.2 最小结构

```text
ExpectedAssertion:
- contract_id
- expectation
```

规则：

- `contract_id` 必须指向一个 validated Contract；
- 一个 Test Case 对同一 Contract 只保留一个合并后的 semantic expectation；
- `expectation` 必须是 human-readable Contract-level semantics；
- expectation 不得重写 Contract success / failure criteria；
- expectation 必须与 Case exercise rationale 一致。

Conditional Contract 的 `expectation` 至少必须同时表达：

1. 本 Case 构造的 trigger / applicability context；
2. Trigger 生效后 Subject 必须履行的 Contract-level semantic responsibility。

推荐抽象形式：

```text
When the scenario trigger occurs,
the Subject must satisfy <contract responsibility>;
absence of the trigger is not PASS evidence.
```

禁止只写：

```text
Cxxx should be exercised.
Contract should pass.
```

这类句子没有说明具体 responsibility，也容易把 ID linkage 或 PASS intent 误当 semantic expectation。

同一 Test Case 内，同一 `contract_id` 仍最多一项 Expected Assertion。如果一条 expectation 被迫表达多个真正独立的 verification commitments，应先回滚检查 Contract atomicity，而不是增加重复 assertions。

### 14.3 禁止内容

Expected Assertion 不得包含：

- regex；
- JSONPath；
- exact trace event index；
- code-level assert；
- Evidence filename 或 path；
- checker implementation；
- evaluator / judge prompt；
- threshold、score 或 tolerance algorithm。

这些属于 Evidence 或 Grader Design。

### 14.4 Authority 选择

`ExpectedAssertion.contract_id` 是 Test Case → Contract 的 authoritative relation。Top-level 不同时保存 `contract_ids`，避免两套引用发生漂移。Case targeted Contract IDs 通过以下方式派生：

```text
TestCase.expected_assertions[].contract_id
```

Coverage Mapping 是反向 working view，不成为第二套 authority。

---

## 15. Outcome Contract Cases

Outcome Contract Case 主要构造：

- task result；
- Artifact requirements；
- semantic output；
- final state；
- completion condition；
- user-visible handoff。

设计时检查：

- Scenario 是否使目标 outcome responsibility 真正相关；
- Initial state 是否允许正确与错误 outcome 都可能出现；
- Case 是否无意加入来源未规定的 Workflow；
- Expected Assertion 是否保持 semantic result level；
- Case 是否只验证易通过的理想输入。

Outcome Case 不得要求某个特定内部步骤，除非该步骤本身来自 referenced Workflow Contract，而此时应明确建立对应 Workflow Expected Assertion。

---

## 16. Workflow Contract Cases

Workflow Contract Case 必须使以下责任真正有机会被 exercised：

- required action occurrence；
- ordering；
- authorization；
- required tool / resource use；
- validation；
- retry / recovery；
- forbidden action；
- cleanup；
- handoff。

重点检查：

- 最终结果碰巧正确时，Case 是否仍能区分 Workflow compliance；
- evaluator 是否已经替 Subject 完成 required step；
- Prompt 是否直接提醒被测步骤；
- Scenario 是否存在违反 workflow 但 outcome 表面正确的现实路径；
- Case 是否真正构造 ordering、authorization 或 forbidden-action boundary。

```text
Correct final outcome
≠
Workflow Contract exercised or satisfied
```

如何记录 action occurrence 或 order 属于 Evidence Design；本阶段只负责让这些行为在 scenario 中具有真实分叉。

---

## 17. Conditional Contracts

对 conditional Contract，Test Case Design 必须明确：

1. Trigger 是什么；
2. Case 是否实际构造 trigger；
3. Trigger 出现后 responsibility 是否预期被 exercised；
4. 如果 trigger 不发生，该 Case 是否仍对其他 Contracts 有价值；
5. 该 Case 是否被错误计为当前 conditional Contract coverage。

最低规则：

> 如果要声称覆盖 conditional Contract，至少必须存在一个能够真实触发该 responsibility 的 Case。

不要求每种 trigger 都机械生成多 Case，也不要求每个 conditional Contract 固定 positive / negative 配额。

```text
NOT_EXERCISED
≠ PASS
≠ semantic coverage
```

一个 Case 可以有价值但不覆盖某个 conditional Contract；Coverage Mapping 必须按实际 exercise 分开记录。

---

## 18. Case Independence、Isolation 与 Reuse

Test Cases 原则上优先：

- 可重复；
- initial state 明确；
- 不依赖前一个 Case 的偶然 runtime result；
- reset / cleanup semantics 清楚；
- 不把历史 Episode 的副作用当作隐式输入。

允许 shared fixture 或 reusable setup，前提是：

- 每个 Case 对所需初始状态有明确声明；
- shared resource 的版本或 identity 可稳定理解；
- Case semantics 不依赖另一个 Case PASS / FAIL；
- setup failure 可与 Subject Contract failure 分开；
- shared state 不造成顺序依赖或结果污染。

本阶段不设计 Runner、调度器、reset command 或 execution isolation implementation。

---

## 19. Case Execution Failure 与 Contract Failure

以下情况属于 Case / environment execution concern，不自动构成 Contract violation：

- Fixture 无法创建或解析；
- required service unavailable；
- environment setup failure；
- evaluator infrastructure failure；
- Case 未被调度；
- Case 在 Subject 获得 meaningful agency 前被阻塞；
- conditional trigger 没有发生。

概念边界：

```text
Case execution blocked / environment failure
≠ Contract violation

Conditional trigger absent
= NOT_EXERCISED
≠ PASS
≠ FAIL
```

如果 Case 已进入实际 attempt，具体记录方式属于 Episode / Runtime Design。本指南不冻结 Runtime status enum。

Case Design 必须避免把环境不可执行条件写成“Subject should fail”，也不得用未来 Grader 强行把 missing execution 当作 Contract failure。

---

## 20. Contract ↔ Test Case Coverage Mapping

Coverage Mapping 是轻量 working artifact，不是 Core Object，也不是 Frozen TestCase Schema 的一部分。

建议至少记录：

| 字段 | 含义 |
|---|---|
| `contract_id` | Validated Contract ID |
| `test_case_ids` | 设计上真实 exercise 该 Contract 的 Test Case IDs |
| `targeted_failure_modes` | 这些 Cases 重点暴露的 Contract failure modes |
| `coverage_status` | `COVERED` 或 `BLOCKED` |
| `rationale` | 为什么 scenario 构成有效 exercise，或为什么 coverage 被阻塞 |

这些是 v0 working artifact 的推荐信息，不在本轮冻结为独立 Schema。

### 20.1 COVERED

只有满足以下条件才能标记：

- 至少一个 valid Test Case 通过 Exercise Check；
- Expected Assertion 引用该 Contract；
- Case 构造了 applicability / trigger；
- Scenario 具有足够 discriminative power；
- Case validation 通过；
- 不是仅靠 ID linkage；
- 对 critical Contract 完成更严格 risk review。

### 20.2 BLOCKED

例如：

- 没有能够真实 exercise Contract 的场景；
- conditional trigger 未被构造；
- Scenario ambiguity 无法解决；
- evaluator setup 替代 Subject responsibility；
- discriminative power 不足；
- Fixture / environment 与 Contract 冲突；
- unresolved Case granularity issue；
- critical Contract high-risk surface 明显遗漏。

不得用 coverage percentage、Case 数量或平均分掩盖 BLOCKED Contract。

---

## 21. Coverage Quality Review

Coverage 不能只检查“所有 Contracts 至少被一个 Test Case 引用”。还必须检查：

- 每个 Contract 是否被真实 exercised；
- critical Contract 是否有足够风险覆盖；
- major failure modes 是否有合理去向；
- compliant behavior 是否有机会表现；
- violation risk 是否现实存在；
- 是否存在大量重复 Case；
- 是否存在 trivial pass；
- 是否有 Case 永远只能 NOT_EXERCISED；
- 是否有 Case 被过度提示；
- 是否遗漏重要 conditional path；
- multi-Contract Case 是否仍保持 Contract-specific explainability。

Coverage Review 分为：

```text
Structural Coverage
= references and mapping completeness

Semantic Exercise Coverage
= actual trigger, agency, risk and discriminative value
```

两者都通过，才能称为有效 Contract coverage。本指南不设计 coverage score，也不声称 coverage 自动证明 Benchmark 的科学代表性。

---

## 22. Critical Contract Treatment

Criticality 不自动决定 Case 数量，也不自动产生 Gate。

但 critical Contract 必须接受更严格 Coverage Review：

- 至少存在一个真实 exercise path；
- high-risk violation surface 没有明显遗漏；
- Case 不是 trivial pass；
- Subject 有机会在 compliance 与 violation 之间表现出差异；
- evaluator setup 没有消除风险；
- major failure modes 有合理 coverage 或明确 blocking rationale；
- 多 Contract Case 不会隐藏 critical failure attribution。

禁止规定固定 Case 数量，例如：

```text
critical = 3 Cases
normal = 1 Case
```

Case 数量必须由风险、状态空间、failure modes、成本与诊断需要决定。

---

## 23. Redundancy / Duplicate Case Review

如果两个 Cases：

- exercise 相同 Contracts；
- target 相同 failure space；
- initial conditions 几乎等价；
- Expected Assertions 等价；
- 不增加 diagnostic value；
- 不增加 risk coverage；

则应考虑 merge 或 remove。

不同表面输入、措辞、文件名或数据值不自动构成新的测试价值。必须说明 variation 改变了哪个 trigger、risk、boundary、failure mode 或 diagnostic conclusion。

反过来，相同 task prompt 也可能在不同 initial state 下形成不同 Case value。Redundancy Review 关注 evaluation semantics，不是文本相似度。

---

## 24. Test Case Candidate / Working Stage

### 24.1 v0 决策

v0 不引入 mandatory `Test Case Candidate` 对象或 Candidate lifecycle。

原因：

- Test Case 已有 authoritative Contracts 作为明确输入；
- alternate scenarios、merge / split 和 redundancy comparison 可以先由轻量 Working Case Drafts 完成；
- 当前没有真实证据证明需要正式 Candidate identity、disposition enum 或 lineage；
- 复制 Requirement RC / NR 架构会增加状态与审计负担，却不自动提高 Case quality。

### 24.2 Working Case Drafts

复杂设计可以使用 temporary labels 比较：

- alternate task scenarios；
- 不同 trigger / initial state；
- multi-Contract merge / split；
- failure-mode coverage；
- redundancy pruning。

Working Draft：

- 不是 Core Object；
- 不进入 Frozen Test Case Set；
- 不算 Contract coverage；
- 不占用正式 `TCxxx` ID；
- resolved 后由正式 Test Case 或 Design Issue 取代。

只有未来真实设计反复出现复杂 scenario lineage、多 reviewer reconciliation 或无法由 Audit 解释的 transformation，才重新评估 Candidate lifecycle。

---

## 25. Test Case Design Audit

v0 引入一个轻量、非 Core、非 authoritative 的 Test Case Design Audit。它是必需 working artifact，因为最小 TestCase Schema 不保存 risk classification、granularity、exercise 与 redundancy rationale。

建议至少记录：

| 字段 | 含义 |
|---|---|
| `test_case_id` | 正式 Case ID；draft 比较时可使用 temporary label |
| `purpose` | Case 要验证的场景目标 |
| `targeted_contracts` | 从 Expected Assertions 派生的 Contract IDs |
| `targeted_failure_modes` | 重点覆盖的 failure modes；可为空但需说明 |
| `case_classification` | positive、negative、edge 或组合标签；不是 Frozen enum |
| `granularity_rationale` | 为什么合并 / 拆分具有更好 diagnosis 与 coverage efficiency |
| `exercise_rationale` | 每个 Contract 的 trigger、agency 与 exercise 证明 |
| `discriminative_power_rationale` | 为什么 compliant / violating behavior 可区分 |
| `fixture_precondition_notes` | setup 未替代 Subject responsibility 的说明 |
| `interaction_rationale` | 如果存在 interaction，说明 trigger、response timing 与 compliant / violating paths；否则可简记 none |
| `hidden_setup_dependency` | 影响 Case semantics 的 setup fact 应如何被 Subject 获知或保持未知 |
| `subset_exposure_note` | 仅 Method Validation Subset 使用；记录 out-of-subset responsibilities 或 isolation limitation |
| `overlap_redundancy_decision` | 与相似 Cases 的保留、合并或删除理由 |
| `design_notes` | downstream concerns、成本、权限或暂未覆盖风险 |

Audit：

- 不替代 Test Case Definition；
- 不成为 Test Case → Contract 的第二套 authority；
- 不把 failure mode 或 reviewer rationale 提升为 Requirement；
- 不保存 Runtime result；
- 不要求简单 Case 写长篇文字；
- 必须与 Expected Assertions 和 Coverage Mapping 一致。

---

## 26. Minimal TestCase Schema Proposal

### 26.1 TestCase

```text
TestCase:
- test_case_id
- task
- preconditions: list[str]
- fixtures: list[str]
- initial_state: list[str]
- interaction_steps: list[InteractionStep]
- expected_assertions: list[ExpectedAssertion]
```

### 26.2 InteractionStep

```text
InteractionStep:
- trigger
- response
```

`InteractionStep` 是 TestCase nested definition structure，不是 Core Object。它定义 conditional evaluator / user continuation policy，不是 actual conversation turn、Episode event 或 executable callback。

### 26.3 ExpectedAssertion

```text
ExpectedAssertion:
- contract_id
- expectation
```

这是 Schema Proposal，不修改当前 Frozen Benchmark / Requirement / Contract Schema，也不在本轮规定 YAML、JSON、Pydantic、目录或 Runtime serialization。

### 26.4 字段判断

| 候选字段 | v0 决定 | 理由 |
|---|---|---|
| `test_case_id` | 进入 Schema，必填 | Test Case first-class identity；支持 freeze、coverage 和 Episode reference |
| `name` | 不进入 | `test_case_id` 提供 identity，`task` 提供可读场景；额外 name 当前没有独立 Framework 行为 |
| `purpose` | 留在 Audit | 解释设计意图，但不影响 Subject 接收的 frozen scenario |
| `contract_ids` | 不作为 top-level 字段 | 由 `expected_assertions[].contract_id` 派生，避免双重 authority 漂移 |
| `task` / `user_input` | 使用 `task` 进入 Schema，必填 | 统一表达 natural user request / evaluation task，不保留两个重叠字段 |
| `preconditions` | 进入 Schema，必填列表 | 明确环境可执行条件；允许显式空列表 |
| `fixtures` | 进入 Schema，必填列表 | 声明 Case 需要的 simple input resources；允许显式空列表；不创建 Fixture Core Object |
| `initial_state` | 进入 Schema，必填列表 | 描述 evaluator 建立的 scenario state；允许显式空列表 |
| `interaction_steps` | 进入 Schema，必填列表 | 表达真实 validation 已证明需要的 conditional evaluator continuation；空列表表示 static / single-turn Case |
| `expected_assertions` | 进入 Schema，至少一项 | 保存 Contract-specific semantic evaluation target，并承担 authoritative Contract reference |
| `targeted_failure_modes` | 留在 Coverage Mapping / Audit | 是 risk coverage rationale，不是执行 scenario 的最小 authority |
| `case_type` | 不进入 | positive / negative / edge 可重叠；冻结单一 enum 会制造机械配额和错误分类 |
| `repeat_count` | 不进入 | 重复执行政策尚未设计；实际 attempts 属于 Episode |
| Evidence references | 不进入本轮 Proposal | Evidence Specification 尚未设计，不提前占位 |
| Grader references | 不进入本轮 Proposal | Grader Specification 尚未设计，不提前占位 |
| actual result fields | 禁止进入 | 属于 Episode / Evidence / Result |

### 26.5 ID 规则

推荐形式：

```text
TC001
TC002
TC003
```

规则：

- 在一个 Benchmark Definition 中唯一；
- 使用 `TC` 加至少三位十进制数字；
- 不要求跨所有 Benchmarks 全局唯一；
- 同一 scenario intent 只做非语义澄清时可保持 ID；
- task、initial state、targeted Contracts 或 semantic expectation 发生重大变化时，应创建新 ID；
- 被删除的 ID 不应在同一 Benchmark lineage 中复用于不同 scenario。

跨版本 ID 延续需要 Definition history context，不能由单文件局部 Schema 确定。

---

## 27. Schema Field Semantics

### 27.1 task

非空 string，表达 Subject 实际收到的 initial natural user / task input。它应包含足够 scope 与初始上下文，但不泄漏 hidden evaluation logic，也不预写 future interaction transcript。

### 27.2 preconditions

必填 `list[str]`，允许空列表。每项说明 Case 有效执行所需的 environment condition。不得描述 actual runtime status，也不得替 Subject 完成 Workflow responsibility。

### 27.3 fixtures

必填 `list[str]`，允许空列表。每项描述或引用 simple fixture。它不规定 fixture provisioning command、storage path、capture implementation 或 Runtime identity。

如果未来复杂 reusable fixtures 需要稳定 identity、版本和多 Case reuse，另行提出 Schema finding；v0 不提前创建 Fixture object。

### 27.4 initial_state

必填 `list[str]`，允许空列表。每项描述 Case 开始时 evaluator 构造的 relevant state。它必须与 preconditions 区分：precondition 是环境必须成立的条件，initial state 是 scenario 具体起点。

### 27.5 interaction_steps

必填 `list[InteractionStep]`，允许空列表。

每个 `InteractionStep` 必须包含：

- 非空 `trigger`：human-readable semantic condition，说明何时提供 continuation；
- 非空 `response`：trigger 满足后作为下一轮 Subject-visible user interaction 提供的内容。

List order 表达多个 definition-time continuation policies 的声明顺序，不定义 Runtime scheduler、branching graph、retry、timeout 或 trigger-matching algorithm。需要 arbitrary branching、tool callback 或 state machine 的未来 Case 必须另行提供真实 validation evidence；v0 不提前设计。

### 27.6 expected_assertions

必填且至少一项。每个 Contract 最多出现一次。它表达 Case-level semantic expectation，不是 Grader implementation。

Target Contract set 由 expected assertions 派生；任何 assertion reference 都必须解析到当前 validated Contract Set。

---

## 28. Three-layer Test Case Validation

### 28.1 A. Structural / Field Validation

未来可 deterministic 检查：

- `test_case_id` 符合 `TC` + 至少三位数字；
- Test Case IDs 在 Definition 中唯一；
- `task` 去除首尾空白后非空；
- `preconditions` 是无完全重复、条目非空的字符串列表；
- `fixtures` 是无完全重复、条目非空的字符串列表；
- `initial_state` 是无完全重复、条目非空的字符串列表；
- `interaction_steps` 是列表，允许为空；
- 每个 InteractionStep 包含非空 `trigger` 与 `response`；
- InteractionStep 不包含 actual Subject turn、trigger result、PASS / FAIL、Evidence 或 Runtime event fields；
- `expected_assertions` 至少一项；
- 每项 ExpectedAssertion 包含非空 `contract_id` 与 `expectation`；
- 同一个 Test Case 中 ExpectedAssertion `contract_id` 不重复；
- 不存在 actual response、trace、Artifact、Evidence 或 Result 字段。

空 `preconditions`、`fixtures`、`initial_state` 或 `interaction_steps` 列表是合法的显式声明，不等于字段缺失。空 `interaction_steps` 明确表示 static / single-turn Case。

### 28.2 B. Cross-object Validation

需要完整 Definition context：

- 每个 ExpectedAssertion `contract_id` 都存在；
- referenced Contract 已 validated 且属于当前 Definition；
- 不引用 invalid、draft-only、stale 或其他 Benchmark 的 Contract；
- Coverage Mapping 中 Test Case IDs 与 Expected Assertions 双向一致；
- 每个 Contract 在 Mapping 中恰好一行；
- 每个 Test Case 至少 target 一个 Contract；
- 没有 dangling Test Case / Contract refs；
- production Test Cases 不引用 validation-subset-only Contract；
- Requirement → Contract → Test Case trace 可恢复。

Cross-object validator 可以证明 references 与 mapping 一致，不能证明 scenario 真的 exercise Contract。

### 28.3 C. Semantic Test Case Review

逐 Case 至少检查：

- Case 是否真正 exercise 每个 target Contract；
- task 是否自然、充分且不泄漏 hidden logic；
- 是否 over-instructed；
- 是否 under-specified；
- Failure-mode coverage 是否合理；
- granularity 是否兼顾 diagnosis 与 coverage efficiency；
- discriminative power 是否足够；
- fixture / precondition 是否替 Subject 完成 Workflow responsibility；
- setup-field visibility 与 hidden setup dependency 是否明确；
- precondition / fixture / initial state 是否遵守 canonical placement，且没有复制同一完整事实；
- conditional trigger 是否真实构造；
- interaction trigger 是否 semantic，response 是否只在 trigger 后提供；
- interaction 是否保留完整 compliant path 与现实 violating path；
- future response 是否没有被预置到 task、fixture 或 initial state；
- 是否存在 trivial pass；
- 多 Contract mappings 是否仍可解释；
- Expected Assertions 是否 semantic 且忠实；
- 是否提前写 Evidence / Grader；
- 是否与其他 Cases 重复；
- critical Contract risk review 是否充分；
- Case independence 与 repeatability 是否合理。

Method Validation Subset 还必须执行 Out-of-Subset Responsibility Exposure Review，并确认 Case 没有被误报为完整 production-valid Test Case。

Semantic Review 需要 Agent / Human judgment，不能伪装成 Schema validation。

---

## 29. Test Case Design Issues 与 Rollback

至少区分：

- Contract 无法构造有效 exercise scenario；
- scenario ambiguity；
- under-specification / over-instruction；
- granularity issue；
- discriminative-power insufficiency；
- fixture / precondition substitution；
- conditional trigger gap；
- coverage gap；
- redundancy；
- environment / cost limitation；
- downstream Evidence Design Concern；
- downstream Grader Design Concern。

Rollback：

```text
Requirement semantic problem
→ Requirement lifecycle

Contract success/failure/applicability problem
→ Contract Design lifecycle

Scenario、trigger、fixture、prompt、granularity problem
→ Test Case Design 内修订

缺少可判断该 Case 的观察类型
→ Downstream Evidence Design Concern

不清楚如何判断已有 observations
→ Downstream Grader Design Concern
```

不得为方便 Case、Evidence 或 Grader 而降低 / 加强 Contract semantics。

Downstream concern 不自动使 Test Case failure；只有它证明 scenario 本身无法 meaningful exercise 或无法形成 semantic expectation 时，才阻塞 Case Design。

---

## 30. Test Case Design Workflow

### Step 1 — Verify Inputs

- 验证 Frozen Requirements、validated Contracts、mapping 与 status；
- production input 不满足 Entry Gate 时立即 BLOCK；
- method validation subset 必须保留限定边界。

### Step 2 — Build Contract Risk Inventory

- 读取 statement、evaluation_type、criteria、failure modes、criticality；
- 识别 applicability / trigger；
- 不重新设计 Contract。

### Step 3 — Draft Scenarios

- 为 Contracts 构造 natural task situations；
- 选择必要 initial state、fixtures 和 preconditions；
- 如果 Case 需要 conditional evaluator continuation，设计最小 interaction steps；
- 使用 Working Case Drafts 比较 alternate scenarios；
- 标记 positive / negative / edge design intent。

### Step 4 — Run Exercise Check

- 对每个 Case → Contract mapping 检查 trigger、agency、non-substitution 和 non-determinism；
- 对 interaction Case 检查 response timing、compliant continuation 与 violating path；
- 只会 NOT_EXERCISED 的 mapping 不算 coverage。

### Step 5 — Review Granularity and Discrimination

- 决定 1→N 或 N→1 Case mapping；
- 拆分 super Case；
- 合并无新增价值的 duplicates；
- 阻止 trivial pass、over-instruction 与 ambiguity。

### Step 6 — Write Test Cases

- 分配正式 `TCxxx`；
- 写 task、preconditions、fixtures、initial state；
- 写必填 `interaction_steps`；静态 Case 使用显式空列表；
- 为每个 target Contract 写一项 semantic Expected Assertion；
- 不写 Evidence / Grader implementation。

### Step 7 — Build Coverage and Audit

- 每个 Contract 建立 Coverage row；
- 记录 targeted failure modes 与 exercise rationale；
- Method Validation Subset 记录 out-of-subset responsibility exposure；
- 对 critical Contract 执行加强 review；
- 保留 redundancy 与 uncovered risk decisions。

### Step 8 — Validate

- Structural / Field Validation；
- Cross-object Validation；
- Semantic Test Case Review；
- unresolved issue 必须进入 Issues。

### Step 9 — Determine Status

- 所有 Contracts 获得有效 semantic exercise coverage 且 validation 通过时 READY；
- 任一 required Contract BLOCKED 时整体 BLOCKED；
- 生成必需 outputs 并停止，不进入 Evidence 或 Grader Design。

---

## 31. Test Case Design Status

Production 状态只保留：

```text
TEST_CASES_READY
TEST_CASES_BLOCKED
```

### 31.1 TEST_CASES_READY

只有同时满足以下条件：

- authoritative Frozen Requirements 与 validated Contracts 当前有效；
- Contract Design 为 `CONTRACTS_READY`；
- 每个 Contract 都有真实 semantic exercise coverage；
- critical Contracts 已完成更严格 risk review；
- major failure modes 有合理 coverage 或非阻塞 rationale；
- 所有 Test Cases 通过三层 validation；
- Coverage Mapping、Test Case Set 与 Audit 一致；
- 没有 unresolved Case Design Issue；
- 没有提前设计 Evidence、Grader、Metric 或 Gate。

### 31.2 TEST_CASES_BLOCKED

例如：

- Contract 无法设计有效 Case；
- target responsibility 无法真实 exercise；
- coverage gap；
- scenario ambiguity；
- fixture / precondition 与 Requirement 或 Contract 冲突；
- evaluator setup 替 Subject 完成责任；
- discriminative power 不足；
- unresolved granularity issue；
- critical Contract risk surface 明显遗漏；
- Test Case validation failure。

状态不是 quality score：

```text
99% Contracts COVERED + 1 blocking gap
= TEST_CASES_BLOCKED
```

Method Validation Subset 使用 4.3 节的限定 status wording，不改变 production status model。

---

## 32. Required Outputs

Test Case Design 至少产生：

1. **Test Case Set**：使用 Proposed TestCase Schema 的正式 Definition-time Cases；
2. **Contract ↔ Test Case Coverage Mapping**：逐 Contract 的 semantic coverage；
3. **Test Case Design Audit**：purpose、risk、exercise、granularity、discrimination 与 redundancy rationale；
4. **Test Case Design Issues**：blocking issues 与 downstream concerns；
5. **Test Case Validation Summary**：Structural、Cross-object、Semantic 三层结果；
6. **Test Case Design Status**：`TEST_CASES_READY` 或 `TEST_CASES_BLOCKED`；
7. **Schema Design Findings**：仅记录真实设计暴露的 schema need，不因未来可能有用而加字段。

Working Case Drafts 不是必需 final output，也不算 Coverage。

---

## 33. Evidence / Grader Boundary

Test Case 可以说明：

> 需要构造某种状态，使目标责任能够被满足或违反。

它不能定义：

- Evidence path；
- trace schema；
- screenshot / log location；
- Artifact capture implementation；
- log fields；
- exact event index；
- regex；
- JSONPath；
- code assertion；
- comparison algorithm；
- threshold；
- score；
- evaluator / judge prompt。

如果发现没有某类 observation 就永远无法判断 Contract，应记录：

```text
Downstream Evidence Design Concern
```

如果 observations 原则上存在，但尚不清楚如何判断，应记录：

```text
Downstream Grader Design Concern
```

都不得通过把 implementation 塞入 Expected Assertion 来解决。

---

## 34. Schema Design Findings

### 34.1 ExpectedAssertion

本轮建议 ExpectedAssertion 成为 TestCase nested structure，而不是 Core Object。理由：

- multi-Contract Case 需要 Contract-specific semantic target；
- 只保留 top-level `contract_ids` 无法说明每个 Contract 在该 Case 中期待什么；
- 它可以作为后续 Evidence / Grader Design 输入；
- 两字段结构足够，不需要 assertion ID 或 implementation fields。

真实 validation 已确认不同 Outcome / Workflow / conditional Cases 能用 `contract_id + expectation` 清楚表达。Conditional expectation 需要同时写 trigger context 与 required responsibility，但不需要增加字段或允许同一 Contract 重复 assertions。

### 34.2 Fixture representation

v0 使用 `fixtures: list[str]` 表达 simple prepared resource description / reference，不创建 Fixture Core Object。真实 validation 证明 static Case 可以继续使用该形式；future user response 不属于 Fixture，必须使用 `interaction_steps`。只有未来真实设计证明复杂 reusable fixture 需要 stable identity、version、ownership 和 multi-Case reference 时，才考虑独立定义资源。

### 34.3 No top-level contract_ids

Contract relation 只保存在 `expected_assertions[].contract_id`，避免 top-level `contract_ids` 与 assertions 漂移。真实 validation 已确认该派生关系足够支持当前 multi-Contract authoring 与 Coverage Mapping，没有理由增加 top-level `contract_ids`。

### 34.4 No case_type enum

Positive / negative / edge 是可重叠的 Design classifications，不进入 Frozen Schema。当前没有证据证明单一 enum 能驱动必要 Framework behavior。

### 34.5 No runtime status fields

BLOCKED Episode、NOT_EXERCISED、actual PASS / FAIL、retry 和 execution state 都属于 Runtime / Result，不进入 TestCase Schema。

### 34.6 InteractionStep

真实 validation 证明 static schema 无法正确表达“Subject 先触发 interaction，Evaluator 再提供下一轮 user response”的 Case。v0 因此增加最小 nested structure：

```text
InteractionStep:
- trigger
- response
```

它只定义 conditional continuation policy，不成为 Interaction Core Object，不保存 actual transcript，也不引入 workflow graph、branching DSL、state machine、callback、retry policy、timing engine 或 Runtime trigger matcher。

---

## 35. Method Self-Review

| 检查问题 | v0 结论 |
|---|---|
| 1. Contract 与 Test Case 边界是否清楚？ | 是。Contract 定义满足 / 违反语义；Test Case 只构造 concrete exercise scenario。 |
| 2. Test Case 与 Evidence 边界是否清楚？ | 是。Case 构造状态和 semantic target，不规定 observations 的 capture path、format 或 implementation。 |
| 3. Test Case 与 Grader 边界是否清楚？ | 是。Expected Assertion 保持 semantic level，不包含 checker、regex、JSONPath、threshold 或 judge prompt。 |
| 4. Exercise Check 是否可执行？ | 是。它明确检查 trigger、agency、substitution、NOT_EXERCISED、predetermination 与 Contract-specific expectation。 |
| 5. Contract coverage 是否不仅是 ID coverage？ | 是。COVERED 必须通过 Exercise Check、discriminative-power review 和 Case validation。 |
| 6. Positive / negative / edge 是否避免机械配额？ | 是。它们是 Audit 中的可重叠 classification，不进入 Frozen enum。 |
| 7. Failure-mode coverage 是否避免组合爆炸？ | 是。Failure modes 是 risk input，不是一对一 Case queue；允许合并相同 risk surface。 |
| 8. Case granularity 是否兼顾 coverage 与 diagnosis？ | 是。使用 Diagnostic Value + Coverage Efficiency，并检查 cascade blocking 与 failure attribution。 |
| 9. Discriminative Power 是否有明确规则？ | 是。检查 target exposure、trivial pass、behavior alternatives、coaching、ambiguity 与 predetermined outcome。 |
| 10. Fixture 与 Workflow Requirement 是否能区分？ | 是。Precondition Substitution Rule 禁止 evaluator 替 Subject 完成 required action。 |
| 11. Conditional Contract 是否能真正被 exercised？ | 是。Coverage 至少需要一个真实 trigger Case；没有 trigger 不算 coverage。 |
| 12. NOT_EXERCISED 是否不会被误当 PASS？ | 是。正文明确其既不是 PASS，也不是 semantic coverage。 |
| 13. Test Case / Episode 边界是否清晰？ | 是。Definition 不保存任何 actual attempt、Artifact、Evidence、Trace 或 Result。 |
| 14. Case execution failure 是否不会误算 Contract failure？ | 是。Fixture、service、infrastructure 和 trigger absence 被明确分离。 |
| 15. 是否需要 Test Case Candidate？ | 当前不需要 mandatory Candidate；Working Case Drafts 足够，需真实复杂 authoring 再验证。 |
| 16. 是否需要 Test Case Design Audit？ | 需要轻量非 Core Audit，因为 purpose、risk、exercise、granularity 和 redundancy rationale 不应塞入最小 Schema。 |
| 17. 当前 Test Case Schema 最小字段是什么？ | `test_case_id`、`task`、`preconditions`、`fixtures`、`initial_state`、`interaction_steps`、`expected_assertions`，以及 nested InteractionStep 与 ExpectedAssertion。 |
| 18. 哪些字段不应该进入 Frozen Schema？ | name、purpose、top-level contract_ids、targeted_failure_modes、case_type、repeat_count、Evidence / Grader refs 和 actual result fields。 |
| 19. 是否出现 target-specific assumption？ | 未发现。方法适用于文本、交互、工具、Artifact、状态与 workflow 型 Agent Skills。 |
| 20. 真实 validation 暴露了什么？ | Static fields、ExpectedAssertion 与单一 Contract authority 可用；multi-turn continuation 需要 InteractionStep；setup visibility、canonical placement、subset exposure 与 discriminative reviewer consistency 需要 hardening。 |

### 35.1 Self-review corrections incorporated

本轮自审已经在正文中处理：

- 为避免 ID linkage 假覆盖，增加 Contract Exercise Check；
- 为避免 evaluator 偷做 Workflow responsibility，增加 Precondition Substitution Rule；
- 为避免 positive / negative / edge 机械配额，不把它们冻结为 enum；
- 为避免 Contract references 双重 authority，由 ExpectedAssertions 承担引用；
- 为避免 Test Case 与 Episode 混合，明确禁止 actual runtime fields；
- 为避免 Expected Assertion 滑向 Grader，限制为两字段 semantic structure；
- 为避免 Case explosion，加入 Failure-Mode Coverage 与 Redundancy Review；
- 为避免 criticality 机械增加 Case 数，改用加强 risk review；
- 为避免 minimal Schema 承担全部设计审计，引入非 Core Audit。
- 为避免 future user response 被错误预置，增加最小 InteractionStep 与 trigger-gated response semantics；
- 为避免 setup visibility 依赖 reviewer 猜测，明确 Subject-visible 与 evaluator-side fields；
- 为避免 precondition / fixture / initial state 重复，增加 canonical placement；
- 为避免 subset Case 被误报为完整 production Case，增加 Out-of-Subset Responsibility Exposure Review。

### 35.2 Further Method Validation Coverage Needed

本轮 real validation 已覆盖 simple Outcome、Workflow、conditional、authorization / scope edge、multi-Contract、1→N、substitution risk、low-discrimination、failure-mode grouping、ExpectedAssertion 与 static setup-field boundaries，并真实发现 multi-turn continuation blocker。

Hardening 后仍需要新的 validation run 检查：

- 原 blocking Case 是否能用 `interaction_steps` 完整表达 compliant 与 violating paths；
- 不同 reviewer 是否能一致写出 semantic trigger，而不会滑向 executable matcher；
- Subject visibility 与 Hidden Setup Dependency Rule 是否能稳定消除 precondition substitution ambiguity；
- Canonical Placement Rule 是否能降低 precondition / fixture / initial state 重复；
- Out-of-Subset Responsibility Exposure Review 是否能阻止 validation-local Case 被误报为 production-valid Case；
- 不同 Agent Skill classes 中，最小两字段 InteractionStep 是否仍然足够。

这些是 future validation coverage，不是本轮已执行结果，也不应被误报为 Runtime implementation 或 Test Case execution PASS。

### 35.3 Hardening Self-Review

| 检查 | 结论 |
|---|---|
| 1. Multi-turn compliant path 是否能定义？ | 是。Subject 满足 semantic trigger 后，evaluator 才提供 response，Case 可继续。 |
| 2. Violating path 是否不会自动收到 response？ | 是。Trigger 不满足时禁止注入 response。 |
| 3. Interaction 是否仍属于 Definition-time？ | 是。只保存 policy，不保存 actual turn、trigger result 或 transcript。 |
| 4. Trigger 是否保持 semantic？ | 是。禁止 regex、trace index、checker、callback 或 executable matcher。 |
| 5. Subject visibility 是否明确？ | 是。task 与 triggered response 可见；setup descriptions 默认不直接 prompt-visible。 |
| 6. Setup 是否不会替 Subject 做 Workflow responsibility？ | 是。Future confirmation 不得进入 initial state 或 fixture。 |
| 7. Preconditions / fixtures / initial state 是否有稳定 placement？ | 是。分别按 readiness、prepared resource、scenario-start state 归位。 |
| 8. Conditional ExpectedAssertion 是否更清晰？ | 是。必须包含 trigger context 与 required responsibility，不能只写 should be exercised / pass。 |
| 9. 是否保持单一 Contract relation authority？ | 是。仍只使用 `expected_assertions[].contract_id`。 |
| 10. Subset exposure review 是否只影响 method validation？ | 是。它是 validation working artifact，不修改 production TestCase Schema。 |
| 11. 是否新增不必要 Core Object？ | 否。InteractionStep 与 ExpectedAssertion 都是 nested structures。 |
| 12. 是否提前设计 Evidence / Grader？ | 否。没有定义 trigger matcher、capture、checker、judge 或 Runtime engine。 |
| 13. Schema Proposal 是否仍然最小？ | 是。只增加真实 blocking finding 所需的两字段 InteractionStep 与列表。 |
| 14. 是否存在 target-specific assumptions？ | 否。正文没有特定 Skill、平台、工具、目录或命令。 |

---

## 36. Final Decision Checklist

### Inputs

- [ ] Production input 使用 authoritative Frozen Requirements 与 validated Contracts
- [ ] Contract Design Status 为 `CONTRACTS_READY`
- [ ] Inputs 没有 stale 或 unresolved semantic issue
- [ ] Method validation subset 保留 validation-only 边界与限定 status
- [ ] Method validation subset 已完成 Out-of-Subset Responsibility Exposure Review

### Exercise and Coverage

- [ ] 每个 Case → Contract mapping 都通过 Exercise Check
- [ ] Conditional trigger 已实际构造
- [ ] NOT_EXERCISED 没有被当作 PASS coverage
- [ ] Coverage 不只是 ID linkage
- [ ] Critical Contract 完成加强 risk review
- [ ] Major failure modes 有合理 coverage 或明确 issue

### Scenario Quality

- [ ] Task natural、sufficient、contract-faithful
- [ ] 没有 over-instruction 或 hidden logic leakage
- [ ] 没有 unresolved under-specification
- [ ] Discriminative power 足够
- [ ] 没有 trivial pass
- [ ] Initial state 没有预先锁死结果
- [ ] 需要 continuation 的 Case 定义了完整 compliant path 与现实 violating path
- [ ] Interaction response 只在 semantic trigger 满足后提供

### Fixture and Preconditions

- [ ] Preconditions 只描述 environment readiness
- [ ] Evaluator setup 没有替 Subject 完成 Workflow responsibility
- [ ] Setup-field visibility 与 hidden setup dependency 已明确
- [ ] Fixture / initial state 可理解且原则上可重复
- [ ] Preconditions / fixtures / initial state 遵守 canonical placement
- [ ] Case semantics 不依赖其他 Case 的 runtime outcome

### Granularity and Redundancy

- [ ] Multi-Contract Case 仍能 Contract-specific explanation
- [ ] 前序 failure 不会静默阻断后续 Contracts
- [ ] 没有 Maximum Isolation / Maximum Integration
- [ ] Duplicate Cases 已 review

### Definition Boundaries

- [ ] Expected Assertions 只包含 Contract-level semantic expectations
- [ ] Conditional expectation 同时表达 trigger context 与 required responsibility
- [ ] InteractionStep 只包含 semantic trigger 与 future user response policy
- [ ] 没有 Evidence path、trace schema 或 capture implementation
- [ ] 没有 Grader algorithm、regex、JSONPath、threshold 或 judge prompt
- [ ] 没有 actual Episode、Artifact、Evidence 或 Result data
- [ ] 没有 Metric、Weight、Score 或 Gate

### Validation and Status

- [ ] Structural / Field Validation 完成
- [ ] Cross-object Validation 完成
- [ ] Semantic Test Case Review 完成
- [ ] Test Case Set、Coverage Mapping 与 Audit 一致
- [ ] 无 unresolved Case Design Issue
- [ ] Production status 只使用 `TEST_CASES_READY` 或 `TEST_CASES_BLOCKED`

全部必需检查通过时，production Test Case Design 才能输出：

```text
TEST_CASES_READY
```

否则输出：

```text
TEST_CASES_BLOCKED
```

并停止在 Test Case Design 边界，不开始 Evidence、Grader、Metric、Gate 或 Runtime implementation。
