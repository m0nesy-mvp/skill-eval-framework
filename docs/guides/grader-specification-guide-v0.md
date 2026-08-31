# 《Grader Specification 设计指南 v0》

Status: Design Guide

本文定义从 authoritative Frozen Requirements、validated Contracts、validated Test Cases 与 validated Evidence Specifications 到 Grader Specification 的通用设计方法。它适用于通用 Agent Skill Eval，不绑定特定 Skill、平台、工具、Artifact 格式、执行器或判断实现。

本文提出最小 GraderSpecification Schema Proposal，但不修改已经冻结的 Requirement、Contract、Test Case、Evidence Specification、Concept Model 或其他 Schema，不实现 Runtime，不开始 Metric 或 Gate Design，也不编写 concrete checker。

---

## 1. Grader Specification 的角色

Grader Specification 回答：

> 应如何根据目标 Contract 语义判断合格 Evidence？

它是 Definition-time first-class object，预先冻结：

- judgment target；
- 必需 Evidence Specification 输入；
- 忠实于 Contract 的 judgment criteria；
- satisfied、violated、insufficient 与适用时 not-exercised 的 semantic meaning；
- qualitative judgment需要时的Rubric policy；
- Evidence不足时停止substantive judgment的原则；
- Grader Result应提供的explanation语义。

Grader Specification 不负责：

- 保存actual Evidence；
- 保存actual PASS / FAIL或其他实际judgment；
- 保存actual explanation、failure diagnosis或score；
- 运行Episode；
- 收集或qualify Evidence；
- 选择Runtime collector；
- 编写regex、JSONPath、exact matcher、code function或judge prompt；
- 聚合多个Grader Results；
- 定义Metric、Weight、Benchmark score或Gate；
- 决定critical failure是否阻断整个Benchmark。

---

## 2. Grader Specification 与 Grader Result

Concept Model 已冻结：

```text
Grader Specification
= Definition-time judgment policy

Grader Result
= Runtime application of that policy to qualified Evidence
```

Grader Specification 描述：

- 对哪些 ExpectedAssertions 采用什么 judgment semantics；
- 每个target必须消费哪些Evidence Specifications；
- 什么Evidence relation支持satisfied或violated；
- Evidence不足时为什么不得形成substantive verdict；
- future result应解释哪些semantic basis。

Grader Result 描述：

- 某次Run / Episode实际应用了哪个Grader Specification；
- 实际消费了哪些qualified Evidence；
- 实际判断了哪个Contract-specific target；
- 实际得到什么judgment；
- 实际 explanation、failure diagnosis、insufficiency reason或Grader error是什么。

因此Grader Specification中禁止保存：

- actual Episode ID；
- actual Evidence ID或value；
- actual verdict；
- actual rationale；
- 实际 失败 mode attribution；
- 实际 Rubric anchor 选择；
- actual local score；
- actual Runtime error。

---

## 3. Contract 与 Grader 的边界

Contract 回答：

> 什么情况算满足或违反 Requirement？

Grader Specification 回答：

> 如何解释合格的观察结果，以决定本 Episode 是否满足或违反已定义语义？

Grader Specification 必须忠实消费：

- Contract statement；
- success criteria；
- failure criteria；
- failure modes；
- evaluation type；
- applicability / trigger semantics；
- Test Case ExpectedAssertion 上下文。

它不得：

- 修改Contract；
- 新增normative responsibility；
- strengthen或weaken success criteria；
- 把failure mode升级为新failure requirement；
- 用容易实现的proxy替代Contract semantics；
- 因Evidence难以获得而降低判断标准；
- 因criticality而增加来源未规定的violation。

如果Contract无法形成清楚judgment，应按原因回退：

```text
Contract semantics ambiguous or internally inconsistent
→ Contract Design lifecycle

Required facts are not observable or qualified
→ Evidence Specification / Evidence qualification concern

Evidence facts exist but their semantic relation is not yet articulated
→ Grader Specification Design
```

不得由Grader临时发明规则填补upstream gap。

---

## 4. Evidence Specification 与 Grader 的边界

Evidence Specification 回答：

> 必须能够观察到什么？

Grader Specification 回答：

> 如何根据 Contract 语义解释这些合格的观察结果？

允许的Grader-level表达：

> 判断authorization observation与destructive-action observation是否属于同一次operation，并判断authorization是否先于action。

Evidence Specification阶段只负责要求same-operation与ordering information可用，不负责形成上述judgment。

Grader Specification必须消费qualified Evidence，而不是直接消费任意Artifact、raw Trace或未qualification的captured data。Artifact存在、log存在或字段可读取都不自动等于可进行substantive grading。

---

## 5. Grader Specification 与 Concrete Checker

Grader Specification可以声明semantic grading rule，例如：

> 实际影响范围必须保持在已授权范围内。

它不应写成：

```python
set(actual_paths).issubset(set(authorized_paths))
```

Specification level允许：

- equality、containment、ordering、identity、correspondence等semantic relation；
- required semantic elements是否存在；
- observations是否共同支持Contract success或failure semantics；
- qualitative dimensions与anchors；
- absence-of-event reasoning所需的完整性前提。

Concrete implementation level包括：

- code function；
- library call；
- regex；
- JSONPath；
- exact event index；
- trace field selector；
- timestamp comparison code；
- prompt 模板 / system prompt；
- model name与temperature；
- database query；
- filesystem traversal algorithm；
- executable matcher或threshold implementation。

如果authoritative Requirement本身规定特定validator、格式或标准，该规范事实可以进入judgment criteria；如何调用工具、解析输出和执行comparison仍属于后续implementation。

---

## 6. Authoritative Inputs 与 Entry Gate

### 技术主题：6.1 Production inputs

Production Grader Specification Design必须消费：

1. 权威 Frozen Requirement Set；
2. validated Contract Set；
3. 已验证 Test Case Set；
4. valid ExpectedAssertions；
5. 已验证 Evidence Specification Set；
6. ExpectedAssertion → Evidence Specification 覆盖映射；
7. Contract success criteria、failure criteria与failure modes；
8. Contract `evaluation_type`与`criticality`；
9. Test Case task、initial state、fixtures、interaction steps与expectation；
10. Evidence observation、provenance、context与qualification requirements；
11. 相关 upstream Design Audits when needed。

Audit只帮助理解既有decision，不得成为新的normative authority。

### 6.2 Production 入口门禁

只有以下条件全部满足，才能开始production Grader Specification Design：

- Evidence Specification Design Status为`EVIDENCE_SPECS_READY`；
- Requirements、Contracts、Test Cases与Evidence Specifications当前有效且没有stale；
- ExpectedAssertion target pairs可解析；
- EvidenceTarget coverage完整；
- 没有unresolved upstream semantic blocker；
- 所有对象属于同一个有效Definition context。

任一条件不满足时：

```text
Grader Specification Design Status = GRADERS_BLOCKED
```

不得用Grader wording修补Contract ambiguity、Test Case exercise gap或Evidence insufficiency。

### 6.3 Method 验证 Subset

如果上游状态是完整限定的：

```text
EVIDENCE_SPECS_READY for validation subset
```

Grader method validation可以使用同一validation-local Requirements、Contracts、Test Cases与Evidence Specifications，但必须：

- 只用于method validation、Schema adequacy research或review；
- 不进入production Benchmark Definition；
- 不形成authoritative complete Grader Specification Set；
- 不进入production Metric或Gate Design；
- 不绕过任何benchmark-wide upstream blocker；
- 不宣称完整Target的Graders READY。

Subset状态必须完整写成：

```text
GRADERS_READY for validation subset
```

或：

```text
GRADERS_BLOCKED for validation subset
```

Grader Method Validation Subset不是Core Object，也不是production lifecycle state。

---

## 7. Grader Target 与关系 Authority

当前ExpectedAssertion没有独立ID，但同一Test Case内同一`contract_id`最多出现一次。因此：

```text
(test_case_id, contract_id)
```

能够在Definition context中唯一定位一个ExpectedAssertion。

Grader Specification使用独立nested type：

```text
GraderTarget:
- test_case_id
- contract_id
- evidence_spec_ids
```

它与EvidenceTarget语义不同：

- EvidenceTarget表示某Evidence Specification服务哪个ExpectedAssertion；
- GraderTarget表示某Grader policy应用于哪个ExpectedAssertion，并冻结该target消费哪些Evidence Specifications。

规则：

- pair必须解析到Test Case的`expected_assertions[].contract_id`；
- ExpectedAssertion仍是Test Case → Contract relation的唯一authority；
- GraderTarget不得创建新的Test Case → Contract relation；
- 不增加ExpectedAssertion ID；
- `evidence_spec_ids`是该target的显式Evidence consumption authority，不是新的EvidenceTarget authority。

---

## 8. 技术主题：Evidence Consumption Model

Concept Model要求每个Grader Specification明确其Evidence Specification依赖。v0不采用“运行时自动拿所有看起来相关Evidence”的隐式模型。

每个GraderTarget必须显式保存：

```text
evidence_spec_ids: list[str]
```

因为一个Grader Specification可以应用到多个targets，不使用单一top-level `evidence_spec_ids`；否则无法确定某份Evidence Specification服务哪个target，并可能产生Cartesian ambiguity。

对每个target，`evidence_spec_ids`必须：

- 非空；
- 无重复；
- 全部存在且validated；
- 每个Evidence Specification的targets包含同一pair；
- 覆盖该ExpectedAssertion的完整minimum required Evidence Specification set；
- 不省略Cross-Spec Composition所需的任一Spec；
- 不加入只用于debugging或与target无关的Spec；
- 不引用其他Test Case、其他Contract或其他Definition中的Spec。

核心原则：

```text
Explicit evidence consumption
≠ arbitrary evidence selection
```

Grader可以消费多个Evidence Specifications，一份Evidence Specification也可以被多个Grader targets复用；复用不表示它自动适用于所有judgments。

---

## 9. 技术主题：Evidence Sufficiency Before Judgment

Grader进行Contract semantic judgment前，必须先确认required Evidence inputs在本次Episode中具有合法判断基础。

至少区分：

```text
Evidence sufficient for substantive judgment

Evidence insufficient for substantive judgment
```

如果任一required evidence contribution：

- missing；
- incomplete；
- corrupted；
- incompatible；
- provenance不明；
- qualification失败；
- cross-Spec relation无法建立；

则Grader不得根据剩余片段伪造satisfied或violated判断，除非Contract semantics与本Grader criteria明确证明缺失部分对当前特定判断不再必要；这种情况应首先回查Evidence Specification minimality，而不能由Runtime临时选择。

Evidence sufficiency check不是Contract verdict，也不是Grader error。

### 基线 insufficiency authoring template

每个`insufficiency_handling`应只选择该target真实相关的项目，至少检查：

1. required Evidence Specification是否缺失；
2. Evidence虽然存在但是否unqualified、incomplete或corrupted；
3. required cross-Evidence semantic relation是否无法建立；
4. provenance、participant、Artifact或operation identity是否有歧义；
5. relevant observation interval或surface是否不完整；
6. Evaluator / capture mechanism是否发生关键failure；
7. Grader execution failure是否被错误吞入Evidence insufficiency。

这是authoring checklist，不是Frozen enum，也不要求每个Spec机械复制全部七项。Spec只保留会真实阻止该target形成substantive judgment的边界。

### 技术主题：Evidence insufficiency vs Grader execution failure

```text
Required qualified Evidence unavailable or unusable
→ Evidence insufficiency

Qualified Evidence complete,
but checker / LLM judge / Human evaluation process fails
→ future Grader execution status
```

后者不是`insufficient_evidence`，因为输入Evidence本身并不不足。Grader Specification不得使用insufficiency meaning掩盖implementation、judge invocation、review process或Runtime failure；本Guide不因此设计Runtime error enum。

---

## 10. 技术主题：Judgment Semantics

Grader Specification的judgment criteria必须把qualified Evidence中的事实与Contract已经冻结的语义相连。

每项criteria至少应说明：

- 使用哪些semantic observations；
- 需要建立什么relation；
- 该relation支持Contract satisfied、violated、insufficient或not-exercised中的哪种meaning；
- 哪些前提必须完整，特别是absence-of-event reasoning；
- 为什么没有增加或削弱Contract responsibility。

较弱表达：

> 检查authorization。

较稳定表达：

> 当目标operation实际发生时，判断qualified interaction evidence是否建立针对同一operation的有效authorization，并判断该authorization是否先于operation。

禁止写：

> 查找event[4]，比较timestamp并返回1或0。

---

## 11. 技术主题：Satisfied / Violated / Insufficient / Not Exercised

本Guide不冻结完整Runtime Grader Result enum，但Definition-time result semantics必须清楚区分至少以下meaning。

### 技术主题：11.1 Satisfied

只有qualified Evidence提供affirmative basis，能够建立Contract success criteria要求的semantic facts与relations时，才支持satisfied meaning。

```text
Satisfied
≠ no failure observed
```

Authoring question：

> 哪些合格事实可以明确建立 Contract 成功语义？

### 技术主题：11.2 Violated

只有qualified Evidence提供affirmative basis，能够建立Contract failure criteria描述的真实violation时，才支持violated meaning。

```text
Violated
≠ no proof of success
```

Authoring question：

> 哪些合格事实可以明确建立 Contract 失败语义？

### 技术主题：11.3 Insufficient Evidence

Required Evidence缺失、无资格、不完整或关键relation不可建立时，应停止substantive judgment并使用insufficiency meaning。

```text
Insufficient Evidence
≠ Violated
```

Authoring question：

> 哪些缺失、无效或未解决的 Evidence contribution 或 relation 会阻止形成任一实质结论？

### 技术主题：11.4 Not Exercised

Not Exercised只有在以下条件全部满足时才可使用：

1. Episode确实存在，并产生了足够qualified Evidence；
2. 目标Contract具有真实applicability / trigger condition；
3. Evidence能够affirmatively establish该condition在本Episode中没有发生；
4. 因此目标responsibility没有进入可评价状态。

```text
Not Exercised
≠ Satisfied
≠ Insufficient Evidence
≠ Case blocked
≠ Episode not executed
≠ Subject task noncompletion
```

“目标动作没有发生”不自动支持not-exercised。它还可能表示：

- trigger已经发生，但Subject没有履行required action；
- Subject stopped early；
- Case / task execution没有完成；
- Evidence不完整；
- Contract failure criterion已经成立；
- 或trigger确实没有发生。

必须先读取Contract的trigger semantics，再决定absence属于violated、insufficient、not-exercised或future Case / Episode lifecycle concern。

以下状态不由Grader Specification重新定义：

- Case未调度；
- Episode未创建；
- Runtime启动失败；
- environment precondition阻塞；
- Grader engine自身错误。

它们属于未来Run / Episode / Runtime Result lifecycle边界。Grader不能把“没有Episode”解释为not-exercised，也不能把Grader error解释为insufficient Evidence。

### 技术主题：11.5 Trigger vs Required Action

Contract trigger / applicability condition与Subject required action必须严格分开：

```text
When condition X occurs,
Subject must perform action Y.

Complete Evidence establishes X occurred,
but Y did not occur
→ potential violated meaning

Complete Evidence establishes X did not occur
→ potential not-exercised meaning

Evidence cannot establish whether X occurred
→ insufficient Evidence
```

这条规则适用于conditional Workflow、conditional Outcome、authorization、retry / recovery、cleanup、handoff与optional-branch responsibilities。

不得把“没有观察到required action Y”直接当作“trigger X没有发生”。

### 技术主题：11.6 Case / Task Noncompletion Boundary

Subject没有完成整个Test Case task，不直接决定任一target Contract verdict。每个target仍须独立判断：

- Contract trigger是否发生；
- target responsibility是否已经适用；
- required Evidence是否完整；
- success或failure semantics是否得到affirmative support。

可能同时出现：

```text
Case overall not completed
+ one Contract already violated

Case overall not completed
+ another Contract not exercised

Case overall not completed
+ another Contract has insufficient Evidence
```

Grader Specification不定义Case overall execution status。Case未完成、Subject stopped early或Episode lifecycle状态由未来Episode / Runtime层处理，不能被压缩成单一target的not-exercised meaning。

---

## 12. Positive Evidence、Negative Evidence 与 Complete Observation Surface

某些judgments依赖affirmative compliance evidence，例如：

```text
authorization request
→ valid confirmation
→ same-operation action
```

某些violations依赖affirmative violation evidence，例如：

```text
action occurred
+ complete relevant interaction interval
+ no valid authorization before action
```

### 技术主题：12.1 Complete Observation Surface / Interval Principle

如果Grader使用某个object、event、action或interaction“没有出现”作为satisfied或violated basis，必须先确认：

1. relevant observation source被完整覆盖；
2. relevant temporal interval完整；
3. relevant participants、resources与Artifact identities明确；
4. relevant provenance完整；
5. capture没有关键gap；
6. target fact不会合理发生在未覆盖的alternative surface；
7. qualification足以支持absence inference；
8. absence与当前Episode、operation或attempt正确关联。

如果interaction、Trace或action interval不完整：

```text
event not observed
≠ event did not occur
```

也就是：

```text
Absence of observation
≠ observation of absence
```

Grader Specification必须在judgment criteria或insufficiency handling中写明所需completeness语义，但不得规定具体trace schema或event matcher。

推荐表达：

> 在 X 的缺失可以支持 Contract 失败语义前，合格 Evidence 必须建立完整且相关的观察区间。

避免：

> 如果未找到 X，则标记为 violated。

### 12.2 Artifact Absence 检查清单

在“required Artifact不存在”可以支持violation前，至少检查：

- correct target identity已知；
- current Episode / operation已知；
- expected location或output surface已知；
- observation surface完整可用；
- collector / capture mechanism没有关键failure；
- historical、intermediate或同名Artifact不会造成混淆；
- qualification足以确认真实absence。

```text
Evidence object unavailable
≠ Artifact did not exist
```

### 12.3 Action Absence 检查清单

在“Subject没有执行required action”可以支持violation前，至少检查：

- action responsibility已经由Contract trigger激活；
- relevant action surface被完整观察；
- relevant interval完整；
- action identity与operation context明确；
- capture没有关键gap；
- absence不是因为Case从未进入applicable branch。

否则应根据真实原因进入insufficient、not-exercised或future Case / Episode lifecycle concern，而不是机械FAIL。

### 12.4 Interaction Absence 检查清单

在“Subject没有请求确认、没有响应或没有进行required interaction”可以支持violation前，至少检查：

- relevant participant identities；
- relevant interaction interval；
- initial trigger context；
- conversation continuity；
- interaction capture completeness；
- current-operation association。

如果turn recorder有关键gap：

```text
Subject request not observed
≠ Subject did not request
```

这些checklists定义semantic completeness，不引入event index、timestamp comparison、log parser或Runtime matcher。

---

## 13. 技术主题：Temporal Judgment

Workflow Contracts经常依赖：

```text
A before B
A after C
retry after failure
cleanup after completion
handoff after final write
```

Grader Specification可以定义：

- relevant events的semantic identity；
- 同一操作 / 同一 attempt 关系；
- before、after、during或continuation relation；
- 哪个ordering支持satisfied或violated semantics；
- ordering Evidence不足时停止判断。

它不得规定：

- timestamp format；
- event index；
- trace field；
- comparison function；
- executable ordering matcher。

Temporal judgment必须利用Evidence Specification已要求的`context_requirements`，不能要求Runtime临时产生未在Evidence Design中声明的新context。

---

## 14. Scope 与 Identity Judgment

Grader Specification可以定义semantic relations，例如：

- 实际影响保持在授权范围内；
- reported 对象 身份 corresponds to 实际 produced Artifact；
- 最终文件名 身份 与重命名后的组件 身份 对应；
- 受影响资源只对应目标资源；
- 当前 输出 身份 与历史 输出 身份 不同。

Equality、subset / containment、correspondence与identity match在Specification中可以作为semantic relation出现。它们变成具体set operation、path normalization、string comparison或ID lookup时，才进入checker implementation。

Boundary rule：

```text
Specify the semantic relation that must hold.
Do not specify the executable procedure that computes it.
```

---

## 15. 技术主题：Structured Output Grading

对structured Artifact，Grader Specification可以判断：

- required semantic elements是否存在；
- required block是否完整；
- identity是否一致；
- required relations是否保持；
- final Artifact与intermediate declaration是否正确区分；
- content是否符合Contract规定的semantic format。

不得：

- 因每个字段都可检查就机械创建一个Grader；
- 在Grader中新增Contract未规定的field；
- 把一个validator的默认规则当成Contract semantics；
- 写JSONPath、schema call或field-by-field checker；
- 把Artifact parse failure自动当Contract violation，而不先区分Evidence qualification。

Contract atomicity仍然约束Grader granularity。多个criteria共同描述同一个atomic Contract时，可以由一个Grader Specification整体判断。

---

## 16. Deterministic 与 Semantic Grading

### 技术主题：16.1 Clearly deterministic semantics

常见包括：

- Artifact existence；
- required element presence；
- exact semantic identity；
- ordering relation；
- scope containment；
- explicit action occurrence；
- required handoff occurrence。

“deterministic”描述judgment relation原则上可以稳定决定，不等于本Guide已经选择了具体checker。

### 技术主题：16.2 Semantic / qualitative semantics

常见包括：

- answer correctness；
- relevance；
- explanation quality；
- instruction fidelity；
- nuanced policy compliance；
- user-facing usefulness。

Qualitative Grader Specification必须给出bounded、Contract-faithful criteria或Rubric，不能只写：

> 判断输出是否良好。

### 技术主题：16.3 Grader type taxonomy decision

v0不在Schema中增加`grader_type` enum。

理由：

- deterministic / semantic描述judgment semantics；
- program / Human / LLM / mixed描述可能的execution actor；
- 同一semantic policy可能由不同actor实现；
- 当前没有稳定Framework behavior要求用type字段改变Result semantics；
- `rubric`是否存在已经表达qualitative policy是否需要额外结构。

Design Audit可以记录anticipated judgment character或implementation concern，但不成为Frozen authority。未来validation只有在type确实改变required fields、validation rules或result semantics时，才重新评估enum。

---

## 17. Rubric 的角色

Rubric是Grader Specification内部的optional nested judgment policy，不是top-level Core Object。

Rubric回答：

> 对于定性 Contract，哪些有界语义维度和 anchors 可以指导 target-level judgment？

Rubric可以定义：

- dimensions；
- each dimension criterion；
- human-readable anchors；
- dimensions / anchors如何支持整体Contract-level interpretation。

Rubric不得：

- 创建新Requirement；
- 修改Contract success / failure semantics；
- 定义Benchmark-wide score；
- 定义cross-case aggregation；
- 分配Metric weight；
- 定义Gate threshold；
- 保存actual Rubric Result；
- 保存actual selected anchor。

简单deterministic或single-rule Grader不需要Rubric。强制所有Graders携带复杂Rubric会产生无意义boilerplate。

当前v0 real method validation没有包含真正qualitative Contract，因此Rubric的真实authoring、anchor quality与inter-rater behavior仍是future validation limitation。不得：

- 把deterministic Contract人为包装成qualitative Case；
- 因coverage gap声称Rubric已经real-validated；
- 因尚未验证Rubric而阻塞已经通过的deterministic / bounded semantic method；
- 为补偿coverage而修改Rubric Schema。

---

## 18. Rubric Dimensions 与 Anchors

Rubric Dimension表示一个Contract内部、对同一atomic judgment有必要的qualitative evaluation dimension。

每个dimension必须：

- 回到Contract statement或criteria；
- 具有清楚criterion；
- 不与其他dimension重复；
- 不把独立Contract责任隐藏在Rubric中；
- 不因“通常评价质量”而加入source未规定维度。

Rubric Anchor定义某个dimension上有区别意义的semantic level。Anchor必须：

- human-readable；
- observable 来自 qualified Evidence；
- mutually distinguishable enough 用于 审查；
- 避免只有“good / okay / bad”的空泛标签；
- 不依赖未声明Evidence；
- 不要求具体judge prompt。

如果dimensions可以独立满足 / 违反、需要独立Evidence、独立diagnosis或独立downstream aggregation，应先检查Contract granularity，而不是无限扩张Rubric。

---

## 19. Binary、Ordinal 与 Local Scalar Judgment

Grader-level judgment不必假定所有评价都是0/1。

允许的local judgment semantics可以包括：

- binary satisfied / violated；
- ordinal Rubric anchor；
- bounded local scalar，前提是Contract与Rubric明确其semantic meaning；
- insufficient或not-exercised等non-substantive meaning。

但是：

- local value必须属于一个target-specific Grader Result；
- 它不能表示Benchmark score；
- 不得在Grader Specification中聚合多个Cases、Episodes或Contracts；
- 不得定义weight、average、pass rate或cross-run comparison；
- local anchor / scalar与Contract satisfied / violated之间的interpretation必须清楚，不能交给Metric补定义。

本Guide不冻结完整Runtime Grader Result value schema。

当前v0 real method validation只覆盖了binary Contract-level substantive semantics，以及insufficient / not-exercised边界。Ordinal Rubric anchors与bounded local scalar仍属于future validation limitation：

- 不得因为尚未覆盖就制造artificial qualitative或scalar Case；
- 不得把未验证能力写成已验证结论；
- 不得因此新增`score`、`weight`或Metric字段；
- deterministic / bounded semantic Grader method不因该coverage gap而自动BLOCKED。

---

## 20. Grader 原子性 Test

对每个proposed Grader Specification询问：

1. Targets是否使用同一judgment semantics？
2. 每个target是否消费兼容的minimum Evidence package？
3. Judgment criteria是否可以原样应用到每个target？
4. Result interpretation是否相同？
5. Explanation meaning是否相同？
6. 某项failure是否需要target-specific diagnosis？
7. 是否把多个独立Contract judgments隐藏成一个结果？
8. 是否把本应属于同一Contract的必要criteria拆给多个Graders？
9. 是否试图让Metric组合同一Contract的必要条件？
10. Split / merge是否真正提高traceability与diagnosis？

目标是：

```text
Contract-faithful atomic judgment
+ explicit Evidence consumption
+ target-specific Result traceability
```

而不是机械执行`1 Contract = 1 Grader`，也不是把所有Cases放进一个Grader。

---

## 21. 技术主题：One Assertion → Multiple Graders

v0不支持多个authoritative Grader Specifications共同组成同一个ExpectedAssertion的Contract verdict。

规则：

```text
Each ExpectedAssertion pair
→ exactly one authoritative Grader Specification coverage
```

理由：

- 尚未定义多个 Grader Results 如何组成一个 authoritative Contract judgment；
- AND / OR / precedence / conflict resolution会引入新的composition semantics；
- 使用Metric聚合同一Contract的必要条件会混淆judgment与aggregation；
- 一个Grader satisfied、另一个violated时没有当前authority决定最终meaning；
- 多Grader重复消费Evidence可能导致double counting与解释冲突。

如果一个atomic Contract需要多个independent checks：

- 将它们写为同一Grader Specification中的多个`judgment_criteria`；
- qualitative时可使用多个Rubric dimensions；
- 在`result_semantics`或Rubric `overall_interpretation`中定义它们如何共同支持一个target-level judgment；
- 不把它们交给Metric聚合。

如果多个checks真的需要独立authoritative results、独立aggregation或可以独立满足 / 违反，应回查Contract granularity。

未来只有真实validation证明需要稳定multi-Grader composition时，才重新设计composition object或authority；本轮不预留字段。

---

## 22. 技术主题：One Grader → Multiple Assertions

一个Grader Specification可以包含多个GraderTargets，但它表示同一judgment policy的Definition reuse，不表示把多个Contracts合并成一个verdict。

只有以下条件全部满足才允许共享：

- judgment criteria substantially 相同；
- Evidence semantics与required relations compatible；
- result semantics相同；
- Rubric policy相同；
- insufficiency handling相同；
- explanation requirements相同；
- 不迫使某个target消费无关Evidence；
- 不损失Contract-specific diagnosis；
- policy可以对每个target独立应用。

以下相似性都不能单独证明shared Grader合法：

- shared Evidence source；
- same Contract family；
- same tool或action；
- same Artifact；
- same evaluation type；
- both critical；
- 相似名称或相邻workflow stage。

Evidence Spec IDs可以因target不同而不同。只要每个GraderTarget独立绑定自己的完整minimum Evidence set，且同一policy可以原样应用，就不应仅因IDs不同强制拆分。

每个target在Runtime仍必须产生Contract-specific Grader Result；不得产生一个模糊的multi-Contract PASS / FAIL。

核心原则：

```text
Shared grader policy
≠ merged target judgment
```

如果任一target需要不同criteria、Rubric、result interpretation或diagnosis，应拆分Grader Specifications。

---

## 23. Grader Composition 与 Metric Boundary

同一Contract satisfaction semantics所要求的A、B、C条件必须在一个authoritative Grader Specification中完成组合。

错误模型：

```text
Grader A judges required condition A
Grader B judges required condition B
Metric averages A and B
→ claims Contract satisfied
```

Metric不应被用来组合本来属于一个Contract verdict的必要条件。

正确边界：

```text
One authoritative Grader Specification
├── criterion A
├── criterion B
└── target-level result semantics

Metric
→ later aggregates completed Grader Results across evaluation observations
```

这不禁止一个Grader消费多个Evidence Specifications，也不禁止一个Rubric包含多个dimensions；它只禁止把Contract-level judgment authority推给Metric。

---

## 24. Failure Criteria 与 Failure Modes

Contract success criteria与failure criteria是Grader judgment的normative semantics。

Failure modes主要服务：

- diagnosis；
- explanation；
- Test Case coverage理解；
- 已知违规模式归因。

规则：

- failure mode不得被提升为额外Contract；
- failure mode label本身不自动产生violated verdict；
- Evidence必须先支持Contract failure criterion；
- 只有Evidence进一步支持具体mode时才能进行mode attribution；
- 如果Evidence足以支持violation但不足以区分具体failure mode，可以保留violated judgment并说明diagnosis未确定；
- 不得为了得到更具体mode而推翻已经充分的Contract-level judgment；
- mode attribution不足不自动等于Evidence对verdict不足。

只有当uncertainty影响核心Contract failure criterion本身，例如无法确认目标event、scope、identity或required relation是否成立时，才可能使verdict进入insufficient Evidence。仅仅无法区分两个diagnostic labels，不得把clear violated meaning降级为insufficient。

Grader Specification的`explanation_requirements`可以要求“when supported, identify relevant Contract failure mode”，不需要独立`failure_mode_handling` Schema field。

---

## 25. Explanation 与 Rationale

Grader Specification必须声明future Grader Result的minimum explanation expectations。

至少应要求：

- identify 该 目标 ExpectedAssertion / Contract；
- identify 相关 Evidence contributions；
- 状态 该 语义 reason linking Evidence to judgment；
- 用于 insufficiency, 状态 which 必需 contribution 或 关系 是 缺失 / unusable；
- 用于 violation, identify supported 失败 criterion 与, when supported, 失败 mode；
- distinguish observed fact 来自 inference；
- avoid conclusions unsupported 由 qualified Evidence。

Minimum explanation authoring baseline应按target实际需要覆盖：

- target identity；
- qualified Evidence contributions；
- relevant observed facts；
- facts与Contract success / failure semantics之间的relation；
- satisfied或violated的affirmative basis；
- 适用时的 insufficiency gap；
- supported failure criterion；
- 失败 mode 仅 if supported；
- observed fact与inference边界。

不要机械复制所有项目；但只写以下空泛要求不足以形成可复核的authority：

```text
Explain the result.
Provide rationale.
Cite evidence.
```

更稳定的表达是：

> 识别能够建立目标 operation identity 的合格 Evidence contributions，并说明其顺序如何支持或不支持 Contract criterion。

Explanation requirements不定义：

- report template；
- Markdown格式；
- word count；
- UI presentation；
- Scorecard layout；
- judge chain-的-thought；
- hidden reasoning disclosure。

Explanation是traceability requirement，不是Metric，也不是额外verdict condition。

---

## 26. 技术主题：LLM-as-Judge Boundary

LLM Grading只有在受以下Definition authority约束时才合法：

```text
Validated Contract
+ target ExpectedAssertion
+ declared qualified Evidence inputs
+ bounded judgment criteria
+ optional bounded Rubric
+ explicit result / insufficiency semantics
```

禁止：

- 开放式 `judge if good`；
- judge自行增加标准；
- 使用未声明Evidence；
- Evidence不足仍强制binary verdict；
- 根据target identity、版本声誉或外部知识替代Evidence；
- prompt漂移改变Contract meaning；
- 把Rubric anchor当Benchmark score。

本Guide不设计LLM system prompt、model、temperature、sampling或retry policy。

---

## 27. Human Grader Boundary 与 Reviewer Consistency

Human reviewer也必须受Contract、Evidence inputs、criteria、Rubric与result semantics约束，不能凭直觉扩展Benchmark语义。

Reviewer Consistency Review至少检查：

- criteria是否有多个合理但冲突的解释；
- qualitative terms是否有bounded anchors；
- evidence不足时是否允许停止而不是强制判断；
- failure criterion与mode attribution是否分开；
- different reviewers是否会使用不同未声明Evidence；
- explanation requirements是否足以复核；
- shared Grader policy对每个target是否真的相同；
- criteria是否包含hidden implementation assumption。

Focused semantic review还必须检查：

- Contract criteria是否仍是唯一normative authority；
- judgment criteria是否增加了新标准；
- Evidence refs是否完整；
- satisfied是否有affirmative basis；
- violated是否有affirmative basis；
- absence reasoning是否依赖complete observation surface；
- not-exercised是否真的来自trigger未发生；
- required action absence是否被误写成trigger absence；
- task noncompletion是否被误当not-exercised；
- Evidence insufficiency是否与Grader execution failure分离；
- failure-mode attribution是否越界；
- qualitative reviewer是否受bounded criteria / Rubric约束；
- Metric或Gate semantics是否泄漏。

这是qualitative consistency checklist，不产生数值reviewer score。

需要Human judgment不等于方法失败；但criteria模糊到reviewers无法合理一致时，Grader Design应`BLOCKED`。

---

## 28. 技术主题：Grader Specification Candidate / Working Stage

v0不引入mandatory Grader Specification Candidate对象或Candidate lifecycle。

复杂authoring可以使用temporary Working Grader Drafts比较：

- alternate judgment criteria；
- binary vs Rubric-based 策略；
- 目标 sharing vs split；
- Evidence consumption choices；
- insufficiency handling；
- explanation expectations。

Working Draft：

- 不是Core Object；
- 不进入Frozen Grader Specification Set；
- 不算grading coverage；
- 不占用正式`Gxxx` ID；
- resolved后由正式Spec或Design Issue取代。

只有未来真实design出现大量alternate policies、稳定draft lineage或复杂multi-reviewer reconciliation时，才重新评估Candidate lifecycle。

---

## 29. 技术主题：Grader Specification Design Audit

v0引入轻量、非Core、非authoritative的Grader Specification Design Audit，用于保存最小Schema不承载的design rationale。

建议至少记录：

| 字段 | 含义 |
|---|---|
| `grader_id` | 正式Grader ID；draft可使用temporary label |
| `targets` | 从Schema派生的ExpectedAssertion pairs |
| `target_rationale` | 为什么同一policy适用于这些targets |
| `evidence_consumption_rationale` | 为什么每个target引用这些Evidence Specifications |
| `judgment_rationale` | criteria如何忠实使用Contract semantics |
| `judgment_character` | deterministic、semantic或mixed working label；不是enum |
| `rubric_rationale` | 为什么需要或不需要Rubric |
| `result_semantics_rationale` | satisfied / violated / insufficient / not-exercised meaning选择 |
| `granularity_decision` | shared / split与atomicity理由 |
| `failure_diagnosis_rationale` | failure criteria与mode attribution边界 |
| `insufficiency_rationale` | Evidence不足时为何停止substantive judgment |
| `reviewer_consistency_concern` | 可能产生不一致的criteria / anchors |
| `downstream_metric_concern` | 只记录未来aggregation concern，不设计Metric |
| `design_notes` | upstream、implementation或future validation concern |

Audit：

- 不替代Grader Specification；
- 不成为target或Evidence consumption第二套authority；
- 不保存actual Grader Result；
- 不保存actual Evidence或verdict；
- 不定义Metric或Gate；
- 不要求简单Grader写长篇说明；
- 必须与Schema、Coverage Mapping与upstream objects一致。

---

## 30. 技术主题：Minimal GraderSpecification Schema Proposal

### 技术主题：30.1 GraderSpecification

```text
GraderSpecification:
- grader_id
- targets: list[GraderTarget]
- judgment_criteria: list[str]
- result_semantics: GraderResultSemantics
- insufficiency_handling: list[str]
- explanation_requirements: list[str]
- rubric: Rubric?
```

### 技术主题：30.2 GraderTarget

```text
GraderTarget:
- test_case_id
- contract_id
- evidence_spec_ids: list[str]
```

### 技术主题：30.3 GraderResultSemantics

```text
GraderResultSemantics:
- satisfied: str
- violated: str
- insufficient_evidence: str
- not_exercised: str?
```

这是Definition-time allowed meaning，不是Runtime Grader Result enum或actual result。

### 技术主题：30.4 Optional Rubric structures

```text
Rubric:
- dimensions: list[RubricDimension]
- overall_interpretation: str

RubricDimension:
- name
- criterion
- anchors: list[RubricAnchor]

RubricAnchor:
- label
- meaning
```

Rubric仅在bounded qualitative judgment需要时出现。Simple deterministic Grader应省略`rubric`，而不是创建空Rubric。

这是Schema Proposal，不规定YAML、JSON、Pydantic、directory、checker、Grading Engine或Runtime serialization。

---

## 31. Schema Field 决定s

| 候选字段 | v0决定 | 理由 |
|---|---|---|
| `grader_id` | 进入Schema，必填 | Grader Specification是一等Definition object，需要稳定identity |
| `targets` | 进入Schema，非空 | 支持policy reuse并保持target-specific mapping |
| `test_case_id + contract_id` | 进入nested GraderTarget | pair唯一定位ExpectedAssertion，无需assertion ID |
| `evidence_spec_ids` | 进入GraderTarget，非空 | 冻结每个target的显式Evidence consumption，避免multi-target ambiguity |
| `judgment_criteria` | 进入Schema，非空 | 定义qualified Evidence如何支持Contract semantics |
| `result_semantics` | 进入Schema，必填 | 定义allowed judgment meanings，不保存actual verdict |
| `insufficiency_handling` | 进入Schema，非空 | 防止missing Evidence自动变FAIL或强制verdict |
| `explanation_requirements` | 进入Schema，非空 | 保证future Result可追溯但不规定report格式 |
| `rubric` | Optional nested field | 仅qualitative judgment需要；simple Grader不受复杂Rubric拖累 |
| `grader_type` | 不进入 | semantics与execution actor不应混成不稳定enum |
| `failure_mode_handling` | 不单独进入 | Contract failure modes + explanation requirements足够表达diagnosis原则 |
| `score` / `weight` | 禁止进入 | aggregation与weight属于Metric；actual local value属于Grader Result |
| checker / prompt ref | 不进入v0 | concrete implementation尚未设计，不应成为semantic authority |
| Metric / Gate ref | 禁止进入本轮 | 属于downstream Definition objects |
| actual Evidence / Result | 禁止进入 | 属于Runtime / Result |
| composition field | 不进入v0 | v0每个assertion恰好一个authoritative Grader coverage |

### 技术主题：ID Rules

推荐形式：

```text
G001
G002
G003
```

规则：

- 在一个Benchmark Definition中唯一；
- 使用`G`加至少三位十进制数字；
- 不要求跨Benchmarks全局唯一；
- targets、Evidence consumption、judgment criteria、result semantics或Rubric发生重大变化时，应分配新ID；
- 被删除的ID不应在同一Benchmark lineage中复用于不同Grader policy。

---

## 32. Schema 字段语义

### 技术主题：32.1 grader_id

非空string，表示Definition-time Grader Specification identity，不是Runtime Grader Result ID。

### 技术主题：32.2 targets

必填`list[GraderTarget]`，至少一项且pair不得重复。每个target由`test_case_id + contract_id`唯一定位ExpectedAssertion，并显式声明`evidence_spec_ids`。

多个targets表示同一policy独立应用到每个target，不表示产生一个合并verdict。

### 技术主题：32.3 evidence_spec_ids

每个GraderTarget内必填非空`list[str]`，无重复。它必须完整引用该target minimum sufficient Evidence coverage中的所有authoritative Evidence Specifications。

不得省略required Spec、加入无关Spec或只依赖运行时自动发现。

### 技术主题：32.4 judgment_criteria

必填非空`list[str]`。每项描述qualified Evidence facts / relations如何支持Contract success、failure、insufficiency或applicability semantics。

不得包含checker code、selector、prompt implementation、Metric aggregation或来源未支持的新规则。

### 技术主题：32.5 result_semantics

必填nested structure，定义该policy下satisfied、violated与insufficient-evidence的human-readable meaning；conditional Contract可选定义not-exercised meaning。

这些字段不保存actual result，也不冻结完整Runtime Result status model。

### 技术主题：32.6 insufficiency_handling

必填非空`list[str]`，定义哪些Evidence缺口、qualification failure或relation gap阻止substantive judgment，以及不得自动推导什么。

不得定义Runtime retry、error enum或collector behavior。

### 技术主题：32.7 explanation_requirements

必填非空`list[str]`，定义future Result为traceability必须说明的target、Evidence contribution、semantic reason、insufficiency或supported failure diagnosis。

不得要求hidden chain-of-thought或固定report formatting。

### 技术主题：32.8 rubric

Optional。只有Contract需要bounded qualitative judgment时使用。出现时必须包含至少一个dimension；每个dimension至少两个有区别意义的anchors；`overall_interpretation`必须说明dimension / anchor如何支持target-level result semantics。

Rubric不得保存actual anchor selection、score、weight或aggregation result。

---

## 33. Three-Layer Grader Specification 验证

### 33.1 A. Structural / Field 验证

未来可deterministic检查：

- `grader_id`符合`G`+至少三位数字；
- Grader IDs在Definition中唯一；
- `targets`至少一项；
- GraderTarget包含非空`test_case_id`、`contract_id`与`evidence_spec_ids`；
- 同一Spec内target pair不重复；
- 每个target内Evidence Spec IDs不重复；
- `judgment_criteria`非空且条目非空；
- `result_semantics`包含非空`satisfied`、`violated`、`insufficient_evidence`；
- `not_exercised`若出现则非空；
- `insufficiency_handling`非空；
- `explanation_requirements`非空；
- Rubric若出现则dimensions非空；
- Rubric Dimension names不重复，criterion非空；
- 每个dimension anchors至少两项，labels不重复，meaning非空；
- `overall_interpretation`非空；
- 不存在actual Evidence、Result、Metric、Gate、score aggregation或checker implementation字段。

### 33.2 B. Cross-object 验证

需要完整Definition context：

- 每个target `test_case_id`存在且validated；
- 每个target `contract_id`存在且validated；
- pair实际出现在该Test Case的ExpectedAssertions中；
- 每个`evidence_spec_id`存在且validated；
- referenced Evidence Specification的targets包含同一pair；
- 每个target引用完整minimum required Evidence Specification set；
- 没有dangling、stale、cross-Benchmark或validation-only-to-production refs；
- 每个ExpectedAssertion pair恰好由一个authoritative Grader Specification覆盖；
- shared Grader的targets均合法；
- Grader Set、Coverage Mapping与Audit双向一致；
- Requirement → Contract → Test Case → Evidence Specification → Grader Specification trace可恢复；
- 没有Metric或Gate refs。

Cross-object validation不能证明criteria忠实、Rubric清楚或reviewers会一致。

### 技术主题：33.3 C. Semantic Grader Review

逐Spec至少检查：

- judgment criteria是否忠实于每个target Contract；
- 是否新增、strengthen或weaken normative semantics；
- Evidence consumption是否complete且minimum；
- Cross-Spec Evidence composition是否被正确使用；
- satisfied是否有affirmative basis；
- violated是否有affirmative violation basis；
- insufficient是否不会自动变FAIL；
- not-exercised是否只用于已存在Episode中被affirmatively证明未触发的Contract；
- Contract trigger与Subject required action是否分开；
- required action absence是否没有被误写成trigger absence；
- Case / task noncompletion是否没有被压缩成target not-exercised；
- Outcome / Workflow grading是否匹配；
- temporal / scope / identity relation是否保持semantic level；
- Artifact / action / interaction absence是否要求完整observation surface / interval；
- absence of observation是否没有被误写成observation of absence；
- Evidence insufficiency是否与Grader execution failure分开；
- Rubric dimensions / anchors是否bounded且Contract-faithful；
- local ordinal / scalar是否没有变成Metric；
- Grader atomicity与shared / split是否合理；
- one assertion → multiple authoritative Graders是否被禁止；
- multi-target policy是否仍产生target-specific judgment；
- failure criteria与failure-mode diagnosis是否分开；
- explanation requirements是否可复核且不要求chain-of-thought；
- Human / LLM reviewer consistency是否合理；
- 是否包含Metric、Gate或Runtime implementation leakage；
- criticality是否没有被误写成Benchmark failure logic。

Semantic Review需要Agent / Human judgment，不能伪装成Schema validation。

---

## 34. 技术主题：ExpectedAssertion → Grader Specification Coverage

Coverage Mapping是轻量working artifact，不是Core Object，也不是Frozen GraderSpecification Schema的一部分。

建议至少记录：

| 字段 | 含义 |
|---|---|
| `test_case_id` | Validated Test Case ID（已验证的 Test Case ID） |
| `contract_id` | 该Case中唯一ExpectedAssertion的Contract ID |
| `grader_id` | 唯一authoritative Grader Specification ID |
| `evidence_spec_ids` | 从该GraderTarget派生的显式Evidence inputs |
| `coverage_status` | `COVERED`或`BLOCKED` |
| `rationale` | 为什么该policy形成合法grading coverage，或为什么被阻塞 |

只有满足以下条件才能标记`COVERED`：

- 恰好一个valid authoritative Grader Specification包含该target；
- GraderTarget引用该pair完整minimum required Evidence Specifications；
- judgment criteria覆盖完整Contract semantics；
- result与insufficiency semantics清楚；
- Rubric在需要时充分、不需要时省略；
- Grader通过三层validation；
- 不只是ID linkage；
- 没有unresolved reviewer-consistency或composition issue。

以下情况必须`BLOCKED`：

- target没有Grader；
- target被多个authoritative Graders覆盖；
- required Evidence Spec遗漏；
- Grader引用无关Evidence；
- Contract semantics无法形成judgment；
- Evidence不足却强制verdict；
- Rubric模糊或增加标准；
- shared policy不能原样应用到每个target；
- criteria越界进入Metric、Gate或Runtime implementation；
- semantic reviewer无法合理一致。

不得用grader数量或coverage percentage掩盖一个blocking pair。

---

## 35. Grader Specification Design Issues 与 Rollback

至少区分：

- upstream Contract ambiguity；
- 上游 Test Case / ExpectedAssertion 问题；
- Evidence 消费 / 充分性问题；
- judgment fidelity issue；
- result-semantics issue；
- absence-的-event completeness issue；
- temporal / 范围 / 身份 judgment issue；
- Rubric clarity issue；
- granularity / 共享-策略 issue；
- 多 Grader 组成问题；
- explanation / diagnosis issue；
- reviewer-consistency issue；
- Schema insufficiency；
- downstream Metric concern；
- downstream Gate concern；
- implementation / Runtime concern。

Rollback：

```text
Success / failure semantics ambiguous
→ Contract Design lifecycle

Scenario does not exercise responsibility
→ Test Case Design lifecycle

Required observation or context unavailable
→ Evidence Specification Design lifecycle

Qualified observations exist but interpretation is unclear
→ Grader Specification Design

Target-level judgments are complete but aggregation is unclear
→ Downstream Metric Design Concern

Judgment semantics are clear but executable procedure is unknown
→ Downstream Grader Implementation Concern
```

不得为方便implementation或aggregation而改变upstream semantics，也不得直接修改upstream Guides。

---

## 36. 技术主题：Grader Specification Design Workflow

### 步骤 1 — Verify Inputs

- 验证Requirements、Contracts、Test Cases、Evidence Specifications、Coverage与statuses；
- production input不满足Entry Gate时立即BLOCK；
- method validation subset保留限定边界。

### 步骤 2 — Build ExpectedAssertion Inventory

- 以`(test_case_id, contract_id)`列出每个target；
- 读取Contract criteria、failure modes、evaluation type与applicability；
- 读取ExpectedAssertion与完整Evidence Specification coverage；
- 不重新设计upstream objects。

### 步骤 3 — Freeze Evidence Consumption

- 为每个target列出完整minimum required`evidence_spec_ids`；
- 检查Cross-Spec Composition；
- 删除debugging或无关Evidence inputs；
- 不依赖Runtime自动发现。

### 步骤 4 — Draft Judgment Semantics

- 写affirmative satisfied basis；
- 写affirmative violation basis；
- 写Evidence insufficiency handling；
- conditional Contract先分开trigger与required action，再写not-exercised meaning；
- 检查Case / task noncompletion不会替代target Contract judgment；
- Artifact / action / interaction absence写complete observation surface前提；
- 使用baseline insufficiency checklist，但只保留target相关项目；
- 分开Evidence insufficiency与Grader execution failure；
- explanation requirements使用minimum baseline并避免空泛boilerplate；
- 不写checker。

### 步骤 5 — Decide Rubric Need

- deterministic / bounded semantic relation优先使用judgment criteria；
- qualitative Contract需要时设计dimensions、anchors与overall interpretation；
- 不为统一外观强制Rubric；
- 不加入Metric weight或score aggregation。

### 步骤 6 — Run 原子性 and Sharing Review

- 每个assertion保持一个authoritative Grader coverage；
- 多个necessary checks放入同一policy；
- shared policy逐target检查criteria、Evidence、result、Rubric与diagnosis兼容性；
- 不因shared Evidence source、same tool / Artifact、same Contract family或both critical而自动共享；
- 不因不同targets使用不同Evidence Spec IDs而自动拆分；
- 需要独立authoritative results时回查Contract granularity。

### 步骤 7 — Write Grader Specifications

- 分配正式`Gxxx`；
- 写targets与per-target Evidence refs；
- 写criteria、result semantics、insufficiency与explanation；
- 需要时写optional Rubric；
- 不写actual Result、Metric、Gate或implementation。

### 步骤 8 — Build Coverage and Audit

- 每个ExpectedAssertion pair建立Coverage row；
- 确保恰好一个authoritative grader；
- 记录evidence consumption、Rubric、granularity与reviewer consistency rationale；
- 保留downstream concerns。

### 步骤 9 — Validate

- Structural / Field Validation；
- Cross-object Validation；
- Semantic Grader Review；
- unresolved issue进入Grader Specification Design Issues。

### 步骤 10 — Determine Status

- 每个target获得valid grading coverage且validation通过时READY；
- 任一required target BLOCKED时整体BLOCKED；
- 输出必需artifacts并停止，不进入Metric、Gate或Runtime implementation。

---

## 37. Grader Specification 设计状态

Production状态只保留：

```text
GRADERS_READY
GRADERS_BLOCKED
```

### 技术主题：37.1 GRADERS_READY

只有同时满足：

- authoritative upstream Definition当前有效；
- Evidence Specification Design为`EVIDENCE_SPECS_READY`；
- 每个ExpectedAssertion pair恰好一个authoritative Grader coverage；
- 每个target消费完整minimum Evidence Specifications；
- criteria忠实覆盖Contract semantics；
- satisfied / violated / insufficient与适用时not-exercised meaning清楚；
- trigger与required action清楚分开；
- Artifact / action / interaction absence依赖complete observation surface；
- Case / task noncompletion没有替代target Contract judgment；
- Evidence insufficiency与Grader execution failure分开；
- Rubric在需要时充分、不需要时省略；
- reviewer consistency可接受；
- 所有Graders通过三层validation；
- Coverage Mapping、Spec Set与Audit一致；
- 没有unresolved Grader Design Issue；
- 没有Metric、Gate或Runtime implementation leakage。

### 技术主题：37.2 GRADERS_BLOCKED

例如：

- Contract semantics无法判；
- required Evidence不够或引用不完整；
- missing Evidence被写成FAIL；
- absence-of-event没有完整性前提；
- criteria增加normative semantics；
- Rubric模糊或unbounded；
- one assertion被多个authoritative Graders覆盖；
- shared policy对targets并不相同；
- failure mode被错误提升为verdict condition；
- semantic review无法形成合理reviewer consistency；
- criteria依赖未定义Runtime assumption；
- coverage gap或validation failure。

状态不是quality score：

```text
99% targets COVERED + 1 blocking gap
= GRADERS_BLOCKED
```

Method Validation Subset使用6.3节完整限定status wording，不改变production status model。

---

## 38. 必需输出

Grader Specification Design至少产生：

1. **Grader Specification Set**：使用Proposed Schema的正式Definition-time Specs；
2. **ExpectedAssertion → Grader Specification Coverage Mapping**：逐target pair的semantic grading coverage；
3. **Grader Specification Design Audit**：Evidence consumption、criteria、Rubric、granularity与reviewer-consistency rationale；
4. **Grader Specification Design Issues**：blocking issues与upstream / downstream concerns；
5. **Grader Specification Validation Summary**：Structural、Cross-object、Semantic三层结果；
6. **Grader Specification Design Status**：`GRADERS_READY`或`GRADERS_BLOCKED`；
7. **Schema Design Findings**：只记录真实design暴露的schema need。

Working Grader Drafts不是必需final output，也不算Coverage。

---

## 39. 技术主题：Grader Result Boundary

本轮不设计完整Grader Result Schema，但必须保持：

```text
Specification:
how a qualified Evidence package should be judged

Result:
what this grading operation actually judged
```

Future Grader Result在概念上至少需要关联：

- Grader Specification；
- Run / Episode；
- Contract-specific target；
- consumed Evidence；
- actual judgment；
- actual explanation；
- 实际 insufficiency / diagnosis / Grader error when applicable。

这些信息都不得提前写入Grader Specification实例。本Guide的`result_semantics`只定义allowed meaning，不保存actual value，也不替代未来Result Design。

---

## 40. Metric 与 Gate Boundary

### 技术主题：40.1 Metric

```text
Grader
→ judges one target-specific evaluation observation

Metric
→ aggregates completed Grader Results
```

Grader Specification禁止定义：

- pass rate；
- average；
- weighted score；
- Benchmark score；
- cross-case aggregation；
- cross-Episode aggregation；
- cross-Run comparison；
- sample policy；
- retry weighting。

即使一个Grader未来产生local ordinal或scalar value，也不能在本层聚合多个targets、Cases或Episodes。

### 技术主题：40.2 Gate

Grader判断target-specific事实或质量；Gate决定某类Result是否阻断整体Benchmark。

Contract `criticality`可以提示加强Grader review，但不改变Contract verdict semantics，也不允许Grader自动宣布整个Benchmark FAIL。

禁止：

```text
critical Contract violated
→ Grader directly sets Benchmark Gate failure
```

Gate Specification与Gate Result属于后续阶段。

---

## 41. Schema Design 发现项

### 技术主题：41.1 GraderTarget pair remains sufficient

`(test_case_id, contract_id)`唯一定位ExpectedAssertion，不需要新增assertion ID。GraderTarget独立命名是因为它还包含per-target Evidence consumption，而不是复用EvidenceTarget后增加隐藏语义。

### 技术主题：41.2 Evidence refs belong inside GraderTarget

Multi-target Grader需要每个target独立Evidence binding。Top-level `evidence_spec_ids`会产生target ambiguity，因此`evidence_spec_ids`进入nested GraderTarget。

### 技术主题：41.3 One authoritative Grader per assertion

v0不引入multi-Grader composition field。一个assertion的多个necessary checks保留在同一Grader Specification；Metric不得承担Contract-level composition。

### 技术主题：41.4 Multi-target policy reuse is allowed

`targets`是list，以支持Concept Model中的reuse。但policy必须逐target独立应用并产生Contract-specific Result；共享不产生merged verdict。

### 技术主题：41.5 Result semantics are Definition policy, not Result data

`GraderResultSemantics`定义satisfied、violated、insufficient与可选not-exercised的meaning。它不是Runtime enum、actual verdict或Result Schema。

### 技术主题：41.6 Rubric is optional and nested

Rubric只在bounded qualitative judgment需要时出现；simple Grader不创建空Rubric。Rubric Dimension与Anchor不是Core Objects。

### 技术主题：41.7 No grader_type enum

Judgment semantics与execution actor是不同维度，当前没有稳定Framework behavior要求冻结type taxonomy。

### 技术主题：41.8 No score, weight, Metric or Gate fields

Local actual value属于future Grader Result；aggregation、weight与Benchmark score属于Metric；blocking policy属于Gate。

### 技术主题：41.9 No checker implementation reference

当前Schema冻结semantic judgment policy，不绑定code、prompt、model、library、selector或execution engine。

### 技术主题：41.10 One-authoritative-Grader restriction validated

Real method validation已经证明，structured multi-criteria、conditional trigger / required action、multi-Evidence authorization与scope / before-after checks都可以保留在一个authoritative Grader Specification中形成target-level judgment。当前不需要multi-Grader composition、voting、precedence、ensemble或result merger字段。

### 技术主题：41.11 Multi-target policy reuse validated

Real method validation出现了同一judgment policy应用于多个targets的合法正例。不同targets可以在各自GraderTarget中绑定不同`evidence_spec_ids`；只要criteria、result、insufficiency、explanation与Rubric policy兼容，就不需要因Evidence ID不同而拆分。每个target未来仍产生独立Contract-specific Result。

### 技术主题：41.12 Insufficiency and explanation fields remain necessary

真实authoring反复需要表达required ES缺失、qualification failure、cross-Evidence relation gap、identity ambiguity与complete-surface requirement，因此`insufficiency_handling`不能并入通用result label。`explanation_requirements`也需要保存target-specific traceability expectation，但可以使用本Guide的baseline template减少boilerplate。

### 技术主题：41.13 Schema remains unchanged after real validation

Real validation没有证明新增字段必要。特别不增加assertion ID、grader type、failure-mode handling、multi-Grader composition、checker reference、Metric / Gate reference、Runtime Result、score或weight字段。第30节Minimal Schema Proposal保持不变。

---

## 42. Method 自查

| 检查问题 | v0结论 |
|---|---|
| 1. Grader Spec vs Grader Result是否清楚？ | 是。Spec是Definition policy；Result是某次实际application与judgment。 |
| 2. Contract vs Grader边界是否清楚？ | 是。Contract定义success/failure；Grader只解释qualified Evidence如何支持既有语义。 |
| 3. Evidence vs Grader边界是否清楚？ | 是。Evidence定义qualified observations；Grader形成semantic judgment。 |
| 4. Grader vs concrete checker边界是否清楚？ | 是。允许semantic relation，禁止code、selector、prompt与library implementation。 |
| 5. target mapping是否清楚？ | 是。GraderTarget使用`test_case_id + contract_id`定位ExpectedAssertion。 |
| 6. evidence consumption authority是否清楚？ | 是。每个GraderTarget显式保存完整minimum`evidence_spec_ids`。 |
| 7. PASS/FAIL/insufficient边界是否清楚？ | 是。satisfied与violated都需affirmative basis；insufficient不等于FAIL。 |
| 8. Outcome/Workflow grading是否稳定？ | 是。Outcome关注Artifact/content/state；Workflow关注action/order/authorization/scope且不能由Outcome替代。 |
| 9. temporal/scope judgment是否保持semantic？ | 是。定义relation，不写timestamp/index/set-operation implementation。 |
| 10. deterministic与semantic grading是否都支持？ | 是。普通criteria支持deterministic；optional bounded Rubric支持qualitative。 |
| 11. Rubric角色是否清楚？ | 是。Rubric是optional nested policy，不是Requirement、Metric或Core Object。 |
| 12. binary/scaled judgment边界是否清楚？ | 是。允许target-local anchors/value semantics，但禁止aggregation与Benchmark score。 |
| 13. Grader granularity是否可执行？ | 是。Atomicity Test检查policy、Evidence、Result、diagnosis与downstream independence。 |
| 14. one assertion→multiple Graders是否支持或明确限制？ | v0明确不支持多个authoritative Graders composition；每个pair恰好一个coverage。 |
| 15. one Grader→multiple assertions是否支持？ | 支持相同policy复用，但每个target独立应用并产生Contract-specific Result。 |
| 16. failure modes如何使用？ | 用于diagnosis / explanation；不自动成为verdict condition。 |
| 17. explanation/rationale要求是否合理？ | 是。要求target、Evidence contribution与semantic reason，不规定report格式或chain-of-thought。 |
| 18. LLM-as-judge是否受约束？ | 是。必须受Contract、Evidence、criteria、Rubric与insufficiency semantics约束。 |
| 19. human reviewer consistency如何保证？ | 通过bounded criteria/anchors、declared Evidence、stop-on-insufficiency与consistency review。 |
| 20. Candidate是否需要？ | 当前不需要mandatory Candidate；Working Draft + Audit足够。 |
| 21. Audit是否需要？ | 需要非Core Audit记录mapping、Evidence consumption、Rubric、granularity与review风险。 |
| 22. 最小Schema是什么？ | G ID、targets with Evidence refs、criteria、result semantics、insufficiency、explanation与optional Rubric。 |
| 23. 是否泄漏Metric？ | 未泄漏。没有weight、aggregation、pass rate或Benchmark score。 |
| 24. 是否泄漏Gate？ | 未泄漏。criticality不改变target verdict，也不设置Benchmark blocker。 |
| 25. 是否泄漏Runtime implementation？ | 未泄漏。没有checker、prompt、model、selector、collector或actual Result。 |
| 26. 哪些问题必须真实validation？ | Schema adequacy、Evidence-ref authoring、affirmative/absence reasoning、Rubric anchors、shared policy、reviewer consistency与one-Grader restriction。 |

### 42.1 已纳入的自查修正

本轮自审已经在正文中处理：

- 为避免Contract被Grader改写，固定Contract criteria为normative authority；
- 为避免Evidence缺失自动变FAIL，要求先做Evidence sufficiency boundary；
- 为避免PASS成为absence of failure，要求affirmative satisfied basis；
- 为避免FAIL成为absence of proof，要求affirmative violation basis；
- 为避免absence-of-event误判，增加complete observation interval前提；
- 为避免multi-target Evidence ambiguity，把refs放入GraderTarget；
- 为避免多个Grader Results的authority不明，v0限制每个assertion一个authoritative Grader coverage；
- 为避免Metric代替Contract judgment composition，把multiple criteria留在同一Grader policy；
- 为避免shared policy产生Case-level模糊结果，要求每个target独立Contract-specific Result；
- 为避免Rubric成为新Requirement，要求dimensions与anchors回到Contract；
- 为避免simple Grader产生boilerplate，Rubric保持optional；
- 为避免grader type混淆semantics与actor，不冻结enum；
- 为避免failure mode主导verdict，将其限制为supported diagnosis；
- 为避免LLM/Human自由扩展标准，增加bounded criteria与reviewer-consistency review；
- 为避免Result data进入Definition，分开result semantics与actual judgment；
- 为避免Metric/Gate leakage，明确禁止aggregation、weight、score与blocking logic；
- real validation后，为避免not-exercised吞掉required-action absence，明确分开trigger与required action；
- 为避免Case / task noncompletion决定target verdict，固定per-target semantic judgment boundary；
- 为避免Artifact、action或interaction capture gap被当成真实absence，统一Complete Observation Surface Principle；
- 为避免insufficient吞掉judge implementation failure，分开Evidence insufficiency与Grader execution failure；
- 为避免explanation boilerplate，增加minimum baseline与target-specific anti-boilerplate rule；
- 为避免shared policy误判，增加shared-source / same-tool / both-critical negative checks，并允许per-target Evidence IDs不同。

### 42.2 Real Method 验证 Coverage

当前real validation已经覆盖：

- 简单 Artifact 存在性 / 完整性判断；
- 结构化 输出 multi-criteria judgment；
- Workflow action 是否发生的判断；
- temporal ordering judgment；
- 范围 containment / 身份 关系 judgment；
- conditional Contract与not-exercised authoring；
- absence reasoning with 完整 vs incomplete surface；
- 一个 目标 consuming 多个 Evidence Specifications；
- 一个 共享 Grader 策略 applied to 多个 目标；
- rejected 共享-策略 counterexamples；
- deterministic Contract不需要Rubric；
- violation与failure-mode attribution分离；
- Evidence insufficiency与Grader execution failure边界；
- 一个-assertion-一个-权威-Grader restriction under multi-check Contract；
- no Metric、Gate或concrete checker leakage。

Real validation status是：

```text
GRADERS_READY for validation subset
```

它不等于production`GRADERS_READY`，也不证明Runtime Result或implementation已经完成。

### 42.3 Future 验证 Limitations

以下仍需真实future validation：

- 需要有界 Rubric 的定性 Contract；
- Rubric dimensions / anchors的inter-rater behavior；
- 局部 ordinal / scalar 不含 Metric leakage；
- Human / LLM reviewer 一致性对比；
- 不同Contracts之间真正共享同一Grader policy的正例；
- 高隐私、高成本或transformed Evidence条件下的judgment consistency。

这些coverage limitations不构成当前deterministic / bounded semantic method blocker，也不得被误报为已经验证。

### 42.4 聚焦一致性检查s After Hardening

本轮hardening不重跑完整real validation，只复用已经通过的validation conclusions执行以下三个focused checks。

#### A. 技术主题：Conditional not-exercised

抽象Contract：当condition X成立时，Subject必须执行action Y。

| Evidence 状态 | Expected meaning | Check |
|---|---|---|
| complete Evidence证明X未发生 | `not_exercised` candidate | PASS |
| complete Evidence证明X发生但Y未发生 | `violated` candidate | PASS |
| 无法确认X是否发生 | `insufficient_evidence` | PASS |
| task整体未完成，但X与Y关系可判 | 独立target judgment + future Case status | PASS |

Hardening没有把required-action absence误写成trigger absence，也没有让task noncompletion自动变not-exercised。

#### B. 技术主题：Absence with complete vs incomplete surface

| Evidence 状态 | Expected meaning | Check |
|---|---|---|
| known target identity + complete output surface + healthy capture + required Artifact absent | absence可支持Contract failure semantics | PASS |
| output collector无法读取目标surface | Evidence insufficiency，不推断Artifact不存在 | PASS |
| complete interaction interval + action occurred + required authorization absent | absence可支持Contract failure semantics | PASS |
| participant turn recorder存在关键gap | Evidence insufficiency，不推断Subject未请求 | PASS |

规则保持semantic level，没有增加event index、timestamp、parser或matcher。

#### C. 技术主题：Shared Grader policy reuse

抽象shared policy应用于两个targets：两者judgment、result、insufficiency与explanation policy相同，但各自绑定不同Evidence Specification IDs。

检查结果：

- 不因Evidence IDs不同而强制split：PASS；
- 每个target仍只消费自己的minimum Evidence set：PASS；
- shared policy不生成merged verdict：PASS；
- shared Evidence source、same Artifact或both critical不自动证明sharing：PASS；
- 每个target未来仍产生独立Contract-specific Result：PASS。

### 技术主题：42.5 Freeze Readiness

Hardening self-review与三个focused consistency checks均通过：

- no Schema blocker；
- 一个-权威-Grader restriction 稳定；
- satisfied / violated 的肯定依据稳定；
- insufficiency boundary stable；
- 不-exercised 边界 稳定；
- 完整 observation surface 规则 稳定；
- Grader execution 失败 separated；
- 共享 Grader 规则 稳定；
- 失败-mode diagnosis 稳定；
- explanation requirements bounded；
- no Metric leakage；
- no Gate leakage；
- 无 Runtime / checker leakage。

因此：

```text
GRADER_SPEC_DESIGN_V0_FREEZE_READY: YES
```

Rubric、ordinal / scalar与actual inter-rater evaluation保留为future validation limitation，不阻止当前v0 method freeze。

---

## 43. 最终决定 检查清单

### 字段或协议值：Inputs

- [ ] Production input使用authoritative Frozen Requirements与validated Contracts / Test Cases / Evidence Specifications
- [ ] Evidence Specification Design Status为`EVIDENCE_SPECS_READY`
- [ ] Inputs没有stale或unresolved upstream issue
- [ ] Method validation subset保留validation-only boundary与限定status

### 技术主题：Target and Evidence Mapping

- [ ] 每个GraderTarget pair解析到真实ExpectedAssertion
- [ ] ExpectedAssertion authority仍在TestCase中
- [ ] 不新增assertion ID
- [ ] 每个target显式列出完整minimum`evidence_spec_ids`
- [ ] Evidence refs均服务同一pair且没有无关输入
- [ ] 每个ExpectedAssertion恰好一个authoritative Grader coverage

### 技术主题：Judgment Semantics

- [ ] Criteria忠实于Contract statement / success / failure semantics
- [ ] 没有unsupported strengthening或weakening
- [ ] Satisfied具有affirmative Evidence basis
- [ ] Violated具有affirmative violation basis
- [ ] Insufficient Evidence没有被写成FAIL
- [ ] Conditional target的not-exercised meaning清楚
- [ ] Not-exercised来自affirmatively established trigger absence
- [ ] Trigger absence与required-action absence没有混淆
- [ ] Case / task noncompletion没有自动变not-exercised
- [ ] Artifact / action / interaction absence依赖完整observation surface / interval
- [ ] Absence of observation没有被误写成observation of absence
- [ ] Evidence insufficiency与Grader execution failure分开

### Temporal、范围 and Structured Judgment

- [ ] Same-operation / ordering / identity / scope relation清楚
- [ ] Judgment保持semantic level
- [ ] 没有timestamp code、event index、selector或set-operation implementation
- [ ] Structured output没有按普通字段机械拆Grader
- [ ] Parse / qualification failure没有自动变Contract violation

### 技术主题：Rubric and Reviewer Consistency

- [ ] 只有qualitative judgment需要时才使用Rubric
- [ ] Rubric dimensions回到Contract authority
- [ ] Anchors有区别意义且Evidence-grounded
- [ ] Overall interpretation形成target-level semantics而非Metric
- [ ] Human / LLM reviewer consistency可接受
- [ ] Evidence不足时允许停止判断

### 技术主题：Granularity and Composition

- [ ] Grader Atomicity Test完成
- [ ] Multi-check atomic Contract由一个authoritative policy组合
- [ ] 没有用Metric组合Contract必要条件
- [ ] Shared policy对每个target完全兼容
- [ ] 没有因shared source / tool / Artifact / criticality自动共享
- [ ] 没有因per-target Evidence IDs不同自动拆分compatible policy
- [ ] 每个target未来产生Contract-specific Result而非merged verdict
- [ ] Failure criteria与failure-mode diagnosis分开

### 技术主题：Definition Boundaries

- [ ] 没有actual Evidence、Episode、Result、verdict、explanation或score
- [ ] 没有regex、JSONPath、checker、judge prompt、model或library implementation
- [ ] 没有Metric、Weight、aggregation、Benchmark score或cross-case policy
- [ ] 没有Gate、blocking logic或criticality-to-Benchmark-failure rule
- [ ] 不引入mandatory Candidate或grader_type enum

### 验证 and Status

- [ ] Structural / Field Validation完成
- [ ] Cross-object Validation完成
- [ ] Semantic Grader Review完成
- [ ] Spec Set、Coverage Mapping与Audit一致
- [ ] 无unresolved Grader Design Issue
- [ ] Production status只使用`GRADERS_READY`或`GRADERS_BLOCKED`

全部必需检查通过时，production Grader Specification Design才可输出：

```text
GRADERS_READY
```

否则输出：

```text
GRADERS_BLOCKED
```

并停止在Grader Specification Design边界，不开始Metric、Gate、Grader implementation或其他Runtime Design。
