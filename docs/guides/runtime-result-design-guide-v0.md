# 《Runtime / Result Design Guide v0》

Status: RUNTIME_RESULT_DESIGN_METHOD_READY_FOR_REAL_VALIDATION — Authority Integration Hardened

本文定义从已经冻结的 Benchmark Definition 到 Runtime / Result objects 的通用设计方法，并提出以下八个 Core Objects 的最小 pseudo-schema：

- Runtime：Run、Episode、Artifact、Evidence；
- Result：Grader Result、Metric Result、Gate Result、Scorecard。

本文适用于 coding agent、tool-use agent、browser agent、conversational agent、research agent、structured-output agent、local skill、remote service 与 model endpoint，不绑定 Android、HarmonyOS、ADB、Git、本机文件系统或任何 concrete evaluator。

本文正式消费`docs/benchmark-definition-schema-design-v0.2.md`已经定义并完成architecture-level controlled validation的Benchmark Definition authority。本轮不修改该Definition schema，也不修改已经frozen的Requirement Extraction、Final Requirement Finalization、Contract、Test Case、Evidence Specification、Grader Specification、Metric Specification、Gate Specification或Concept Model。本轮不进行Runtime real validation，不实现Pydantic、CLI、collector、grader engine、Metric calculator、Overall calculator、Acceptance evaluator、digest generator、storage、database、UI或packaging。

---

## 1. Design Goal and Completion Boundary

Runtime / Result Design必须让一次Run至少可以回答：

1. 实际执行的是哪个不可漂移的Frozen Benchmark Definition；
2. 实际评估的是哪个外部Subject；
3. 哪些Test Cases产生了哪些distinct Episodes / attempts；
4. 哪些Artifacts被产生、消费或观察；
5. 哪些actual observations被qualification为Evidence；
6. 哪些target-specific Grader Results形成；
7. Metric如何选择、排除、聚合Grader Results；
8. Gate使用了哪些Result以及为何OPEN、TRIGGERED或INDETERMINATE；
9. 哪些预期Results缺失以及发生了什么system / evaluator failure；
10. Scorecard实际组织了哪些Results，哪些final view具有Definition authority。

本轮authority-integration hardening完成条件仅为：

- 通用方法；
- 最小pseudo-schema proposal；
- Structural、Cross-object、Semantic validation rules；
- frozen Definition authority consumption rules；
- OverallScoreOutcome与AcceptanceEvaluation nested derived views；
- focused cross-document consistency review；
- Schema Findings、Architecture Findings与Method Self-Review。

本轮不进行真实Runtime validation，不声称Runtime / Result Schema已real-validated或frozen。

---

## 2. Frozen Architecture Baseline

Runtime / Result Design的直接Definition-time authority是：

```text
docs/benchmark-definition-schema-design-v0.2.md
```

它是以下事项的唯一frozen authority：

- full Benchmark Definition composition；
- `overall_score_policy`；
- `acceptance_policy`；
- complete Frozen Definition Closure；
- semantic resource bindings；
- canonicalization与definition digest protocol。

Runtime Guide只消费这些authority，不重新定义Definition-time policy、canonical JSON、collection ordering、decimal normalization、Unicode normalization、SHA-256 protocol或resource binding schema。

Definition layer共有8个Definition-time Core Object types：

```text
BenchmarkDefinition                     root Core Object
├── requirements                        Requirement collection
├── contracts                           Contract collection
├── test_cases                          Test Case collection
├── evidence_specifications             Evidence Specification collection
├── grader_specifications               Grader Specification collection
├── metric_specifications               Metric Specification collection
└── gate_specifications                 Gate Specification collection
```

即：1个root Core Object内部包含7类Core Object collections。不得称为“8 nested Core Object collections”。这是terminology clarification，不是Benchmark Definition v0.2 schema change。

Runtime / Result：

```text
Frozen Benchmark Definition
+ exactly one external Subject
→ Run
→ Episodes
→ Artifacts / Evidence
→ Grader Results
→ Metric Results
→ Gate Results
→ Scorecard
```

始终保持：

```text
Definition objects
≠ Runtime objects
≠ Result objects
```

一个Run只评估一个Subject。Baseline与Candidate必须分别形成两个Run；跨Run comparison是派生视图，本轮不创建Comparison Core Object，也不允许一个Metric Result聚合多个Runs。

---

## 3. Framework-Wide Invariants

### 3.1 Definition binding is content-specific

`benchmark_id + benchmark_version`只表示human-readable lineage与declared version，不能独立证明同version内容没有漂移。Run必须同时保存closure profile与不可变的`definition_digest`。

```text
benchmark_id + benchmark_version
≠ sufficient frozen-content identity

benchmark_id
+ benchmark_version
+ definition_closure_profile
+ definition_digest
= Frozen Definition binding tuple
```

`definition_digest`必须按Benchmark Definition v0.2冻结的closure profile与canonical digest protocol产生。它是Run引用的content identity；可选`definition_snapshot_ref`只用于检索与audit，不替代digest。

### 3.2 One Run, one Subject

Subject是Run中的nested external reference，不是第17个Core Object。一个Run不得同时保存baseline与candidate Subject。

### 3.3 Execution state is not evaluation meaning

```text
Run / Episode completed
≠ Contract satisfied

Run / Episode failed operationally
≠ Contract violated
```

Episode completed并产生`violated` Grader Result是完全合法组合。

### 3.4 System failure is not semantic Result

```text
collector failure
≠ Evidence violation

grader engine failure
≠ insufficient_evidence

Metric calculator failure
≠ Metric unavailable

Gate evaluator failure
≠ INDETERMINATE

Overall calculator failure
≠ Overall unavailable

Acceptance evaluator failure
≠ BLOCKED / INDETERMINATE
```

System / evaluator failure进入Runtime diagnostics。只有对应semantic evaluation成功完成时才创建authoritative Result object。

### 3.5 Identity, not payload equality, defines duplicates

相同序列化记录具有相同object ID时是同一logical object的duplicate serialization；不同Episode IDs即使输入与输出完全相同，也表示两个legitimate attempts。

```text
same episode_id
→ same logical Episode

different episode_id
→ distinct Episode
```

Result同理。Metric / Gate必须在selection前按logical Result ID去重，不能按内容相等去重distinct attempts。

### 3.6 Same-Run closure

除Definition references外，任何Result dependency必须属于同一Run。禁止把Run A的Grader Result放入Run B的Metric Result，或把不同Runs的Metric Results混入一个Gate Result或Scorecard。

---

## 4. Run

### 4.1 Definition

```text
Run
= exactly one Frozen Benchmark Definition
+ exactly one external Subject
+ one benchmark execution context
+ all Runtime / Result objects belonging to that execution
```

Run是Runtime顶层identity与same-Run referential-integrity boundary，不是Benchmark performance verdict。

### 4.2 FrozenDefinitionRef

```text
FrozenDefinitionRef:
- benchmark_id: str
- benchmark_version: str
- definition_closure_profile: str
- definition_digest: str
- definition_snapshot_ref: str?
```

字段语义：

- `benchmark_id`：required；Definition lineage authority；
- `benchmark_version`：required；human-visible declared version；
- `definition_closure_profile`：required；必须精确等于`skill-eval-frozen-definition-closure-v0`；
- `definition_digest`：required；immutable complete content identity，格式必须是`sha256:<64 lowercase hexadecimal characters>`；
- `definition_snapshot_ref`：optional；可检索snapshot的generic locator，不具有content-identity authority。

Run validation必须按Benchmark Definition v0.2 canonical protocol对loaded Definition重新计算digest，并确认ID、version、profile与digest四者全部匹配。仅比较ID与version不足以形成valid Run；snapshot locator匹配也不能替代digest validation。

### 4.3 SubjectReference

```text
SubjectReference:
- subject_ref: str
- subject_kind: str
- version_ref: str?
- content_digest: str?
- identity_metadata: map[str, scalar]?
```

选择hybrid结构：required opaque stable reference + small structured identity claims。

- `subject_ref`：required；Framework外部可解析或可审计的stable reference，可表示directory、repository revision、API agent、remote service、local program、model endpoint或tool-enabled agent；
- `subject_kind`：required；开放但非空的type label，不冻结Git-only enum；
- `version_ref`：optional；repository revision、deployment revision、model revision、release version等；
- `content_digest`：optional；能取得immutable content时用于加强identity；
- `identity_metadata`：optional；只保存resolution / audit所需的small scalar claims，不作为隐藏Subject Schema或任意业务data垃圾桶。

Git commit只是一种合法`version_ref`，不是唯一形式。对于无法提供immutable digest的remote subject，Run仍可记录可观察identity，但reproducibility review必须明确其identity strength与限制。

Subject identity与Definition identity必须保持独立：Definition digest表示“考试规则”content identity；Subject reference / digest表示“被评对象”identity。二者都服务Run reproducibility，但不能互相替代或混用。一个Run始终绑定one Frozen Definition + one Subject。

### 4.4 RuntimeExecutionContext

Run必须保存本次执行实际使用的最小execution context identity，而不能只依赖当前机器状态或未记录的CLI defaults。

```text
RuntimeExecutionContext:
- execution_context_id: str
- orchestrator: str
- environment_ref: str?
- configuration_ref: str?
- configuration_digest: str?
- context_metadata: map[str, scalar]?
```

- `execution_context_id`与`orchestrator` required，用于定位本次execution setup与执行责任方；
- `environment_ref`可引用container image、host profile、remote environment、browser session class或其他generic environment record；
- `configuration_ref`与`configuration_digest`在实际执行受外部configuration控制时使用；digest比mutable locator更强；
- `context_metadata`只保存small reproducibility claims，例如declared platform / region / model runtime label，不保存完整environment dump；
- large environment manifests应成为Run-level Artifact，由`environment_ref`或Artifact relation引用。

Execution context记录实际条件，不自动证明环境有效，也不是Gate或Subject performance semantic。

### 4.5 Run execution status

Framework真正需要区分以下execution states：

```text
created
running
completed
partial
blocked
failed
cancelled
```

语义：

- `created`：Run identity已建立，但没有Episode进入meaningful execution；
- `running`：至少一个Runtime operation仍在进行，尚未形成terminal execution state；
- `completed`：declared execution plan已到达正常terminal boundary；不表示所有Contracts satisfied，也不自动表示Run valid；
- `partial`：至少一个Episode进入meaningful execution，但required execution plan未完成；
- `blocked`：Run在meaningful Episode execution前被外部precondition、environment或orchestration dependency阻止；
- `failed`：Run-level execution / orchestration发生system failure并终止；
- `cancelled`：由明确cancellation request终止。

`no Episodes executed`不需要单独状态：它由`episode_ids: []`结合`created / blocked / failed / cancelled`解释。`partial`不能用于零Episode Run。

### 4.6 Run validity

Execution completion与evaluation validity分开：

```text
RunValidityStatus:
- pending
- valid
- invalid
```

- `pending`：必要identity与integrity validation尚未完成；
- `valid`：Definition binding、semantic resource binding、Subject binding、same-Run references与minimum integrity checks通过，可按各Metric completeness policies形成authoritative evaluation Results，并允许应用frozen Overall / Acceptance policies；
- `invalid`：Definition digest mismatch、cross-Run contamination、identity ambiguity或其他integrity blocker使本Run不能作为authoritative evaluation record。

`valid`不表示execution complete。一个`partial + valid` Run可以合法产生partial/unavailable Metric Results，只要Definition policy允许并完整披露coverage。`completed + invalid`同样可能存在，例如执行结束后发现Definition snapshot与digest不一致。

Definition binding或external semantic resource digest mismatch必须：

```text
Run validity = invalid
+ RuntimeDiagnostic(phase=definition_binding)
```

不得fallback到ID/version、自动更新digest、自动接受loaded Definition、创建Gate Result或创建Contract violation。Integrity mismatch不是evaluation semantic。

### 4.7 Runtime authority precedence

Runtime processing authority固定为：

```text
Definition binding / integrity
↓
Run validity
↓
Result inventory
↓
Overall Score policy application
↓
Acceptance policy application
↓
Scorecard finalization
```

Authoritative Overall Score与authoritative whole-benchmark Acceptance只允许在`validity_status=valid`时产生。

`invalid` Run允许保留Episodes、Artifacts、Evidence、Grader Results、Metric Results、Gate Results、diagnostics与audit Scorecard inventory，但这些不能发布为authoritative final evaluation view。它必须记录Overall / Acceptance为`not_produced_run_invalid`，而不是将invalid改写为`BLOCKED`、Gate `TRIGGERED`或Metric `unavailable`。

`pending` Run可以具有intermediate Runtime objects与interim Scorecard，但不得形成finalized authoritative Overall / Acceptance，也不得让Scorecard表示evaluation complete。不得假设pending最终一定valid。

### 4.8 Run timestamps

保留最小audit timestamps：

- `created_at`：required；
- `started_at`：conditional，进入running或meaningful execution后required；
- `ended_at`：conditional，terminal state时required。

时间戳不得作为attempt ordering、duplicate identity或Result authority。

### 4.9 Minimal Run schema

```text
Run:
- run_id: str
- definition_ref: FrozenDefinitionRef
- subject_ref: SubjectReference
- execution_context: RuntimeExecutionContext
- execution_status: RunExecutionStatus
- validity_status: RunValidityStatus
- validity_findings: list[ValidityFinding]
- created_at: datetime
- started_at: datetime?
- ended_at: datetime?
- episode_ids: list[str]
- diagnostic_ids: list[str]
```

字段 rationale：

- identity、Definition、Subject binding与actual execution context全部required；
- status与validity分离required；
- `validity_findings`可以为空，但`invalid`时必须非空；
- Episode refs保留Run inventory，不能复制Episode内容；
- diagnostics保存system boundary，不进入Gate semantic。

---

## 5. Episode

### 5.1 Definition and creation boundary

Episode是某Test Case在某Run中的一次actual attempt。

当Framework已经：

1. 为该Test Case分配稳定`attempt_index`；并且
2. 建立可审计的attempt record，

即创建Episode。它可以在meaningful subject interaction前变成`blocked`。Case从未被调度时不创建Episode；这由Run plan / Scorecard missing inventory表达，不能伪造`not_exercised` Grader Result。

### 5.2 Deterministic attempt ordering

```text
attempt_index: positive integer
```

规则：

- 在`(run_id, test_case_id)`内unique；
- 从1开始并按attempt admission order单调递增；
- 一旦分配不可修改或复用；
- cancelled、blocked或failed attempt仍占用其index；
- 不从timestamp、file order、UUID lexicographic order或Result arrival order推导。

因此Metric / Gate可以稳定实现first attempt、final attempt与all distinct attempts。

### 5.3 Episode execution status

```text
created
running
completed
blocked
failed
cancelled
```

- `created`：Episode record存在但meaningful execution尚未开始；
- `running`：attempt正在执行；
- `completed`：Runtime完成declared observation window；Subject是否回答、是否产生Artifact、Contract是否满足均由trace / Evidence / Grader Result另行说明；
- `blocked`：meaningful subject execution前被precondition阻止；
- `failed`：attempt期间Runtime / environment execution failure使observation window无法正常完成；
- `cancelled`：明确取消。

不使用`successful`作为Contract-like状态。Runtime success统一表达为`completed`；subject response existence是observation，不是execution-status verdict。

### 5.4 TraceEvent boundary

Interaction Trace与Tool / Action Trace是Episode components，不是Core Objects。

```text
TraceEvent:
- trace_event_id: str
- event_index: int
- actor: str
- event_type: str
- semantic_summary: str?
- content_ref: str?
- tool_ref: str?
- operation: str?
- result_ref: str?
- occurred_at: datetime?
```

规则：

- `event_index`在Episode内unique且单调，提供semantic ordering；
- `actor`区分Subject、user、framework、tool、environment等参与者，但不冻结平台enum；
- `semantic_summary`与`content_ref`至少一个存在；
- tool fields只在tool/action event时出现；
- raw payload或大型content通过reference保存，不直接塞入Episode；
- TraceEvent是runtime observation source，不自动成为Evidence。

### 5.5 Minimal Episode schema

```text
Episode:
- episode_id: str
- run_id: str
- test_case_id: str
- attempt_index: int
- execution_status: EpisodeExecutionStatus
- created_at: datetime
- started_at: datetime?
- ended_at: datetime?
- trace_events: list[TraceEvent]
- artifact_ids: list[str]
- evidence_ids: list[str]
- diagnostic_ids: list[str]
```

Episode不复制Test Case task、fixtures、ExpectedAssertions或Definition policy。它只引用`test_case_id`并记录actual attempt。

---

## 6. Artifact

### 6.1 Definition

Artifact是Run中被产生、消费或观察的persistent runtime object。它不是Evidence，也不承担judgment semantics。

Artifact始终属于一个Run，但不要求只属于一个Episode：

- Run-level environment manifest可以没有Episode relation；
- 一个Episode产生的Artifact可以被后续Episodes消费；
- shared Artifact仍只有一个`artifact_id`，通过relations表达多个Episode关联。

### 6.2 ArtifactRelation

```text
ArtifactRelation:
- relation: produced | consumed | observed
- episode_id: str?
- trace_event_id: str?
- source: str
```

- `episode_id`为空表示Run-level relation；
- `trace_event_id`出现时必须属于同一Episode；
- 一份Artifact可以有多个relations；
- relation不是ownership duplication。

### 6.3 Content boundary

Artifact Schema保存identity + generic locator + metadata，不直接保存大型bytes。

`locator`可以是URI、object-store key、repository-relative locator、content-addressed reference或其他Framework可解析reference，不假设本机path。

### 6.4 Minimal Artifact schema

```text
Artifact:
- artifact_id: str
- run_id: str
- artifact_kind: str
- locator: str
- media_type: str?
- content_digest: str?
- producer: str
- relations: list[ArtifactRelation]
- metadata: map[str, scalar]?
```

字段 rationale：

- identity、Run、kind、locator、producer与至少一项relation required；
- `media_type`可选，因为部分logical Artifact没有IANA media type；
- `content_digest`可选但对immutable integrity strongly recommended；
- metadata只允许small scalar audit claims，不存actual file content或arbitrary nested payload。

---

## 7. Evidence

### 7.1 Definition

Evidence是从某Episode的Artifact、Trace、state或runtime observation中取得，已经满足某Evidence Specification qualification requirements，并可以被Grader合法消费的actual observation package。

```text
Artifact exists
≠ Evidence exists

Trace event exists
≠ Evidence exists
```

### 7.2 Evidence exists only after successful qualification

v0选择严格语义：Evidence object只在qualification成功后存在。

- captured observation + qualification passed → create Evidence；
- captured observation + qualification rejected → retain Artifact / Trace source and create qualification diagnostic；不创建Evidence；
- collector / capture mechanism failed → create collector diagnostic；不创建Evidence；
- no required observation becauseSubject behavior omitted it → 是否构成violation、insufficiency或not-exercised由Grader根据完整observation surface判断，不由collector诊断替代。

因此不创建`Evidence(status=failed)`或`Evidence(status=unqualified)`伪对象。Evidence中的`qualification`记录实际通过的basis，而不是可失败的collector execution state。

### 7.3 EvidenceTargetRef

```text
EvidenceTargetRef:
- test_case_id: str
- contract_id: str
```

只保存`evidence_spec_id`不足，因为一个Evidence Specification可以服务多个target pairs。每份actual Evidence必须显式声明本次qualification服务哪些target applications。

一个Evidence可以在同一Episode内服务多个qualified targets，但每个target仍产生独立Grader Result。Shared Evidence不允许合并Contract judgments。

### 7.4 Cross-Test-Case isolation

每份Evidence必须关联exactly one Episode。由于Episode只对应一个Test Case，所有`qualified_targets[].test_case_id`必须等于Episode的`test_case_id`。

```text
same evidence_spec_id + different episode_id
→ different runtime Evidence
```

Evidence Specification的Definition-level跨Case复用不允许actual Evidence跨Episode自动满足另一Case。

### 7.5 EvidenceSourceRef

```text
EvidenceSourceRef:
- source_type: artifact | trace_event | state_observation | runtime_output
- source_id: str
- locator: str?
- portion_ref: str?
```

- Artifact / Trace source使用同Run、同Episode可解析ID；
- state observation / runtime output使用stable source ID与可选locator；
- `portion_ref`可引用文件片段、message、frame、record range或semantic subsection，但不冻结platform-specific syntax。

### 7.6 Actual observation, provenance, context and qualification

```text
EvidenceObservation:
- summary: str
- content_ref: str?

EvidenceProvenance:
- source_refs: list[EvidenceSourceRef]
- collector: str
- observed_from: str

EvidenceContext:
- context_summary: str
- related_trace_event_ids: list[str]

EvidenceQualification:
- status: qualified
- checks: list[QualificationCheck]
- qualified_by: str
- qualified_at: datetime

QualificationCheck:
- requirement: str
- outcome: passed
- detail: str
```

`status`与`outcome`是fixed-value invariants，用于让serialized object自证其类型边界；任何非passed check都禁止创建Evidence。

### 7.7 Minimal Evidence schema

```text
Evidence:
- evidence_id: str
- run_id: str
- episode_id: str
- evidence_spec_id: str
- qualified_targets: list[EvidenceTargetRef]
- observation: EvidenceObservation
- provenance: EvidenceProvenance
- context: EvidenceContext
- qualification: EvidenceQualification
```

Evidence不复制Evidence Specification requirements，也不保存Grader verdict。

---

## 8. Runtime Diagnostics

Diagnostic是nested runtime record，不是第17个Core Object，也不是semantic Result。

```text
RuntimeDiagnostic:
- diagnostic_id: str
- run_id: str
- episode_id: str?
- phase: definition_binding | environment | collection | grading | metric | gate | scorecard | orchestration
- code: str
- message: str
- related_object_refs: list[ObjectRef]
- occurred_at: datetime
- retryable: bool?
```

它合法记录：

- environment failure；
- collector / qualification failure；
- grader engine failure；
- Metric calculator failure；
- Gate evaluator failure；
- orchestration error；
- Definition / semantic resource binding mismatch；
- identity / integrity validation concern；
- Overall / Acceptance production engine failure。

Diagnostic可以被Run、Episode与Scorecard引用，但不能被Metric或Gate偷偷当作Contract semantic input，除非未来Definition明确建立合法execution-status vocabulary与condition authority。

`definition_binding`是Definition与external semantic resource integrity的最小专用phase。`scorecard`覆盖Overall calculator与Acceptance evaluator production；v0不再为每个nested derived view扩展独立phase enum。System failure不得伪装为Overall semantic unavailable或Acceptance semantic。

---

## 9. Grader Result

### 9.1 Identity and atomicity

Grader Result是最小可聚合evaluation observation。每个Result只判断一个Contract-specific target。

最小identity tuple：

```text
(run_id, episode_id, grader_id, test_case_id, contract_id)
```

`test_case_id`必须等于Episode的Test Case。一个multi-target Grader Specification可以复用policy，但必须为每个target产生separate Result。

### 9.2 Judgment enum

上游语义已经稳定，v0 Runtime Result适合冻结以下actual enum：

```text
satisfied
violated
insufficient_evidence
not_exercised
```

- `satisfied`与`violated`都需要qualified Evidence的affirmative semantic basis；
- `insufficient_evidence`表示required Evidence缺失、unusable或required relation无法建立；
- `not_exercised`只在Episode存在、qualified observation surface足够且能肯定证明trigger / applicability未发生时合法；
- no Episode、Episode blocked、Runtime启动失败或grader engine failure都不是`not_exercised`。

### 9.3 Grader execution failure decision

v0选择：

```text
grader engine failure
→ no GraderResult
+ RuntimeDiagnostic(phase=grading)
```

不创建judgment为空的GraderResult shell。原因：Metric / Gate已经依赖以下关键边界：

```text
Grader Result exists with insufficient_evidence
≠ no Grader Result exists
```

shell会把“semantic Result存在”与“grading operation没有完成”混淆。Engine retry可以在成功emit前重试；成功后只产生一个authoritative immutable Result。

### 9.4 Evidence consumption

`evidence_ids`只引用实际qualified Evidence，不复制内容。Cross-object validation必须确认：

- Evidence属于同一Run与Episode；
- Evidence的`evidence_spec_id`属于对应GraderTarget的`evidence_spec_ids`；
- Evidence的`qualified_targets`包含当前`(test_case_id, contract_id)`；
- substantive judgment满足Definition-time evidence consumption policy；
- insufficiency可以引用已有但不足以完成完整package的Evidence，并在explanation列出missing contributions。

### 9.5 Explanation without hidden chain-of-thought

```text
GraderExplanation:
- evidence_contributions: list[EvidenceContribution]
- observed_facts: list[str]
- semantic_basis: str
- supported_failure_criterion: str?
- supported_failure_mode: str?
- insufficiency_gaps: list[str]
- inference_notes: list[str]

EvidenceContribution:
- evidence_id: str
- contribution: str
```

Explanation保存可审计结论依据，不要求hidden reasoning或chain-of-thought。`supported_failure_mode`只在Evidence支持时出现，不是authoritative verdict，也不能替代`judgment`。

Consistency rules：

- `violated`要求`supported_failure_criterion`；
- `insufficient_evidence`要求非空`insufficiency_gaps`；
- `satisfied / not_exercised`不得伪造failure criterion；
- 所有observed facts与inference notes必须明确分开。

### 9.6 Optional rubric output

v0选择保留一个最小optional structured extension，而不是把future rubric detail塞进free-form explanation：

```text
RubricResult:
- dimensions: list[RubricDimensionResult]
- overall_interpretation: str?

RubricDimensionResult:
- dimension_name: str
- selected_anchor_label: str?
- local_value: number?
- explanation: str
```

只有referenced Grader Specification声明Rubric时才允许出现。它不替代四值`judgment`。由于Rubric真实Runtime validation尚未完成，此nested structure是validation-limited proposal，不构成当前freeze claim。

### 9.7 Minimal GraderResult schema

```text
GraderResult:
- grader_result_id: str
- run_id: str
- episode_id: str
- grader_id: str
- test_case_id: str
- contract_id: str
- evidence_ids: list[str]
- judgment: satisfied | violated | insufficient_evidence | not_exercised
- explanation: GraderExplanation
- rubric_result: RubricResult?
- created_at: datetime
```

---

## 10. Metric Result

### 10.1 Identity and uniqueness

```text
(run_id, metric_id)
```

在一个Run内，一个Metric Specification至多产生一个authoritative Metric Result。重复serialization使用同一`metric_result_id`；重新计算不得创建第二个并列authoritative Result。

### 10.2 Available, unavailable and missing

必须保持三分：

```text
Metric Result exists + status=available
→ canonical value exists

Metric Result exists + status=unavailable
→ semantic calculation completed but value is undefined

no Metric Result
→ calculator did not complete or application was never produced
```

`unavailable`不是engine failure状态。

### 10.3 Canonical value

当前v0只提议支持已经有明确Gate comparison need的numeric domains：

```text
MetricValue:
- value_kind: rate | count | scalar
- canonical_value: number
- unit: str?
- display_value: str?
```

- `canonical_value`是Gate threshold、recalculation audit与cross-Run compatible comparison的唯一numeric authority；
- `display_value`可选，只用于presentation，不得反向改变canonical value；
- rate、count、scalar的range / precision / unit仍由Metric Specification验证；
- ordinal union延后到真实Runtime validation，不在v0假装已稳定。

### 10.4 MetricCoverageSummary

```text
MetricCoverageSummary:
- expected_input_count: int
- available_raw_result_count: int
- distinct_result_count: int
- selected_result_count: int
- substantive_eligible_count: int
- not_exercised_count: int
- insufficient_evidence_count: int
- unavailable_input_count: int
- declared_aggregation_unit: str
- contributing_unit_count: int
- denominator: number?
- coverage_ratio: number?
```

这些字段不是任意`details: dict`。它们分别证明expected population、duplicate removal、selection、eligibility、non-substantive / missing boundary、aggregation unit、denominator与coverage。

`denominator`只在Metric semantics存在denominator时出现；`coverage_ratio`只在Specification定义其numerator / denominator meaning时出现。

### 10.5 Input traceability

```text
MetricInputTrace:
- grader_result_id: str
- disposition: included | excluded
- reason: str
- aggregation_unit_key: str?
- contribution_value: number?

MissingMetricInput:
- test_case_id: str
- contract_id: str
- reason: str
```

- `input_traces`覆盖所有actual selected / examined Grader Results；
- duplicate serialization在进入此列表前按ID去重；
- `included`说明实际参与Metric；
- `excluded`保留not-exercised、insufficient或selection policy exclusion reason；
- `missing_inputs`表示expected MetricInput没有actual Grader Result，因此没有可引用ID；
- Result只引用Grader Results，不复制其Evidence与explanation。

### 10.6 Unavailable reason

```text
MetricUnavailableReason:
- empty_denominator
- completeness_failed
- required_inputs_missing
- incompatible_input_values
```

这是bounded semantic enum。它只描述Metric policy正常执行后为何没有canonical value。Engine crash、timeout、implementation bug或invocation failure禁止进入该enum。

`unavailable_explanation`必须给出具体failed policy / population facts，不能只有enum。

### 10.7 Metric calculator failure decision

```text
Metric calculator failure
→ no MetricResult
+ RuntimeDiagnostic(phase=metric)
```

这保持：

```text
exists but unavailable
≠ missing Result
```

### 10.8 Minimal MetricResult schema

```text
MetricResult:
- metric_result_id: str
- run_id: str
- metric_id: str
- status: available | unavailable
- value: MetricValue?
- unavailable_reason: MetricUnavailableReason?
- unavailable_explanation: str?
- coverage: MetricCoverageSummary
- input_traces: list[MetricInputTrace]
- missing_inputs: list[MissingMetricInput]
- created_at: datetime
```

Consistency rules：

- `available`要求`value`存在且unavailable fields为空；
- `unavailable`禁止`value`，并要求reason + explanation；
- canonical numeric zero是合法value时必须来自Metric semantics，不能用来替代unavailable；
- 所有referenced Grader Results必须属于同一Run。

---

## 11. Gate Result

### 11.1 Identity and uniqueness

```text
(run_id, gate_id)
```

一个Run内一个Gate Specification至多产生一个authoritative Gate Result。

### 11.2 Semantic enum

```text
OPEN
TRIGGERED
INDETERMINATE
```

- `OPEN`：atomic condition determinately false；只表示该Gate未触发，不表示whole Benchmark PASS；
- `TRIGGERED`：condition true，或Definition明确将overall UNKNOWN经`unavailable_handling=triggered`映射为trigger；
- `INDETERMINATE`：overall condition UNKNOWN且`unavailable_handling=indeterminate`；
- 禁止使用PASS / FAIL。

### 11.3 Evaluation path and trigger source

为区分真实condition trigger与unavailable-policy trigger，保存：

```text
GateEvaluationPath:
- condition_true
- condition_false
- unknown_indeterminate
- unknown_triggered
```

确定映射：

```text
condition_true         → TRIGGERED, trigger_source=condition
condition_false        → OPEN,      trigger_source absent
unknown_indeterminate  → INDETERMINATE, trigger_source absent
unknown_triggered      → TRIGGERED, trigger_source=unavailable_handling
```

### 11.4 Source traceability

```text
GateInputSummary:
- condition_type: grader_result | metric_threshold | metric_availability
- grader_contributions: list[GateGraderContribution]
- metric_result_id: str?
- metric_input_state: available | unavailable | missing | not_applicable
- observed_canonical_value: number?
- comparator_outcome: true | false | unknown | not_applicable
- quantifier: any | all | not_applicable
- condition_outcome: true | false | unknown

GateGraderContribution:
- grader_result_id: str?
- target: EvidenceTargetRef
- contribution: MATCH | NON_MATCH | UNKNOWN
- detail: str
```

Direct Grader Gate保存selected Result refs、per-input contribution、quantifier与condition outcome。Missing selected Result使用`grader_result_id: null + UNKNOWN`，不伪造Result。

Metric Gate保存Metric Result ref（若存在）、available / unavailable / missing、comparison summary与observed canonical value。它不复制整个Metric Result。

### 11.5 Gate engine failure decision

```text
Gate evaluator failure
→ no GateResult
+ RuntimeDiagnostic(phase=gate)
```

`INDETERMINATE`是合法condition semantic，不是engine crash fallback。

### 11.6 Minimal GateResult schema

```text
GateResult:
- gate_result_id: str
- run_id: str
- gate_id: str
- result: OPEN | TRIGGERED | INDETERMINATE
- evaluation_path: GateEvaluationPath
- trigger_source: condition | unavailable_handling?
- input_summary: GateInputSummary
- explanation: str
- created_at: datetime
```

所有source Result refs必须属于同一Run；explanation必须说明scope、source results或missing inputs、selection / quantifier或comparator、condition outcome与blocking / indeterminate reason。

---

## 12. Scorecard

### 12.1 Role

Scorecard是一个Run的Result-layer top-level summary与traceability entrypoint。它组织已有Results，并记录由Runtime policy-application layer依据Frozen Benchmark Definition产生的nested derived views；它自身不重新grade、不重新计算Metric internals、不重新evaluate Gates，也不发明或执行隐藏的Overall / Acceptance policy。

```text
Scorecard
≠ hidden evaluator
≠ hidden Overall aggregation policy
≠ hidden Acceptance policy
≠ cross-Run comparison object
```

### 12.2 Result inventory

```text
MissingResultRef:
- result_type: grader | metric | gate
- definition_ref: str
- test_case_id: str?
- contract_id: str?
- diagnostic_ids: list[str]
- explanation: str

ScorecardResultInventory:
- episode_ids: list[str]
- grader_result_ids: list[str]
- metric_result_ids: list[str]
- gate_result_ids: list[str]
- missing_results: list[MissingResultRef]
```

Inventory既列出存在的authoritative Results，也明确预期但缺失的applications。Missing result必须追溯到Run / Episode diagnostic或明确的non-application reason，不得静默消失。

Case Summary与Contract Summary可以由这些refs派生或缓存，但不是新的authoritative Core Results，也不能覆盖target-specific Grader Results。

### 12.3 Frozen policy reference

Overall与Acceptance都通过同一最小nested reference绑定Frozen Definition authority：

```text
DefinitionPolicyRef:
- definition_digest: str
- policy_path: /overall_score_policy | /acceptance_policy
```

`definition_digest`必须等于Run的FrozenDefinitionRef digest。`policy_path`是fixed canonical path，不是自由JSON Pointer，也不创建独立OverallScorePolicy或AcceptancePolicy ID。

### 12.4 OverallScoreOutcome

Overall Score不再是裸numeric optional field，而是Scorecard nested derived view：

```text
OverallEvaluationStatus:
- disabled
- available
- unavailable
- not_produced_run_pending
- not_produced_run_invalid
- production_failed

OverallScoreOutcome:
- policy_ref: DefinitionPolicyRef
- evaluation_status: OverallEvaluationStatus
- canonical_value: decimal?
- contribution_traces: list[OverallMetricContributionTrace]
- total_selected_weight: decimal?
- available_weight: decimal?
- available_weight_fraction: decimal?
- minimum_required_weight_fraction: decimal?
- final_included_denominator: decimal?
- unavailable_reason: OverallUnavailableReason?
- explanation: str

OverallMetricContributionTrace:
- metric_id: str
- weight: decimal
- metric_result_id: str?
- application_state: available | unavailable | missing
- policy_handling: included | overall_unavailable | exclude_and_renormalize
- normalized_value: decimal?
- weighted_contribution: decimal?
- exclusion_reason: str?

OverallUnavailableReason:
- participating_metric_unavailable
- participating_metric_missing
- available_weight_below_minimum
- empty_included_set
```

`OverallScoreOutcome`不是第17个Core Object，没有独立authoritative identity；它由`run_id + policy_ref`确定，并嵌套在Scorecard中。

Conditional rules：

- `disabled`：valid Run且policy mode为disabled；禁止canonical value、weight fields与contribution traces；
- `available`：valid Run且weighted policy成功产生canonical value；要求complete traces、weight fields与value；
- `unavailable`：valid Run且policy正常求值得出semantic unavailable；禁止canonical value，要求policy reason、trace与coverage fields；
- `not_produced_run_pending`：Run pending；没有final authoritative value或semantic unavailable；
- `not_produced_run_invalid`：Run invalid；没有authoritative Overall semantic；
- `production_failed`：valid Run进入policy application后，Overall calculator发生system failure；禁止canonical value与semantic unavailable reason，必须关联`RuntimeDiagnostic(phase=scorecard)`。

### 12.5 Overall disabled, available and unavailable

当`overall_score_policy.mode=disabled`时，Scorecard必须显式记录`evaluation_status=disabled`。不得平均所有Metrics、输出0、使用ambiguous null或报告calculator failure。

当`mode=weighted_normalized_mean`时，Runtime只消费Frozen policy显式列出的Metric IDs、actual canonical Metric Result values、normalization、cross-Metric weights、unavailable / missing handling与minimum coverage。

`display_value`、UI percentage与formatted number永远不能参与Overall。Metric内部weighting也不能冒充cross-Metric weight。Runtime引用Benchmark Definition v0.2公式，不在本Guide重新定义formula或rounding protocol。

必须保持：

```text
MetricResult exists + unavailable
≠ expected MetricResult missing
≠ Overall calculator failure
```

如果frozen policy得出Overall unavailable，`OverallScoreOutcome`仍然存在并使用`evaluation_status=unavailable`，但不含`canonical_value`。不得用0、NaN或ambiguous null表示。

### 12.6 Exclude-and-renormalize trace

使用`exclude_and_renormalize`时，contribution traces与weight fields必须共同证明：selected Metric IDs、available Metric Result IDs、excluded unavailable Metric Result IDs、missing Metric applications、each cross-Metric weight、normalized contributions、available weight fraction、minimum required fraction与final included denominator。

Trace只引用Metric Result ID与必要derived numbers，不复制完整Metric Results。Missing application没有Metric Result ID。

### 12.7 Overall engine failure boundary

```text
Overall calculator implementation failure
→ OverallScoreOutcome.evaluation_status = production_failed
+ RuntimeDiagnostic(phase=scorecard)
→ no authoritative Overall available / unavailable semantic
```

`scorecard` phase足以覆盖nested Overall production，不增加独立`overall` phase。Engine crash、timeout、bug或invocation failure不能成为Metric unavailable、Overall unavailable或canonical value 0。

### 12.8 AcceptanceEvaluation

Whole-benchmark acceptance不再是裸optional status，而是Scorecard nested derived view：

```text
AcceptanceEvaluationStatus:
- disabled
- produced
- not_produced_run_pending
- not_produced_run_invalid
- production_failed

AcceptanceSemantic:
- ACCEPTABLE
- BLOCKED
- INDETERMINATE

AcceptanceEvaluation:
- policy_ref: DefinitionPolicyRef
- evaluation_status: AcceptanceEvaluationStatus
- acceptance: AcceptanceSemantic?
- gate_contributions: list[AcceptanceGateContributionTrace]
- explanation: str

AcceptanceGateContributionTrace:
- gate_id: str
- gate_result_id: str?
- application_state: OPEN | TRIGGERED | INDETERMINATE | MISSING
- policy_handling: open | actual_triggered | overall_indeterminate | overall_blocked
- propagation_outcome: no_block | blocked | indeterminate
- explanation: str
```

`AcceptanceEvaluation`不是Core Object，也没有独立authoritative identity；它由`run_id + policy_ref`确定。`acceptance`只在`evaluation_status=produced`时存在，并且只能是`ACCEPTABLE | BLOCKED | INDETERMINATE`。禁止PASS、FAIL、INVALID或NOT_EVALUABLE。

Conditional rules：

- `disabled`：valid Run且policy mode为disabled；禁止acceptance与gate contributions；
- `produced`：valid Run且gate-based evaluation完成；要求acceptance与complete gate traces；
- `not_produced_run_pending`：Run pending；禁止acceptance；
- `not_produced_run_invalid`：Run invalid；禁止acceptance；
- `production_failed`：valid Run进入Acceptance application后implementation失败；禁止acceptance，要求`RuntimeDiagnostic(phase=scorecard)`。

Acceptance production failure不是BLOCKED或INDETERMINATE semantic，也不得fabricate Gate Result。

### 12.9 Acceptance disabled and gate-based

当`acceptance_policy.mode=disabled`时，valid Run必须显式记录`evaluation_status=disabled`。Valid Run不会自动变成ACCEPTABLE；合法zero-Gate Benchmark也不使用vacuous truth产生ACCEPTABLE。这正式消费Benchmark Definition v0.2删除`validity_only`的决定。

当`mode=gate_based`时，Runtime只消费`participating_gates`显式列出的Gate IDs及其actual Gate Results。不得自动读取all Gates、使用Gate scope或name selector、重新evaluate Gate，或回读Metric、Grader、Evidence来重建Gate semantic。

每个participating Gate application只能分类为`OPEN | TRIGGERED | INDETERMINATE | MISSING`。

### 12.10 Acceptance propagation and scope

对valid Run，传播precedence固定为：

```text
any actual TRIGGERED
→ BLOCKED

otherwise any INDETERMINATE/MISSING mapped to overall_blocked
→ BLOCKED

otherwise any INDETERMINATE/MISSING mapped to overall_indeterminate
→ INDETERMINATE

otherwise all participating Gate Results exist and are OPEN
→ ACCEPTABLE
```

Explanation与trace必须区分actual `GateResult=TRIGGERED`导致blocked，以及AcceptancePolicy把INDETERMINATE或MISSING fail-closed映射为blocked。

Missing application只有expected `gate_id`、MISSING state与policy handling，没有`gate_result_id`。不得fabricate `GateResult(INDETERMINATE)`。

`Gate.scope`定义local blocking scope；只有`gate_id ∈ acceptance_policy.participating_gates`时，该Gate才传播到whole Benchmark。Runtime不得看到任意Gate TRIGGERED就自动推导Benchmark BLOCKED。

Gate evaluator failure保持：

```text
no GateResult
+ RuntimeDiagnostic(phase=gate)
→ participating application state = MISSING
→ apply frozen missing_result_handling
```

这允许AcceptancePolicy对required result absence fail closed，但engine failure本身没有被转换为Gate semantic。

### 12.11 Overall and Acceptance independence

AcceptancePolicy不消费Overall Score。Runtime不得添加Overall threshold：

```text
Overall = 0.95
+ participating Gate TRIGGERED
→ Overall remains 0.95
→ Acceptance BLOCKED

low Overall
+ all participating Gates OPEN
→ Acceptance ACCEPTABLE
```

### 12.12 Scorecard finalization and minimal schema

```text
ScorecardFinalizationStatus:
- interim
- finalized_evaluation
- finalized_audit
```

```text
Scorecard:
- scorecard_id: str
- run_id: str
- definition_ref: FrozenDefinitionRef
- subject_ref: SubjectReference
- result_inventory: ScorecardResultInventory
- diagnostic_ids: list[str]
- overall_score_outcome: OverallScoreOutcome
- acceptance_evaluation: AcceptanceEvaluation
- finalization_status: ScorecardFinalizationStatus
- finalized_at: datetime?
```

Rules：

- pending Run只能使用`interim`，两个nested views分别为`not_produced_run_pending`；
- valid Run只有在Overall处于`disabled | available | unavailable`且Acceptance处于`disabled | produced`时，才可使用`finalized_evaluation`；
- valid Run若任一nested view为`production_failed`，可以在保留diagnostics后使用`finalized_audit`，但不能声称final evaluation complete；
- invalid Run可以使用`finalized_audit`，两个nested views分别为`not_produced_run_invalid`；
- `finalized_at`只在两个finalized states存在；
- Scorecard finalized不等于evaluation valid；
- `definition_ref`与`subject_ref`是Run refs的traceable copy，必须完全相等，不能成为第二套authority。

Scorecard最终只组织Run identity、Frozen Definition identity、Subject identity、Episode inventory、Grader / Metric / Gate Results、missing expected applications、diagnostics、OverallScoreOutcome与AcceptanceEvaluation。它不得regrade、recompute Metric internals、reevaluate Gate、invent policies或cross-Run compare。

---

## 13. Result Uniqueness and Immutability

### 13.1 Authoritative uniqueness

| Object | Authoritative uniqueness within current model |
|---|---|
| Episode | `(run_id, test_case_id, attempt_index)` and `episode_id` |
| Grader Result | `(run_id, episode_id, grader_id, test_case_id, contract_id)` |
| Metric Result | `(run_id, metric_id)` |
| Gate Result | `(run_id, gate_id)` |
| Scorecard | `run_id` |
| OverallScoreOutcome | nested only；derived by `(run_id, definition_digest, /overall_score_policy)` |
| AcceptanceEvaluation | nested only；derived by `(run_id, definition_digest, /acceptance_policy)` |

OverallScoreOutcome与AcceptanceEvaluation没有独立ID、独立storage identity或Core Object status。它们随Scorecard保持one-per-Run derived uniqueness。

### 13.2 Immutable v0 policy

Authoritative Runtime / Result objects一旦finalized不得in-place mutate。

- transient engine retry在成功emit authoritative object前允许；
- same logical object重复写出必须保留同一ID与相同content digest；
- 成功emit后发现需要重新grade、recalculate或reevaluate时，v0不创建并列authoritative revision；
- 需要改变Definition、Subject identity、Episode facts或authoritative Results时，创建new Run；
- event sourcing、result revision graph与supersession本轮不设计。

这是v0为保持uniqueness与reproducibility选择的简单政策。真实validation必须检验“regrade without re-execution”是否需要未来受控revision extension；在此之前不加入revision fields。

---

## 14. Referential Integrity

### 14.1 Run and Definition

- Run只引用一个Frozen Definition；
- ID、version、closure profile与digest全部匹配；
- profile必须是`skill-eval-frozen-definition-closure-v0`；
- loaded Definition按v0.2 protocol重新计算的digest必须匹配Run ref；
- external semantic resource content digests必须匹配v0.2 bindings；
- digest mismatch使Run invalid，即使execution completed；
- Definition或resource integrity mismatch只产生validity finding + definition-binding diagnostic，不产生Contract、Metric或Gate semantic；
- Scorecard definition ref必须完全等于Run ref。

### 14.2 Episode

- Episode属于一个Run；
- Test Case存在于Run绑定Definition；
- `(run_id, test_case_id, attempt_index)` unique；
- all Episode child refs属于same Run。

### 14.3 Artifact

- Artifact属于一个Run；
- optional Episode / Trace relations属于same Run；
- locator存在不证明Evidence qualification。

### 14.4 Evidence

- Evidence属于一个Run和exactly one Episode；
- Evidence Specification存在于Run Definition；
- qualified target pair属于该Specification targets；
- target Test Case等于Episode Test Case；
- all sources可解析到same Run / Episode合法observation surface。

### 14.5 Grader Result

- Grader Specification与target pair存在；
- Episode与target Test Case一致；
- Evidence refs属于same Run / Episode；
- Evidence Spec set与GraderTarget consumption authority一致；
- one Result只判断one Contract target。

### 14.6 Metric Result

- Metric Specification存在于Run Definition；
- actual Grader Result refs属于same Run；
- refs符合MetricInput population、duplicate removal、selection、eligibility与unit policy；
- missing inputs不能伪造成insufficient Grader Results。

### 14.7 Gate Result

- Gate Specification存在于Run Definition；
- source refs符合condition variant；
- all source Results属于same Run；
- canonical Metric value是threshold authority；
- Result、evaluation path与trigger source一致。

### 14.8 Scorecard

- Scorecard只对应one Run；
- listed Results与Episodes属于same Run；
- authoritative Result set没有duplicate IDs；
- expected but missing Result applications显式进入missing inventory；
- two policy refs必须使用Run definition digest与fixed canonical path；
- Overall contribution Metric refs全部属于same Run并匹配explicit policy membership；
- Acceptance Gate refs全部属于same Run并匹配explicit participating Gates；
- finalization status与Run validity一致；
- invalid / pending Run没有authoritative Overall或Acceptance semantic。

---

## 15. Three-Layer Runtime / Result Validation

### 15.1 A. Structural Validation

至少检查：

- IDs非空、格式合法、object-level unique；
- required fields存在；
- timestamps满足created / started / ended条件；
- status / value conditional fields一致；
- attempt index为positive integer；
- list IDs无exact duplicate；
- terminal state具有`ended_at`；
- `invalid` Run具有validity finding；
- Evidence qualification只有qualified / passed fixed values；
- Metric available / unavailable field combinations合法；
- Gate Result / evaluation path / trigger source组合合法；
- FrozenDefinitionRef profile与digest格式合法；
- RuntimeDiagnostic phase使用bounded enum；
- Overall evaluation status与conditional value / trace / reason fields一致；
- Acceptance evaluation status与conditional acceptance / trace fields一致；
- policy path只允许两个frozen canonical paths；
- Scorecard finalization status与`finalized_at`组合合法。

### 15.2 B. Cross-object Validation

至少检查：

- Run Definition ID / version / profile / digest解析与匹配；
- external semantic resource digests匹配Definition bindings；
- exactly one Subject ref；
- Episode Test Case存在；
- attempt ordering unique、stable且不由timestamp推导；
- Artifact relations属于same Run；
- Evidence Spec与qualified target membership合法；
- Evidence跨Test-Case隔离；
- Grader target、Evidence consumption与Episode一致；
- Metric population、selected Results与same-Run closure；
- Gate source condition与actual Result refs一致；
- Scorecard包含全部实际authoritative Results且显式记录expected missing applications；
- Overall只引用explicit selected Metric Results并使用canonical values；
- Acceptance只引用explicit participating Gate Results；
- Overall / Acceptance policy refs解析到Run绑定Definition；
- invalid / pending Run production status与validity一致；
- 不存在cross-Run Result aggregation。

### 15.3 C. Semantic Validation

至少检查：

- execution status没有冒充judgment；
- completion与validity没有混合；
- Subject reference足以支撑declared reproducibility claim；
- Artifact没有自动升级为Evidence；
- captured-but-unqualified与capture failure没有伪造Evidence；
- Shared Evidence没有合并target judgments；
- insufficient evidence与grader failure分开；
- Metric unavailable、missing Result与calculator failure分开；
- canonical Metric value与display value分开；
- Metric coverage / denominator没有隐藏excluded或missing population；
- Gate INDETERMINATE与engine failure分开；
- Gate condition trigger与unavailable-policy trigger可解释；
- Gate OPEN没有被解释为whole Benchmark PASS；
- Overall disabled、available、unavailable、run-invalid、run-pending与production failure分开；
- Metric unavailable、Metric missing与Overall engine failure没有混用；
- Overall只消费Frozen Definition v0.2 policy，没有隐藏aggregation authority；
- Acceptance disabled不会把valid Run变成ACCEPTABLE；
- whole-benchmark acceptance只从explicit participating Gates传播；
- Gate MISSING没有被伪造成INDETERMINATE Result；
- actual Gate trigger与policy fail-closed explanation可区分；
- Overall与Acceptance保持独立；
- invalid Run没有被解释为BLOCKED；
- Scorecard finalized没有被解释为Run valid；
- Definition / resource digest mismatch没有进入evaluation semantics；
- duplicate identity没有按payload equality判断；
- cross-Run comparison没有污染单Run Result。

---

## 16. Runtime / Result Design Workflow

### Step 1 — Verify frozen inputs

确认Benchmark Definition v0.2以及Concept Model、Requirement、Contract、Test Case、Evidence、Grader、Metric、Gate Definition designs当前有效。Runtime只引用Definition authority；任何upstream concern只记录Finding，不回改frozen Guide。

### Step 2 — Establish Run identity

绑定Definition ID / version / closure profile / digest与exactly one Subject；验证external semantic resources；定义execution context、status、validity与timestamps。

### Step 3 — Establish attempt model

定义Episode creation boundary、deterministic attempt index、execution state与trace component boundary。

### Step 4 — Establish observation model

区分Artifact、raw trace、qualified Evidence、qualification rejection与collector failure。

### Step 5 — Establish atomic Grader Result

固定target-specific identity、four-value semantic、Evidence refs、explanation与engine-failure boundary。

### Step 6 — Establish Metric Result

固定available / unavailable / missing三分、canonical numeric authority、coverage、selection trace与calculator-failure boundary。

### Step 7 — Establish Gate Result

固定OPEN / TRIGGERED / INDETERMINATE、evaluation path、source refs、condition summary与engine-failure boundary。

### Step 8 — Establish Scorecard views

组织Run Results、missing applications与diagnostics；按Run validity与Frozen policies形成status-aware OverallScoreOutcome、AcceptanceEvaluation和evaluation/audit finalization。

### Step 9 — Validate

执行Structural、Cross-object、Semantic三层method checks与focused consistency review，记录Schema / Architecture Findings；本轮不执行real validation subset。

### Step 10 — Determine status and stop

只输出Design status，不开始Pydantic、CLI、engine、storage或UI。

---

## 17. Design Status

当前method-stage status只允许：

```text
RUNTIME_RESULT_DESIGN_BLOCKED
RUNTIME_RESULT_DESIGN_METHOD_READY_FOR_REAL_VALIDATION
```

### 17.1 RUNTIME_RESULT_DESIGN_METHOD_READY_FOR_REAL_VALIDATION

只有以下条件全部满足才允许：

- eight Core Object schemas与nested records完成method-level三层consistency review；
- immutable Definition binding protocol已被Runtime Design完整消费；
- Subject identity足以审计；
- all execution / semantic failure boundaries稳定；
- Result uniqueness与same-Run integrity稳定；
- Scorecard所有authoritative final views都有frozen Definition authority；
- Architecture Findings的authority已被Runtime Design消费；
- no unresolved generic method blocker；
- representative real validation coverage已经明确。

该status表示method已经适合进入下一阶段真实validation，不表示真实validation通过、implementation ready或design frozen。

### 17.2 RUNTIME_RESULT_DESIGN_BLOCKED

例如：

- Definition digest无法产生或验证；
- attempt order不确定；
- collector / grader / Metric / Gate failure被吞入semantic Result；
- same-Run closure无法保证；
- canonical Metric value不明确；
- Scorecard被要求产生Overall Score但无aggregation authority；
- Scorecard被要求产生whole-benchmark acceptability但无acceptance authority；
- two conforming implementations可能产生不同authoritative Result。

### 17.3 Reserved post-validation wording

只有真实subset validation通过时才可写：

```text
RUNTIME_RESULT_DESIGN_READY for validation subset
```

它不等于production READY，也不表示完整Target Benchmark、implementation或Runtime PASS。

### 17.4 Current v0 status

本轮完成Definition authority integration、nested Scorecard views、focused consistency review与Self-Review，没有执行真实Runtime validation，因此不声明`RUNTIME_RESULT_DESIGN_READY`或freeze。

当前结论是：

```text
RUNTIME_RESULT_DESIGN_METHOD_READY_FOR_REAL_VALIDATION
```

原有Overall authority、Acceptance authority与canonical digest protocol三个generic blockers已经由Benchmark Definition v0.2提供authority，并被本Guide正式消费。本轮未发现新的generic method blocker。

仍未完成：Runtime real validation、digest implementation conformance validation、Runtime binding validation、calculator / evaluator implementation validation。因此本Guide仍不是`RUNTIME_RESULT_DESIGN_READY`，也不是`RUNTIME_RESULT_DESIGN_FROZEN`。

---

## 18. Schema Findings

### SF-RR-001 — Definition digest is required

`benchmark_id + version`不足以防止same-version content drift。Run必须保存required closure profile与`definition_digest`；snapshot locator只能辅助检索。Runtime必须conform to Benchmark Definition v0.2 protocol，不在本Guide复制canonical rules。

### SF-RR-002 — Subject is a nested hybrid reference

Opaque `subject_ref`提供generic extensibility；small structured kind / version / digest claims提供auditability。无需Subject Core Object，也不绑定Git commit。

### SF-RR-003 — Execution and validity require separate fields

单一status无法表达`completed + invalid`或`partial + valid`。`execution_status`与`validity_status`均为required。

### SF-RR-004 — Attempt index is required Runtime authority

first / final / all attempts需要stable deterministic ordering。`attempt_index`不能由timestamp替代。

### SF-RR-005 — Trace is nested, ordered and reference-oriented

Interaction / Tool traces不升级为Core Objects。Episode内`TraceEvent`具有stable identity与event order，并通过refs避免大型payload内嵌。

### SF-RR-006 — Artifact belongs to Run with relations

Artifact不强制exactly one Episode ownership。Run-level identity + zero-or-more Episode relations支持run-level与shared Artifacts。

### SF-RR-007 — Evidence object means qualified

Unqualified capture与collector failure不应扩展Evidence status enum；它们由source object + diagnostic表达。这保持Evidence的Core definition稳定。

### SF-RR-008 — Actual Evidence needs explicit qualified targets

`evidence_spec_id`不能消除multi-target ambiguity。`qualified_targets`保存actual target applications；一份Evidence可服务多个same-Episode targets。

### SF-RR-009 — Grader Result freezes four stable meanings

上游已经稳定定义`satisfied / violated / insufficient_evidence / not_exercised`，适合成为actual Result enum。Engine failure不进入该enum。

### SF-RR-010 — Failed engines produce diagnostics, not shell Results

Grader、Metric与Gate engine failure都形成no Result + diagnostic。这样保留existing-but-semantic与missing-result边界。

### SF-RR-011 — Rubric output is optional and validation-limited

最小structured extension优于free-form垃圾桶，但其Runtime adequacy尚未真实validation，不阻塞binary semantic core validation。

### SF-RR-012 — Metric Result needs explicit availability and canonical value

`available | unavailable`与object absence分开；available时`canonical_value`是唯一threshold authority。

### SF-RR-013 — Metric transparency needs a bounded structure

Expected、raw、distinct、selected、eligible、NE、insufficient、unavailable、unit、denominator与coverage counts具有不同audit meaning，不能藏在`details: dict`。

### SF-RR-014 — Gate Result needs evaluation path

单一TRIGGERED值无法区分condition true与UNKNOWN经unavailable policy触发。`evaluation_path`与conditional`trigger_source`是最小explanation structure。

### SF-RR-015 — Scorecard needs explicit missing-result inventory

只列出已存在Results会隐藏engine failure与non-application。Scorecard必须同时列出existing refs与expected missing applications。

### SF-RR-016 — Authoritative objects are immutable in v0

当前不增加revision / supersession fields。Regrade-without-reexecution作为future validation limitation记录，不提前设计event sourcing。

### SF-RR-017 — Overall is a status-aware nested derived view

裸optional numeric无法区分disabled、semantic unavailable、Run invalid/pending与production failure。OverallScoreOutcome显式保存production state、canonical value条件、policy ref与bounded contribution trace，但不成为新Core Object。

### SF-RR-018 — Acceptance is separate from Run validity

AcceptanceEvaluation只消费Frozen AcceptancePolicy与explicit participating Gate Results。Disabled不会让valid Run自动ACCEPTABLE；invalid Run也不会变成BLOCKED。

### SF-RR-019 — Missing and engine failure remain non-semantic facts

Missing Metric / Gate application使用absence + trace表达；calculator / evaluator crash使用RuntimeDiagnostic表达。Policy可以对absence fail closed，但不能fabricate Result semantic。

### SF-RR-020 — Scorecard finalization has evaluation and audit forms

`finalized_evaluation`与`finalized_audit`分开，使invalid Run可以产生完整audit inventory，同时禁止authoritative Overall / Acceptance。Scorecard finalized不再被误解为Run valid。

### SF-RR-021 — Two derived views reuse digest plus canonical path

`definition_digest + /overall_score_policy`或`definition_digest + /acceptance_policy`已经足以绑定authority，无需增加独立policy ID、Overall Core Object或Acceptance Core Object。

---

## 19. Architecture Findings

### AF-RR-001 — Overall Score authority consumption

```text
Status:
ARCHITECTURE_AUTHORITY_CONSUMED_BY_RUNTIME_DESIGN

Upstream authority:
BenchmarkDefinition.overall_score_policy

Runtime consumption:
OverallScoreOutcome
```

Runtime Design现在显式消费disabled / weighted policy、Metric membership、normalization、cross-Metric weights、unavailable / missing handling、coverage、canonical scale与precision。它不重新定义formula，不使用display value，也不让Gate改变Overall。

Not CLOSED：仍需Runtime real validation与Overall calculator conformance validation。

### AF-RR-002 — Whole-benchmark Acceptance authority consumption

```text
Status:
ARCHITECTURE_AUTHORITY_CONSUMED_BY_RUNTIME_DESIGN

Upstream authority:
BenchmarkDefinition.acceptance_policy

Runtime consumption:
AcceptanceEvaluation
```

Runtime Design现在只从explicit participating Gates传播actual TRIGGERED、INDETERMINATE与MISSING，并保持disabled、zero-Gate、Run validity precedence和scope propagation。它不读取Overall、Metric、Grader或Evidence来发明Acceptance。

Not CLOSED：仍需Runtime real validation与Acceptance evaluator conformance validation。

### AF-RR-003 — Frozen Definition digest authority consumption

```text
Status:
ARCHITECTURE_AUTHORITY_CONSUMED_BY_RUNTIME_DESIGN

Upstream authority:
complete Frozen Definition Closure
+ skill-eval-frozen-definition-closure-v0
+ canonical digest protocol

Runtime consumption:
FrozenDefinitionRef
+ pre-execution binding validation
```

Runtime Design现在要求ID、version、profile与digest四者匹配，并把Definition / semantic resource mismatch稳定映射为Run invalid + definition-binding diagnostic。Runtime只要求implementation conform，不复制canonicalization protocol。

Not CLOSED：仍需digest implementation independent conformance validation与Runtime binding real validation。

### Combined status

三个finding都已从`ARCHITECTURE_AUTHORITY_DEFINED_AND_VALIDATED`提升为：

```text
ARCHITECTURE_AUTHORITY_CONSUMED_BY_RUNTIME_DESIGN
```

它们仍不是`CLOSED`，也没有因此开始implementation。

---

## 20. Method Self-Review

| # | Question | Authority-integration finding |
|---:|---|---|
| 1 | Runtime是否只consume Definition authority？ | 是。v0.2是composition、Overall、Acceptance、closure与digest唯一authority；Runtime不重定义。 |
| 2 | FrozenDefinitionRef是否完整？ | 是。包含ID、version、closure profile、digest与optional retrieval-only snapshot ref。 |
| 3 | digest mismatch是否稳定进入Run validity？ | 是。Run invalid + definition-binding diagnostic；没有fallback或semantic conversion。 |
| 4 | Definition resource mismatch是否不会进入evaluation semantics？ | 是。它是integrity concern，不是Artifact、Evidence、Contract或Gate semantic。 |
| 5 | Overall disabled/available/unavailable是否分开？ | 是，分别使用独立evaluation statuses与conditional fields。 |
| 6 | missing Metric是否与unavailable分开？ | 是。Missing没有MetricResult ID；unavailable引用actual Result。 |
| 7 | Overall engine failure是否与semantic unavailable分开？ | 是。`production_failed + scorecard diagnostic`，不使用OverallUnavailableReason。 |
| 8 | canonical Metric values是否唯一authority？ | 是。display/UI/formatted values禁止参与Overall。 |
| 9 | Overall trace是否足够？ | Method层足够：membership、Result IDs/absence、weights、normalization contributions、coverage、threshold与denominator全部可追踪；仍需real validation。 |
| 10 | Acceptance disabled是否稳定？ | 是。显式disabled，不产生acceptance semantic。 |
| 11 | zero-Gate valid Run是否不会自动ACCEPTABLE？ | 是。使用disabled，不使用vacuous truth或validity_only。 |
| 12 | Gate TRIGGERED是否只在explicit membership下传播？ | 是。非participating Gate不会自动影响whole Benchmark。 |
| 13 | Gate INDETERMINATE是否按policy处理？ | 是，映射到overall indeterminate或fail-closed blocked。 |
| 14 | missing Gate Result是否按missing policy处理？ | 是，MISSING独立于INDETERMINATE。 |
| 15 | Gate evaluator failure是否不会变INDETERMINATE？ | 是。no GateResult + gate diagnostic；Acceptance看到MISSING。 |
| 16 | policy fail-closed与actual Gate trigger是否可解释区分？ | 是。trace的application state、policy handling与explanation分开。 |
| 17 | invalid Run是否不会变BLOCKED？ | 是。使用not-produced statuses与audit Scorecard。 |
| 18 | Overall与Acceptance是否独立？ | 是。Acceptance不消费Overall；Gate也不修改Overall。 |
| 19 | Scorecard是否仍只是Result organizer？ | 是。它组织Results与policy-application outputs，不执行隐藏计算、不重算Metric/Gate内部semantic或发明authority。 |
| 20 | 是否出现新的Architecture gap？ | 否。Focused consistency review没有发现new generic blocker。 |
| 21 | 是否需要新Core Object？ | 否。OverallScoreOutcome与AcceptanceEvaluation都是Scorecard nested derived views。 |
| 22 | 是否已经适合进入real Runtime validation？ | 是，状态为`RUNTIME_RESULT_DESIGN_METHOD_READY_FOR_REAL_VALIDATION`；不表示validation已完成。 |

### 20.1 Self-review corrections incorporated

本轮Self-Review已经在proposal中处理：

- 为防same-version drift，增加required Definition digest；
- 为防Git-only Subject model，选择opaque ref + structured claims；
- 为防completion冒充validity，拆分两类status；
- 为防timestamp排序不确定，加入attempt index；
- 为防相同payload被误去重，固定ID-based duplicate invariant；
- 为支持run-level/shared Artifact，采用Run ownership + relations；
- 为保持Evidence定义，拒绝failed / unqualified Evidence shell；
- 为防multi-target ambiguity，actual Evidence加入qualified target pairs；
- 为防shared Evidence合并judgment，固定target-specific Grader Result；
- 为防engine failure污染semantics，统一no Result + diagnostic；
- 为防Metric unavailable与missing混淆，区分object status与absence；
- 为防display rounding改变Gate，固定canonical Metric value；
- 为防Metric audit metadata垃圾桶化，定义bounded Coverage Summary；
- 为防Gate trigger reason丢失，加入evaluation path；
- 为防Scorecard隐藏missing Results，加入missing inventory；
- 为防Scorecard创造authority，Overall与Acceptance均使用definition digest + canonical policy path；
- 为防裸optional numeric混淆，Overall改为status-aware nested outcome；
- 为防validity_only回流，Acceptance disabled不产生ACCEPTABLE；
- 为防scope自动扩大，只有explicit participating Gates传播到whole Benchmark；
- 为防invalid Run变成performance verdict，引入evaluation / audit finalization区分；
- 为防Definition integrity进入evaluation semantics，引入definition-binding diagnostic phase；
- 为防Overall engine crash冒充semantic unavailable，引入production_failed state；
- 为防过早复杂化，v0不设计revision graph、event sourcing、comparison object或storage。

### 20.2 Current self-review conclusion

Run、Episode、Artifact、Evidence、GraderResult、MetricResult、GateResult、Scorecard以及两个nested derived views已经形成一致的method / Schema Proposal，未发现需要第17个Core Object的理由。

Benchmark Definition v0.2已经提供Overall、Acceptance与canonical digest authority；本Guide已经正式消费它们。A–J focused consistency review全部通过，未发现新的generic method blocker。

因此当前status提升为`RUNTIME_RESULT_DESIGN_METHOD_READY_FOR_REAL_VALIDATION`，但不宣称Runtime real validation通过、implementation READY或design frozen。下一阶段只能建立representative real validation subset；在该阶段明确授权前不得开始Pydantic implementation。

---

## 21. Focused Cross-Document Consistency Review

本轮只做Benchmark Definition v0.2与Runtime / Result method的paper consistency execution，不创建Run fixture、不运行calculator / evaluator / digest implementation。`PASS`表示两个设计文档对scenario给出同一唯一结论，不表示Runtime real validation PASS。

| Scenario | Definition authority consumed | Runtime / Result conclusion | Result |
|---|---|---|---|
| A Overall disabled | `overall_score_policy.mode=disabled` | OverallScoreOutcome=`disabled`；no value；no calculator failure | PASS |
| B Metric unavailable | contribution unavailable handling | actual unavailable MetricResult按policy处理；不等于calculator crash | PASS |
| C Metric missing | contribution missing handling | absence按missing policy处理；不伪造unavailable MetricResult | PASS |
| D high Overall + Gate TRIGGERED | Overall / Acceptance independent | Overall保持原值；explicit participating trigger使Acceptance BLOCKED | PASS |
| E Acceptance disabled | `acceptance_policy.mode=disabled` | valid Run不自动ACCEPTABLE；zero-Gate合法 | PASS |
| F Gate INDETERMINATE | explicit indeterminate handling | 映射为INDETERMINATE或policy fail-closed BLOCKED | PASS |
| G Gate missing | explicit missing handling | trace MISSING；不伪造INDETERMINATE GateResult | PASS |
| H invalid Run | Run validity precedence | no authoritative Overall / Acceptance；audit inventory可保留 | PASS |
| I Definition digest mismatch | closure profile + digest protocol | Run invalid + diagnostic；不转Gate | PASS |
| J semantic resource digest mismatch | resource binding integrity | Run validity concern；不转Artifact/Evidence/Contract/Gate semantic | PASS |

Focused consistency decision：

```text
A–J: PASS
new generic architecture blocker: NONE
new Core Object required: NO
Runtime real validation executed: NO
```

---

## 22. Future Real Validation Coverage

后续至少需要覆盖：

1. completed + valid ordinary Run；
2. completed + invalid Definition digest mismatch；
3. zero-Episode blocked Run；
4. partial + valid Run；
5. same Test Case first / final / all distinct attempts；
6. duplicate Episode / Result serialization；
7. Run-level Artifact与跨Episode shared Artifact；
8. captured observation qualified、rejected与collector failure三分；
9. one Evidence serving multiple same-Episode targets；
10. same Evidence Spec across different Episodes的isolation；
11. completed Episode + violated Grader Result；
12. insufficient Evidence vs grader engine failure；
13. Metric available zero、unavailable empty denominator与calculator crash；
14. Metric first/final/all selection与coverage audit；
15. Gate condition-triggered与unavailable-policy-triggered；
16. Gate INDETERMINATE vs evaluator crash；
17. Scorecard existing / missing Result inventory completeness；
18. high Overall + TRIGGERED Gate并列表达；
19. Overall disabled / available / unavailable / production failed四类boundary；
20. Acceptance disabled、zero-Gate与valid Run不自动ACCEPTABLE；
21. Gate missing vs INDETERMINATE与policy fail-closed trace；
22. pending / invalid Run的not-produced nested views；
23. finalized evaluation vs finalized audit Scorecard；
24. Definition / external resource digest mismatch binding validation；
25. canonical digest implementation independent conformance；
26. cross-Run Result contamination rejection；
27. regrade-without-reexecution need analysis。

---

## 23. Final Decision Checklist

### Run and identity

- [ ] Run binds one Definition ID / version / closure profile / digest
- [ ] Digest matches v0.2 canonical Frozen Definition closure
- [ ] Semantic external resource digests match bindings
- [ ] Run has exactly one Subject ref
- [ ] Subject identity strength and limits are auditable
- [ ] Execution and validity statuses are separate
- [ ] Timestamps are not ordering authority

### Episode and attempts

- [ ] Every Episode resolves to same-Run Test Case
- [ ] Attempt indexes are positive, unique and stable
- [ ] Blocked / failed / cancelled attempts retain assigned index
- [ ] Duplicate serialization is ID-based
- [ ] Trace events are ordered and remain non-Core components

### Artifact and Evidence

- [ ] Artifact locator is generic and content is external
- [ ] Run-level and Episode relations are valid
- [ ] Artifact is not automatically Evidence
- [ ] Evidence exists only after qualification passes
- [ ] Capture / collector failure is diagnostic
- [ ] Evidence Spec and qualified target pairs resolve
- [ ] All target Test Cases match the Episode
- [ ] Shared Evidence does not merge Grader targets

### Grader Result

- [ ] Identity is Run + Episode + Grader + target pair
- [ ] Judgment uses only four stable meanings
- [ ] Evidence refs satisfy target consumption authority
- [ ] Explanation separates observed facts and inference
- [ ] Failure mode is supported and non-authoritative
- [ ] Grader engine failure creates no shell Result

### Metric Result

- [ ] At most one authoritative Result per Run + Metric
- [ ] Available / unavailable / missing are distinct
- [ ] Canonical value is authoritative and numeric domain valid
- [ ] Display value cannot affect Gate
- [ ] Coverage Summary is internally consistent
- [ ] Included / excluded / missing inputs are traceable
- [ ] Calculator failure creates no unavailable Result

### Gate Result

- [ ] At most one authoritative Result per Run + Gate
- [ ] Only OPEN / TRIGGERED / INDETERMINATE are used
- [ ] Evaluation path matches Result
- [ ] Trigger source distinguishes condition vs unavailable policy
- [ ] Direct Grader or Metric input summary is complete
- [ ] Gate engine failure creates no INDETERMINATE Result
- [ ] OPEN is not presented as Benchmark PASS

### Scorecard and architecture

- [ ] Scorecard only organizes same-Run objects
- [ ] Existing and expected-missing Results are both visible
- [ ] Diagnostics remain operational facts
- [ ] Overall policy ref uses Definition digest + canonical path
- [ ] Overall disabled / available / unavailable / production failure are distinct
- [ ] Missing and unavailable Metric applications are distinct
- [ ] Overall trace covers weights, normalization, coverage and denominator
- [ ] Acceptance policy ref uses Definition digest + canonical path
- [ ] Acceptance disabled does not produce ACCEPTABLE
- [ ] Only explicit participating Gates propagate
- [ ] Missing Gate is not fabricated as INDETERMINATE Result
- [ ] Actual trigger and policy fail-closed remain explainable
- [ ] Invalid / pending Run produces no authoritative final views
- [ ] Evaluation and audit Scorecard finalization remain distinct
- [ ] Gate Result remains independent from Overall Score
- [ ] Case / Contract summaries remain derived views
- [ ] No cross-Run comparison object is introduced

### Status

- [ ] Structural validation completed
- [ ] Cross-object validation completed
- [ ] Semantic validation completed
- [ ] Focused A–J consistency review completed
- [ ] Architecture authority consumed by Runtime Design
- [ ] Representative real validation subset completed before READY claim
- [ ] Architecture Findings closed only after required real validation
- [ ] No Pydantic / CLI / engine / storage / UI implementation started

本轮method-level checks通过且没有generic blocker时，允许：

```text
RUNTIME_RESULT_DESIGN_METHOD_READY_FOR_REAL_VALIDATION
```

只有representative real validation与required conformance checks完成后，future review才可以考虑：

```text
RUNTIME_RESULT_DESIGN_READY
```

本轮不满足后一个条件，也不声明frozen。
