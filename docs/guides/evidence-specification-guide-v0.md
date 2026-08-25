# 《Evidence Specification Design Guide v0》

Status: Design Guide

本文定义从 authoritative Frozen Requirements、validated Contracts 与 validated Test Cases 到 Evidence Specification 的通用设计方法。它适用于通用 Agent Skill Eval，不绑定特定 Skill、平台、工具、Artifact 类型、交互界面或业务领域。

本文提出最小 EvidenceSpecification Schema Proposal，但不修改任何已经冻结的 Requirement、Contract、Concept Model 或 Schema，不修改 Test Case Guide，不实现 Runtime，不开始 Grader、Metric 或 Gate Design。

---

## 1. Evidence Specification 的角色

Evidence Specification 回答：

> What observations must be available so that downstream evaluation can legitimately judge the Contract exercised by this Test Case?

它是 Definition-time first-class object，预先声明未来 Episode 中为了评价目标 ExpectedAssertion，必须取得什么观察、来源、上下文与最低资格条件。

Evidence Specification 负责定义：

- required observation semantics；
- minimum sufficient observation scope；
- provenance expectations；
- temporal、ordering、scope 或 before / after context；
- qualification expectations；
- Evidence need 与 Test Case / Contract target 的关系。

Evidence Specification 不负责：

- 决定 PASS / FAIL；
- 定义 Grader algorithm；
- 定义 regex、JSONPath、checker、judge prompt 或 threshold；
- 定义 Test Case scenario；
- 修改 Contract success / failure semantics；
- 保存 actual Evidence；
- 保存 actual Artifact；
- 保存 actual message、trace、log、screenshot、tool call 或 timestamp；
- 执行 evidence collection；
- 定义 Metric、Score、Weight 或 Gate。

---

## 2. 为什么 Test Case 之后仍需要 Evidence Specification

Test Case 回答：

> 构造什么场景，使 Contract 真正有机会被满足或违反？

Evidence Specification 回答：

> 在该场景的未来 Episode 中，必须观察到什么，才有合法基础进行判断？

例如：

```text
Contract:
受限操作前必须取得用户确认。

Test Case:
用户提出操作请求；Subject 正确请求确认时，Evaluator 再提供确认。

Evidence Specification:
需要能够建立 relevant user request、Subject confirmation request、
Evaluator confirmation response 与后续受限操作之间的身份、scope 和顺序关系。
```

Evidence Specification 不继续规定：

```text
读取 trace.events[3]，比较 action.path，或运行某个 checker。
```

这些属于未来 Runtime encoding 或 Grader Design。

---

## 3. Evidence Specification 与 Runtime Evidence

Concept Model 已冻结：

```text
Evidence Specification
= Definition-time required evidence definition

Evidence
= Runtime qualified evidence
```

Evidence Specification 描述：

- 需要观察什么；
- 观察必须来自什么语义来源；
- 需要保留什么 context；
- 什么最低完整性与身份条件使观察有资格被下游消费。

Evidence 描述：

- 某次 Episode 实际取得了什么；
- 来自哪个 Episode；
- 是否完整、当前、可归因；
- 是否满足相关 Evidence Specification；
- 是否可以被 Grader 合法消费。

因此，Evidence Specification 中禁止保存：

- actual message；
- actual tool call；
- actual screenshot；
- actual log line；
- actual file；
- actual value；
- actual timestamp；
- actual availability / qualification result。

---

## 4. Artifact 与 Evidence 的边界

Artifact 是 Episode 在执行过程中产生或捕获的可持久化 runtime object，例如文件、结构化输出、报告、截图、日志、中间产物或持久化 Trace。

Evidence 是从 Episode output、Artifact、Trace、state 或 observation 中选取并资格确认、可用于评价 Contract 的信息。

```text
Artifact existence
≠ Evidence qualification
```

一个 Artifact 只有在满足以下条件时，才可能成为 Evidence source：

- 与某个 Evidence Specification 相关；
- 来源与 identity 可确认；
- 可关联到当前 Episode；
- 包含目标判断所需的信息；
- context 与完整性足够；
- 被明确纳入本次 evaluation。

Evidence 也不一定来自独立 Artifact。以下 observation 可以直接成为 Evidence source：

- interaction history；
- action occurrence；
- action ordering；
- tool / resource usage；
- environment state；
- before / after state；
- Episode output 或 status transition。

Definition-time Evidence Specification 可以语义描述“最终 Subject-produced output Artifact”或“relevant interaction observations”，但不得预先绑定尚未存在的 runtime Artifact ID。

---

## 5. Authoritative Input 与 Entry Gate

### 5.1 Production inputs

Production Evidence Specification Design 必须消费：

1. authoritative Frozen Requirement Set；
2. validated Contract Set；
3. validated Test Case Set；
4. Test Case → Contract authority，即 `expected_assertions[].contract_id`；
5. ExpectedAssertion semantics；
6. Contract success criteria；
7. Contract failure criteria；
8. Contract failure modes；
9. Contract `evaluation_type` 与 `criticality`；
10. Test Case task、initial state、fixtures、preconditions 与 interaction steps；
11. Test Case Design Audit context when needed。

Audit context 只帮助理解既有 design，不得修改 Requirement、Contract 或 Test Case semantics。

### 5.2 Production Entry Gate

只有以下条件全部满足，才能开始 production Evidence Specification Design：

- Test Case Design Status 为 `TEST_CASES_READY`；
- Requirements、Contracts 与 Test Cases 当前有效且没有 stale；
- ExpectedAssertion references 可解析；
- 没有 unresolved upstream semantic issue；
- 所有对象属于同一个有效 Definition context。

任一条件不满足时：

```text
Evidence Specification Design Status = EVIDENCE_SPECS_BLOCKED
```

不得通过 downstream Evidence wording 修补 Contract ambiguity、Test Case exercise gap 或 upstream blocker。

### 5.3 Method Validation Subset

如果上游状态是完整限定的：

```text
TEST_CASES_READY for validation subset
```

Evidence Specification method validation 可以继续使用同一 validation-local Requirements、Contracts 与 Test Cases，但必须：

- 只用于 method validation、Schema adequacy research 或 review；
- 不进入 production Benchmark Definition；
- 不形成 authoritative complete Evidence Specification Set；
- 不进入 downstream production Grader Design；
- 不绕过 `TRACE_BLOCKED`、`CONTRACTS_BLOCKED`、`TEST_CASES_BLOCKED` 或其他 production blocker；
- 不宣称完整 Target / Benchmark 的 Evidence Specifications READY。

Subset 状态必须完整写成：

```text
EVIDENCE_SPECS_READY for validation subset
```

或：

```text
EVIDENCE_SPECS_BLOCKED for validation subset
```

Evidence Specification Method Validation Subset 不是 Core Object，也不是 production lifecycle state。

---

## 6. Contract / Test Case → Evidence Specification Mapping

Concept Model 冻结：

```text
Contract N ↔ N Evidence Specification
Test Case N ↔ N Evidence Specification
```

一个 ExpectedAssertion 可能需要多个 Evidence Specifications，例如独立的 Outcome observation 与 Workflow ordering observation。

一个 Evidence Specification 也可以服务多个 ExpectedAssertions，前提是这些 targets 真的需要同一 observation package，并且：

- observation semantics 相同；
- provenance expectations 相同；
- temporal / context requirements 相同；
- qualification requirements 相同；
- 共享不会掩盖 target-specific sufficiency 或 diagnosis。

不得机械假定：

```text
1 ExpectedAssertion = 1 Evidence Specification
```

也不得为了减少 Spec 数量，把不同 observation surfaces、provenance 或 qualification needs 强行合并。

核心原则：

```text
Evidence Need Semantics
而不是
ID Linkage
```

---

## 7. Evidence Target 与关系 Authority

ExpectedAssertion 当前没有独立 ID，但 Test Case Guide 已冻结以下局部唯一性规则：

```text
同一 Test Case 内，同一 contract_id 最多一个 ExpectedAssertion。
```

因此以下 pair 可以在 Definition context 中唯一定位一个 ExpectedAssertion semantic target：

```text
(test_case_id, contract_id)
```

Evidence Specification 使用 nested target：

```text
EvidenceTarget:
- test_case_id
- contract_id
```

规则：

- pair 必须解析到 Test Case 的 `expected_assertions[].contract_id`；
- EvidenceTarget 不创建新的 Test Case → Contract relation；
- Test Case → Contract 的唯一 authority 仍是 ExpectedAssertion；
- EvidenceTarget 只是对已有 authoritative pair 的 downstream reference；
- 不增加 ExpectedAssertion ID；
- 不使用独立 `test_case_ids` 与 `contract_ids` 两个列表，避免产生不明确的 Cartesian product。

---

## 8. Evidence Need Categories

Evidence need categories 是 Design dimensions，不在 v0 中冻结为 enum。

常见维度包括：

- final output observation；
- Artifact existence、content 或 state；
- final response / handoff；
- user / Subject interaction；
- action occurrence；
- action ordering；
- tool / resource usage；
- affected scope；
- environment state；
- before / after state；
- error / recovery observation；
- cleanup；
- completion state。

一个 Evidence Specification 可以涉及多个维度，只要它们共同构成一个不可合理分离的 minimum sufficient observation package。

Category labels 可以记录在 Design Audit 中帮助 review，但不进入 Frozen Schema，除非未来真实 Framework behavior 需要稳定 taxonomy。

---

## 9. Outcome Evidence 与 Workflow Evidence

### 9.1 Outcome Contract

Outcome Evidence need 通常关注：

- final Artifact；
- final response；
- final state；
- semantic content；
- structure；
- completion result；
- user-visible handoff。

设计检查：

- 是否观察了 Contract 真正要求的 Outcome，而不是无关中间过程；
- final Artifact existence 是否足够，还是需要 content / state；
- Case 是否可能产生相似但错误的 Artifact identity；
- handoff Contract 是否需要 user-visible response observation，而不能只看文件存在。

### 9.2 Workflow Contract

Workflow Evidence need 通常关注：

- required action occurrence；
- ordering；
- authorization / consent；
- required tool / resource use；
- forbidden action absence or occurrence；
- retry / recovery；
- cleanup；
- before / after state；
- interaction sequence；
- handoff sequence。

禁止：

```text
Correct final Outcome
→ automatically sufficient Workflow Evidence
```

如果 Contract 要求 Subject 在 final write 前执行 validation，仅有“final Artifact valid”原则上不足以证明 validation action occurred 或 order correct。

如何具体判断 occurrence 或 order 属于未来 Grader Design；本阶段只要求必要 observations 原则上可用。

---

## 10. Evidence Sufficiency

Evidence Sufficiency 回答：

> 这些 observation requirements 在原则上是否足以让未来 Grader 对目标 ExpectedAssertion 作出合法判断？

Sufficiency Review 至少检查：

1. 每个 target responsibility 的关键事实是否可观察？
2. Compliant 与 violating semantics 是否原则上可区分？
3. Conditional trigger 是否可建立？
4. 如果涉及 action，occurrence 是否可建立？
5. 如果涉及 ordering，relevant relation 是否可建立？
6. 如果涉及 scope，authorized 与 affected scope 是否都可理解？
7. 如果涉及 Artifact，identity、content 或 state 是否达到目标所需范围？
8. Observation 是否来自正确 Episode 与 source？
9. 需要 before / after 时是否两端状态都被覆盖？
10. 缺少某一 observation 时，是否仍能对部分 target 作独立判断？

弱表达：

```text
需要 logs。
```

更充分的 semantic 表达：

```text
需要能够确定 validation action 是否发生，
并建立它相对于 final write 的顺序。
```

禁止继续写成：

```text
读取 trace.events[3] 并比较 timestamp。
```

---

## 11. Minimum Sufficient Evidence

Evidence Specification 不应要求保存整个 Episode 的所有内容。设计目标是：

```text
足够合法判断
+
避免无意义过度收集
```

Minimality Review 至少检查：

- 哪些信息对判断目标 Contract 必须？
- 哪些只方便 debugging？
- 哪些只是未来可能有用？
- 是否收集与当前 target 无关的交互、文件、状态或日志？
- 是否要求完整 Trace，而实际只需要一个 action relation？
- 是否收集超出 scope 的 user content 或 environment data？
- 是否产生明显 privacy、cost 或 storage overcollection？
- 是否可以在不降低 sufficiency 的情况下缩小 observation scope？

本指南不设计 privacy policy、retention period 或 storage system，只固定 minimum sufficient principle。

Debugging / supporting observations 不自动进入 authoritative Evidence Specification。它们可以留在 Design Audit 或未来 Runtime diagnostics policy。

---

## 12. Evidence Provenance

Evidence Specification 必须声明对 qualification 语义必要的最低 provenance expectations。

至少考虑：

- observation source；
- Subject、Evaluator、Environment 或 Tool origin；
- current Episode association；
- current Test Case / target relation；
- relevant Artifact identity；
- interaction participant identity；
- action / state observation origin；
- transformed observation 与 original source 的 lineage；
- 需要时的 temporal relation。

Provenance expectation 不是 actual runtime provenance record。Evidence Specification 不保存 Episode ID、Artifact ID、actual path 或 timestamp，只说明未来 Evidence 必须能够证明这些关系中的哪些。

例如：

```text
需要能够确认 final output observation 来自当前 Episode 的 Subject-produced Artifact，
而不是历史 Run 中名称相似的文件。
```

---

## 13. Temporal、Ordering 与 Context Evidence

Workflow Contracts 经常依赖：

```text
A before B
A after confirmation
retry after failure
cleanup after completion
handoff after final write
```

Evidence Specification 应表达：

- 哪些 semantic events 需要建立 relation；
- relation 是 before、after、during、same-operation scope 或 causal continuation；
- 是否需要保持 relevant interaction / action context；
- 是否必须区分不同 attempts 或重复操作。

它不得要求：

- timestamp format；
- exact event index；
- trace schema；
- field name；
- comparison function。

除非这些信息本身由 authoritative Requirement规定，否则它们属于 Runtime encoding或Grader implementation。

---

## 14. Before / After State Evidence

并非所有 Contracts 都需要 before / after state。

通常需要两端状态的情况：

- affected scope；
- destructive action；
- state transition；
- cleanup；
- retry / recovery；
- mutation correctness；
- forbidden collateral effect。

只需要 final state 的倾向：

- Contract 只承诺 final semantic output；
- before state 与判断无关；
- final Artifact 本身足以建立目标 Outcome；
- 添加 before capture 不增加 sufficiency。

如果仅观察 final state 无法区分“Subject造成的变化”“原本就存在”或“影响了不允许的scope”，则通常需要 before + after context。

不得机械要求所有 Case capture before / after。

---

## 15. Interaction Evidence

对于包含 `interaction_steps` 的 Test Case，Evidence need 可以涉及：

- initial user turn；
- trigger-relevant Subject behavior；
- conditional evaluator response occurrence；
- later Subject action；
- relevant interaction participants；
- confirmation / consent scope；
- response 与 action 的 ordering relation。

Definition-time example：

```text
需要能够建立：
1. Subject 是否主动请求当前受限操作的确认；
2. Evaluator response 是否只在该请求后出现；
3. 后续受限操作是否发生；
4. response 与操作是否属于同一 scope；
5. confirmation 是否发生在操作之前。
```

Evidence Specification 不保存 actual transcript，也不把 `InteractionStep.trigger` 改成 executable matcher。Trigger 仍然是 Test Case Definition 中的 semantic condition；Evidence Specification 只声明未来必须有足够 interaction observations。

如果 Evidence Design 证明 InteractionStep 无法表达需要观察的 scenario semantics，应记录：

```text
Upstream Test Case Design Concern
```

不得在本阶段直接修改 Test Case Guide。

---

## 16. Evidence Qualification Principles

Captured data 不自动成为 qualified Evidence。未来 observation 至少应按相关 Evidence Specification 检查：

- 与 target Contract / ExpectedAssertion 相关；
- 可归因到当前 Episode；
- source identity 正确；
- Artifact 或 interaction identity 没有与其他 Run混淆；
- 必需内容完整；
- 没有 stale；
- 没有被不明 transformation破坏；
- temporal / scope context 在需要时被保留；
- 没有因截断、corruption或ambiguity失去判断价值。

Evidence Specification 只声明 qualification expectations，不保存 actual qualification status，也不设计 automatic Evidence validator。

Qualification 不等于 Grading：

```text
Qualification:
这份 observation 是否是当前 Episode、当前 target 所需且足够完整的合法输入？

Grading:
这些 qualified observations 是否说明 Contract satisfied or violated？
```

---

## 17. Missing Evidence 与 Contract Failure

必须保持：

```text
Absence of required Evidence
≠ observed Contract violation
```

例如，Contract 要求 Subject 请求授权，但 Episode interaction observation 丢失。此时可能是：

- Evidence insufficient；
- Evidence capture failure；
- Episode incomplete；
- environment / infrastructure failure；
- observation ambiguous。

不能仅因没有授权 Evidence 就自动判 Subject 没有请求授权。

同样：

```text
Evidence collection failure
≠ Subject failure
```

除非 Contract 本身要求 Subject 产生某个 evidence-like Artifact，而该 Artifact 缺失本身就是 Contract violation。即便如此，也必须区分：

- Subject 未产生 required Artifact；
- Subject 已产生，但 evaluator capture / qualification失败。

具体 Result enum 与 Grader missing-input policy 不在本轮设计。

---

## 18. Evidence Collection Failure Boundary

至少区分：

### A. Subject responsibility failure

Subject 未履行 Contract 本身要求的 action、Outcome、handoff或Artifact responsibility。

### B. Evaluator / infrastructure capture failure

例如：

- recorder不可用；
- observation丢失；
- Artifact capture失败；
- Trace被截断；
- collector无法关联Episode；
- evaluator channel没有保留interaction context。

Evidence Specification 应描述 required observation，不把具体 capture mechanism 当作 Subject responsibility。

如果一个 required observation 原则上无法合理获得，Evidence Specification Design 应 `BLOCKED`，并记录 design issue；不得等到 Runtime 后把基础设施缺口改写为 Subject FAIL。

---

## 19. Multi-Contract Test Case 的 Shared / Split Evidence

Multi-Contract Case 中，不同 targets 可以共享或拆分 Evidence Specifications。

适合共享的倾向：

- 同一 observation package 同时包含多个 targets所需事实；
- provenance相同；
- temporal / scope context相同；
- qualification相同；
- 共享不隐藏任一 target的sufficiency；
- 共享显著减少重复收集。

应拆分的倾向：

- Outcome Artifact 与Workflow interaction来自不同surface；
- 一个需要before / after，另一个只需要final state；
- provenance不同；
- qualification不同；
- 一个observation缺失时另一个仍有效；
- 合并导致downstream无法定位缺少哪类Evidence；
- 合并要求保存大量与某一target无关的信息。

共享 Evidence Specification 不表示多个 Contracts 被合并，也不改变 ExpectedAssertion authority。

---

## 20. Evidence Need Atomicity Test

对每个 proposed Evidence Specification 询问：

1. 其中是否包含多个 required observation groups？
2. 这些 groups 的provenance是否不同？
3. Collection surface是否不同？
4. Qualification expectations是否不同？
5. 一个group缺失时，另一个是否仍可成为qualified Evidence？
6. Temporal / context relation是否不同？
7. 拆分是否提高missing-evidence diagnosis？
8. 合并是否真正形成不可分的minimum sufficient package？

如果 A 与 B provenance、collection、qualification或独立缺失语义不同，通常拆分。

如果 A 与 B 在同一 observation package中天然不可分，且拆分不增加评价或诊断价值，可以保留一个 Spec。

目标是：

```text
Evidence Sufficiency
+
Missing-evidence Diagnosis
+
Collection Efficiency
```

而不是 Maximum Fragmentation 或 Maximum Integration。

---

## 21. Required 与 Optional Evidence 决策

v0 不在 Evidence Specification Schema 中增加 `required | optional` enum。

理由：

- Evidence Specification 本身定义 minimum required evidence；
- 如果 observation 对合法判断不是必需，就不应进入 authoritative minimum；
- supporting / debugging observations 不应因“可能有用”被提升为required definition；
- optional evidence若没有明确Framework behavior，只会增加ambiguous coverage和overcollection；
- downstream Grader不能依赖未声明为minimum required的偶然observation。

当前决策：

```text
Evidence Specification
= minimum required evidence need

Supporting / optional observations
= Design Audit note or future Runtime diagnostics policy
```

如果未来真实validation证明某类optional observation具有稳定、必要的Framework行为，再重新评估字段；本轮不预留enum。

---

## 22. Evidence Specification Design Audit

v0引入轻量、非Core、非authoritative的Evidence Specification Design Audit。它是必需working artifact，因为最小Schema不保存sufficiency、minimality、atomicity与shared / split rationale。

建议至少记录：

| 字段 | 含义 |
|---|---|
| `evidence_spec_id` | 正式Spec ID；draft时可使用temporary label |
| `targets` | 从Schema targets派生的Test Case / Contract pairs |
| `evidence_need_rationale` | 为什么这些observations支持targets |
| `sufficiency_rationale` | 为什么原则上足够合法判断 |
| `minimality_rationale` | 为什么没有过度收集 |
| `provenance_rationale` | 为什么这些source / identity expectations必要 |
| `context_rationale` | temporal、scope、before / after等context选择 |
| `qualification_rationale` | completeness、staleness、ambiguity等最低资格要求 |
| `category_labels` | Outcome、interaction、ordering、scope等working labels；不是enum |
| `shared_split_decision` | 多target共享或拆分理由 |
| `overcollection_concern` | privacy、cost、storage或无关数据风险 |
| `downstream_grader_concern` | observations存在但未来判断仍需解决的问题 |
| `design_notes` | upstream concern、环境限制或暂未解决风险 |

Audit：

- 不替代Evidence Specification Definition；
- 不成为EvidenceTarget第二套authority；
- 不保存Runtime Evidence；
- 不保存actual capture result；
- 不定义Grader；
- 不要求简单Spec写长篇文字；
- 必须与Schema targets和Coverage Mapping一致。

---

## 23. Evidence Specification Candidate / Working Stage

v0不引入mandatory `Evidence Specification Candidate`对象或Candidate lifecycle。

复杂authoring可以使用temporary Working Evidence Spec Drafts比较：

- alternate observation packages；
- shared vs split；
- provenance choices；
- before / after necessity；
- minimum vs overcollection；
- interaction / action / Artifact surfaces。

Working Draft：

- 不是Core Object；
- 不进入Frozen Evidence Specification Set；
- 不算Evidence coverage；
- 不占用正式`ESxxx` ID；
- resolved后由正式Spec或Design Issue取代。

只有未来真实design反复出现复杂lineage、多reviewer reconciliation或无法由Audit解释的transformation，才重新评估Candidate lifecycle。

---

## 24. Minimal EvidenceSpecification Schema Proposal

### 24.1 EvidenceSpecification

```text
EvidenceSpecification:
- evidence_spec_id
- targets: list[EvidenceTarget]
- observation_requirements: list[str]
- provenance_requirements: list[str]
- context_requirements: list[str]
- qualification_requirements: list[str]
```

### 24.2 EvidenceTarget

```text
EvidenceTarget:
- test_case_id
- contract_id
```

这是Schema Proposal，不修改当前Frozen Benchmark / Requirement / Contract Schema，不修改TestCase Schema Proposal，也不规定YAML、JSON、Pydantic、目录、collector或Runtime serialization。

### 24.3 字段判断

| 候选字段 | v0决定 | 理由 |
|---|---|---|
| `evidence_spec_id` | 进入Schema，必填 | Evidence Specification是一等对象，需要稳定Definition-time identity |
| `test_case_id + contract_id` | 作为nested EvidenceTarget进入 | pair唯一定位当前ExpectedAssertion，无需新增assertion_id |
| `targets` | 进入Schema，非空列表 | 支持Concept Model的many-to-many复用，并避免两个独立ID列表的Cartesian ambiguity |
| `description` / `evidence_need` | 不单独进入 | `observation_requirements`已表达authoritative need；purpose与rationale留Audit，避免重复 |
| `observation_requirements` | 进入Schema，非空列表 | 定义目标判断必须可获得的observation semantics |
| `provenance_requirements` | 进入Schema，非空列表 | 定义source、origin、Episode / Artifact / participant identity等最低语义要求 |
| `context_requirements` | 进入Schema，必填列表，允许空 | 定义temporal、ordering、scope、before / after或interaction context；无额外context时显式空列表 |
| `qualification_requirements` | 进入Schema，非空列表 | 定义completeness、currentness、non-ambiguity等最低Evidence qualification expectations |
| `required / optional` | 不进入 | 每个Spec本身就是minimum required need；supporting observations留Audit / diagnostics |
| `evidence_type` / `category` | 不进入 | 当前只用于Design分类，没有稳定Framework behavior |
| `producer` | 不作为独立字段 | Semantic source与origin由provenance requirements表达；不提前绑定collector implementation |
| Artifact ID / Episode ID | 禁止进入 | Runtime identity尚不存在，不能Definition-time绑定 |
| actual value / path / message / trace | 禁止进入 | 属于Runtime Evidence、Artifact或Episode |
| grader reference | 不进入本轮 | Grader Specification尚未设计，不提前反向占位 |
| actual qualification status | 禁止进入 | 属于Runtime Evidence qualification result |

### 24.4 ID规则

推荐形式：

```text
ES001
ES002
ES003
```

规则：

- 在一个Benchmark Definition中唯一；
- 使用`ES`加至少三位十进制数字；
- 不要求跨所有Benchmarks全局唯一；
- observation semantics、targets、provenance、context或qualification发生重大变化时，应创建新ID；
- 被删除的ID不应在同一Benchmark lineage中复用于不同evidence need。

---

## 25. Schema Field Semantics

### 25.1 evidence_spec_id

非空string，表示Definition-time Evidence Specification identity。它不是Runtime Evidence ID。

### 25.2 targets

必填`list[EvidenceTarget]`，至少一项且pair不得重复。每个pair必须解析到当前validated Test Case中唯一的ExpectedAssertion contract reference。

Targets表示该Spec服务哪些ExpectedAssertions，不表示这些targets最终共享同一Grader或Result。

### 25.3 observation_requirements

必填`list[str]`，至少一项。每项描述必须可用的human-readable observation semantics，例如action occurrence、final Artifact content、interaction sequence或affected scope。

不得包含checker、field selector、path、runtime ID或actual observation。

### 25.4 provenance_requirements

必填`list[str]`，至少一项。每项描述qualification所需的semantic origin / identity / lineage，例如current Episode association、Subject-produced output identity或interaction participant identity。

不得填写actual Episode ID、Artifact ID、filepath或timestamp。

### 25.5 context_requirements

必填`list[str]`，允许空列表。每项描述判断所需的temporal、ordering、scope、before / after、attempt或interaction relation。

空列表表示该Spec没有超出observation与provenance本身的额外context requirement，不表示Runtime没有context。

### 25.6 qualification_requirements

必填`list[str]`，至少一项。每项描述observation成为qualified Evidence所需的最低completeness、currentness、integrity、non-ambiguity或transformation-lineage expectation。

它不能描述Contract PASS / FAIL，也不能定义Grader algorithm。

---

## 26. Runtime Evidence 与 Artifact Reference Boundary

Evidence Specification禁止保存：

- actual evidence value；
- actual filepath；
- actual log；
- actual model / user message；
- actual timestamp；
- actual screenshot；
- actual tool call；
- actual Artifact ID；
- actual Episode ID；
- actual qualification result；
- actual availability status。

Definition可以语义描述：

```text
最终Subject-produced output Artifact
当前Episode的relevant interaction history
operation前后的target state
```

不能预先写：

```text
artifact_id = A-123
episode_id = E-456
path = /run/output/result.json
timestamp = 2026-...
```

Runtime identity只能在Episode实际发生后建立。

---

## 27. Three-layer Evidence Specification Validation

### 27.1 A. Structural / Field Validation

未来可deterministic检查：

- `evidence_spec_id`符合`ES`+至少三位数字；
- Evidence Specification IDs在Definition中唯一；
- `targets`至少一项；
- EvidenceTarget包含非空`test_case_id`与`contract_id`；
- 同一Spec内EvidenceTarget pair不重复；
- `observation_requirements`是非空、条目非空且无完全重复的字符串列表；
- `provenance_requirements`是非空、条目非空且无完全重复的字符串列表；
- `context_requirements`是条目非空且无完全重复的字符串列表，允许空；
- `qualification_requirements`是非空、条目非空且无完全重复的字符串列表；
- 不存在actual Evidence、Artifact、Episode、Result或Grader implementation字段。

### 27.2 B. Cross-object Validation

需要完整Definition context：

- 每个target `test_case_id`存在；
- referenced Test Case已validated且属于当前Definition；
- 每个target `contract_id`存在并已validated；
- `contract_id`实际出现在该Test Case的`expected_assertions[].contract_id`中；
- 不引用invalid、draft-only、stale或其他Benchmark的对象；
- Coverage Mapping与Evidence Specification targets双向一致；
- 每个ExpectedAssertion pair在Coverage Mapping中恰好一行；
- 没有dangling Evidence Spec / Test Case / Contract refs；
- production Specs不引用validation-subset-only对象；
- Requirement → Contract → Test Case → Evidence Specification trace可恢复。

Cross-object validator可以证明pair与mapping一致，不能证明observation requirements真的足够。

### 27.3 C. Semantic Evidence Review

逐Spec至少检查：

- Evidence need是否真的支持每个target assertion；
- Outcome / Workflow evidence need是否匹配；
- observations是否principle-level sufficient；
- 是否minimum sufficient，还是过量收集；
- provenance是否明确且必要；
- temporal / ordering / scope relation是否在需要时表达；
- before / after state是否真正必要；
- interaction evidence是否覆盖相关turn、action与relation；
- multi-target共享是否合理；
- atomicity与split / merge是否合理；
- qualification expectations是否没有滑向Grading；
- missing Evidence是否没有被写成Contract failure；
- capture failure是否没有被归咎于Subject；
- 是否提前写Grader；
- 是否包含Runtime fields；
- 是否存在明显privacy、cost或storage overcollection；
- critical Contract的Evidence sufficiency是否完成加强review。

Semantic Review需要Agent / Human judgment，不能伪装成Schema validation。

---

## 28. ExpectedAssertion → Evidence Specification Coverage

Coverage Mapping是轻量working artifact，不是Core Object，也不是Frozen EvidenceSpecification Schema的一部分。

建议至少记录：

| 字段 | 含义 |
|---|---|
| `test_case_id` | Validated Test Case ID |
| `contract_id` | 该Case中唯一ExpectedAssertion的Contract ID |
| `evidence_spec_ids` | 引用该target pair的Evidence Specification IDs |
| `coverage_status` | `COVERED`或`BLOCKED` |
| `rationale` | 为什么这些Specs形成minimum sufficient coverage，或为什么被阻塞 |

只有满足以下条件才能标记`COVERED`：

- 至少一个valid Evidence Specification引用该target pair；
- combined observation requirements足以支持目标assertion；
- provenance、context与qualification requirements合理；
- atomicity / shared-split review通过；
- semantic validation通过；
- 不是仅靠ID linkage；
- critical Contract完成更严格sufficiency review。

例如以下情况必须`BLOCKED`：

- assertion无法定义principle-level sufficient observations；
- required observation原则上不可获得；
- provenance无法确定；
- temporal / scope relation无法建立；
- Evidence need依赖未定义Runtime assumption；
- Spec越界进入Grader；
- minimum coverage gap；
- critical Contract的关键observation surface遗漏。

不得用coverage percentage或Spec数量掩盖一个blocking pair。

---

## 29. Evidence Specification Design Issues 与 Rollback

至少区分：

- upstream Contract observability issue；
- upstream Test Case exercise / interaction issue；
- Evidence sufficiency issue；
- Evidence minimality / overcollection issue；
- provenance issue；
- temporal / context issue；
- qualification issue；
- atomicity / granularity issue；
- coverage issue；
- shared / split issue；
- Schema insufficiency；
- downstream Grader concern；
- environment / capture limitation。

Rollback：

```text
Contract success / failure semantics无法形成可观察事实
→ Contract Design lifecycle

Scenario没有真正exercise responsibility
→ Test Case Design lifecycle

需要什么observations、provenance或context不清楚
→ Evidence Specification Design内修订

Observations原则上存在，但如何判断不清楚
→ Downstream Grader Design Concern

Capture mechanism原则上无法提供required observation
→ Evidence Producer / Execution Design Concern
```

不得为方便Evidence collection或Grader而降低、加强Contract semantics，也不得直接修改upstream Guides。

---

## 30. Evidence Specification Design Workflow

### Step 1 — Verify Inputs

- 验证Requirements、Contracts、Test Cases、ExpectedAssertions与status；
- production input不满足Entry Gate时立即BLOCK；
- method validation subset保留限定边界。

### Step 2 — Build Assertion Inventory

- 以`(test_case_id, contract_id)`列出每个ExpectedAssertion；
- 读取Contract criteria、failure modes、evaluation_type与criticality；
- 读取Case trigger、state、fixtures与interaction；
- 不重新设计Contract或Case。

### Step 3 — Draft Evidence Needs

- 识别required observations；
- 区分Outcome与Workflow surfaces；
- 识别provenance、temporal、scope、before / after与qualification需要；
- 使用Working Drafts比较alternate packages。

### Step 4 — Run Sufficiency and Minimality Review

- 确认compliant / violating semantics原则上可区分；
- 删除仅用于debugging或future convenience的overcollection；
- 对critical targets执行加强review。

### Step 5 — Run Atomicity and Sharing Review

- 决定一个target需要1→N Specs还是多个targets共享1 Spec；
- 拆分不同provenance、context或qualification surfaces；
- 合并真正不可分的observation package；
- 避免Maximum Fragmentation与Maximum Integration。

### Step 6 — Write Evidence Specifications

- 分配正式`ESxxx`；
- 写targets；
- 写observation、provenance、context与qualification requirements；
- 不写Runtime IDs、actual Evidence或Grader implementation。

### Step 7 — Build Coverage and Audit

- 每个ExpectedAssertion pair建立Coverage row；
- 记录sufficiency、minimality与shared / split rationale；
- 保留upstream、capture与downstream concerns。

### Step 8 — Validate

- Structural / Field Validation；
- Cross-object Validation；
- Semantic Evidence Review；
- unresolved issue进入Evidence Specification Design Issues。

### Step 9 — Determine Status

- 所有ExpectedAssertions获得minimum sufficient Evidence Specification coverage且validation通过时READY；
- 任一required target BLOCKED时整体BLOCKED；
- 生成必需outputs并停止，不进入Grader Design。

---

## 31. Evidence Specification Design Status

Production状态只保留：

```text
EVIDENCE_SPECS_READY
EVIDENCE_SPECS_BLOCKED
```

### 31.1 EVIDENCE_SPECS_READY

只有同时满足：

- authoritative upstream Definition当前有效；
- Test Case Design为`TEST_CASES_READY`；
- 每个ExpectedAssertion pair拥有minimum sufficient Evidence Specification coverage；
- Outcome与Workflow needs正确区分；
- provenance、context与qualification requirements充分；
- critical targets完成加强review；
- 所有Specs通过三层validation；
- Coverage Mapping、Spec Set与Audit一致；
- 没有unresolved Evidence Design Issue；
- 没有提前设计Grader、Metric或Gate。

### 31.2 EVIDENCE_SPECS_BLOCKED

例如：

- assertion无法定义可获得的sufficient observations；
- provenance无法确定；
- required observation原则上无法合理取得；
- temporal / scope context无法建立；
- Spec依赖未定义Runtime assumption；
- Spec把capture mechanism与Subject responsibility混合；
- Evidence need越界进入Grader；
- coverage gap；
- validation failure。

状态不是quality score：

```text
99% targets COVERED + 1 blocking gap
= EVIDENCE_SPECS_BLOCKED
```

Method Validation Subset使用5.3节的完整限定status wording，不改变production status model。

---

## 32. Required Outputs

Evidence Specification Design至少产生：

1. **Evidence Specification Set**：使用Proposed Schema的正式Definition-time Specs；
2. **ExpectedAssertion → Evidence Specification Coverage Mapping**：逐target pair的semantic coverage；
3. **Evidence Specification Design Audit**：sufficiency、minimality、provenance、context、qualification与shared / split rationale；
4. **Evidence Specification Design Issues**：blocking issues与upstream / capture / downstream concerns；
5. **Evidence Specification Validation Summary**：Structural、Cross-object、Semantic三层结果；
6. **Evidence Specification Design Status**：`EVIDENCE_SPECS_READY`或`EVIDENCE_SPECS_BLOCKED`；
7. **Schema Design Findings**：只记录真实design暴露的schema need。

Working Evidence Spec Drafts不是必需final output，也不算Coverage。

---

## 33. Evidence Specification 与 Grader Boundary

Evidence Specification允许：

> 需要观察actual affected scope与authorized scope，并保留二者属于同一操作的context。

禁止：

> 比较`trace.delete.path`是否位于`authorized_paths`中。

Evidence Specification允许：

> 需要观察最终Artifact的结构化semantic content与current Episode identity。

禁止：

> 使用某JSON Schema validator、JSONPath或assertion code检查字段。

Evidence Specification定义：

```text
What observations must be available?
```

Grader定义：

```text
How are qualified observations judged?
```

如果authoritative Requirement本身规定某种validator或格式，该事实可以保留为normative observation need；但如何执行validator、解释结果与形成判断仍属于Grader / Runtime Design。

---

## 34. Schema Design Findings

### 34.1 EvidenceTarget pair

`(test_case_id, contract_id)`能够唯一定位当前Test Case中的ExpectedAssertion，因为同一Case内同一Contract最多一项assertion。无需增加ExpectedAssertion ID。

Nested pair支持many-to-many共享，并避免独立`test_case_ids`与`contract_ids`列表产生Cartesian ambiguity。

### 34.2 Observation / Provenance / Context / Qualification分离

四组字段分别回答：

- what must be observed；
- where / from whom / which Episode relation it must come；
- what temporal / scope / before-after relation must be preserved；
- what minimum completeness / identity / non-ambiguity makes it qualified。

它们是Evidence Specification作为Definition / Runtime interface的最小独立语义，不是Grader fields。

### 34.3 No required / optional enum

Evidence Specification本身定义minimum required evidence。Optional / supporting observations没有当前authoritative Framework行为，留在Audit或Runtime diagnostics。

### 34.4 No evidence category enum

Outcome、interaction、ordering、Artifact、scope等categories可以重叠，当前只帮助Design Review，不进入Schema。

### 34.5 No producer implementation field

Source / origin semantic expectation由`provenance_requirements`表达。具体collector、script、trace recorder或capture mechanism属于后续Execution Design，不进入本轮Schema。

### 34.6 No Runtime identity fields

Evidence Specification不保存Episode ID、Artifact ID、actual path、timestamp、value、availability或qualification result。Definition只声明未来identity / association必须可证明。

---

## 35. Method Self-Review

| 检查问题 | v0结论 |
|---|---|
| 1. Evidence Specification和Evidence是否清楚？ | 是。前者是Definition-time need，后者是Runtime qualified observation。 |
| 2. Artifact和Evidence是否清楚？ | 是。Artifact是runtime object；只有被选取、资格确认并关联目标的内容才可能成为Evidence source。 |
| 3. Test Case与Evidence Spec边界是否清楚？ | 是。Case构造scenario；Spec定义判断该scenario中assertion所需observations。 |
| 4. Evidence Spec与Grader边界是否清楚？ | 是。Spec写what observations；Grader写how to judge，禁止checker与算法。 |
| 5. Outcome / Workflow evidence needs是否稳定？ | 是。Outcome关注final content/state/handoff；Workflow关注occurrence/order/authorization/tool/recovery等。 |
| 6. Evidence Sufficiency是否可判断？ | 是。逐target检查facts、trigger、action、order、scope、identity与before/after。 |
| 7. Minimality是否能防过度收集？ | 是。只保留minimum required observations，debugging/supporting内容不进入authority。 |
| 8. Provenance是否有最小要求？ | 是。要求source、origin、Episode association、identity与必要lineage semantics。 |
| 9. Temporal / order evidence是否可表达？ | 是。通过context requirements表达semantic event relation，不写timestamp或trace schema。 |
| 10. Interaction evidence是否可表达？ | 是。可要求initial turn、Subject trigger behavior、response、later action与ordering/scope observations。 |
| 11. Missing Evidence是否不会自动变FAIL？ | 是。absence of Evidence与observed violation明确分离。 |
| 12. Capture failure是否不会误归Subject？ | 是。Evaluator/infrastructure failure与Subject responsibility分开。 |
| 13. Multi-Contract Case是否支持shared / split evidence？ | 是。Targets支持共享，Atomicity Test按provenance/context/qualification决定拆分。 |
| 14. Evidence atomicity是否可执行？ | 是。检查独立缺失、collection surface、provenance、qualification与diagnosis。 |
| 15. 是否需要required / optional distinction？ | 当前不需要。Spec就是minimum required；supporting observations留Audit。 |
| 16. 是否需要Evidence Spec Candidate？ | 当前不需要mandatory Candidate；Working Draft + Audit足够。 |
| 17. 是否需要Design Audit？ | 需要非Core Audit保存sufficiency、minimality、atomicity与overcollection rationale。 |
| 18. 最小Schema是什么？ | ES ID、EvidenceTarget pairs、observation、provenance、context与qualification requirements。 |
| 19. ExpectedAssertion没有ID是否造成真实关联问题？ | 当前没有。Test Case内唯一`contract_id`使pair可唯一定位assertion。 |
| 20. 是否出现target-specific assumption？ | 未发现。方法适用于coding、browser、research、file、tool-use、conversational、multi-turn与data-processing Skills。 |
| 21. 哪些问题必须真实validation？ | Field adequacy、pair target authoring、shared-spec复用、atomicity、minimality、interaction evidence、provenance表达与reviewer consistency。 |

### 35.1 Self-review corrections incorporated

本轮自审已经在正文中处理：

- 为避免Artifact自动等于Evidence，增加qualification与provenance boundary；
- 为避免ID coverage假充Evidence coverage，增加Sufficiency gate；
- 为避免两个ID列表产生pair ambiguity，引入nested EvidenceTarget；
- 为避免新增ExpectedAssertion ID，使用现有局部唯一pair；
- 为避免全Episode过度收集，增加Minimum Sufficient Evidence；
- 为避免Workflow被final Outcome假覆盖，分开Outcome / Workflow needs；
- 为避免ordering滑向trace实现，限制为semantic context relation；
- 为避免missing Evidence误判Subject FAIL，固定capture / violation boundary；
- 为避免Spec explosion，增加Atomicity与shared / split review；
- 为避免optional observation弱化authority，不增加required / optional enum；
- 为避免Audit成为第二套authority，所有targets只以Schema为准。

### 35.2 Method Validation Coverage Needed

在冻结EvidenceSpecification Schema前，至少需要真实validation检查：

- simple final Outcome Artifact Case；
- structured output content Case；
- Workflow action occurrence / ordering Case；
- multi-turn authorization Case；
- destructive scope before / after Case；
- handoff Case；
- one assertion → multiple Specs；
- multiple assertions → one genuinely shared Spec；
- provenance ambiguity反例；
- missing / incomplete Evidence边界；
- minimum evidence与overcollection对比；
- EvidenceTarget pair authoring与Coverage反向生成。

这些是future validation coverage，不应被误报为Runtime Evidence、Grader或execution PASS。

---

## 36. Final Decision Checklist

### Inputs

- [ ] Production input使用authoritative Frozen Requirements、validated Contracts与validated Test Cases
- [ ] Test Case Design Status为`TEST_CASES_READY`
- [ ] Inputs没有stale或unresolved upstream issue
- [ ] Method validation subset保留validation-only boundary与限定status

### Target Mapping and Coverage

- [ ] 每个EvidenceTarget pair解析到真实ExpectedAssertion
- [ ] ExpectedAssertion authority仍在TestCase中
- [ ] 没有新增assertion ID或Cartesian ID lists
- [ ] 每个ExpectedAssertion获得principle-level sufficient coverage
- [ ] Coverage不只是ID linkage
- [ ] Critical targets完成加强review

### Sufficiency and Minimality

- [ ] Required facts、action、order、scope或state可被观察
- [ ] Compliant与violating semantics原则上可区分
- [ ] 没有收集整个Episode作为默认策略
- [ ] Debugging / future-convenience data没有进入minimum authority
- [ ] 没有明显privacy、cost或storage overcollection

### Provenance and Context

- [ ] Current Episode association可建立
- [ ] Source / participant / Artifact identity requirements明确
- [ ] Temporal / ordering / scope relation在需要时表达
- [ ] Before / after只在必要时要求
- [ ] Interaction Evidence覆盖相关turn与later action context

### Qualification and Failure Boundaries

- [ ] Completeness、staleness、ambiguity与lineage expectations明确
- [ ] Missing Evidence没有被写成Contract failure
- [ ] Capture failure没有被归咎于Subject
- [ ] Qualification没有滑向Grading

### Granularity and Audit

- [ ] Atomicity Test完成
- [ ] Shared / split decision有rationale
- [ ] 没有Maximum Fragmentation / Integration
- [ ] Audit没有成为第二套authority
- [ ] 不引入mandatory Candidate

### Definition Boundaries

- [ ] 没有actual Evidence、Artifact、Episode、message、trace、path或timestamp
- [ ] 没有regex、JSONPath、checker、judge prompt、threshold或comparison algorithm
- [ ] 没有Grader、Metric、Weight、Score或Gate design
- [ ] 没有Runtime collector或validator implementation

### Validation and Status

- [ ] Structural / Field Validation完成
- [ ] Cross-object Validation完成
- [ ] Semantic Evidence Review完成
- [ ] Spec Set、Coverage Mapping与Audit一致
- [ ] 无unresolved Evidence Design Issue
- [ ] Production status只使用`EVIDENCE_SPECS_READY`或`EVIDENCE_SPECS_BLOCKED`

全部必需检查通过时，production Evidence Specification Design才可输出：

```text
EVIDENCE_SPECS_READY
```

否则输出：

```text
EVIDENCE_SPECS_BLOCKED
```

并停止在Evidence Specification Design边界，不开始Grader、Metric、Gate或Runtime implementation。
