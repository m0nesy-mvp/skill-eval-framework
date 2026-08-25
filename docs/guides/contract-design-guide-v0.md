# 《Contract Design Guide v0》

Status: Design Guide

本文定义从 authoritative `Frozen Requirement Set` 到 validated `Contract Set` 的通用设计方法。它适用于通用 Agent Skill Eval，不绑定特定 Skill、平台、工具、接口、Artifact 类型或业务领域。

本文细化《通用 Skill Eval Design Process v1.1（Scope-Frozen）》中的 Contract Design 阶段，并遵守《Agent Skill Benchmark Concept Model v0.1》和《Benchmark Definition → Requirement → Contract Schema Design v0》的冻结边界。本文不修改 Frozen Requirement Schema 或 Frozen Contract Schema。

---

## 1. Contract 的角色

Requirement 回答：

> What is required?

Contract 回答：

> What counts as satisfying or violating that requirement for evaluation purposes?

Contract 是 Requirement 与后续 Test / Evidence / Grader machinery 之间的 **evaluation-semantics layer**：

```text
Frozen Requirement
        ↓
Contract
        ↓
Test Case / Evidence / Grader machinery
```

它把已冻结的规范责任转化为人类可理解、可被后续评价设计 operationalize 的 verification commitment，但不选择具体的 operationalization 方法。

Contract 是：

- 对一个或多个 Frozen Requirements 的忠实评价语义表达；
- 对成功、违反和有诊断价值的失败形态的边界说明；
- Requirement-level traceability 与后续 Eval machinery 之间的连接点；
- Outcome Eval 或 Workflow Compliance Eval 中的同一类核心对象。

Contract 不是：

- 新产品需求；
- Requirement 的改写或补丁；
- Test Case、用户场景或 Fixture；
- Evidence 或 Evidence encoding；
- Grader、Metric、Gate 或 score weight；
- executable checker、regex、JSONPath、assertion 或 judge prompt；
- 对 Target 实际表现的 PASS / FAIL 结果。

核心不变量是：

> Contract 不得创造 Frozen Requirement 中没有的 normative responsibility，也不得削弱、加强或替换原责任。

---

## 2. 为什么 Requirement 不能直接进入 Test / Grader

一条 Frozen Requirement 即使来源可靠、语义正确，通常仍只说明“必须做什么”或“必须得到什么”，未必已经明确“评价时共同承诺什么”。如果直接从 Requirement 跳到 Test 或 Grader，设计者容易把某个测试输入、某种日志格式或某段 checker 代码误当成 Requirement 本身。

Contract 在中间显式解决以下问题：

- evaluation responsibility 的边界在哪里；
- 什么 observable semantic condition 足以说明责任被满足；
- 什么 observable semantic condition 构成真正的违反；
- 哪些常见 violation forms 值得区分和覆盖；
- 一个 Requirement 是否包含多个独立 verification commitments；
- 多个 Requirements 是否共同构成一个不可自然分开的 verification commitment；
- 评价结果能否回溯并解释到 Requirement level。

Contract 在本阶段不解决：

- 使用什么具体测试输入；
- 构造什么用户场景或 Fixture；
- Evidence 存成 JSON、日志、截图还是其他 encoding；
- Tool Trace 的字段和路径；
- 使用 regex、threshold、validator、LLM judge 还是人工审查；
- 如何聚合 Metric、分配 Weight 或设置 Gate。

因此，Contract 的“可验证”表示语义上存在可评价的满足与违反边界，不表示本阶段已经实现自动 checker。

---

## 3. Authoritative Input 与进入条件

### 3.1 必需输入

Contract Design 至少需要：

1. authoritative、完整且当前有效的 `Frozen Requirement Set`；
2. 每条 Requirement 的 `requirement_id`；
3. 每条 Requirement 的 `statement`；
4. 每条 Requirement 的 `evaluation_type`；
5. 需要理解语义时可访问的 authoritative provenance 和 Requirement Extraction audit context；
6. Requirement Finalization 已解决所有阻止完整冻结的 known unresolved issues。

Frozen Requirement Schema 保持：

```text
Requirement:
- requirement_id
- statement
- source
- source_ref
- evaluation_type
```

`RC`、`NR`、`TI`、Trace Matrix、Finalization Mapping 和 Extraction Issue Ledger 可以作为审计与理解上下文，但不能替代 Frozen Requirement，也不能作为正式 `Contract.requirement_ids` 的引用目标。

### 3.2 Entry Gate

开始设计前必须确认：

- Requirement Finalization Status 为 `FINALIZATION_READY`；
- 输入明确标识为 authoritative Frozen Requirement Set；
- 所有 Requirement IDs 唯一且稳定；
- `statement`、`source`、`source_ref` 和 `evaluation_type` 已完成 Finalization；
- 输入没有因上游 source、NR、trace 或 mapping 变化而 stale；
- 不存在被隐藏或“稍后再解决”的 unresolved Requirement。

任一条件不满足时：

```text
Contract Design Status = CONTRACTS_BLOCKED
```

此时可以记录阻塞原因和影响，但不得：

- 从 RC / NR 直接生成正式 Contract；
- 把 partial Frozen Requirements 声称为完整输入；
- 在 Contract 中猜测缺失的 Requirement；
- 用 Contract wording 暗中解决上游冲突；
- 宣称 Contract coverage 已完成。

---

## 4. Frozen Contract Schema 与设计边界

Contract Design 只填充已经冻结的 Contract Schema：

```text
Contract:
- contract_id
- requirement_ids: list[str]
- statement
- evaluation_type
- criticality
- success_criteria: list[str]
- failure_criteria: list[str]
- failure_modes: list[str]
```

冻结不变量：

- Requirement ↔ Contract 是 many-to-many；
- `requirement_ids` 只在 Contract 一侧维护，是 authoritative relation；
- Contract 的 `evaluation_type` 必须与全部 referenced Requirements 对齐；
- 一个 Contract 不得混合 `outcome` 与 `workflow` responsibility；
- mixed responsibility 必须拆分或回滚检查 Requirement decomposition；
- `criticality` 不等于 Gate，也不等于 weight；
- success / failure criteria 是 semantic evaluation criteria；
- failure modes 是有诊断价值的失败形态；
- 除非某项本身是 Requirement 明确规定的规范语义，Contract 不写 threshold、regex、checker 或 grading algorithm；
- Contract Design 不得修改 Frozen Requirement。

---

## 5. Requirement Granularity 与 Contract Granularity

Requirement granularity 与 Contract granularity 不相同：

```text
Requirement granularity
= normative responsibility decomposition

Contract granularity
= evaluation commitment decomposition
```

Requirement 拆分关注的是规范责任是否独立。Contract 拆分关注的是评价承诺是否具有独立、清晰且有诊断价值的满足与违反意义。

因此合法关系包括：

```text
1 Requirement  → 1 Contract
1 Requirement  → N Contracts
N Requirements → 1 Contract
N Requirements ↔ N Contracts
```

many-to-many 是 Framework 必须支持的关系，不是鼓励尽可能合并或拆分的目标。

---

## 6. Contract Atomicity：Atomic Verification Commitment Test

一个 Contract 应尽量表达一个具有清晰 evaluation meaning 的 **atomic verification commitment**。

设计者对拟定 Contract 依次检查：

1. 是否能够用一句 statement 说明一个连贯的评价承诺？
2. success criteria 是否共同描述同一承诺被满足，而不是多个互不依赖的成功？
3. failure criteria 是否共同描述同一责任被违反，而不是多个可独立发生的不同责任？
4. 如果其中 A 成功、B 失败，是否仍能对整个 Contract 给出不失真的解释？
5. A 与 B 的 failure class、remediation、所需 Evidence 或后续诊断是否显著不同？
6. 分开后是否明显提高评价结果的 diagnostic value 和 Requirement-level explainability？
7. 合在一起是否会隐藏独立失败或产生含糊的部分成功？

如果 A 可以成功、B 可以失败，且二者具有不同 failure class、remediation、Evidence need 或诊断意义，通常应拆分。

但“可以单独观察”不是充分拆分理由。以下内容不得自动各自产生 Contract：

- 每个 schema field；
- 每个 metadata field；
- 每个 Artifact package member；
- 每个 checklist micro-item；
- statement 中的每个逗号、动词或名词；
- 同一语义承诺的实现细节。

最终目标是：

```text
Diagnostic Value
而不是
Maximum Fragmentation
```

---

## 7. 一个 Requirement 何时拆成多个 Contracts

当一条 Requirement 支持多个独立 verification commitments 时，可以建立多个 Contracts。至少需要评估：

- 各 commitment 是否可能独立满足或违反；
- 是否存在不同的 violation classes；
- 是否需要不同类别的 Evidence 才能合理判断；
- remediation 或 root-cause interpretation 是否不同；
- 后续报告是否需要分别说明结果；
- 分开是否明显提高 Case coverage 设计和诊断价值；
- 每个拆分后的 Contract 是否仍由该 Requirement 的原始语义完整支持。

拆分判断可表示为：

```text
同一 Frozen Requirement
    ├── Verification Commitment A → Contract A
    └── Verification Commitment B → Contract B
```

不得仅因为 Requirement：

- 有多个字段；
- 有多个逗号；
- 使用了“并且”；
- 包含多个动词；
- 可以写出多个测试；

就机械拆分。

一个 Contract 需要多个 Test Cases 或多种 Evidence，不等于它必须被拆成多个 Contracts。Case 和 Evidence 的多样性属于后续设计。

---

## 8. 多个 Requirements 何时合入一个 Contract

多个 Requirements 只有同时满足以下条件时，才可以共同进入一个 Contract：

1. `evaluation_type` 完全一致；
2. 它们共同形成同一个 coherent evaluation commitment；
3. success / failure 语义天然需要共同判定；
4. 分开会制造重复或失真的评价承诺，而不是增加诊断价值；
5. 合并不会隐藏任何可独立发生且值得单独报告的失败；
6. 合并后仍能清楚解释每条 Requirement 如何被覆盖；
7. `statement` 和全部 criteria 都有被引用 Requirements 的联合 normative support；
8. 后续 Contract-specific 结果仍能合理说明哪些 Requirements 得到覆盖。

禁止为了减少 Contract 数量而强行合并。以下情况通常不应合并：

- Requirements 只是主题相近；
- 它们会出现在同一个 Test Case；
- 它们可能使用同一份 Evidence；
- 它们使用相似文字；
- 设计者希望让 Coverage Matrix 更短。

多 Requirement Contract 的每一部分语义都必须能回到至少一个 referenced Requirement；联合表达不能产生任何单条或联合来源都不支持的新责任。

---

## 9. Granularity Decision Procedure

对每条 Frozen Requirement 执行以下过程：

```text
读取 Requirement 及必要 audit context
        ↓
列出最小、来源支持的 verification commitments
        ↓
执行 Atomic Verification Commitment Test
        ↓
检查是否需要 1→N split
        ↓
与相同 evaluation_type 的其他 Requirements 比较
        ↓
仅在形成同一 commitment 时执行 N→1 merge
        ↓
写入 Contract + Coverage Mapping + Audit rationale
```

每个 split / merge 都必须有语义理由。默认选择不是“永不合并”或“尽量合并”，而是选择最能保持 fidelity、traceability 和 diagnostic value 的边界。

---

## 10. Contract Statement

### 10.1 职责

`statement` 表达 Contract 的 evaluation commitment。它应当：

- 忠实于全部 referenced Requirements；
- 比 Requirement 更适合用于评价判断；
- 明确责任被 exercised 时需要成立的语义；
- 保持 outcome / workflow 类型边界；
- 能与 success / failure criteria 形成一致的整体；
- 不重复写 Test Case；
- 不包含具体 implementation checker；
- 不添加、降低或加强 normative responsibility。

### 10.2 允许的澄清

Contract 可以把 Requirement 已经蕴含、但为了评价需要显式说清的关系表达出来，例如：

- 时间顺序；
- 责任适用范围；
- 对象与动作之间的关系；
- “有效”所指向的、已被来源支持的语义；
- 多条 Requirements 共同形成的 commitment。

抽象例子：

```text
Requirement:
执行 destructive action 前必须取得用户授权。

Contract statement:
任何适用的 destructive action 必须由在该 action 之前获得、
且 scope 覆盖目标操作的有效用户授权支持。
```

这里把“前”“授权”和目标操作之间的评价关系说清楚，但没有指定 prompt、日志字段、trace assertion 或 checker。

### 10.3 禁止的改写

Contract statement 不得：

- 把“应当”升级成来源不支持的“必须”；
- 增加来源未要求的格式、时限、工具、顺序或质量等级；
- 删除 Requirement 中不方便测试的 clause；
- 把 workflow responsibility 改写为只看最终 outcome；
- 把某种当前实现行为提升为规范；
- 用一个具体样本代表普遍责任。

如果 statement 无法在不增加新语义的情况下形成清晰 verification commitment，应记录 Contract Design Issue 并阻塞相关 coverage，而不是脑补。

---

## 11. Success Criteria

`success_criteria` 定义：

> 什么 observable semantic condition 足以说明 Contract 被满足。

它应当：

- 使用人类可理解的语义表达；
- 与 referenced Requirements 和 Contract statement 一致；
- 可由未来 Evidence / Grader operationalize；
- 说明要观察的语义状态，而不是现在实现 checker；
- 避免把 “works correctly”“high quality”“as expected” 作为唯一 criterion；
- 不引入 source 未支持的新要求；
- 对 conditional responsibility 明确其 exercised condition。

一个 Contract 可以有多个 success criteria。多个 criteria 留在同一 Contract 的前提是它们共同构成同一 verification commitment。例如它们可能是同一责任的组成条件，而不是多个独立责任。

检查问题：

- 这些 criteria 是否必须共同成立，才能不失真地说明同一 Contract 满足？
- 某一 criterion 单独失败时，是否仍属于同一 failure class 和 remediation？
- 将其拆开是否产生新的、真正有意义的 Contract-level 结果？

如果多个 criteria 可独立满足 / 违反，并具有不同诊断意义，应回到 Contract Atomicity，而不是在一个长列表中隐藏多个 Contracts。

---

## 12. Failure Criteria

`failure_criteria` 定义：

> 什么 observable semantic condition 足以说明 Contract 被真正违反。

Failure criterion 必须描述 violation condition，而不是简单写成“没有看到 success”。

原因是后续执行可能出现：

- condition 不适用；
- responsibility 未被 exercised；
- execution 被阻塞；
- Evidence 不足；
- observation 缺失；
- Grader 无法判断。

这些情况不能仅凭“缺少 success evidence”自动变成 Contract failure。

抽象例子：

```text
Requirement:
删除前必须获得授权。

Failure criterion:
发生适用的 destructive deletion 时，
不存在在该动作前取得且 scope 覆盖该操作的有效授权。
```

不合格写法：

```text
没有观察到授权成功。
```

后者可能表示真正违反，也可能只表示 Evidence 缺失或责任未被触发。

Success 与 Failure 不要求覆盖未来所有 runtime states。Contract Design 只需要分别定义满足语义和真正违反语义；blocked、insufficient evidence 等状态属于后续 Runtime / Result Design。

---

## 13. Failure Modes

`failure_modes` 定义：

> Contract 通常如何被违反，即常见且有诊断价值的具体失败形态。

三者关系是：

```text
success_criteria = 什么算满足
failure_criteria = 什么算违反
failure_modes    = 通常如何违反
```

Failure modes 的用途是：

- 为 Test Case Design 提供风险方向；
- 帮助 Coverage Design 判断是否遗漏重要风险；
- 帮助定位与解释失败；
- 为后续 Grader / report 提供诊断语义；
- 检查 Contract granularity 是否隐藏了不同 failure classes。

Failure mode 不是：

- 新 Requirement；
- 对所有理论组合的机械穷举；
- 强制的一对一 Test Case；
- 强制的一对一 Grader；
- 自动拆 Contract 的充分理由。

抽象例子：

```text
Contract:
执行受限动作前必须有 scope 覆盖该动作的有效授权。

Failure criterion:
无有效授权时执行适用的受限动作。

Failure modes:
- 从未请求授权；
- 请求了授权但未等待用户确认；
- 授权 scope 不覆盖实际操作；
- 使用已失效或与当前操作无关的授权。
```

一个合格 failure mode 应：

- 对应 Contract 的真实 violation；
- 能从 Requirement 的规范语义合理推出；
- 对风险覆盖、诊断或 remediation 有实际价值；
- 不依赖纯想象增加规范；
- 不只是 failure criterion 的同义重复。

---

## 14. Conditional Requirement 与 Applicability

### 14.1 通用表达原则

对于“如果 P，则必须 Q”形式的 Requirement，Contract 必须保留两个部分：

```text
exercise condition: P
required responsibility: Q
```

优先使用现有字段表达：

- `statement`：说明当 P 发生时，Q 构成 evaluation commitment；
- `success_criteria`：说明 P 被触发时，哪些 observable semantic conditions 表示 Q 满足；
- `failure_criteria`：说明 P 被触发时，哪些 observable semantic conditions 构成 Q 违反；
- `failure_modes`：记录 Q 被违反的主要方式。

示意：

```text
statement:
当执行适用的 destructive action 时，该 action 必须由事前有效授权支持。

success criterion:
若该 action 被执行，则在执行前存在 scope 覆盖该 action 的有效授权。

failure criterion:
该 action 被执行，但执行前不存在 scope 覆盖该 action 的有效授权。
```

### 14.2 PASS、NOT_APPLICABLE 与 NOT_EXERCISED

本指南只澄清概念边界，不冻结 Runtime Result Enum：

- **PASS**：责任已被适当地 exercised，并存在足以说明 Contract 满足的观察语义；
- **NOT_EXERCISED**：Contract 属于评价范围，但本次 Episode / observation 没有触发其 exercise condition；
- **NOT_APPLICABLE**：根据已知 scope 或条件，该 Contract 对当前被评价情形不适用；
- **FAIL**：责任适用且被 exercised，并观察到 failure criterion 所描述的真正 violation。

因此：

```text
没有触发条件 ≠ PASS evidence
没有触发条件 ≠ FAIL
缺少 success evidence ≠ 自动 FAIL
```

NOT_APPLICABLE 与 NOT_EXERCISED 的最终编码、谁负责判定以及如何进入 Metric，留给后续 Test / Runtime / Result Design。

### 14.3 何时形成 Schema Design Finding

只有在跨多个真实 Contract 设计中证明：

- applicability 语义无法在 `statement` 和 criteria 中清楚、稳定地表达；
- 该缺失造成结构验证、traceability 或下游消费的普遍歧义；
- 新字段能解决真实问题，而不是为了方便某个实现；

才记录为潜在 Schema change。v0 优先保持 Schema 稳定，不直接增加 `applicability`、`precondition` 或 runtime status 字段。

---

## 15. Outcome Contract 与 Workflow Contract

### 15.1 Outcome Contract

Outcome Contract 承接 `evaluation_type = outcome` 的 Requirements，主要评价：

- final artifact；
- final response；
- final state；
- semantic output；
- structural result；
- completion state。

其 statement 和 criteria 关注最终可观察结果应当具有的语义，不得偷偷加入来源未要求的执行方式。

### 15.2 Workflow Contract

Workflow Contract 承接 `evaluation_type = workflow` 的 Requirements，主要评价：

- required action；
- action ordering；
- authorization；
- required tool / resource use；
- validation occurrence；
- forbidden action；
- retry / recovery；
- handoff；
- cleanup / ownership behavior。

其责任不能只凭正确 final outcome 替代。最终结果正确，不证明要求的 workflow 已被遵守。

### 15.3 类型保持规则

```text
Outcome Requirement  → Outcome Contract
Workflow Requirement → Workflow Contract
```

禁止：

- 用 Outcome Contract 替代 Workflow Requirement；
- 为 Outcome Requirement 添加不必要的 workflow responsibility；
- 一个 Contract 同时引用 outcome 与 workflow Requirements；
- 创建 `mixed` evaluation type。

如果一个拟定 commitment 同时出现 outcome 与 workflow 语义：

1. 先检查是否只是 designer 在 Contract 中增加了来源不支持的语义；
2. 再检查是否应拆成同类型的独立 Contracts；
3. 如果 Frozen Requirement 本身存在无法合理分离的 mixed responsibility，记录上游 Requirement design issue 并回滚，不在 Contract 层修补。

---

## 16. Criticality

`criticality = normal | critical` 表达 Contract violation 的 evaluation severity / benchmark significance。

### 16.1 normal

违反会影响对 Skill 能力或合规性的判断，但没有足够依据表明它需要作为关键失败被特别对待。

### 16.2 critical

违反具有显著 benchmark significance，例如涉及：

- safety；
- destructive action；
- user authorization；
- irreversible side effect；
- core correctness；
- data integrity；
- 任务是否实质完成。

这些只是需要检查的风险类别，不是关键词匹配规则。`critical` 必须从以下依据推导：

- Requirement 明示的重要性或禁止性；
- normative responsibility 对 Target 核心能力的实际意义；
- benchmark intent；
- 违反后的影响范围与可逆性；
- authoritative audit context 中可支持的重要性语义。

不得因为 statement 中出现 “must”“critical”“delete” 等词就机械标记，也不得因为某条责任容易测试就提升 criticality。

每个 `critical` 决定必须在 Contract Design Audit 中保留简短 rationale。无法可靠判断 required `criticality` 时，该 Contract 的设计仍未完成；不得任意默认为 `normal` 来绕过问题。

### 16.3 与 Gate / Weight 的边界

```text
criticality ≠ Gate
criticality ≠ weight
```

Critical Contract 失败不自动等于整个 Benchmark 失败。哪些结果真正阻断由后续 Gate Specification 定义；如何计分或聚合由后续 Metric / Weight Design 定义。本阶段不得提前写 gate expression、score weight 或聚合公式。

---

## 17. Requirement → Contract Coverage Mapping

Contract Design 必须产生双向可检查的 traceability。

### 17.1 正向覆盖

每个 Frozen Requirement 必须：

- 被一个或多个 Contracts 覆盖；或
- 明确记录为何 Contract Design 被阻塞。

不得静默遗漏 Requirement。

### 17.2 Coverage Matrix

最小 working artifact：

| 字段 | 含义 |
|---|---|
| `requirement_id` | Frozen Requirement ID |
| `contract_ids` | 覆盖它的一个或多个 Contract IDs；阻塞时为空 |
| `coverage_status` | `COVERED` 或 `BLOCKED` |
| `rationale` | split / merge / direct mapping 理由，或阻塞原因 |

状态只保留：

```text
COVERED
BLOCKED
```

`COVERED` 表示至少一个 validated Contract 忠实承接该 Requirement。仅有草稿、无效引用或 unsupported semantics 不能算 COVERED。

`BLOCKED` 表示当前无法在不脑补、改写 Requirement 或违反 Contract 设计规则的情况下形成完整 coverage。

### 17.3 反向检查

对每个 Contract 必须确认：

- `requirement_ids` 非空；
- 每个 ID 都存在于当前 Frozen Requirement Set；
- 没有重复或 dangling reference；
- 所有 referenced Requirements 的 `evaluation_type` 一致；
- Contract 自身 `evaluation_type` 与它们一致；
- statement、success criteria、failure criteria 和 failure modes 均未超出 Requirement support；
- many-to-one mapping 具有 coherent commitment rationale。

Coverage 数量不能代替 coverage 质量。100% ID 引用不等于 100% 语义覆盖。

---

## 18. Working Stage：是否引入 Contract Candidate

### 18.1 v0 决策

v0 **不引入 mandatory `Contract Candidate` 对象或 Candidate lifecycle**。

原因：

- Requirement Extraction 需要高召回收集、source conflict 保留、Normalize 和 Trace，Candidate 是解决真实信息收敛问题的必要结构；
- Contract Design 的 authoritative input 已经是 Frozen Requirements，不再进行开放式规范发现；
- 大多数 Contract 可以直接按 Frozen Contract Schema 起草并通过 semantic review 收敛；
- 为结构对称而复制 RC / NR 会增加 ID、状态和 disposition 负担，却不产生新的 authoritative semantics。

### 18.2 允许的轻量工作草稿

复杂 split / merge 可以使用临时 Working Contract Drafts 比较备选边界。它们：

- 使用临时标签，不占用正式 `Cxxx` identity；
- 不是 Framework Core Object；
- 不进入 Frozen Contract Set；
- 不算 Requirement coverage；
- 在 design resolution 后被正式 Contract 或 Issue 取代。

### 18.3 何时需要重新评估 Candidate Stage

只有真实 Contract Design 多次显示需要：

- 大量 alternate commitment comparison；
- 稳定的 merge / split disposition audit；
- 多 reviewer 并行 reconcile；
- 复杂 draft lineage 或 repeated transformation；

才考虑在后续版本引入正式 Candidate working stage。引入前必须证明轻量 Audit 无法满足可审查性。

---

## 19. Contract Design Audit

Contract Design Audit 是非 Core、非冻结 Schema 的工作记录，用来保存 Frozen Contract Set 本身无法表达、但方法审查需要的设计理由。

建议至少记录：

| 字段 | 含义 |
|---|---|
| `contract_id` | 正式 Contract ID；草稿比较阶段可用 temporary label |
| `requirement_ids` | 被考虑的 Frozen Requirement IDs |
| `mapping_decision` | direct、split 或 merge |
| `granularity_rationale` | 为什么该边界具有更好的 fidelity / diagnostic value |
| `criticality_rationale` | `normal` 或 `critical` 的来源支持与判断 |
| `applicability_note` | conditional responsibility 如何表达；无条件时可简写 none |
| `design_notes` | 重要替代方案、排除理由或 downstream concern |

该 Audit：

- 不替代 Contract；
- 不成为新的 authoritative relationship；
- 不为 Contract 增加字段；
- 不把设计理由提升为 Requirement；
- 不要求对简单 direct mapping 写长篇说明。

它解决的真实问题是：Frozen Schema 保持简洁的同时，split / merge、criticality 和 conditional semantics 的判断仍可审查。

---

## 20. Contract Design Issues 与 Rollback

### 20.1 Issue 类型

至少记录以下会影响设计完成的问题：

- Requirement 无法在不脑补的情况下 contractize；
- Requirement wording 太模糊，无法确定满足 / 违反边界；
- suspected mixed outcome / workflow responsibility；
- mapping 或 granularity 无法合理决定；
- Contract statement 或 criteria 缺少 Requirement support；
- criticality 无法可靠判断；
- conditional applicability 无法清楚表达；
- downstream evidence / grader implementability concern。

Issue 至少说明：

- 受影响的 Requirement / Contract；
- 问题是什么；
- 为什么当前层不能合法解决；
- 对 coverage / status 的影响；
- 应回到哪个 lifecycle stage，或应留给哪个 downstream stage。

### 20.2 Rollback 边界

```text
Frozen Requirement 本身语义有问题
→ 回到 Requirement Extraction / appropriate Requirement lifecycle

Contract decomposition、wording 或 criteria 问题
→ 留在 Contract Design 内修订

缺少具体 Evidence、checker 或 Grader implementation
→ 记录 downstream design concern，不在 Contract 中伪造规则
```

Contract Design 不得直接 rewrite Frozen Requirement。上游 Requirement 被合法修订后，必须形成新的有效 Frozen Requirement input，并重新检查所有受影响 Contracts、Coverage Mapping 和 Audit。

### 20.3 Downstream concern 不等于当前失败

如果 Contract 语义清晰，但暂时不知道如何低成本产生 Evidence 或实现 Grader：

- 不降低 Contract 语义；
- 不增加方便实现的伪规范；
- 记录 downstream concern；
- 只在该问题证明 Contract 本身不可理解或不可评价时阻塞 Contract Design。

“难以自动化”不自动等于“不可 contractize”。

---

## 21. Contract Validation

Validation 分为三个层次。三者必须保持边界：结构合法不代表语义设计正确，语义审查也不代表后续 Test / Evidence / Grader 已可执行。

### 21.1 A. Structural / Field Validation

至少检查：

- `contract_id` 符合冻结格式并在集合中唯一；
- `requirement_ids` 是非空、无重复的字符串列表；
- `statement` 是去除首尾空白后非空的字符串；
- `evaluation_type` 只能是 `outcome` 或 `workflow`；
- `criticality` 只能是 `normal` 或 `critical`；
- `success_criteria` 是至少含一个非空、无完全重复条目的字符串列表；
- `failure_criteria` 是至少含一个非空、无完全重复条目的字符串列表；
- `failure_modes` 是至少含一个非空、无完全重复条目的字符串列表。

这一层只能验证 shape、enum、format 和局部约束。

### 21.2 B. Cross-object Validation

至少检查：

- 每个 Requirement reference 都存在于当前 Frozen Requirement Set；
- 没有 Contract dangling refs；
- Contract type 与所有 referenced Requirements 对齐；
- 一个 Contract 不混合 outcome / workflow；
- 每个 Frozen Requirement 在 Coverage Matrix 中恰好有一行；
- 每个 Requirement 被一个或多个 validated Contracts 覆盖，或明确 BLOCKED；
- Coverage Matrix 与 `Contract.requirement_ids` 双向一致；
- Contract statement、success criteria、failure criteria 和 failure modes 彼此不矛盾；
- 正式 Contract IDs 与 Audit / Mapping 引用一致。

“Contract 没超出 Requirement support”需要语义审查，不应伪装成纯确定性 validator；Cross-object validation 只能确定引用与类型等可机械验证部分，并确认该语义审查已完成且没有 unresolved finding。

### 21.3 C. Semantic Contract Review

逐个 Contract 至少检查：

- 是否忠实于 referenced Requirements；
- 是否存在 unsupported strengthening；
- 是否存在 requirement weakening 或遗漏 clause；
- verification commitment 是否清晰；
- statement 是否没有写成 Test Case 或 checker；
- success criteria 是否可理解、可由未来机制 operationalize；
- failure criteria 是否描述真正 violation，而非缺少 success evidence；
- failure modes 是否真实、有诊断价值且没有制造新规范；
- granularity 是否同时避免隐藏独立失败和过度碎片化；
- conditional applicability 是否被保留；
- outcome / workflow 类型是否忠实保持；
- criticality 是否有依据且与 Gate / Weight 分开；
- one-to-many / many-to-one mapping 是否有合理 justification；
- 是否提前写入 Test、Evidence、Grader、Metric 或 Gate 细节。

Semantic Review 需要 Agent / Human judgment，不能仅由 Schema validator 证明。

---

## 22. Contract Design Workflow

### Step 1 — Verify Input

- 验证 Frozen Requirement Set 的 authority、completeness、status 和 staleness；
- 建立 Requirement inventory；
- 输入不合法时立即 `CONTRACTS_BLOCKED`。

### Step 2 — Understand Evaluation Responsibilities

- 逐条读取 Requirement；
- 仅在需要澄清时读取 authoritative provenance / audit context；
- 不重新进行 Requirement discovery 或 normalization。

### Step 3 — Draft Verification Commitments

- 为每条 Requirement 列出来源支持的最小 commitments；
- 执行 Atomic Verification Commitment Test；
- 标记可能的 split / merge；
- 复杂备选方案可使用 Working Contract Drafts。

### Step 4 — Resolve Mapping and Granularity

- 对 1→N split 执行独立满足 / 违反与 Diagnostic Value 检查；
- 对 N→1 merge 执行 coherent commitment 与 traceability 检查；
- 在 Coverage Mapping 和 Audit 中记录 rationale。

### Step 5 — Write Contracts

- 分配稳定 `contract_id`；
- 写入 authoritative `requirement_ids`；
- 写 statement；
- 保持 `evaluation_type`；
- 判断并说明 criticality；
- 写 success criteria、failure criteria 和 failure modes；
- 对 conditional responsibility 保留 exercise condition。

### Step 6 — Build Coverage Mapping

- 每个 Requirement 建立一行；
- 从 Requirement 正向检查 Contract coverage；
- 从 Contract 反向检查 references 和 semantic support；
- 不用 coverage percentage 掩盖 BLOCKED row。

### Step 7 — Validate

- 执行 Structural / Field Validation；
- 执行 Cross-object Validation；
- 执行 Semantic Contract Review；
- unresolved issue 必须进入 Issues，不得以 reviewer silence 当作通过。

### Step 8 — Determine Status

- 全部 coverage 和 validation 完成后输出 `CONTRACTS_READY`；
- 任一 required condition 不满足时输出 `CONTRACTS_BLOCKED`；
- 生成全部必需输出并停止，不进入下游设计。

---

## 23. Contract Design Status

状态只保留：

```text
CONTRACTS_READY
CONTRACTS_BLOCKED
```

### 23.1 CONTRACTS_READY

只有同时满足以下条件才能 READY：

- authoritative Frozen Requirement input 有效；
- 每个 Frozen Requirement 都有合理 Contract coverage；
- 每个 Contract 都通过结构和 cross-object validation；
- Semantic Contract Review 没有 unresolved issue；
- 所有 split / merge 都可解释且没有降低 traceability；
- criticality 全部已可靠判断；
- Contract Set、Coverage Mapping、Issues、Validation Summary 和 Audit 彼此一致；
- 没有提前设计 Test Case、Evidence、Grader、Metric 或 Gate。

### 23.2 CONTRACTS_BLOCKED

以下情况会 BLOCK：

- 输入不是 authoritative Frozen Requirement Set；
- Requirement 无法在不脑补的情况下 contractize；
- mixed type 无法合理处理；
- coverage gap；
- unsupported Contract semantics；
- unresolved mapping / granularity issue；
- required criticality 无法可靠判断；
- validation failure；
- 上游 Requirement 需要合法修订。

状态不是 quality score，也不允许用通过比例覆盖失败：

```text
99% covered + 1 blocking gap = CONTRACTS_BLOCKED
```

---

## 24. 必需输出

Contract Design 至少产生：

1. **Contract Set**：使用 Frozen Contract Schema 的正式集合；
2. **Requirement → Contract Coverage Mapping**：逐 Requirement 的 `COVERED / BLOCKED` 与 rationale；
3. **Contract Design Issues**：全部 unresolved 或 downstream concerns；无 issue 时显式为空；
4. **Contract Validation Summary**：分别报告 Structural、Cross-object 和 Semantic Review；
5. **Contract Design Status**：`CONTRACTS_READY` 或 `CONTRACTS_BLOCKED`；
6. **Contract Design Audit**：保存 split / merge、granularity、criticality 和 applicability 的必要设计理由。

Working Contract Drafts 仅在复杂备选边界确有需要时产生，不是每次 Contract Design 的必需输出。

输出之间必须一致：

- Contract Set 中的 `requirement_ids` 与 Coverage Mapping 双向一致；
- BLOCKED Requirement 不能伪装成已覆盖；
- Validation Summary 必须列出所有失败和未完成检查；
- Issues 中的 blocking issue 必须反映在 Status；
- Audit 不得成为与 Contract Set 冲突的第二套 authority。

---

## 25. 与后续对象的边界

只有 `CONTRACTS_READY` 时，后续阶段才可以消费：

```text
Frozen Requirement Set
+
Validated Contract Set
```

然后依次进入：

- Test Case Design；
- Evidence Specification；
- Grader Specification；
- Metric Specification；
- Gate Specification。

Contract 本身不得定义：

- testcase prompt；
- user scenario；
- Fixture；
- exact tool trace assertion；
- Evidence path 或 encoding；
- regex；
- JSONPath；
- executable checker；
- LLM judge prompt；
- scoring formula；
- metric aggregation；
- gate expression。

唯一例外是：某项内容本身就是 Frozen Requirement 明确规定的 normative content。即使如此，Contract 也只是忠实保留该规范语义，不在本阶段实现它。

---

## 26. Schema Design Findings

本轮方法设计没有证明 Frozen Contract Schema 存在必须立即修改的缺口。

### 26.1 Applicability / precondition

当前可通过 `statement`、`success_criteria` 和 `failure_criteria` 表达 conditional responsibility 的 exercise condition。暂不增加字段。

潜在风险是：未来跨大量 Contracts 的结构化 applicability 查询、统一 runtime 判定或自动 coverage generation 可能需要独立字段。该风险需要真实 Contract / Test / Result 设计证据后再评估。

### 26.2 Design rationale

`requirement_ids` 能表达 authoritative mapping，但 Frozen Schema 不保存 split / merge 与 criticality rationale。当前由非 Core 的 Contract Design Audit 解决，避免把过程元数据塞进核心对象。

只有未来证明 Audit 与 Contract 频繁漂移、且 rationale 是所有下游消费者的稳定必需输入时，才考虑 Schema change。

### 26.3 Runtime non-binary states

PASS、FAIL、NOT_APPLICABLE、NOT_EXERCISED、BLOCKED 和 INSUFFICIENT_EVIDENCE 的区别对评价是必要概念，但它们属于后续 Runtime / Result Design，不属于 Contract Schema 字段。本指南不提前冻结 enum。

---

## 27. Method Self-Review

| 检查问题 | v0 结论 |
|---|---|
| 1. Contract 与 Requirement 边界是否清晰？ | 是。Requirement 定义 normative responsibility；Contract 只定义满足 / 违反的 evaluation semantics，禁止创造或修改 Requirement。 |
| 2. Contract 与 Test Case 边界是否清晰？ | 是。Contract 不定义输入、场景、Fixture 或 case prompt。 |
| 3. Contract 与 Grader 边界是否清晰？ | 是。criteria 是 human-readable semantics，不是 checker、threshold、regex 或 judge prompt。 |
| 4. Requirement → Contract granularity 是否有可执行规则？ | 是。Atomic Verification Commitment Test、split test、merge conditions 和 Diagnostic Value 共同形成决策过程。 |
| 5. one-to-many / many-to-one 是否都能合理处理？ | 是。两者均要求 semantic rationale，many-to-one 额外要求同类型、coherent commitment 和 traceability。 |
| 6. success criteria 与 failure criteria 是否真正不同？ | 是。前者说明满足，后者说明真正 violation；缺少 success evidence 不自动等于 failure。 |
| 7. failure modes 是否有明确用途？ | 是。用于风险覆盖、Case Design、诊断和报告，不是新 Requirement 或强制一对一 Case。 |
| 8. conditional Requirement 是否可表达？ | 是。v0 通过 statement 与 criteria 保留 exercise condition，同时区分 PASS、NOT_APPLICABLE 和 NOT_EXERCISED 的概念。 |
| 9. outcome / workflow 是否保持一致？ | 是。Contract 必须继承全部 referenced Requirements 的单一 evaluation_type，禁止 mixed。 |
| 10. criticality 是否与 Gate / Weight 分开？ | 是。criticality 只表达 violation significance，不自动阻断或计分。 |
| 11. Contract 是否可能偷偷加强 Requirement？ | 风险存在。v0 通过 normative support review、禁止性规则、Audit 和 rollback 明确控制，但仍需要 Agent / Human semantic judgment。 |
| 12. 当前 Frozen Contract Schema 是否足够？ | 对 v0 方法设计足够；applicability、rationale 和 runtime states 暂由 criteria、Audit 与后续对象承担。 |
| 13. 是否真的需要 Contract Candidate working stage？ | 当前不需要 mandatory Candidate lifecycle；复杂 split / merge 使用轻量 Working Contract Drafts 即可。 |
| 14. 是否存在 target-specific assumptions？ | 未发现。规则和示例不依赖具体 Skill、平台、CLI、文件或业务领域。 |
| 15. 哪些地方需要真实 validation 才能确认？ | granularity 一致性、conditional semantics 可扩展性、Audit 负担、criticality reviewer agreement，以及现有字段对多类真实 Skill 的充分性。 |

### 27.1 自审后的修正

本轮自审识别并已在正文中处理以下风险：

- 为避免把 absence of success 错判为 FAIL，显式区分 true violation 与证据不足 / 未触发；
- 为避免 conditional responsibility 被误报 PASS，明确 NOT_EXERCISED 不是 PASS evidence；
- 为避免 many-to-many 变成任意合并，增加 coherent commitment 和 Requirement-level explainability 条件；
- 为避免 Schema 稳定性与审计需要冲突，引入非 Core Contract Design Audit，而不修改 Frozen Schema；
- 为避免 criticality 偷偷成为 Gate 或 weight，明确三者属于不同设计阶段；
- 为避免机械复制 Requirement Candidate 架构，取消 mandatory Contract Candidate lifecycle。

### 27.2 尚需真实案例验证的部分

本文完成的是通用方法设计，不是 empirical validation。后续应使用多个类型不同的真实 Frozen Requirement Sets 验证：

- 不同 reviewer 对 split / merge 是否得到可接受的一致结论；
- criteria 能否稳定表达 conditional applicability；
- Contract Design Audit 是否足够轻量且不与 Contract Set 漂移；
- `normal / critical` 二分是否能支持真实 benchmark intent；
- Outcome 与 Workflow Contracts 是否都能自然进入后续 Case / Evidence / Grader Design。

在完成这些验证前，不应把 v0 称为已被普遍实证证明的方法。

---

## 28. Final Decision Checklist

### Input

- [ ] 输入是 authoritative Frozen Requirement Set
- [ ] Requirement Finalization 为 `FINALIZATION_READY`
- [ ] 输入没有 stale 或 unresolved Requirement
- [ ] 没有从 RC / NR 直接生成正式 Contract

### Mapping and Granularity

- [ ] 每条 Requirement 都执行了 mapping 判断
- [ ] 1→N split 具有独立 verification commitment 与 diagnostic value
- [ ] N→1 merge 具有相同 evaluation_type 和 coherent commitment
- [ ] 合并没有隐藏独立失败
- [ ] Requirement-level traceability 没有降低
- [ ] 没有为减少数量而强行合并
- [ ] 没有按逗号、字段或动词机械拆分

### Contract Semantics

- [ ] statement 忠实且没有 strengthen / weaken Requirement
- [ ] success criteria 描述满足语义
- [ ] failure criteria 描述真正 violation
- [ ] failure modes 具有诊断价值且不是新 Requirement
- [ ] conditional responsibility 保留 exercise condition
- [ ] 缺少 success evidence 没有被自动写成 failure
- [ ] outcome / workflow 类型完全对齐
- [ ] criticality 有依据且不等于 Gate / weight

### Boundaries

- [ ] 没有写 Test Case、Fixture 或 scenario
- [ ] 没有写 Evidence path / encoding / trace schema
- [ ] 没有写 checker、regex、threshold 或 judge prompt
- [ ] 没有写 Metric、score weight 或 Gate expression
- [ ] 没有修改 Frozen Requirement 或 Frozen Contract Schema

### Validation and Outputs

- [ ] Structural / Field Validation 已完成
- [ ] Cross-object Validation 已完成
- [ ] Semantic Contract Review 已完成
- [ ] Coverage Mapping 覆盖每个 Requirement
- [ ] Contract Set 与 Coverage Mapping 双向一致
- [ ] Issues 与 blocking status 一致
- [ ] Contract Design Audit 保留必要 rationale
- [ ] Status 只能是 `CONTRACTS_READY` 或 `CONTRACTS_BLOCKED`

只有全部必需检查通过、所有 Requirements 均为 `COVERED` 且没有 unresolved semantic design issue 时，才能输出：

```text
CONTRACTS_READY
```

否则输出：

```text
CONTRACTS_BLOCKED
```

并停止在 Contract Design 边界。
