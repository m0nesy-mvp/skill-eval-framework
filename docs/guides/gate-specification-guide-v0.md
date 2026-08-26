# 《Gate Specification Design Guide v0》

Status: Design Guide

本文定义从已经冻结的Grader Specification / Metric Specification到Definition-time Gate Specification与future Runtime Gate Result的通用设计方法。它适用于tool-use、coding、browser、conversational、research、structured-output、qualitative与workflow evaluation，不绑定特定Skill、平台、业务领域、Runtime engine、Scorecard layout或Overall Score implementation。

本文提出最小GateSpecification Schema Proposal，但不修改已经冻结的Requirement、Contract、Test Case、Evidence Specification、Grader Specification、Metric Specification、Concept Model或其他upstream Schema；不实现Gate Evaluator、Runtime Result、CLI、Pydantic、Scorecard或Overall Score。

---

## 1. Gate Specification 的角色

Gate Specification回答：

> What condition makes the declared Benchmark, Run, or evaluation scope unacceptable regardless of otherwise favorable aggregate performance?

它是Definition-time conditional first-class object，预先冻结：

- Gate semantic identity；
- declared decision scope；
- one atomic non-offsettable blocking condition；
- Definition-level input reference；
- target或Metric membership；
- Grader Result semantic match或Metric Result predicate；
- quantifier；
- threshold与scale compatibility；
- required input unavailable时的handling；
- future Gate Result的`OPEN`、`TRIGGERED`与`INDETERMINATE` meaning；
- future explanation与traceability requirements。

Gate Specification不负责：

- 重新读取或解释raw Evidence；
- 执行Test Case或收集Artifact；
- 重判Contract；
- 把多个Grader Results组合成新的Contract verdict；
- 聚合Grader Results形成descriptive Metric；
- 为Gate分配weight或计算Gate average；
- 计算Overall Score；
- 组织Scorecard layout；
- 保存actual Result value、triggered boolean、matching target、Metric value或Runtime IDs；
- 实现Gate Evaluator、boolean engine或comparison code。

---

## 2. Gate Specification 与 Gate Result

必须严格分开：

```text
Gate Specification
= Definition-time trigger policy

Gate Result
= Runtime evaluation of that policy for one Run and one Subject
```

Gate Specification保存：

- 应引用哪个Definition object；
- 应检查什么condition；
- 哪个scope会被该condition阻断；
- input unavailable时condition如何解释；
- future Result status与explanation应表示什么。

Gate Result未来保存：

- 关联的Gate Specification；
- Run与Subject；
- 实际定位到的Grader Results或Metric Result；
- actual matched observations或Metric value；
- actual input availability；
- `OPEN`、`TRIGGERED`或`INDETERMINATE`；
- blocking reason与traceability。

Definition阶段只能引用已经存在的Definition对象，不能引用未来才产生的Grader Result、Metric Result或Gate Result。Future Gate Evaluator才按Definition-level reference定位本Run的actual Results。

---

## 3. Grader、Metric、Gate 与 Scorecard Boundary

### 3.1 Grader vs Gate

```text
Grader
→ judges one target-specific Contract observation

Gate
→ checks whether an already-established Result satisfies one blocking condition
```

Gate不得读取Evidence后自行判断authorization、scope、completion或其他Contract semantics。Target judgment必须已经由authoritative Grader Specification形成。

禁止：

```text
Evidence A + Evidence B
→ Gate re-judges Contract
→ Benchmark blocked
```

允许：

```text
Explicit target pair
→ authoritative Grader Result meaning = violated
→ atomic Gate condition matches
```

### 3.2 Metric vs Gate

```text
Metric
→ descriptive aggregation with independent interpretation

Gate
→ non-offsettable acceptability boundary over an existing Result
```

例如：

```text
Metric Specification:
Workflow compliance rate, scale 0..1, higher is better

Gate Specification:
TRIGGER if that Metric Result is available and value < 0.90
```

`0.90`属于Gate，不得写回Metric Specification。Metric value本身不宣布Benchmark PASS / FAIL。

### 3.3 Gate vs Scorecard / Overall Score

Gate Result未来进入Scorecard，但Gate不定义：

- Scorecard结构；
- Gate Result display order；
- Overall Score；
- 多个Metrics之间的weight；
- 多个Gate Results的presentation；
- Benchmark comparison UI。

Scorecard可以并列展示Metric Results、Gate Results与Overall Score，但高Overall Score不能自动抵消`TRIGGERED` Gate。

---

## 4. Non-Offsettable Semantics

Gate是non-offsettable decision policy：

```text
Gate TRIGGERED
≠ a negative contribution that can be averaged away
```

一个Gate condition一旦成立：

- 其他Metric高分不能自动抵消；
- 其他Contracts satisfied不能自动抵消；
- Overall Score高不能自动抵消；
- 另一个Gate OPEN不能自动抵消。

Gate Specification必须说明被阻断的declared scope。多个Gate Results如何形成最终Benchmark acceptance summary属于future Scorecard / Run evaluation policy，但任何汇总都不得静默把triggered Gate转换为可补偿分数。

如果某种negative result允许由其他表现补偿，它通常应进入Metric或Overall aggregation，而不是Gate。

---

## 5. Criticality 与 Gate

Contract `criticality = normal | critical`表达violation的Definition-level significance。它不是executable policy：

```text
criticality ≠ Gate
criticality ≠ Gate Result
criticality ≠ weight
criticality ≠ Benchmark fail
```

禁止隐含：

```text
critical Contract violated
→ automatically block Benchmark
```

允许：

```text
Benchmark acceptance intent
+ explicit target membership
+ explicit Gate condition
→ selected critical target violation is non-offsettable
```

Criticality可以成为Gate Design Audit中的blocking rationale input，但不能自动生成Gate、target membership或trigger condition。Normal Contract也可能因明确Benchmark acceptance policy进入Gate；Critical Contract也可能只影响review priority而没有Gate。

---

## 6. Authoritative Inputs 与 Entry Gate

### 6.1 Production inputs

Gate Specification Design至少需要：

1. Frozen Benchmark Definition identity与version；
2. Frozen Requirement Set；
3. Validated Contract Set与criticality rationale；
4. Validated Test Cases与ExpectedAssertion pairs；
5. Validated Grader Specification Set及authoritative target coverage；
6. Validated Metric Specification Set及result semantics、scale与availability policy；
7. Explicit Benchmark acceptance / non-offsettable intent；
8. 当前unresolved upstream issues；
9. 已有Concept Model边界。

### 6.2 Production Entry Gate

Production Gate Design只有在下列条件满足时开始：

- required upstream Definitions frozen且current；
- Grader Specification Design为`GRADERS_READY`；
- 被Gate引用的Metric Specification Design为`METRICS_READY`；
- target pairs或metric IDs可唯一解析；
- Benchmark owner / Definition提供explicit blocking rationale；
- 没有会改变condition meaning的upstream ambiguity。

否则：

```text
GATES_BLOCKED
```

### 6.3 Method Validation Subset

如果production Entry Gate未满足，但存在明确、稳定、可追踪的validated subset，可以输出：

```text
GATES_READY for validation subset
```

前提：

- subset boundaries显式；
- unresolved full-Benchmark blockers保留；
- 不把validation-only Gate写成production acceptance policy；
- 不声称整个Target或Benchmark `GATES_READY`。

本文第一版只定义方法与future real method validation plan，不执行真实Gate validation，也不为当前Target声明Gate Set status。

---

## 7. Gate Scope

每个Gate必须说明：

> If this condition triggers, what declared evaluation scope becomes unacceptable?

常见scope可能是：

- whole Benchmark Run；
- Outcome evaluation scope；
- Workflow evaluation scope；
- capability-specific scope；
- other explicitly named Benchmark-defined scope。

v0使用required deterministic `scope: str`，不冻结scope taxonomy enum。Scope必须：

- human-readable且single-meaning；
- 关联当前Benchmark Definition；
- 不依赖Runtime临时label；
- 不把Result status与scope混在一起；
- 让`TRIGGERED`的blocking effect有明确对象。

禁止只写：

> failed

而不说明什么scope failed。

如果未来真实authoring出现可复用、需要跨Gate结构验证的scope vocabulary，再记录structured scope Schema Finding。

---

## 8. Gate Input Types

v0直接支持两类Definition-level source families：

1. **Grader Result source**：通过explicit ExpectedAssertion target pairs定位本Run的authoritative Grader Results；
2. **Metric Result source**：通过`metric_id`定位本Run的Metric Result。

Metric source进一步支持两个atomic predicate kinds：

- numeric threshold；
- Metric availability。

v0 Gate不得直接消费：

- raw Evidence；
- Evidence Specification；
- Artifact；
- Test Case setup；
- CLI/log text；
- Scorecard；
- Overall Score；
- another Gate Result；
- ad hoc Runtime field。

Concept Model允许future predefined execution-state conditions，但当前没有冻结的execution-status vocabulary或Definition-level reference surface。因此v0不以human-readable hidden string临时实现execution-state Gate；真实need出现时，应先完成Run validity / execution-status modeling，再决定是否增加condition variant。

---

## 9. Atomic Gate Principle

v0采用：

```text
one Gate Specification
= one atomic blocking condition
```

不支持arbitrary nested AND / OR expression graph。

多个可独立trigger、具有不同诊断或remediation的conditions应拆成多个Gates。例如：

```text
Gate A:
any selected destructive-authorization target violated

Gate B:
workflow compliance Metric < 0.90
```

而不是：

```text
Gate Mega:
A OR B OR C AND NOT D
```

### 9.1 Gate Atomicity Test

每个Gate至少检查：

1. condition是否可独立trigger blocking；
2. source Result family是否一致；
3. blocking rationale是否相同；
4. remediation是否相同；
5. explanation是否可以使用同一个reason template；
6. unavailable handling是否相同；
7. declared scope是否相同；
8. 合并是否会隐藏哪个condition实际trigger；
9. condition是否需要boolean composition才能解释。

如果任一子条件有独立meaning、remediation、scope或unavailable policy，拆Gate。

### 9.2 多targets仍可能是atomic

一个Grader Result Gate可以监控多个explicit targets，前提是：

- 它们共享同一blocking rationale；
- 匹配同一Result semantics；
- quantifier清楚；
- remediation与explanation一致；
- membership全部显式。

例如“任何selected destructive-authorization target violated”可以是一个atomic Gate。如果每个target代表不同风险和remediation，应拆成多个Gates。

---

## 10. Gate Condition Model

Gate必须高度deterministic，因此v0使用discriminated condition union，而不是单个free-form condition string。

```text
GateCondition =
  GraderResultGateCondition
  | MetricThresholdGateCondition
  | MetricAvailabilityGateCondition
```

每个Gate只能选择一个variant。Condition variant决定：

- Definition-level reference type；
- predicate fields；
- Structural / Cross-object validation path；
- future Gate Evaluator定位哪类actual Result。

v0不支持：

- arbitrary boolean DSL；
- nested condition tree；
- Gate-to-Gate reference；
- custom executable expression；
- raw Evidence predicate。

---

## 11. Grader Result Gate Condition

Grader Result Gate回答：

> Across explicitly selected ExpectedAssertion targets and their selected authoritative Grader Results, does the declared Result semantic predicate satisfy the quantifier?

### 11.1 Membership authority

```text
GateTarget:
- test_case_id
- contract_id
```

不保存`grader_id`。理由：

- pair唯一定位ExpectedAssertion；
- pair解析到authoritative GraderTarget；
- shared Grader ID不能说明引用全部还是部分targets；
- pair + grader ID会形成双authority；
- Grader policy演化时由Benchmark Definition version与Cross-object Validation处理。

Cross-object validation必须确认：

```text
GateTarget pair
→ one validated ExpectedAssertion
→ exactly one authoritative GraderTarget
```

### 11.2 Result selection

一个GateTarget在同一Run semantic scope内可能关联多个distinct Episode / attempt Grader Results。Direct Grader Result Gate必须有required deterministic `result_selection_policy: str`，在quantifier前说明选择：

- all distinct Results；
- first distinct Result；
- final distinct Result；
- other explicitly bounded deterministic subset。

Duplicate logical Result records必须先去重。Future Runtime提供Result identity、Episode identity、attempt ordering与Run association；Gate Specification不保存这些actual IDs。

Selection policy不得写：

- best Result；
- most relevant Result；
- final valid Result；

除非相关semantics已经完整且不会循环依赖Gate trigger judgment。

### 11.3 Trigger semantics

`trigger_result_semantics`必须是非空、明确、与referenced Grader Specification Result meanings兼容的list。

最稳定的v0 pattern：

```text
trigger_result_semantics: [violated]
```

`insufficient_evidence`与`not_exercised`不得因criticality或risk concern自动加入该list。如果Benchmark需要阻断judgment insufficiency或exercise gap，应使用独立Metric与Gate，或在有明确独立blocking rationale时建立另一个atomic Gate。

### 11.4 Quantifier

v0结构化支持：

```text
quantifier: any | all
```

Quantifier应用于去重和result selection之后的selected Result observations：

- `any`：至少一个selected Result的semantic meaning匹配trigger list；
- `all`：每一个required selected Result observation都匹配trigger list。

空selected population不能使用vacuous truth让`all`自动trigger，也不能让`any`自动OPEN；它进入`unavailable_handling`。

Count threshold、比例或跨Case normalization不进入Grader Result Gate。需要“至少N个violations”或“Contract across Cases低于比例”时，优先设计具有独立meaning的Metric，再由Metric threshold Gate引用。

---

## 12. Multiple Test Cases for One Contract

同一个Contract可能出现在多个Test Cases。Gate不得因为`contract_id`相同而隐式聚合：

```text
Contract C007
├── TC005/C007
└── TC006/C007
```

如果policy是：

> Any explicitly selected target violated triggers.

则两个pairs都必须显式进入`targets`，并使用`quantifier: any`。

如果policy是：

> Contract-level performance across Cases is below an acceptable threshold.

则Gate应引用已经完成Case multiplicity处理的Metric Specification，不在Gate里临时计算mean、ratio、worst-case或normalization。

Case multiplicity必须在Gate Design Audit说明是：

- explicit independent blocking observations；
- 还是已经交给Metric处理的performance samples。

---

## 13. Metric Threshold Gate Condition

Metric threshold Gate回答：

> Does the available Metric Result for the referenced Metric Specification cross the explicit non-offsettable acceptability boundary?

最小字段：

```text
MetricThresholdGateCondition:
- condition_type: metric_threshold
- metric_id
- comparator
- threshold_value
```

### 13.1 Comparator

v0支持结构化comparator enum：

```text
lt | lte | gt | gte | eq | neq
```

它们分别表示：

```text
actual < threshold
actual <= threshold
actual > threshold
actual >= threshold
actual == threshold
actual != threshold
```

Comparator表达的是trigger condition，而不是success condition。Spec必须避免“minimum 0.90”但又填写`gte`导致反向trigger。

### 13.2 Threshold value

`threshold_value`是Definition-time numeric value。必须满足：

- referenced Metric scale支持numeric comparison；
- threshold在Metric declared scale/range内，除非Metric semantics明确允许outside-range boundary；
- comparator与Metric direction、interpretation一致；
- precision足以唯一比较；
- equality comparator只在scale支持exact equality时使用；
- unit与normalization不发生转换歧义。

例如：

```text
Metric scale: [0, 1]
direction: higher is better

Gate comparator: lt
threshold_value: 0.90

Trigger iff actual Metric value < 0.90
```

禁止：

- `score too low`；
- `performance unacceptable`；
- `approximately 90%`；
- 在Gate里重新计算Metric denominator；
- 在Gate里把多个Metric Results加权平均。

---

## 14. Metric Availability Gate Condition

Metric availability Gate用于独立表达：

> The referenced required Metric Result must have an available interpretable value; its unavailable / undefined semantic state is non-offsettable.

最小字段：

```text
MetricAvailabilityGateCondition:
- condition_type: metric_availability
- metric_id
- trigger_on: unavailable
```

`trigger_on`在v0固定为`unavailable`。它不是完整Metric Result lifecycle enum，只引用Metric Specification已声明的future unavailable / undefined semantics。

为什么与threshold Gate分开：

- below-threshold与unavailable通常有不同diagnosis；
- remediation不同；
- explanation不同；
- 一个atomic Gate Result应有单一blocking reason。

如果Benchmark明确认为threshold miss与unavailable具有完全相同scope、blocking rationale、remediation和explanation，也仍优先拆成两个Gates，避免一个Result隐藏实际trigger path。

No Metric Result与Metric Result exists but unavailable不是同一actual state。前者适用Gate-level `unavailable_handling`；后者匹配Metric availability condition。

---

## 15. Unavailable Input Handling

每个Gate必须定义：

```text
unavailable_handling:
  indeterminate | triggered
```

它适用于Gate无法取得评估condition所需的required direct input，例如：

- required Grader Result missing；
- required target没有selected Result；
- referenced Metric Result missing；
- Metric threshold Gate收到unavailable Metric Result；
- required Result identity或attempt order不足，无法执行selection；
- actual Result与Definition reference无法可靠关联。

### `indeterminate`

Gate Result为`INDETERMINATE`：当前证据不足以确定blocking condition是否成立。它不等于OPEN，也不等于TRIGGERED。

### `triggered`

Gate Result为`TRIGGERED`：Definition明确把required input unavailable本身定义为该Gate的non-offsettable condition。

### 不支持隐式open

v0不允许：

```text
missing required input
→ default OPEN
```

如果Benchmark不要求该input，应该从Gate membership中删除；如果input required但不可用，必须选择`INDETERMINATE`或显式`TRIGGERED`。

### 不把 deferred 冻结为Result meaning

`deferred`通常是orchestration / lifecycle状态，表示Gate尚未被评估，而不是对condition的最终semantic evaluation。v0 Gate Result meanings不增加`DEFERRED`；future Runtime lifecycle可单独建模。

---

## 16. Insufficient Evidence Propagation

对于condition：

```text
trigger_result_semantics: [violated]
```

则：

```text
insufficient_evidence ≠ violated
```

它不匹配critical violation condition，也不能被Gate重新解释为Contract failure。

如果selected Grader Result明确存在且meaning为insufficient，它不是missing direct input；Gate按condition semantic match得到non-match。若Benchmark认为critical judgment insufficiency本身不可接受，应建立：

- Evidence / Judgment Sufficiency Metric + Metric threshold Gate；
- 或具有独立blocking rationale的atomic direct condition，前提是upstream Result vocabulary与Benchmark intent明确支持。

不要把violation risk与judgment availability混成一个Gate。

---

## 17. Not-Exercised Propagation

同样：

```text
not_exercised ≠ violated
```

Not-exercised Result不匹配critical violation Gate。

如果Benchmark要求critical responsibility至少被exercise一次，优先使用：

```text
Exercise / Coverage Metric
→ Metric threshold or availability Gate
```

这样critical violation、exercise coverage与evidence sufficiency保留不同Metric/Gate meaning，不会互相偷换。

---

## 18. Gate Result Semantics

v0使用以下conceptual Gate Result meanings：

```text
OPEN
TRIGGERED
INDETERMINATE
```

### OPEN

Required direct inputs可用，atomic condition经过declared policy计算后没有成立。

`OPEN`只表示：

> This Gate condition did not trigger for this Run.

它不表示：

- Contract PASS；
- 所有Metrics达标；
- whole Benchmark accepted；
- Overall Score高；
- 所有其他Gates OPEN。

### TRIGGERED

Atomic blocking condition成立，或Definition明确规定required input unavailable使Gate trigger。Declared scope因此不可接受，且不能被其他高分自动抵消。

### INDETERMINATE

Required input、identity、ordering或compatible Result不足，无法确定condition是否成立。它不能静默显示为OPEN。

使用`OPEN / TRIGGERED / INDETERMINATE`而不是`PASS / FAIL`，减少与Contract judgment、Metric threshold success和overall Benchmark acceptance混淆。

---

## 19. Gate Explanation Requirements

Gate Specification使用required `explanation_requirements: list[str]`，要求future Gate Result至少能说明：

- gate identity；
- declared scope；
- condition type；
- Definition-level source reference；
- actual Result(s) used或missing；
- result selection与quantifier where applicable；
- comparator、threshold与actual Metric value where applicable；
- whether condition matched；
- actual unavailable input where applicable；
- Gate Result meaning；
- concise blocking或indeterminate reason；
- traceability to source Result(s)。

Explanation不得保存到Specification中的actual fields，也不要求：

- chain-of-thought；
- Scorecard layout；
- report formatting；
- remediation workflow implementation。

---

## 20. Gate Weight、Severity 与 Offset Prohibition

Gate没有weight：

```text
Gate A weight 2
+ Gate B weight 1
→ average
```

是非法Gate semantics，会把blocking condition重新变成Metric。

v0也不增加Gate severity enum。Gate本身已经表示non-offsettable condition；`warning / info / advisory`等non-blocking concerns不应伪装成Gate。

Contract criticality保留在Contract层。Gate的blocking rationale进入Audit，不复制`normal / critical`成为Gate severity。

---

## 21. Gate vs Run Validity / Execution Status

Run可能出现：

- execution failed；
- no Episodes；
- infrastructure unavailable；
- environment setup failure；
- cancellation；
- incomplete orchestration。

Gate不应成为所有Runtime failures的垃圾桶。

区分：

```text
Gate condition
→ evaluates acceptability of declared evaluation Results

Run validity / execution status
→ states whether execution produced a valid evaluable Run
```

如果Benchmark明确要求“infrastructure failure itself blocks acceptance”，需要先有合法的predefined execution-status Definition vocabulary和Runtime Result surface。当前v0不发明hidden status string，也不在Gate Schema加入generic `runtime_status_condition`。

Metric Result missing可以触发Gate-level unavailable handling，但Gate不得猜测missing背后的Runtime原因。

---

## 22. Required Gate Set 与 Coverage

不是每个Requirement、Contract、Test Case、Grader或Metric都必须有Gate。

Gate coverage回答：

> Have all explicitly required non-offsettable acceptance conditions been represented by validated Gate Specifications?

而不是：

> Does every Contract have a Gate?

Required Gate Set可能来自：

- Benchmark Definition explicit acceptance policy；
- explicit safety / authorization / prohibited-action blocking intent；
- explicit mandatory completion policy；
- explicit required Metric threshold；
- explicit required Metric availability / evaluation coverage policy；
- Contract criticality combined with authoritative blocking rationale。

禁止因为看到`criticality: critical`自动创建Gate。

一个Benchmark可以合法没有Gate，但必须在Gate Coverage Review中明确记录：

```text
No non-offsettable acceptance condition is required for this Benchmark revision.
```

不能因为没有authoring Gate而默认coverage complete。

### Gate Coverage Review

建议至少记录：

| 字段 | 含义 |
|---|---|
| `benchmark_revision` | 当前Definition identity/version |
| `required_blocking_conditions` | authoritative acceptance intent中的required conditions |
| `gate_ids` | 覆盖这些conditions的Gate Specifications |
| `uncovered_conditions` | 尚未覆盖的required conditions |
| `non_gate_critical_items` | critical但没有explicit Gate rationale的items及原因 |
| `coverage_status` | `GATE_COVERAGE_VALID`或`GATE_COVERAGE_BLOCKED` |
| `rationale` | coverage为何完整或为何blocked |

Coverage Review不是Core Object，也不成为Gate membership或blocking policy的第二套authority。

---

## 23. Gate Specification Candidate / Working Stage

v0不引入mandatory Gate Specification Candidate对象或Candidate lifecycle。

复杂authoring可以使用temporary Working Gate Drafts比较：

- atomic split vs combined condition；
- direct Grader Result vs Metric threshold source；
- target membership；
- `any` vs `all`；
- threshold direction/value；
- `indeterminate` vs explicit unavailable-trigger；
- scope interpretation；
- explanation requirements。

Working Draft：

- 不是Core Object；
- 不进入Frozen Gate Specification Set；
- 不算Gate coverage；
- 不占用正式`GATExxx` ID；
- resolved后由正式Spec或Gate Design Issue取代。

只有真实authoring证明需要stable alternate lineage、multi-reviewer reconciliation或long-lived draft dependency时，才重新评估Candidate lifecycle。

---

## 24. Gate Specification Design Audit

v0引入轻量、非Core、非authoritative的Gate Specification Design Audit，建议至少记录：

| 字段 | 含义 |
|---|---|
| `gate_id` | 正式Gate ID；draft可使用temporary label |
| `purpose_rationale` | 为什么该condition具有独立acceptability meaning |
| `blocking_rationale` | 为什么它必须non-offsettable |
| `scope_rationale` | 为什么该scope会被trigger阻断 |
| `source_result_rationale` | 为什么选择Grader或Metric Result source |
| `membership_rationale` | targets或metric ID为何minimum且完整 |
| `result_selection_rationale` | direct Grader Results如何选择与去重 |
| `atomicity_rationale` | 为什么condition是atomic或为何拆分 |
| `quantifier_rationale` | `any` / `all`为何匹配blocking intent |
| `threshold_rationale` | comparator/value与Metric scale为何兼容 |
| `unavailable_rationale` | `indeterminate`或`triggered`为何诚实 |
| `criticality_relation` | criticality是否提供rationale但没有自动执行 |
| `multiplicity_rationale` | multi-target、multi-Case、multi-Episode如何处理 |
| `explanation_rationale` | future Result必须说明什么 |
| `downstream_scorecard_concern` | 只记录future presentation/acceptance concern |
| `runtime_dependency` | identity/order/Result location dependency，不写implementation |

Audit：

- 不替代Gate Specification；
- 不成为condition或membership第二套authority；
- 不保存actual Results；
- 不定义Scorecard layout或Overall Score；
- 不用rationale修补ambiguous Schema fields；
- 必须与Gate Set、Coverage Review与upstream Definition一致。

---

## 25. Minimal GateSpecification Schema Proposal

### 25.1 GateSpecification

```text
GateSpecification:
- gate_id
- name
- scope: str
- condition: GateCondition
- unavailable_handling: indeterminate | triggered
- result_semantics: GateResultSemantics
- explanation_requirements: list[str]
```

### 25.2 GateCondition union

```text
GateCondition =
  GraderResultGateCondition
  | MetricThresholdGateCondition
  | MetricAvailabilityGateCondition
```

### 25.3 GraderResultGateCondition

```text
GraderResultGateCondition:
- condition_type: grader_result_semantic
- targets: list[GateTarget]
- result_selection_policy: str
- trigger_result_semantics: list[str]
- quantifier: any | all
```

### 25.4 GateTarget

```text
GateTarget:
- test_case_id
- contract_id
```

### 25.5 MetricThresholdGateCondition

```text
MetricThresholdGateCondition:
- condition_type: metric_threshold
- metric_id
- comparator: lt | lte | gt | gte | eq | neq
- threshold_value: number
```

### 25.6 MetricAvailabilityGateCondition

```text
MetricAvailabilityGateCondition:
- condition_type: metric_availability
- metric_id
- trigger_on: unavailable
```

### 25.7 GateResultSemantics

```text
GateResultSemantics:
- open_meaning
- triggered_meaning
- indeterminate_meaning
- blocking_effect
```

这是Definition-time Schema Proposal，不规定YAML、JSON、Pydantic、storage、Gate Evaluator、Runtime GateResult serialization、Scorecard或CLI。

---

## 26. Schema Field Decisions

| 候选字段 | v0决定 | 理由 |
|---|---|---|
| `gate_id` | 必填 | Gate Specification是conditional first-class Definition object |
| `name` | 必填 | 提供stable human identity，不替代condition semantics |
| `scope` | 必填deterministic string | 必须知道什么evaluation scope会被阻断；暂不冻结taxonomy |
| `condition` | 必填discriminated union | Semantic match、numeric threshold与availability需要不同structured validation |
| `condition_type` | 必填discriminator | 决定fields与Cross-object path，避免ambiguous condition string |
| `targets` | Grader condition必填非空 | Explicit membership authority |
| `test_case_id + contract_id` | nested GateTarget | Pair定位ExpectedAssertion与authoritative GraderTarget |
| `grader_id` | 禁止 | 形成双authority并使shared Grader membership歧义 |
| direct Grader `result_selection_policy` | 必填string | 处理同一target的distinct Episode / attempt Results，不保存Runtime IDs |
| `trigger_result_semantics` | 必填非空list | 冻结semantic match，不把criticality变成implicit trigger |
| `quantifier` | `any | all` enum | 支持当前真实atomic multi-target need，不引入count/boolean DSL |
| `metric_id` | Metric conditions必填 | Definition-level reference；Runtime以后定位本Run Metric Result |
| `comparator` | threshold condition enum | Gate determinism要求结构化comparison direction |
| `threshold_value` | threshold condition number | Definition-time acceptability boundary |
| `trigger_on: unavailable` | availability condition固定literal | 独立表达required Metric unavailable blocker |
| `unavailable_handling` | 必填enum | Missing input不能默认OPEN，也不能全局自动trigger |
| `result_semantics` | 必填nested | OPEN/TRIGGERED/INDETERMINATE meaning必须scope-aware |
| `explanation_requirements` | 必填非空list | Future Result必须可诊断、可追踪 |
| AND / OR graph | 不进入v0 | Atomic Gate Principle优先拆Gate |
| Gate weight | 禁止 | Gate不可平均或抵消 |
| Gate severity | 不进入v0 | Blocking已是Gate identity；warning不是Gate |
| Runtime execution-status condition | 暂不进入v0 | 缺少冻结status vocabulary；保留future Concept Model extension |
| Episode / Result / attempt ID | 禁止 | 属于future Runtime Result identity |
| actual triggered/value/match | 禁止 | 属于Gate Result |
| Scorecard/Overall refs | 禁止 | 属于downstream presentation/aggregation |

### ID Rules

推荐形式：

```text
GATE001
GATE002
GATE003
```

不使用`G001`，避免与Grader Specification ID混淆。

规则：

- 在一个Benchmark Definition中唯一；
- 使用`GATE`加至少三位十进制数字；
- 不要求跨Benchmarks全局唯一；
- scope、condition type、membership、result selection、quantifier、threshold、unavailable handling或result semantics重大变化时，应分配新ID；
- 删除的ID不应在同一Benchmark lineage复用于不同Gate meaning。

---

## 27. Schema Field Semantics

### 27.1 gate_id

非空string，表示Definition-time Gate Specification identity，不是Runtime Gate Result ID。

### 27.2 name

非空、human-readable、meaningful。禁止只有`gate`、`quality check`、`acceptance`等无法区分condition和scope的名称。

### 27.3 scope

非空deterministic string，说明`TRIGGERED`使哪个Benchmark-defined evaluation scope不可接受。不能保存actual Run ID或Subject ID。

### 27.4 condition

必填且恰好匹配一个union variant。Condition fields不得跨variant混用。

### 27.5 unavailable_handling

必填enum，只能是`indeterminate`或`triggered`。它不定义actual missing原因，也不产生Runtime lifecycle `deferred`。

### 27.6 result_semantics

四个非空strings共同定义future OPEN、TRIGGERED、INDETERMINATE与blocking effect。`triggered_meaning`必须与declared scope和condition一致；`blocking_effect`必须明确non-offsettable。

### 27.7 explanation_requirements

必填非空list，定义future Gate Result必须提供的事实解释与traceability categories，不保存actual explanation。

---

## 28. Gate Condition Determinism

两个conforming implementers看到：

```text
same current Benchmark Definition
+ same Gate Specification
+ same qualified Grader / Metric Results from one Run
```

必须得到相同conceptual Gate Result。

逐Gate Independent Decision Test：

1. Resolve declared scope；
2. Resolve condition variant；
3. Resolve Definition-level source references；
4. Locate actual Results for the current Run；
5. Deduplicate and select direct Grader Results where applicable；
6. Apply semantic match / availability predicate / comparator；
7. Apply quantifier where applicable；
8. Apply unavailable handling if required direct input cannot be evaluated；
9. Derive OPEN / TRIGGERED / INDETERMINATE；
10. Verify blocking effect and explanation requirements。

不允许：

- `if performance is unacceptable`；
- `if a serious issue occurs`；
- `if too many failures`；
- `use best judgment`；
- 未声明的numeric tolerance；
- 未声明的Result selection；
- 依赖Scorecard presentation推断condition。

---

## 29. Three-Layer Gate Specification Validation

### 29.1 A. Structural / Field Validation

未来可deterministic检查：

- `gate_id`符合`GATE`+至少三位数字；
- Gate IDs在Definition中唯一；
- `name`非空；
- `scope`非空；
- `condition_type`是支持的variant；
- 恰好一个condition variant fields集合存在；
- Grader condition targets非空且pairs不重复；
- Grader condition `result_selection_policy`非空；
- `trigger_result_semantics`非空且无duplicate；
- quantifier为`any`或`all`；
- Metric condition `metric_id`非空；
- threshold comparator属于allowed enum；
- threshold value为number；
- availability condition `trigger_on`固定为`unavailable`；
- unavailable handling属于allowed enum；
- result semantics四项非空；
- explanation requirements非空；
- 不存在grader ID、Gate weight、severity、actual Result、Scorecard或Overall字段。

### 29.2 B. Cross-object Validation

需要完整Definition context：

- target `test_case_id`存在且validated；
- target `contract_id`存在且validated；
- pair存在于ExpectedAssertions；
- pair恰好由一个authoritative GraderTarget覆盖；
- referenced Grader Specification validated且current；
- trigger semantics与authoritative Grader Result vocabulary兼容；
- referenced `metric_id`存在、validated且current；
- threshold Metric scale支持numeric comparison；
- comparator、threshold、Metric direction/range/unit兼容；
- Metric availability condition与Metric unavailable semantics兼容；
- references属于同一个Benchmark Definition version；
- 没有dangling、stale、cross-Benchmark或validation-only-to-production refs；
- scope属于当前Benchmark Definition的可解释surface；
- condition没有hidden Runtime ID、grader ID或Scorecard authority；
- Gate Set、Coverage Review与Audit双向一致。

### 29.3 C. Semantic Gate Review

逐Gate至少检查：

- condition是否有explicit blocking rationale；
- blocking是否真正non-offsettable；
- scope是否明确；
- source Result family是否appropriate；
- condition是否atomic；
- 多targets是否共享同一reason/remediation；
- membership是否minimum且完整；
- criticality是否没有自动变Gate；
- direct Grader Result selection是否deterministic；
- Case / Episode multiplicity是否intentional；
- semantic match与quantifier是否符合policy；
- insufficient是否没有偷换成violation；
- not-exercised是否没有偷换成failure；
- threshold direction与boundary是否正确；
- Metric unavailable与Metric value threshold是否分开；
- required input unavailable handling是否honest；
- missing input是否没有默认OPEN；
- OPEN是否没有被解释成whole Benchmark PASS；
- TRIGGERED是否没有被其他分数offset；
- INDETERMINATE是否没有被隐藏；
- explanation requirements是否足够；
- Gate是否没有重新grading；
- Gate是否没有重新做Metric aggregation；
- Gate是否没有吸收Run validity concerns；
- Gate是否没有Scorecard / Overall / implementation leakage；
- 两个implementers是否可得到相同Result。

Semantic Review需要Agent / Human judgment，不能伪装成Schema validation。

---

## 30. Gate Design Issues 与 Rollback

至少区分：

- missing authoritative blocking intent；
- gate-purpose ambiguity；
- scope ambiguity；
- required Gate Set / coverage issue；
- atomicity / composition issue；
- target membership issue；
- Metric reference issue；
- Grader Result semantic compatibility issue；
- result-selection / multiplicity issue；
- quantifier issue；
- threshold / comparator / scale issue；
- Metric availability issue；
- unavailable-input issue；
- criticality-to-Gate leakage；
- insufficient / not-exercised misclassification；
- Run validity boundary issue；
- explanation issue；
- Schema insufficiency；
- downstream Scorecard / Overall concern；
- Runtime implementation dependency。

Rollback：

```text
Target judgment unclear
→ Grader Specification lifecycle

Aggregate measure unclear
→ Metric Specification lifecycle

Criticality unclear
→ Contract Design lifecycle

Blocking intent or required acceptance policy unclear
→ Benchmark Definition / Gate Design authority

Run execution validity unclear
→ future Run validity / execution-status design

Gate Result presentation or final overall acceptance summary unclear
→ downstream Scorecard / Run evaluation policy

Gate policy clear but executable Result location unknown
→ downstream Gate Runtime implementation concern
```

不得为方便Gate authoring而修改Grader judgment、Metric value、Contract criticality或Runtime status。

---

## 31. Gate Specification Design Workflow

### Step 1 — Verify Inputs

- 验证Benchmark Definition、Contracts、Graders、Metrics、statuses与versions；
- production Entry Gate不满足时立即BLOCK；
- validation subset保留限定边界。

### Step 2 — Identify Required Non-Offsettable Conditions

- 从authoritative acceptance intent收集required conditions；
- 不因criticality自动造Gate；
- 允许显式记录当前revision不需要Gate。

### Step 3 — Define Gate Meaning and Scope

- 写清condition为何non-offsettable；
- 写清trigger会阻断什么scope；
- 确认它不是Metric、warning、Run status或Scorecard policy。

### Step 4 — Apply Atomicity Test

- 比较source、reason、remediation、scope、unavailable handling与explanation；
- 独立conditions拆成独立Gates；
- 不创建AND/OR mega Gate。

### Step 5 — Choose Condition Variant

- Grader Result semantic；
- Metric threshold；
- Metric availability；
- 不使用raw Evidence或hidden Runtime fields。

### Step 6 — Freeze Membership / Reference

- Direct Grader Gate列explicit target pairs；
- Metric Gate引用one metric ID；
- 不使用grader ID、selector或Runtime discovery。

### Step 7 — Define Result Selection and Quantifier

- Direct Grader Gate定义deduplication invariant与selection intent；
- 明确`any`或`all`；
- 处理empty selected population；
- 不在Gate内做count/rate aggregation。

### Step 8 — Define Threshold or Availability Predicate

- Threshold Gate写comparator与numeric value；
- 验证Metric scale、direction、range、unit与precision；
- Availability Gate只检查declared unavailable semantics。

### Step 9 — Define Unavailable Handling

- required input unavailable时选择`indeterminate`或explicit `triggered`；
- missing不默认OPEN；
- 不猜Runtime root cause。

### Step 10 — Define Result and Explanation Semantics

- OPEN / TRIGGERED / INDETERMINATE；
- non-offsettable blocking effect；
- required facts与traceability；
- 不写actual values或Result IDs。

### Step 11 — Build Gate Specifications

- 分配`GATExxx`；
- 使用Proposed Schema；
- 不写Runtime、Scorecard、Overall或implementation。

### Step 12 — Build Coverage Review and Audit

- required Gate Set与uncovered conditions；
- purpose、scope、atomicity、membership、threshold、unavailable与criticality rationale；
- 保留downstream concerns。

### Step 13 — Validate and Determine Status

- Structural / Field Validation；
- Cross-object Validation；
- Semantic Gate Review；
- unresolved issue进入Gate Design Issues；
- required Gate Set有效时READY，否则BLOCKED；
- 停止，不进入Runtime、Scorecard或Overall Score。

---

## 32. Gate Specification Design Status

Production状态只保留：

```text
GATES_READY
GATES_BLOCKED
```

### 32.1 GATES_READY

只有同时满足：

- authoritative upstream Definition current；
- required Grader / Metric Specifications validated；
- required Gate Set明确；
- explicit no-Gate decision或所有required conditions已覆盖；
- 每个Gate具有独立blocking meaning与scope；
- 每个condition atomic；
- source references valid；
- Grader target membership explicit；
- result selection与quantifier明确；
- Metric comparator、threshold与scale兼容；
- Metric availability semantics兼容；
- unavailable handling明确；
- criticality没有自动变Gate；
- insufficient / not-exercised没有偷换；
- OPEN / TRIGGERED / INDETERMINATE semantics清楚；
- blocking effect non-offsettable；
- explanation requirements充分；
- 所有Gates通过三层validation；
- Gate Set、Coverage Review与Audit一致；
- 没有unresolved blocker；
- 没有Runtime、Scorecard或Overall leakage。

### 32.2 GATES_BLOCKED

例如：

- required blocking intent不明确；
- required Gate Set不完整；
- scope模糊；
- condition不是atomic；
- target membership依赖grader ID或Runtime selector；
- referenced target或Metric不存在/stale；
- result selection或quantifier不清；
- threshold写成模糊text；
- comparator direction与Metric meaning相反；
- threshold与Metric scale/unit不兼容；
- required input missing默认OPEN；
- insufficient或not-exercised被自动当violation；
- criticality被自动当Gate；
- Gate重新grading或聚合；
- Gate吸收未建模Run status；
- Gate weight、AND/OR graph、Scorecard或Overall泄漏；
- 两个implementers无法得到相同Gate Result。

状态不是Gate Result，也不是Benchmark acceptance Result。

### 32.3 Validation subset

只对明确validated subset完成Gate Design时，使用：

```text
GATES_READY for validation subset
```

并保留full-Benchmark blocker。它不等于production `GATES_READY`。

---

## 33. Required Outputs

Gate Specification Design至少产生：

1. **Gate Specification Set**：Definition-time atomic policies；
2. **Gate Coverage Review**：required non-offsettable conditions与coverage；
3. **Gate Specification Design Audit**：purpose、scope、source、atomicity、membership、threshold与unavailable rationale；
4. **Gate Design Issues**：blocking issues与downstream concerns；
5. **Gate Specification Validation Summary**：Structural、Cross-object、Semantic三层结果；
6. **Gate Specification Design Status**：`GATES_READY`或`GATES_BLOCKED`；
7. **Schema Design Findings**：只记录真实design暴露的Schema need。

Working Gate Drafts不是required final output，也不算Gate coverage。

---

## 34. Gate Result Boundary

本轮不设计完整GateResult Schema，但必须保持：

```text
Specification:
what should trigger the Gate and what scope it blocks

Result:
whether that condition triggered for this Run and why
```

Future Gate Result在概念上至少需要关联或表达：

- Gate Specification；
- Run与Subject；
- resolved source Results；
- actual input availability；
- actual semantic matches、Metric value或availability state；
- actual quantifier/comparison evaluation；
- OPEN / TRIGGERED / INDETERMINATE；
- blocking / indeterminate reason；
- traceability。

一个Gate Result只对应一个Run、一个Subject和一个Gate Specification。Actual data不得写入Gate Specification。即使condition无法判断，也应产生可追踪的INDETERMINATE Result，而不是让Gate静默消失。

---

## 35. Scorecard 与 Overall Boundary

Scorecard未来可以组织：

- Grader Results；
- Metric Results；
- Gate Results；
- Overall Score；
- diagnostics。

本Guide不决定：

- Scorecard layout；
- 多Gate状态汇总display；
- Overall Score；
- final acceptance UI；
- comparison presentation。

Gate Specification不引用Scorecard。Gate Result进入Scorecard，但`TRIGGERED`保持独立、non-offsettable，不被Overall Score覆盖或删除。

---

## 36. Schema Design Findings

### 36.1 A discriminated condition union is required

Grader semantic match、Metric numeric threshold与Metric availability具有不同fields、references和validation paths。单一human-readable condition string无法保证Gate-level determinism，因此v0采用三variant union。

### 36.2 Atomic Gates avoid a boolean DSL

当前真实method needs可通过one Gate / one condition与多个Gate Specifications表达。没有证据支持nested AND/OR graph、Gate dependency或condition language。

### 36.3 GateTarget pair is the Grader membership authority

`(test_case_id, contract_id)`唯一定位ExpectedAssertion与authoritative GraderTarget。`grader_id`不进入Gate，避免shared Grader ambiguity与双authority。

### 36.4 Direct Grader Gates need Result selection

同一target可能在一个Run semantic scope内产生多个Episode / attempt Results。Direct Gate必须定义deduplication后选择all / first / final等distinct Results；Runtime identity不进入Definition。

### 36.5 Quantifier is structured but deliberately minimal

`any | all`覆盖当前atomic multi-target semantic match needs。Count、rate和normalized Contract performance应先成为Metric，不在Gate重复aggregation。

### 36.6 Threshold comparator and value must be structured

Gate是acceptability boundary，comparison direction错误会直接改变blocking Result。Comparator enum + numeric threshold优于free-form text，并支持scale compatibility validation。

### 36.7 Metric availability is an independent atomic condition

Metric below threshold与Metric unavailable通常有不同reason/remediation，因此独立availability variant保持diagnosis清楚，也避免threshold condition藏两个trigger paths。

### 36.8 Unavailable handling has no implicit OPEN

Missing required direct input只能显式形成INDETERMINATE或TRIGGERED。`DEFERRED`保留给future Runtime lifecycle，不进入Gate Result semantic enum。

### 36.9 Scope remains deterministic string in v0

当前没有真实evidence要求冻结scope taxonomy。Required string足以表达whole Run、Outcome、Workflow或capability scope；future cross-Gate reuse evidence可触发structured scope finding。

### 36.10 No Gate weight or severity

Gate天然non-offsettable。Weight会把Gate重新变Metric；non-blocking severity/advisory不属于Gate。

### 36.11 Execution status variant is deferred, not hidden

Concept Model允许future predefined execution-state condition，但当前缺少冻结status vocabulary与validity model。v0拒绝用free-form Runtime string临时实现；真实need应先进入Run validity / execution-status design。

### 36.12 No Candidate, Runtime IDs or actual Result fields

Working Draft + Audit足够。Episode/attempt/Result IDs与actual matches属于Runtime Gate Result evidence，不进入Gate Specification。

---

## 37. Method Self-Review

| 检查问题 | v0结论 |
|---|---|
| 1. Gate definition是否稳定？ | 是。Definition-time atomic non-offsettable condition，与future Gate Result分开。 |
| 2. Grader/Metric/Gate边界是否清楚？ | 是。Grader判断target；Metric聚合描述；Gate只检查已有Results的blocking condition。 |
| 3. Gate/Scorecard边界是否清楚？ | 是。Gate Result进入Scorecard，但Gate不定义layout、Overall或presentation。 |
| 4. Gate/Run-status边界是否清楚？ | 是。Infrastructure/execution validity不自动进入Gate；future status variant需先有合法vocabulary。 |
| 5. criticality是否与Gate分开？ | 是。Criticality只是rationale signal，不自动trigger或生成Gate。 |
| 6. non-offsettable semantics是否清楚？ | 是。Triggered Gate不被其他Metrics、Contracts或Overall Score抵消。 |
| 7. membership authority是否单一？ | 是。Direct Grader Gate使用target pair；Metric Gate使用metric ID。 |
| 8. Grader target condition是否deterministic？ | 是。Explicit targets、Result selection、semantic match与quantifier均required。 |
| 9. Metric threshold是否deterministic？ | 是。Comparator enum + numeric threshold。 |
| 10. threshold compatibility是否可验证？ | 是。Cross-object检查scale、direction、range、unit与precision。 |
| 11. unavailable handling是否明确？ | 是。只允许indeterminate或explicit triggered，不默认OPEN。 |
| 12. insufficient是否不会偷换violation？ | 是。只有显式trigger semantics匹配；建议独立Sufficiency Metric/Gate。 |
| 13. not-exercised是否不会偷换failure？ | 是。Exercise gap建议独立Metric/Gate。 |
| 14. quantifier是否需要？ | 需要最小`any | all`，用于atomic multi-target matching。 |
| 15. atomicity是否可执行？ | 是。使用source/reason/remediation/scope/unavailable/explanation test。 |
| 16. multi-condition composition是否需要？ | 当前不需要。独立conditions拆Gates；不引入boolean DSL。 |
| 17. Gate weight是否明确禁止？ | 是。Gate不平均、不加权、不offset。 |
| 18. Candidate是否需要？ | 当前不需要。Working Draft + Audit足够。 |
| 19. Audit是否需要？ | 需要非Core Audit保存blocking、scope、atomicity、membership、threshold与unavailable rationale。 |
| 20. required Gate Set如何确定？ | 来自authoritative non-offsettable acceptance intent，不从criticality机械推导。 |
| 21. Gate coverage含义是否正确？ | 是。覆盖required blocking conditions，不要求每个Contract有Gate。 |
| 22. result semantics是否清楚？ | 是。OPEN/TRIGGERED/INDETERMINATE避免与Contract PASS/FAIL混淆。 |
| 23. explanation要求是否合理？ | 是。要求事实、reason与traceability，不要求chain-of-thought或layout。 |
| 24. Schema最小字段是什么？ | ID、name、scope、condition union、unavailable handling、result semantics、explanation requirements。 |
| 25. 是否泄漏Scorecard？ | 未泄漏。没有layout、Overall、Gate weighting或final presentation。 |
| 26. 是否泄漏Runtime implementation？ | 未泄漏。没有actual IDs、values、evaluator code、CLI或serialization。 |
| 27. 哪些问题必须真实validation？ | Critical violation、insufficient、threshold、unavailable、NE、ANY、atomic split与criticality negative check。 |

### 37.1 Self-review corrections incorporated

本轮自审已在正文处理：

- 为防止criticality自动执行，要求explicit blocking rationale与Gate membership；
- 为防止Gate重新grading，condition只消费authoritative Result meanings；
- 为防止Gate重复Metric aggregation，count/rate/normalization返回Metric层；
- 为防止mega Gate，采用Atomic Gate Principle并拒绝AND/OR graph；
- 为防止shared Grader ambiguity，Direct Gate使用ExpectedAssertion pair，不存grader ID；
- 为防止retries造成歧义，Direct Gate要求Result selection与duplicate invariant；
- 为防止threshold方向错误，结构化comparator与numeric value；
- 为防止unavailable与threshold miss混淆，增加独立Metric availability condition；
- 为防止missing默认pass，unavailable handling不支持implicit OPEN；
- 为防止insufficient / NE偷换violation，明确semantic non-equivalence；
- 为防止Gate变Metric，禁止weight、severity averaging与offset；
- 为防止Run status leakage，execution-state variant延后至合法status model；
- 为防止Scorecard leakage，Gate只定义atomic condition和scope。

### 37.2 Current method conclusion

第一版Schema与method self-review未发现必须在real validation前继续扩Schema的generic blocker。当前结论是：

```text
GATE_SPEC_DESIGN_V0_METHOD_READY_FOR_REAL_VALIDATION
```

它不是`GATES_READY`，也不是任何Benchmark、Run或Target的acceptance status。没有真实Gate Set、Gate Result或Runtime execution被创建。

---

## 38. Future Real Method Validation Plan

Freeze GateSpecification method前，至少执行以下controlled validation cases：

### A. Critical target violated Gate

- explicit critical target pair；
- authoritative Result = violated；
- `quantifier: any`；
- expected `TRIGGERED`。

### B. Same critical target insufficient

- same target；
- Result = insufficient_evidence；
- violation condition不得trigger；
- 验证是否需要独立Sufficiency Metric/Gate。

### C. Metric threshold Gate

- Metric scale `0..1`, higher is better；
- comparator `lt`；
- threshold `0.90`；
- 验证boundary `0.89`、`0.90`、`0.91`。

### D. Metric unavailable Gate input

- threshold Gate收到unavailable Metric；
- 验证`indeterminate` policy；
- 独立Metric availability Gate验证`TRIGGERED`。

### E. Not-exercised critical target

- NE不得匹配violated condition；
- 验证exercise gap通过独立Metric/Gate处理。

### F. Multiple critical targets ANY semantics

- explicit targets至少两个；
- 一个violated、一个satisfied；
- `any`应trigger；
- duplicate和missing behavior可追踪。

### G. Atomic split vs mega Gate

- critical violation与workflow threshold具有不同source/remediation；
- 验证必须拆为两个Gates；
- 不创建OR graph。

### H. Criticality negative check

- critical Contract但没有authoritative blocking intent；
- 不得自动生成Gate；
- Coverage Review保留rationale。

每个case都要执行Independent Decision Test，并记录两个实现者是否得到相同OPEN/TRIGGERED/INDETERMINATE meaning。

---

## 39. Final Decision Checklist

### Inputs and Required Gate Set

- [ ] Upstream Grader / Metric Specifications validated且current
- [ ] Inputs属于同一Benchmark Definition version
- [ ] Required non-offsettable acceptance conditions有authoritative basis
- [ ] Required Gate Set完整，或explicit no-Gate decision已记录
- [ ] Validation subset保留full-Benchmark blocker

### Identity、Scope and Membership

- [ ] Gate name与blocking purpose清楚
- [ ] Scope明确且属于当前Benchmark surface
- [ ] Direct Grader membership只使用target pairs
- [ ] Metric condition只使用metric ID
- [ ] 没有grader ID、selector或Runtime discovery双authority
- [ ] References通过Cross-object Validation

### Atomicity and Condition

- [ ] One Gate只有one atomic condition
- [ ] 不需要AND/OR graph才能解释
- [ ] 多targets共享reason、scope、remediation与unavailable semantics
- [ ] Condition variant与fields一致
- [ ] Blocking确实non-offsettable

### Grader Result Condition

- [ ] Result selection与duplicate invariant明确
- [ ] Trigger semantics与Grader vocabulary兼容
- [ ] Quantifier为明确`any`或`all`
- [ ] Empty selected population不使用vacuous truth
- [ ] Case / Episode multiplicity处理清楚
- [ ] Insufficient与not-exercised没有偷换violation

### Metric Conditions

- [ ] Metric ref存在且validated
- [ ] Comparator、threshold与Metric scale/direction/range/unit兼容
- [ ] Threshold没有写回Metric Specification
- [ ] Metric unavailable与numeric threshold condition分开
- [ ] Gate没有重新计算Metric aggregation

### Unavailable and Result Meaning

- [ ] Missing required input不默认OPEN
- [ ] Unavailable handling明确为indeterminate或triggered
- [ ] OPEN不等于whole Benchmark PASS
- [ ] TRIGGERED scope与blocking effect清楚
- [ ] INDETERMINATE不会被隐藏
- [ ] Explanation requirements完整
- [ ] 没有actual Result values、IDs或triggered boolean

### Boundaries and Validation

- [ ] Criticality没有自动变Gate
- [ ] 没有Gate weight或severity averaging
- [ ] 没有raw Evidence rejudgment
- [ ] 没有未建模Runtime status condition
- [ ] 没有Gate-to-Gate、Scorecard或Overall refs
- [ ] 没有Runtime、CLI、Pydantic或evaluator implementation
- [ ] Structural / Cross-object / Semantic Validation完成
- [ ] Gate Set、Coverage Review与Audit一致
- [ ] 无unresolved Gate Design Issue

全部必需检查通过时，production Gate Specification Design才可输出：

```text
GATES_READY
```

否则输出：

```text
GATES_BLOCKED
```

并停止在Gate Specification Design边界，不开始Runtime、Gate Result implementation、Scorecard或Overall Score Design。
