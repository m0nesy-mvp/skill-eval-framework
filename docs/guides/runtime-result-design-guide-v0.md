# 《Runtime / Result Design Guide v0》

Status: Method and Schema Proposal — Self-Review Only

本文定义从已经冻结的 Benchmark Definition 到 Runtime / Result objects 的通用设计方法，并提出以下八个 Core Objects 的最小 pseudo-schema：

- Runtime：Run、Episode、Artifact、Evidence；
- Result：Grader Result、Metric Result、Gate Result、Scorecard。

本文适用于 coding agent、tool-use agent、browser agent、conversational agent、research agent、structured-output agent、local skill、remote service 与 model endpoint，不绑定 Android、HarmonyOS、ADB、Git、本机文件系统或任何 concrete evaluator。

本文不修改已经 frozen 的 Requirement Extraction、Final Requirement Finalization、Contract、Test Case、Evidence Specification、Grader Specification、Metric Specification、Gate Specification或Concept Model。本轮不实现 Pydantic、CLI、collector、grader engine、Metric calculator、Gate evaluator、storage、database、UI或packaging。

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

本轮完成条件仅为：

- 通用方法；
- 最小pseudo-schema proposal；
- Structural、Cross-object、Semantic validation rules；
- Schema Findings、Architecture Findings与Method Self-Review。

本轮不进行真实Runtime validation，不声称Schema已validated或frozen。

---

## 2. Frozen Architecture Baseline

Definition-time authority：

```text
Benchmark Definition
→ Requirement
→ Contract
→ Test Case
→ Evidence Specification
→ Grader Specification
→ Metric Specification
→ Gate Specification
```

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

`benchmark_id + benchmark_version`只表示human-readable lineage与declared version，不能独立证明同version内容没有漂移。Run必须同时保存不可变的`definition_digest`。

```text
benchmark_id + benchmark_version
≠ sufficient frozen-content identity

benchmark_id + benchmark_version + definition_digest
= minimum Run binding
```

`definition_digest`必须由Definition freeze process对authoritative immutable snapshot产生。它是Run引用的content identity；可选`definition_snapshot_ref`只用于检索，不替代digest。

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
- definition_digest: str
- definition_snapshot_ref: str?
```

字段语义：

- `benchmark_id`：required；Definition lineage authority；
- `benchmark_version`：required；human-visible declared version；
- `definition_digest`：required；immutable content identity，建议使用self-describing form，例如`sha256:<hex>`；
- `definition_snapshot_ref`：optional；可检索snapshot的generic locator，不具有content-identity authority。

Run validation必须确认其加载或执行的Definition内容与`definition_digest`一致。仅比较ID与version不足以形成valid Run。

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
- `valid`：Definition binding、Subject binding、same-Run references与minimum integrity checks通过，可按各Metric completeness policies形成authoritative evaluation Results；
- `invalid`：Definition digest mismatch、cross-Run contamination、identity ambiguity或其他integrity blocker使本Run不能作为authoritative evaluation record。

`valid`不表示execution complete。一个`partial + valid` Run可以合法产生partial/unavailable Metric Results，只要Definition policy允许并完整披露coverage。`completed + invalid`同样可能存在，例如执行结束后发现Definition snapshot与digest不一致。

### 4.7 Run timestamps

保留最小audit timestamps：

- `created_at`：required；
- `started_at`：conditional，进入running或meaningful execution后required；
- `ended_at`：conditional，terminal state时required。

时间戳不得作为attempt ordering、duplicate identity或Result authority。

### 4.8 Minimal Run schema

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
- phase: environment | collection | grading | metric | gate | orchestration
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
- identity / integrity validation concern。

Diagnostic可以被Run、Episode与Scorecard引用，但不能被Metric或Gate偷偷当作Contract semantic input，除非未来Definition明确建立合法execution-status vocabulary与condition authority。

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

Scorecard是一个Run的Result-layer top-level summary与traceability entrypoint。它组织已有Results，不重新grade、不重新aggregate Metric internals、不重新evaluate Gates。

```text
Scorecard
≠ hidden evaluator
≠ hidden Overall aggregation policy
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

### 12.3 Overall Score boundary

Overall Score只能在Frozen Benchmark Definition含有明确Overall aggregation policy时出现。最低要求是Scorecard能够保存：

```text
OverallScoreView:
- policy_ref: str
- canonical_value: number
- included_metric_result_ids: list[str]
- excluded_metric_result_ids: list[str]
- explanation: str
```

但当前frozen Definition-time objects中没有独立OverallScoreSpecification，也没有已冻结的Benchmark-level Overall aggregation policy Schema。Metric内部weighting不能冒充跨Metrics的Overall weight。

因此当前规则是：

- 没有可解析frozen `policy_ref` → `overall_score`必须absent；
- 不允许默认平均所有Metrics；
- 不允许Metric unavailable时自行re-normalize；
- 不允许Gate TRIGGERED自动把Overall Score改成0；
- `overall_score` absent不表示0或计算失败，只表示缺少Definition authority。

### 12.4 Gate and final acceptability boundary

Gate Result与Overall Score独立。合法Scorecard可以同时表达：

```text
Overall Score = high
Gate Result = TRIGGERED
```

`TRIGGERED`使Gate declared scope不可接受并且non-offsettable，但多个scoped Gates如何形成whole-benchmark `acceptable / blocked / indeterminate`尚缺Definition-level aggregation authority。

因此当前Scorecard不得自行添加authoritative`overall_status`或`acceptability_status`。只有未来存在明确frozen acceptance policy时，才允许：

```text
OverallAcceptabilityView:
- policy_ref: str
- status: acceptable | blocked | indeterminate
- gate_result_ids: list[str]
- explanation: str
```

没有`policy_ref`时，Scorecard只能逐项展示Gate Results及其scope，不能推导whole-benchmark PASS / FAIL。

### 12.5 Minimal Scorecard schema

```text
Scorecard:
- scorecard_id: str
- run_id: str
- definition_ref: FrozenDefinitionRef
- subject_ref: SubjectReference
- result_inventory: ScorecardResultInventory
- diagnostic_ids: list[str]
- overall_score: OverallScoreView?
- overall_acceptability: OverallAcceptabilityView?
- finalized_at: datetime
```

`definition_ref`与`subject_ref`是Run identity的traceable copy，必须完全等于Run中的authoritative refs，不能成为第二套authority。

在当前architecture下，两个optional overall fields都受Architecture Findings阻塞；Scorecard inventory、diagnostics与per-Result traceability不受阻。

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
- ID、version与digest全部匹配；
- digest mismatch使Run invalid，即使execution completed；
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
- optional overall views必须有可解析frozen policy authority。

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
- Scorecard optional overall view具有policy ref。

### 15.2 B. Cross-object Validation

至少检查：

- Run Definition ID / version / digest解析与匹配；
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
- Overall Score没有隐藏aggregation authority；
- whole-benchmark acceptability没有从scoped Gates被擅自推导；
- duplicate identity没有按payload equality判断；
- cross-Run comparison没有污染单Run Result。

---

## 16. Runtime / Result Design Workflow

### Step 1 — Verify frozen inputs

确认Concept Model以及Requirement、Contract、Test Case、Evidence、Grader、Metric、Gate Definition designs当前有效。任何upstream concern只记录Finding，不回改frozen Guide。

### Step 2 — Establish Run identity

绑定Definition ID / version / digest与exactly one Subject；定义execution context、status、validity与timestamps。

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

### Step 8 — Establish Scorecard inventory

组织Run Results、missing applications与diagnostics；只在存在frozen policy authority时允许Overall或acceptability view。

### Step 9 — Validate

执行Structural、Cross-object、Semantic三层validation，建立real validation subset，记录Schema / Architecture Findings。

### Step 10 — Determine status and stop

只输出Design status，不开始Pydantic、CLI、engine、storage或UI。

---

## 17. Design Status

Production method status只允许：

```text
RUNTIME_RESULT_DESIGN_READY
RUNTIME_RESULT_DESIGN_BLOCKED
```

### 17.1 RUNTIME_RESULT_DESIGN_READY

只有以下条件全部满足才允许：

- eight Core Object schemas与nested records通过三层validation；
- immutable Definition binding协议可执行；
- Subject identity足以审计；
- all execution / semantic failure boundaries稳定；
- Result uniqueness与same-Run integrity稳定；
- Scorecard所有authoritative final views都有frozen Definition authority；
- no unresolved blocking Schema or Architecture Finding；
- 至少一个representative real validation subset通过。

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

### 17.3 Validation subset wording

只有真实subset validation通过时才可写：

```text
RUNTIME_RESULT_DESIGN_READY for validation subset
```

它不等于production READY，也不表示完整Target Benchmark、implementation或Runtime PASS。

### 17.4 Current v0 status

本轮只完成method + Schema Proposal + Self-Review，没有执行真实Runtime validation，因此不声明READY或freeze。

对于“完整八对象设计可否进入freeze”的当前结论是：

```text
RUNTIME_RESULT_DESIGN_BLOCKED
```

blocking scope仅为：

- Scorecard Overall Score authority；
- Scorecard whole-benchmark acceptability authority；
- Definition digest production / verification protocol仍需真实validation。

这些finding不阻止Run、Episode、Artifact、Evidence、GraderResult、MetricResult、GateResult以及Scorecard result-inventory部分进入后续validation subset；但在findings关闭前，不得把完整Runtime / Result v0称为frozen。

---

## 18. Schema Findings

### SF-RR-001 — Definition digest is required

`benchmark_id + version`不足以防止same-version content drift。Run必须保存required `definition_digest`；snapshot locator只能辅助检索。

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

---

## 19. Architecture Findings

### AF-RR-001 — Overall Score lacks frozen Definition-time authority

当前Concept Model把Overall Score定义为Scorecard中的derived value，并提到Overall Aggregation Policy；但已冻结Definition-time object schemas没有独立OverallScoreSpecification，也没有已经冻结的Benchmark-level aggregation policy Schema。

因此无法权威决定：

- 哪些Metric Results进入Overall；
- cross-Metric weights；
- scale与precision；
- unavailable Metric处理；
- re-normalization；
- Overall disabled semantics。

Classification：`ARCHITECTURE_GAP`。

Impact：blocks OverallScoreView freeze and complete eight-object Runtime / Result freeze；does not block Runtime core、individual Results或Scorecard inventory validation。

禁止临时修复：平均全部Metrics、复用Metric内部weighting、Gate触发后置零、把display score当authority。

### AF-RR-002 — Whole-benchmark acceptance lacks aggregation authority

Gate Result只声明某个Gate scope的non-offsettable acceptability。当前没有冻结policy说明多个scoped Gates如何形成whole-benchmark：

```text
acceptable | blocked | indeterminate
```

特别是以下问题没有authority：

- any TRIGGERED是否总是阻断whole benchmark，还是只阻断declared sub-scope；
- INDETERMINATE如何影响final acceptance；
- 没有Gate时是否自动acceptable；
- partial / invalid Run能否有acceptance status；
- Gate与Run validity的precedence。

Classification：`ARCHITECTURE_GAP`。

Impact：blocks authoritative `overall_acceptability` / PASS-FAIL view and complete Scorecard freeze；does not block individual GateResult semantics。

禁止临时修复：`any triggered → benchmark_failed=true`、`all open → PASS`、`invalid Run → Gate triggered`。

### AF-RR-003 — Definition digest production protocol is not yet frozen

Runtime Schema已经证明需要`definition_digest`，但digest所覆盖的authoritative snapshot bytes、canonicalization与freeze-time production / verification procedure尚未在upstream Definition schema中冻结。

Classification：`UPSTREAM INTEGRATION FINDING`。

Impact：不阻止method schema proposal；blocks implementation与real reproducibility validation，直到freeze process能提供稳定self-describing digest。

本Guide只记录finding，不修改upstream Guide。

---

## 20. Method Self-Review

| # | Question | v0 finding |
|---:|---|---|
| 1 | Run identity是否足够？ | Schema层足够：Run ID + Definition ID/version/digest + one Subject。Digest production仍需validation。 |
| 2 | Frozen Benchmark identity是否可复现？ | 设计上可；必须验证authoritative snapshot digest协议，ID+version单独不够。 |
| 3 | Subject不作为Core Object是否仍可定位？ | 可以。Opaque stable ref + kind/version/digest claims支持generic subjects；remote identity strength需披露。 |
| 4 | Run execution state vs validity是否分开？ | 是。允许completed+invalid与partial+valid。 |
| 5 | Episode identity是否稳定？ | 是。`episode_id`定义logical identity，tuple约束保证attempt uniqueness。 |
| 6 | attempt ordering是否deterministic？ | 是。`attempt_index`是唯一ordering authority，timestamps只审计。 |
| 7 | duplicate Episode / Result能否区分？ | 是。相同ID是duplicate serialization；不同ID是distinct logical attempts / results。 |
| 8 | Artifact / Evidence边界是否稳定？ | 是。Artifact是persistent runtime object；Evidence只在qualification通过后存在。 |
| 9 | Evidence能否服务shared targets？ | 可以。`qualified_targets`支持一个same-Episode Evidence服务多个targets。 |
| 10 | Evidence是否被Episode隔离？ | 是。Evidence exactly one Episode，target Test Case必须匹配Episode。 |
| 11 | capture failure放在哪里？ | RuntimeDiagnostic；captured-but-unqualified保留source + qualification diagnostic，不伪造Evidence。 |
| 12 | GraderResult最小aggregatable identity是否清楚？ | 是。Run + Episode + Grader + Test Case + Contract。 |
| 13 | grader engine failure是否不会变insufficient？ | 是。no Result + grading diagnostic。 |
| 14 | MetricResult available / unavailable / missing是否分开？ | 是。status两值加object absence。 |
| 15 | canonical Metric value是否明确？ | 是。available numeric `canonical_value`是唯一authority；display不参与Gate。 |
| 16 | Metric transparency metadata是否足够？ | Proposal覆盖expected/raw/distinct/selected/eligible/non-substantive/unavailable/unit/denominator/coverage；需real validation。 |
| 17 | metric engine failure是否不会变unavailable？ | 是。no Result + metric diagnostic。 |
| 18 | Gate OPEN / TRIGGERED / INDETERMINATE是否稳定？ | 是，直接继承frozen Gate semantics。 |
| 19 | Gate engine failure是否不会变INDETERMINATE？ | 是。no Result + gate diagnostic。 |
| 20 | Gate trigger reason是否可解释？ | 是。evaluation path区分condition与unavailable-policy trigger。 |
| 21 | Scorecard是否只组织Results？ | 是。Inventory与refs不重新grade / aggregate / evaluate。 |
| 22 | Overall Score authority是否存在gap？ | 是，AF-RR-001；阻塞Overall view freeze。 |
| 23 | overall acceptance authority是否存在gap？ | 是，AF-RR-002；阻塞whole-benchmark status freeze。 |
| 24 | Gate与Overall Score是否独立？ | 是。Gate不置零或删除Overall；两者并列显示。 |
| 25 | Result uniqueness是否明确？ | 是。Grader per attempt+target+grader；Metric per run+metric；Gate per run+gate；Scorecard per run。 |
| 26 | all Result refs是否same Run？ | 是，作为Framework-wide cross-object invariant。 |
| 27 | Runtime diagnostics是否有位置？ | 是，nested RuntimeDiagnostic，不新增Core Object。 |
| 28 | 是否新增不必要Core Object？ | 否。Subject、Trace、Diagnostic、ResultSelection、Comparison均保持nested / external / derived。 |
| 29 | Schema最小字段是什么？ | 本Guide第4–12节给出八对象与必要nested structures。 |
| 30 | 哪些问题必须真实validation？ | Definition digest、remote Subject identity、Episode creation/status transitions、shared Artifact、Evidence qualification rejection、Rubric output、Metric coverage counts、Result selection、Gate missing inputs、Scorecard completeness、regrade policy与两项Architecture Gaps。 |

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
- 为防Scorecard创造authority，Overall与acceptability均要求frozen policy ref；
- 为防过早复杂化，v0不设计revision graph、event sourcing、comparison object或storage。

### 20.2 Current self-review conclusion

Run、Episode、Artifact、Evidence、GraderResult、MetricResult、GateResult以及Scorecard inventory已经形成一致的method / Schema Proposal，未发现需要第17个Core Object的理由。

完整Runtime / Result v0仍有三项真实blocker：

1. Overall Score Definition authority；
2. whole-benchmark acceptance authority；
3. Definition digest production / verification real validation。

因此本Guide不宣称validated、READY或frozen。下一阶段应只建立representative validation subset并验证上述proposal；不得直接进入Pydantic implementation。

---

## 21. Future Real Validation Coverage

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
19. no Overall policy时禁止Overall value；
20. no acceptance policy时禁止whole-benchmark PASS / FAIL；
21. cross-Run Result contamination rejection；
22. regrade-without-reexecution need analysis。

---

## 22. Final Decision Checklist

### Run and identity

- [ ] Run binds one Definition ID / version / digest
- [ ] Digest matches authoritative frozen snapshot
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
- [ ] Overall Score appears only with frozen policy ref
- [ ] Overall acceptability appears only with frozen policy ref
- [ ] Gate Result remains independent from Overall Score
- [ ] Case / Contract summaries remain derived views
- [ ] No cross-Run comparison object is introduced

### Status

- [ ] Structural validation completed
- [ ] Cross-object validation completed
- [ ] Semantic validation completed
- [ ] Representative real validation subset completed
- [ ] Architecture Findings closed or scope explicitly blocked
- [ ] No Pydantic / CLI / engine / storage / UI implementation started

只有全部required checks通过且没有blocking finding时，才允许：

```text
RUNTIME_RESULT_DESIGN_READY
```

否则：

```text
RUNTIME_RESULT_DESIGN_BLOCKED
```
