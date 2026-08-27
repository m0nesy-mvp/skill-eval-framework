# 《Benchmark Definition Schema Design v0.2 — Authority and Digest Hardening》

Version: v0.2
Status: Architecture Authority Defined and Validated
Date: 2026-08-27

## 1. Scope and predecessor

本文是`docs/benchmark-definition-requirement-contract-schema-design-v0.md`的versioned hardening successor。

Predecessor v0是冻结的历史baseline，只覆盖：

```text
BenchmarkDefinition
Requirement
Contract
```

本文不无痕改写该baseline，也不重新设计Requirement、Contract、Test Case、Evidence Specification、Grader Specification、Metric Specification或Gate Specification。已有object schemas继续由各自frozen schema / Guide提供authority；本文只补齐：

1. 完整Benchmark Definition composition；
2. Overall Score Definition-time authority；
3. whole-benchmark Acceptance Definition-time authority；
4. external semantic resource binding；
5. Frozen Definition content closure；
6. canonical serialization与digest protocol；
7. composition / policy / closure层validation。

本文解决以下Architecture Findings的Definition authority：

```text
AF-RR-001
Overall Score lacks frozen Definition-time authority

AF-RR-002
Whole-benchmark acceptance lacks aggregation authority

AF-RR-003
Definition digest production protocol is not yet frozen
```

本轮只进行schema hardening与architecture-level controlled validation，不进行Runtime real validation，不修改Runtime Guide，不实现Pydantic、CLI、Overall calculator、Acceptance evaluator、digest generator、storage或packaging。

---

## 2. Preserved architecture boundary

16个Core Objects保持不变：

```text
Definition: 8
Runtime: 4
Result: 4
Total: 16
```

本文不新增：

- OverallScoreSpecification Core Object；
- AcceptanceSpecification Core Object；
- DefinitionBundle Core Object；
- DefinitionResource Core Object；
- Fixture Core Object；
- Subject Core Object。

新增structures全部依附Benchmark Definition，没有独立lifecycle、独立freeze、独立registry identity或独立Runtime Core Result。

```text
OverallScorePolicy
AcceptancePolicy
DefinitionResourceBinding
Canonical closure profile
```

都是Benchmark Definition composition / freeze protocol的一部分，不改变Concept Model object count。

---

## 3. Imported object schema authorities

本文引用而不复制重写以下object schemas：

| Object | Existing authority |
|---|---|
| Requirement | `docs/benchmark-definition-requirement-contract-schema-design-v0.md` |
| Contract | `docs/benchmark-definition-requirement-contract-schema-design-v0.md` |
| Test Case | `docs/guides/test-case-design-guide-v0.md` |
| Evidence Specification | `docs/guides/evidence-specification-guide-v0.md` |
| Grader Specification | `docs/guides/grader-specification-guide-v0.md` |
| Metric Specification | `docs/guides/metric-specification-guide-v0.md` |
| Gate Specification | `docs/guides/gate-specification-guide-v0.md` |

如果任一imported object authority未来形成新frozen version，Benchmark Definition必须明确使用与本closure profile兼容的schema interpretation；不能由Runtime临时混合不同版本语义。

---

## 4. Final Benchmark Definition composition

```text
BenchmarkDefinition:
- benchmark_id: str
- name: str
- version: str
- description: str?
- status: draft | frozen
- requirements: list[Requirement]
- contracts: list[Contract]
- test_cases: list[TestCase]
- evidence_specifications: list[EvidenceSpecification]
- grader_specifications: list[GraderSpecification]
- metric_specifications: list[MetricSpecification]
- gate_specifications: list[GateSpecification]
- overall_score_policy: OverallScorePolicy
- acceptance_policy: AcceptancePolicy
- semantic_resource_bindings: list[DefinitionResourceBinding]
```

### 4.1 Existing identity and lifecycle fields

`benchmark_id`、`name`、`version`、`description`与`status`继续使用predecessor v0语义：

- `benchmark_id`表示lineage；
- `version`表示declared Definition version；
- `draft | frozen`是lifecycle，不是VALID / INVALID；
- Frozen Definition不得原地修改；
- 修改任何closure content必须创建新version。

### 4.2 Complete composition

八类Definition Core Objects现在全部进入同一Benchmark Definition content boundary。各collection使用既有individual object schemas；本文件只承担：

- composition；
- ID namespace与引用closure；
- complete Definition validation；
- nested Benchmark policies；
- freeze content identity。

### 4.3 Required policy decisions

`overall_score_policy`与`acceptance_policy`都是required。

Benchmark不需要Overall或whole-benchmark acceptance时，必须显式使用`mode: disabled`。禁止通过field absent或`null`表达disabled，因为absence可能表示author遗漏、旧schema或migration未完成。

### 4.4 Semantic resource bindings

`semantic_resource_bindings`是required list，允许空列表。空列表只在Definition没有external semantic resource，或所有相关content已经inline / content-addressed时合法。

---

## 5. OverallScorePolicy union

```text
OverallScorePolicy =
  DisabledOverallScorePolicy
  | WeightedNormalizedMeanOverallScorePolicy
```

Discriminator是`mode`。

不使用：

```text
overall_score_enabled: bool
```

因为boolean无法承载enabled variant所需的membership、normalization、availability与precision authority。

---

## 6. DisabledOverallScorePolicy

```text
DisabledOverallScorePolicy:
- mode: disabled
```

语义：

- Benchmark明确不产生numeric Overall Score；
- Runtime不得默认聚合所有Metrics；
- Runtime不得默认等权；
- Scorecard只能记录Overall disabled outcome；
- disabled不是calculation failure；
- disabled不是Metric unavailable；
- disabled不是Overall unavailable；
- Gate Results与AcceptancePolicy继续独立工作。

`mode: disabled` variant禁止出现其他Overall policy fields。

---

## 7. WeightedNormalizedMeanOverallScorePolicy

```text
WeightedNormalizedMeanOverallScorePolicy:
- mode: weighted_normalized_mean
- metric_contributions: list[OverallMetricContribution]
- minimum_available_weight_fraction: decimal
- canonical_scale: unit_interval
- canonical_precision: int
```

v0只支持：

```text
explicit Metric membership
→ canonical Metric value
→ explicit normalization to [0,1]
→ explicit cross-Metric weight
→ weighted normalized mean
→ one final canonical rounding
```

不设计formula DSL、Metric-to-Metric graph、arbitrary expression、Runtime selector或implicit default aggregation。

### 7.1 metric_contributions

必须非空。每项显式引用一个当前Benchmark `metric_id`。同一个`metric_id`不得重复。

### 7.2 minimum_available_weight_fraction

必须是finite canonical decimal，范围：

```text
0 < minimum_available_weight_fraction <= 1
```

它是exclude-and-renormalize之后仍能保留Overall declared meaning的minimum actual available Metric weight coverage。

### 7.3 canonical_scale

v0固定为：

```text
unit_interval
```

其canonical numeric range为`[0,1]`。0–100等display scale不是authority，不进入本policy。

### 7.4 canonical_precision

必须是integer，范围：

```text
1 <= canonical_precision <= 12
```

它定义final canonical Overall value的小数位数。Framework-wide rounding固定为decimal arithmetic + round-half-even，不允许每个Benchmark另选rounding mode。

---

## 8. OverallMetricContribution

```text
OverallMetricContribution:
- metric_id: str
- weight: decimal
- normalization: MetricNormalization
- unavailable_result_handling:
    overall_unavailable | exclude_and_renormalize
- missing_result_handling:
    overall_unavailable | exclude_and_renormalize
```

### 8.1 Explicit membership

`metric_id`是唯一membership authority。禁止：

- all metrics；
- all Outcome metrics；
- tag / name / evaluation_type selector；
- Runtime selector；
- future metrics auto-inclusion。

新增Metric Specification不会自动改变旧Benchmark Overall Score。

### 8.2 Weight

`weight`必须是positive finite decimal：

```text
weight > 0
```

weights不要求sum to 1；Runtime使用relative weighted mean。

Weight不能从以下内容自动推导：

- Contract criticality；
- Gate significance；
- Test Case count；
- Metric内部`weighting_policy`；
- `evaluation_type`；
- Result availability；
- display order。

```text
Metric weighting_policy
≠ Overall Metric weight
```

### 8.3 Separate unavailable and missing handling

必须分别保存两种handling，因为：

```text
Metric Result exists + status=unavailable
≠ no Metric Result exists
```

两者可以使用相同policy value，但不能共享一个含糊field。

---

## 9. MetricNormalization union

```text
MetricNormalization =
  IdentityUnitIntervalNormalization
  | LinearBoundedNormalization
```

Discriminator是`type`。

---

## 10. IdentityUnitIntervalNormalization

```text
IdentityUnitIntervalNormalization:
- type: identity_unit_interval
```

只在referenced Metric Specification满足以下条件时合法：

- canonical Result是numeric；
- canonical range是`[0,1]`；
- higher表示better；
- 0和1的semantic endpoints与Overall contribution兼容；
- 不依赖display rounding；
- Metric不是ordinal label。

公式：

```text
normalized_contribution = canonical_metric_value
```

Runtime不得因为值“看起来像百分比”而隐式使用identity normalization。

---

## 11. LinearBoundedNormalization

```text
LinearBoundedNormalization:
- type: linear_bounded
- source_min: decimal
- source_max: decimal
- direction: higher_is_better | lower_is_better
```

Required constraints：

```text
source_min and source_max are finite
source_max > source_min
```

### 11.1 Higher is better

```text
normalized
= (canonical_metric_value - source_min)
  / (source_max - source_min)
```

### 11.2 Lower is better

```text
normalized
= (source_max - canonical_metric_value)
  / (source_max - source_min)
```

### 11.3 Compatibility rules

- bounds必须与Metric Specification declared scale、range与unit兼容；
- direction必须与Metric Result semantics兼容；
- Runtime不得clamp out-of-range values；
- out-of-range canonical value是compatibility / Result integrity problem；
- unbounded count没有explicit validated bounds时不能参与；
- ordinal没有validated distance semantics时不能参与；
- formatted或display-rounded value不得参与；
- Runtime不得自行发明min/max、direction或normalization。

---

## 12. Overall unavailable and missing handling

v0只允许：

```text
overall_unavailable
exclude_and_renormalize
```

不允许：

- fixed contribution；
- assume zero；
- assume worst；
- assume best；
- use previous Run value；
- fall back to display value；
- treat missing as semantic unavailable。

### 12.1 overall_unavailable

如果相应selected Metric unavailable或missing：

- Overall policy application完成；
- Overall outcome为unavailable；
- 不产生canonical Overall value；
- 保留Metric Result ref或missing application；
- 不继续用剩余Metrics伪造available score。

### 12.2 exclude_and_renormalize

如果相应selected Metric unavailable或missing：

- 从numeric numerator与included-weight denominator中排除；
- 保留exclusion reason；
- missing不被改写为unavailable；
- 重新归一化剩余included weights；
- 只有available weight coverage满足minimum时才产生available Overall。

### 12.3 Why fixed contribution is excluded

Fixed contribution会把availability、engine failure或missing Result转换为synthetic performance。当前没有真实validation证明这种语义必要，因此v0拒绝该扩展。

---

## 13. Available weight coverage

```text
available_weight_fraction
= sum(weights of actual available Metrics included)
  / sum(weights of all explicitly selected Metrics)
```

其中：

- numerator只计算actual available Metric Results；
- unavailable、missing与synthetic values不进入numerator；
- denominator包含所有explicit selected Metrics的weights；
- duplicate metric IDs在Definition validation阶段禁止。

只有：

```text
available_weight_fraction
>= minimum_available_weight_fraction
```

时，exclude-and-renormalize才允许产生available Overall。

如果included Metric set为空：

```text
Overall outcome = unavailable
```

不得输出0、1、100%或PASS / FAIL。

---

## 14. Overall canonical calculation authority

对于所有included available Metrics：

```text
unrounded_overall
= sum(normalized_contribution_i × weight_i)
  / sum(included_weight_i)
```

然后：

```text
canonical_overall
= round_half_even(
    unrounded_overall,
    canonical_precision
  )
```

Rules：

- 使用canonical Metric Result values；
- normalization不做display rounding；
- weighted products不做intermediate display rounding；
- weighted mean不做多阶段rounding；
- 只在final canonical value上round一次；
- display formatting不具有authority；
- Gate与Acceptance不能修改canonical Overall value。

---

## 15. AcceptancePolicy union

```text
AcceptancePolicy =
  DisabledAcceptancePolicy
  | GateBasedAcceptancePolicy
```

Discriminator是`mode`。

v0不包含`validity_only`。原因见第20节。

---

## 16. DisabledAcceptancePolicy

```text
DisabledAcceptancePolicy:
- mode: disabled
```

语义：

- Benchmark不产生whole-benchmark acceptability semantic；
- valid Run仍然只表示valid Run；
- valid不会自动变ACCEPTABLE；
- zero-Gate Benchmark合法；
- Gate Results仍保留各自declared scope；
- Scorecard不得使用vacuous truth生成ACCEPTABLE；
- disabled不表示blocked或indeterminate。

`mode: disabled`禁止出现`participating_gates`。

---

## 17. GateBasedAcceptancePolicy

```text
GateBasedAcceptancePolicy:
- mode: gate_based
- participating_gates: list[AcceptanceGateContribution]
```

`participating_gates`必须非空。每个Gate ID必须显式列出、unique并解析到当前Benchmark Definition。

禁止：

- all-gates selector；
- scope selector；
- current / future Gates auto-inclusion；
- Gate name matching；
- Runtime selection；
- empty-list truth。

Membership本身是local Gate scope向whole-benchmark acceptance传播的Definition authority。

---

## 18. AcceptanceGateContribution

```text
AcceptanceGateContribution:
- gate_id: str
- indeterminate_handling:
    overall_indeterminate | overall_blocked
- missing_result_handling:
    overall_indeterminate | overall_blocked
```

### 18.1 Actual TRIGGERED

```text
participating Gate Result = TRIGGERED
→ whole-benchmark Acceptance = BLOCKED
```

该effect固定，不增加weight、penalty、severity或offset。

### 18.2 Actual OPEN

```text
participating Gate Result = OPEN
→ no blocking contribution
```

OPEN只对该Gate成立，不单独证明whole Benchmark acceptable。

### 18.3 Actual INDETERMINATE

根据`indeterminate_handling`：

```text
overall_indeterminate
→ whole-benchmark INDETERMINATE

overall_blocked
→ whole-benchmark BLOCKED
```

后者必须解释为AcceptancePolicy fail-closed handling，不得改写原Gate Result为TRIGGERED。

### 18.4 Missing Gate Result

Missing表示required Gate Result object不存在，可能来自Gate evaluator failure或application未产生。它不是Gate Result semantic。

根据`missing_result_handling`：

```text
overall_indeterminate
→ whole-benchmark INDETERMINATE

overall_blocked
→ whole-benchmark BLOCKED
```

禁止：

```text
missing → OPEN
missing → fabricate GateResult(INDETERMINATE)
```

---

## 19. Whole-benchmark acceptance aggregation

本policy只适用于valid Run。对explicit participating Gates解析actual states：

```text
OPEN
TRIGGERED
INDETERMINATE
MISSING
```

固定aggregation precedence：

```text
1. any actual TRIGGERED
   → BLOCKED

2. any INDETERMINATE configured overall_blocked
   → BLOCKED

3. any MISSING configured overall_blocked
   → BLOCKED

4. otherwise,
   any INDETERMINATE configured overall_indeterminate
   or any MISSING configured overall_indeterminate
   → INDETERMINATE

5. otherwise,
   all required participating Gate Results exist and are OPEN
   → ACCEPTABLE
```

Explanation必须区分：

- blocked by actual Gate TRIGGERED；
- blocked by INDETERMINATE fail-closed policy；
- blocked by missing-result fail-closed policy；
- indeterminate due to actual Gate INDETERMINATE；
- indeterminate due to missing required Gate Result。

AcceptancePolicy不重新evaluate Gate condition，不读取Metric、Grader或Evidence。

---

## 20. validity_only decision

Controlled architecture review没有发现必须保留`validity_only`的真实ordinary Benchmark need。

```text
Run validity
= whether this execution is a valid evaluable Run

Benchmark acceptance
= a Definition-authorized conclusion over evaluation Results
```

Zero-Gate Benchmark需要表达的是：

```text
no whole-benchmark acceptance is defined
```

这已经由：

```text
acceptance_policy:
  mode: disabled
```

完整表达。

增加`validity_only`只会把：

```text
Run valid
```

重复包装为：

```text
ACCEPTABLE
```

而没有消费任何evaluation Result，也没有新增独立Benchmark acceptance meaning。因此v0删除`validity_only`。

Future真实Benchmark若证明“valid execution itself就是acceptance policy”具有独立、可审计的业务语义，应作为future extension重新验证，不在v0预留。

---

## 21. Acceptance and Overall remain independent

AcceptancePolicy不消费Overall Score。

```text
Overall = 0.95
+ participating Gate TRIGGERED
→ Overall remains 0.95
→ Acceptance = BLOCKED
```

```text
Overall low
+ all participating Gates OPEN
→ Acceptance = ACCEPTABLE
```

在v0是合法组合。

不自动增加：

```text
Overall threshold → BLOCKED
```

如果future真实Benchmark需要Overall threshold影响acceptance，必须设计explicit acceptance condition extension并独立validation。不得由Runtime、Scorecard或UI临时推导。

---

## 22. Run validity precedence

Definition-time policy冻结以下Runtime application prerequisite：

```text
authoritative Overall outcome
and
authoritative whole-benchmark Acceptance
require Run validity = valid
```

### 22.1 Invalid Run

当Run invalid：

- Scorecard可以保留audit inventory；
- existing Results可以显示；
- no authoritative Overall；
- no ACCEPTABLE / BLOCKED / INDETERMINATE acceptance semantic；
- invalid不转换为blocked；
- invalid不转换为Gate triggered；
- policy不得消费non-authoritative Results形成final view。

```text
Run invalid
≠ Gate TRIGGERED
≠ Acceptance BLOCKED
```

### 22.2 Pending validity

Pending Run同样不能产生final authoritative Overall或Acceptance。

### 22.3 Scope boundary

本文只冻结policy application prerequisite，不设计Runtime Scorecard wrapper、production status fields或UI。

---

## 23. Gate scope propagation

Gate Specification的required`scope: str`保持不变。AcceptancePolicy explicit membership提供另一层、不同问题的authority：

```text
Gate scope
→ what local declared scope becomes unacceptable

AcceptancePolicy membership
→ whether that Gate Result propagates to whole Benchmark
```

Semantic validation必须检查：

- whole-benchmark Gate被遗漏是否形成Definition conflict；
- local-scope Gate传播必须explicit；
- propagation rationale与Gate scope兼容；
- Gate没有被重新evaluate；
- Gate TRIGGERED没有被转换为score penalty；
- unlisted Gate仍保持local scope且进入Scorecard。

由于Gate scope当前是string，该一致性属于Semantic Review，不伪装成纯Field Validation。

---

## 24. Zero-Gate behavior

合法配置：

```text
gate_specifications: []
acceptance_policy:
  mode: disabled
```

结果语义：

- valid Run仍只是valid Run；
- no whole-benchmark acceptance produced；
- no vacuous ACCEPTABLE；
- Scorecard仍可展示Metrics与diagnostics。

非法配置：

```text
gate_specifications: []
acceptance_policy:
  mode: gate_based
  participating_gates: []
```

`gate_based`要求non-empty participating Gate set，不使用`ALL([])=true`。

---

## 25. DefinitionResourceBinding

```text
DefinitionResourceBinding:
- resource_ref: str
- semantic_role: str
- content_digest: str
```

### 25.1 Purpose

任何external resource，只要其content影响以下任一语义，就必须进入Frozen Definition transitive closure：

- Test Case execution；
- fixture semantics；
- grader semantics；
- Metric semantics；
- Gate semantics；
- Overall policy semantics；
- Acceptance policy semantics；
- other authoritative Benchmark policy semantics。

### 25.2 Three valid forms

每个semantic resource必须满足至少一种：

1. content inline进入canonical Definition；
2. reference本身是content-addressed；
3. `semantic_resource_bindings`中存在immutable content digest binding。

只有mutable path且无content digest：

```text
Definition closure incomplete
→ Definition cannot freeze
```

### 25.3 Field rules

- `resource_ref`非空、在当前Definition中unique；
- `resource_ref`是Definition内logical reference，不得使用machine-specific absolute filesystem path；
- `semantic_role`非空，说明该resource影响哪些Definition semantics；
- 同一resource用于多个roles时合并到一个binding的semantic_role说明，不创建conflicting duplicate bindings；
- `content_digest`使用`sha256:<64 lowercase hex>`；
- locator不证明content identity；
- Runtime Artifact digest不能替代Definition-time resource binding。

### 25.4 No Fixture Core Object

Binding只证明external content identity，不创建Fixture lifecycle、Fixture Result或Fixture registry Core Object。

---

## 26. Frozen Definition content identity decision

`definition_digest`在v0.2明确表示：

```text
complete Frozen Definition content identity
```

不使用“只hash部分normative semantics”的另一套classification。

因此：

- 所有schema-declared Benchmark Definition fields进入digest；
- `name`进入digest；
- `description`存在时进入digest；
- Requirement `source_ref`存在时进入digest；
- 所有nested object fields进入digest；
- nested policies进入digest；
- semantic resource bindings进入digest。

这使digest回答：

> 这次Run绑定的是哪一个完整Frozen Definition content snapshot？

而不是：

> 两个不同snapshot是否可能产生类似execution semantics？

如果只修改name、description或source_ref，Frozen content identity也改变；按照Frozen lifecycle必须创建新version并重新digest。v0.2不引入`non_digest_metadata`逃生字段。

---

## 27. Frozen Definition Closure

Closure至少包含：

```text
Benchmark Definition schema-declared fields
├── benchmark_id
├── name
├── version
├── description?
├── status
├── requirements
├── contracts
├── test_cases
├── evidence_specifications
├── grader_specifications
├── metric_specifications
├── gate_specifications
├── overall_score_policy
├── acceptance_policy
└── semantic_resource_bindings
```

并包含任何future schema-declared authoritative Benchmark policies，但只有在closure profile升级并明确字段规则后才允许新增。

### 27.1 Included

- every schema-declared Frozen Definition field；
- all nested Definition objects；
- all nested policy values；
- all source references that are object fields；
- all semantic resource content digests；
- explicit empty lists；
- explicit disabled policy variants。

### 27.2 Excluded

- Run、Episode、Artifact、Evidence；
- Grader / Metric / Gate Results；
- Scorecard；
- Runtime timestamps；
- filesystem layout与checkout path；
- storage location；
- UI / report formatting；
- comments；
- scratch notes；
- Candidate ledgers；
- Design Audits；
- validation outputs；
- `definition_snapshot_ref`；
- `definition_digest`本身。

Design Audit如果包含尚未进入schema的决定，不能靠hash Audit偷偷获得authority；应先把真实authority提升为schema field。

---

## 28. Canonical closure profile

v0 profile固定为：

```text
skill-eval-frozen-definition-closure-v0
```

Invariant：

```text
same profile
+ same complete closure content
→ same canonical bytes
→ same digest
```

Profile变化必须使用新profile ID。v0不做algorithm negotiation或implementation-specific options。

Conceptual canonical envelope：

```text
CanonicalFrozenDefinition:
- closure_profile: skill-eval-frozen-definition-closure-v0
- benchmark_definition: BenchmarkDefinition
```

该envelope只是serialization input，不是DefinitionBundle Core Object。External resource bindings已经位于BenchmarkDefinition中，不重复保存第二份。

---

## 29. Canonical serialization rules

### 29.1 Encoding

- UTF-8；
- no BOM；
- Unicode NFC；
- string line endings规范化为LF；
- no comments；
- no presentation whitespace；
- exactly one canonical byte sequence。

### 29.2 Object keys

Object keys按Unicode code-point lexical order排序。不得依赖YAML source order、JSON pretty printer、Python insertion order或filesystem order。

### 29.3 Strings

- 使用第29.9节固定的JSON string encoding；
- NFC normalization在escaping前完成；
- CRLF与CR normalize为LF；
- 不删除string内部semantic spaces；
- field validation负责禁止非法empty或leading/trailing-only values。

### 29.4 Absent and null

```text
absent != null
```

- optional field absent时不序列化；
- 不自动写`null`；
- `null`默认非法；
- 只有schema明确nullable时才允许；
- current v0.2 Definition schema没有nullable fields；
- empty list与absent不同；
- empty string与absent不同。

### 29.5 Canonical decimals

- only finite decimal；
- NaN与Infinity非法；
- no leading plus；
- no insignificant leading zeros；
- `-0`规范化为`0`；
- no exponent notation；
- remove insignificant fractional trailing zeros；
- decimal point只在存在non-zero fractional part时保留。

因此：

```text
1
1.0
1.000
1e0
```

在schema成功解析为同一decimal value后canonical representation均为：

```text
1
```

### 29.6 Booleans and enums

- booleans使用lowercase`true | false`；
- enums使用schema-declared exact lowercase token，除非既有frozen schema明确使用其他case；
- implementation不得case-fold enum values。

### 29.7 Unknown fields

Unknown Definition或policy field使canonicalization blocked。禁止某实现hash unknown field而另一实现忽略。

```text
unknown field
→ schema invalid
→ canonicalization blocked
→ no digest
→ cannot freeze
```

### 29.8 Ordered vs set-like lists

每个list field必须由profile明确分类。Implementation不得根据当前值自行猜测。

### 29.9 Canonical JSON container and string encoding

Canonical bytes使用固定JSON data-model encoding：

- object使用`{`与`}`；
- array使用`[`与`]`；
- object member name与value之间只使用一个`:`；
- adjacent members / elements之间只使用一个`,`；
- tokens之间不插入空格、tab或line break；
- object keys使用双引号string并按29.2节排序；
- arrays先按第30节分类与规范化，再按JSON array encoding写出；
- scalar只允许canonical string、decimal、boolean或explicitly schema-authorized null；
- current Definition schema没有authorized null。

Canonical string encoding：

- string以ASCII double quote开始和结束；
- `"`固定编码为`\"`；
- `\`固定编码为`\\`；
- U+0008、U+0009、U+000A、U+000C、U+000D分别使用`\b`、`\t`、`\n`、`\f`、`\r`；
- 其他U+0000–U+001F control characters使用lowercase hexadecimal `\u00xx`；
- `/`不得escape；
- U+0020及以上有效Unicode scalar values除`"`与`\`外，以NFC后的UTF-8直接编码，不使用可选`\uXXXX`；
- unpaired UTF-16 surrogate不是valid Unicode scalar，schema validation失败；
- unnecessary escape sequence禁止。

因此同一normalized string只有一个byte representation，不允许一个实现输出literal UTF-8、另一个实现对相同非ASCII character使用optional Unicode escape。

---

## 30. Collection ordering classification

Canonical string sort在NFC与LF normalization后，按Unicode code-point lexical order执行。

Pair sort使用tuple lexical order。

### 30.1 Benchmark-level collections

| Field | Classification | Canonical ordering |
|---|---|---|
| `requirements` | set-like identified collection | `requirement_id` ascending |
| `contracts` | set-like identified collection | `contract_id` ascending |
| `test_cases` | set-like identified collection | `test_case_id` ascending |
| `evidence_specifications` | set-like identified collection | `evidence_spec_id` ascending |
| `grader_specifications` | set-like identified collection | `grader_id` ascending |
| `metric_specifications` | set-like identified collection | `metric_id` ascending |
| `gate_specifications` | set-like identified collection | `gate_id` ascending |
| `semantic_resource_bindings` | set-like identified collection | `resource_ref` ascending |

### 30.2 Requirement and Contract

| Field | Classification | Canonical ordering |
|---|---|---|
| `Contract.requirement_ids` | set-like ID references | ID ascending |
| `Contract.success_criteria` | set-like semantic statements | canonical string ascending |
| `Contract.failure_criteria` | set-like semantic statements | canonical string ascending |
| `Contract.failure_modes` | set-like semantic statements | canonical string ascending |

Requirement没有list fields。

### 30.3 Test Case

| Field | Classification | Canonical ordering |
|---|---|---|
| `TestCase.preconditions` | set-like semantic statements | canonical string ascending |
| `TestCase.fixtures` | set-like semantic statements / refs | canonical string ascending |
| `TestCase.initial_state` | set-like semantic statements | canonical string ascending |
| `TestCase.interaction_steps` | ordered semantic sequence | preserve declared order |
| `TestCase.expected_assertions` | set-like target collection | `contract_id` ascending |

Reversing `interaction_steps` changes semantics and digest。Reordering fixtures without changing content does not。

### 30.4 Evidence Specification

| Field | Classification | Canonical ordering |
|---|---|---|
| `EvidenceSpecification.targets` | set-like target pairs | `(test_case_id, contract_id)` ascending |
| `observation_requirements` | set-like semantic statements | canonical string ascending |
| `provenance_requirements` | set-like semantic statements | canonical string ascending |
| `context_requirements` | set-like semantic statements | canonical string ascending |
| `qualification_requirements` | set-like semantic statements | canonical string ascending |

需要表达temporal order时，order必须写入statement semantics；列表本身不是execution sequence。

### 30.5 Grader Specification

| Field | Classification | Canonical ordering |
|---|---|---|
| `GraderSpecification.targets` | set-like target pairs | `(test_case_id, contract_id)` ascending |
| `GraderTarget.evidence_spec_ids` | set-like ID references | ID ascending |
| `judgment_criteria` | set-like semantic statements | canonical string ascending |
| `insufficiency_handling` | set-like semantic statements | canonical string ascending |
| `explanation_requirements` | set-like semantic statements | canonical string ascending |
| `Rubric.dimensions` | ordered rubric semantics | preserve declared order |
| `RubricDimension.anchors` | ordered rubric semantics | preserve declared order |

Rubric dimension / anchor order保留，因为当前schema没有独立IDs，且ordered interpretation可能影响reviewer application。若future schema证明order非语义并增加stable IDs，需升级profile。

### 30.6 Metric Specification

| Field | Classification | Canonical ordering |
|---|---|---|
| `MetricSpecification.inputs` | set-like target pairs | `(test_case_id, contract_id)` ascending |
| `eligibility_policy.eligible_result_semantics` | set-like semantic tokens | canonical string ascending |
| `eligibility_policy.non_substantive_handling` | set-like semantic statements | canonical string ascending |
| `eligibility_policy.unavailable_input_handling` | set-like semantic statements | canonical string ascending |
| `contribution_mapping` | set-like mapping entries | `(source_semantics, contribution_semantics)` ascending |
| `completeness_policy.transparency_requirements` | set-like semantic statements | canonical string ascending |

`result_selection_policy`、`aggregation_unit`、`unit_reduction`、`aggregation_rule`、`weighting_policy`与other Metric policy fields是scalar strings / nested objects，不是ordered lists。

### 30.7 Gate Specification

| Field | Classification | Canonical ordering |
|---|---|---|
| `GateSpecification.explanation_requirements` | set-like semantic statements | canonical string ascending |
| `GraderResultGateCondition.targets` | set-like target pairs | `(test_case_id, contract_id)` ascending |
| `trigger_result_semantics` | set-like semantic tokens | canonical string ascending |

Metric threshold与availability Gate conditions没有list fields。

### 30.8 Benchmark nested policies

| Field | Classification | Canonical ordering |
|---|---|---|
| `OverallScorePolicy.metric_contributions` | set-like identified collection | `metric_id` ascending |
| `AcceptancePolicy.participating_gates` | set-like identified collection | `gate_id` ascending |

### 30.9 Duplicate rule

Canonical sorting不负责隐藏duplicates。Duplicates必须先使Structural Validation失败；不能通过sort + deduplicate静默修复。

---

## 31. Digest protocol

### 31.1 Algorithm

固定：

```text
SHA-256
```

### 31.2 Format

```text
sha256:<64 lowercase hexadecimal characters>
```

Algorithm identifier保存在digest string中。v0不做algorithm negotiation。

### 31.3 Calculation

```text
complete BenchmarkDefinition closure
→ wrap with closure_profile
→ validate schema and reject unknown fields
→ normalize strings / decimals / optional representation
→ canonicalize collections using section 30
→ order object keys
→ serialize canonical UTF-8 bytes
→ SHA-256
→ sha256:<lowercase hex>
```

### 31.4 Exclusions

- digest不包含自身；
- `definition_snapshot_ref`不进入closure；
- storage path与checkout location不进入closure；
- source YAML / JSON whitespace不具有authority。

### 31.5 Meaning

SHA-256在本Framework只表示：

- Frozen Definition content identity；
- drift detection；
- Run binding；
- audit comparison。

它不是：

- digital signature；
- publisher authentication；
- authorization；
- trust decision；
- confidentiality mechanism。

### 31.6 Freeze output metadata

Freeze process至少输出：

```text
closure_profile: skill-eval-frozen-definition-closure-v0
definition_digest: sha256:<64 lowercase hex>
```

它们是freeze protocol metadata，不是第17个Core Object，也不放回closure造成circular hash。

---

## 32. Snapshot reference boundary

Future Run可以保存：

```text
definition_snapshot_ref
```

但它只用于：

- retrieval；
- audit；
- locating canonical source content。

它不能：

- 替代digest；
- 证明content identity；
- 进入digest；
- 允许mutable location漂移；
- 解决same-version conflict。

```text
digest proves identity
snapshot ref helps locate content
```

---

## 33. Same-version drift

Frozen Definition identity由：

```text
benchmark_id
+ version
+ closure_profile
+ definition_digest
```

共同确定。

如果：

```text
same benchmark_id
+ same version
+ same closure_profile
+ different definition_digest
```

则：

```text
invalid frozen-definition identity state
```

### 33.1 Definition freeze / registry validation

```text
same-version content drift
→ BLOCKED
```

必须创建新version；Framework不得自动改版本、覆盖旧digest或选择“最新文件”。

### 33.2 Runtime validation

```text
expected digest != loaded snapshot computed digest
→ Run validity = invalid
```

不得：

- 自动接受；
- 自动更新Run reference；
- fallback到ID + version；
- 转成Gate Result；
- 转成Contract violation；
- 继续生成authoritative Overall / Acceptance。

---

## 34. Structural Validation

### 34.1 BenchmarkDefinition

- 所有required composition fields存在；
- `description` absent或non-empty；
- status只允许`draft | frozen`；
- eight Definition object collections满足各自existing schema cardinality；
- `gate_specifications`与`semantic_resource_bindings`允许空；
- two policy fields不得absent或null；
- unknown fields rejected。

### 34.2 OverallScorePolicy

- valid `mode` discriminator；
- disabled variant无extra fields；
- weighted variant fields complete；
- contributions non-empty；
- metric IDs unique；
- weight positive finite decimal；
- normalization discriminator与conditional fields一致；
- linear bounds finite且max > min；
- availability handling只使用two v0 values；
- minimum fraction在`(0,1]`；
- canonical scale exactly`unit_interval`；
- precision integer在`[1,12]`；
- no selector / formula / fixed contribution field；
- no unknown policy fields。

### 34.3 AcceptancePolicy

- valid `mode` discriminator；
- disabled variant无participating gates；
- gate-based list non-empty；
- Gate IDs unique；
- both handling fields required；
- handling只允许`overall_indeterminate | overall_blocked`；
- no selector、weight、penalty、Overall threshold或unknown field。

### 34.4 Semantic resources

- resource ref non-empty、unique；
- semantic role non-empty；
- content digest matches `sha256:<64 lowercase hex>`；
- no conflicting duplicate binding。

### 34.5 Freeze metadata

- closure profile exactly`skill-eval-frozen-definition-closure-v0`；
- digest matches required format；
- digest field不出现在closure中。

---

## 35. Cross-object Validation

### 35.1 Complete Definition references

- all IDs unique within object namespace；
- all refs resolve within current Benchmark Definition；
- no cross-Benchmark refs；
- no stale target pairs；
- imported object-level validations全部通过。

### 35.2 Overall policy

- every contribution metric exists；
- normalization compatible with Metric Result semantics；
- identity normalization只用于`[0,1]`higher-is-better numeric Metric；
- linear bounds compatible with declared range/unit/direction；
- ordinal / unbounded Metric没有未经证明进入；
- membership不会因future Metrics自动扩展。

### 35.3 Acceptance policy

- every participating Gate exists；
- each Gate属于current Benchmark；
- membership不使用scope/name selector；
- whole-benchmark scope与membership没有unresolved conflict；
- local Gate propagation有explicit membership；
- no stale Gate ref。

### 35.4 Semantic resources

- every external semantic resource reference可被识别；
- each is inline、content-addressed或有binding；
- mutable locator没有被当成content identity；
- referenced digest与freeze-time resolved content一致；
- no runtime Artifact substitution。

### 35.5 Closure and version

- all schema-declared fields进入closure；
- closure使用one profile；
- same ID/version没有different digest；
- no unknown field silently excluded；
- no definition snapshot from another version mixed in。

---

## 36. Semantic Validation

### 36.1 Overall

- Overall具有独立、可解释purpose；
- selected Metrics适合共同形成Overall；
- normalization preserves declared meaning；
- weights有Benchmark rationale且不从upstream attributes机械推导；
- unavailable与missing handling诚实；
- minimum weight coverage保持interpretation；
- no display or Runtime fallback authority；
- empty included set为unavailable；
- Overall与Acceptance独立。

### 36.2 Acceptance

- participating Gates具有whole-benchmark propagation rationale；
- Gate scope与propagation兼容；
- actual TRIGGERED与policy fail-closed explanation分开；
- missing不当OPEN；
- Gate不被重新evaluate；
- Gate不变成score penalty；
- Run validity不被重复为acceptance；
- zero-Gate + disabled清楚；
- no vacuous truth。

### 36.3 Digest

- closure确实完整；
- content identity与semantic subset概念没有混用；
- ordered / set-like classification完整；
- external resource content immutable；
- numeric / string normalization deterministic；
- same-version drift处理明确；
- no Runtime / Scorecard implementation leakage；
- two conforming implementations原则上产生same bytes。

---

## 37. Architecture-level controlled validation method

本轮validation是Definition / architecture-level paper execution：

1. 构造最小合法Definition fragments；
2. 应用本Guide的Structural rules；
3. 解析explicit Metric / Gate refs；
4. 应用normalization / coverage / aggregation semantics；
5. 应用Acceptance precedence；
6. 应用canonical ordering / numeric rules；
7. 比较expected canonical identity behavior；
8. 不创建Run、Episode或actual Result objects；
9. 不调用calculator、evaluator或digest implementation。

`PASS`表示本Schema与method对该controlled scenario得到唯一预期结论，不表示Runtime implementation PASS。

---

## 38. Controlled validation results

### A — Overall disabled

Setup：valid Definition，multiple Metrics，`overall_score_policy.mode=disabled`。

Expected：Metrics保留；no numeric Overall；disabled不等于unavailable。

Result：`PASS`。

### B — Two compatible Metrics, equal weight

Setup：M001 normalized 0.8 weight 1；M002 normalized 0.6 weight 1；minimum coverage 1。

```text
(0.8×1 + 0.6×1) / 2 = 0.7
```

Expected：canonical Overall 0.7，explicit refs与weights可追踪。

Result：`PASS`。

### C — Two compatible Metrics, unequal weight

Setup：M001 normalized 0.8 weight 3；M002 normalized 0.6 weight 1。

```text
(0.8×3 + 0.6×1) / 4 = 0.75
```

Expected：canonical Overall 0.75；Metric内部weight不参与。

Result：`PASS`。

### D — Metric exists but unavailable

Setup：M001 Result exists but unavailable；M001 handling=`overall_unavailable`。

Expected：Overall unavailable；no canonical value；M001不按0处理。

Result：`PASS`。

### D2 — Metric missing entirely

Setup：M001 available weight 3 value 0.8；M002 missing weight 1；M002 missing handling=`exclude_and_renormalize`；minimum fraction=0.75。

```text
available weight fraction = 3 / 4 = 0.75
```

Expected：coverage threshold met；Overall=0.8；missing application保留且不伪装为unavailable Result。

Result：`PASS`。

### D3 — Exclusion below coverage threshold

Setup同D2，但minimum fraction=0.8。

```text
0.75 < 0.8
```

Expected：Overall unavailable；不从M001单独伪造available score。

Result：`PASS`。

### E — High Overall plus Gate TRIGGERED

Setup：Overall=0.95；participating G001 actual Result=TRIGGERED。

Expected：Overall保持0.95；Acceptance=BLOCKED；Gate不置零Overall。

Result：`PASS`。

### F1 — Gate INDETERMINATE to overall indeterminate

Setup：G001=INDETERMINATE；handling=`overall_indeterminate`。

Expected：Acceptance=INDETERMINATE。

Result：`PASS`。

### F2 — Gate INDETERMINATE fail closed

Setup：G001=INDETERMINATE；handling=`overall_blocked`。

Expected：Acceptance=BLOCKED；explanation为policy fail-closed，不篡改G001为TRIGGERED。

Result：`PASS`。

### G1 — Required Gate Result missing to indeterminate

Setup：G001 required但无Result；missing handling=`overall_indeterminate`。

Expected：Acceptance=INDETERMINATE；no fabricated Gate Result；diagnostic boundary preserved。

Result：`PASS`。

### G2 — Required Gate Result missing fail closed

Setup同G1；handling=`overall_blocked`。

Expected：Acceptance=BLOCKED by missing-result policy；不表示Gate TRIGGERED。

Result：`PASS`。

### H — Zero-Gate Benchmark with acceptance disabled

Setup：`gate_specifications=[]`；`acceptance_policy.mode=disabled`；conceptual Run valid。

Expected：Definition valid；Run仍只表示valid；no acceptance semantic。

Negative：`gate_based + participating_gates=[]`必须Structural INVALID。

Result：`PASS`。没有发现`validity_only`不可替代need。

### I — Invalid Run with otherwise good Results

Setup：conceptual Run invalid；Metrics high；Gates OPEN。

Expected：policy application prerequisite失败；audit inventory可保留；no authoritative Overall；no Acceptance semantic；invalid不等于BLOCKED。

Result：`PASS`。

### J — Same ID/version with different digest

Setup：same B001/v1.0/profile；digest A != digest B。

Expected：freeze / registry BLOCKED；Runtime expected-vs-loaded mismatch使Run invalid；不转Gate。

Result：`PASS`。

### K — External fixture path unchanged, content changed

Setup：`resource_ref=fixtures/input.json`不变；content digest由A变B。

Expected：binding content改变→closure bytes改变→Definition digest改变；same version drift BLOCKED。

Result：`PASS`。

### L — Set-like lists in different source order

Setup：同一Requirements / Contracts / Overall contributions，以不同YAML source order表示。

Expected：stable identity sort后canonical arrays相同→same bytes→same digest。

Result：`PASS`。

### M — Ordered interaction steps reversed

Setup：两个Test Cases只交换`interaction_steps`顺序。

Expected：ordered sequence保留→canonical bytes不同→digest不同。

Result：`PASS`。

### N — Canonical numeric equivalence

Setup：同一weight分别以`1`、`1.0`、`1.000`输入并成功解析为decimal。

Expected：canonical decimal均为`1`→same bytes→same digest。

Result：`PASS`。

### O — Unknown Definition field

Setup：Definition包含profile未声明field `future_magic_policy`。

Expected：schema invalid；canonicalization blocked；no digest；cannot freeze。

Result：`PASS`。

---

## 39. Controlled validation summary

| Scenario | Boundary | Result |
|---|---|---|
| A | Overall disabled | PASS |
| B | Equal weights | PASS |
| C | Unequal weights | PASS |
| D | Existing unavailable Metric | PASS |
| D2 | Missing Metric + allowed exclusion | PASS |
| D3 | Coverage below threshold | PASS |
| E | High Overall + triggered Gate | PASS |
| F1/F2 | Gate indeterminate handling | PASS |
| G1/G2 | Missing Gate Result handling | PASS |
| H | Zero Gates + disabled acceptance | PASS |
| I | Invalid Run precedence | PASS |
| J | Same-version digest mismatch | PASS |
| K | External resource drift | PASS |
| L | Set-like reorder invariance | PASS |
| M | Ordered sequence sensitivity | PASS |
| N | Decimal lexical equivalence | PASS |
| O | Unknown field rejection | PASS |

Controlled validation发现：

- no need for `validity_only`；
- no need for new Core Object；
- no need to reopen Metric Specification；
- no need to reopen Gate Specification；
- no need for formula DSL；
- no need for fixed synthetic contribution；
- no new generic architecture blocker。

---

## 40. Schema Findings

### BDH-001 — Full composition is required

Frozen Definition digest不能只覆盖Requirement与Contract。Benchmark Definition必须组合全部八类Definition Core Objects与Benchmark-level policies。

### BDH-002 — Disabled policy is explicit authority

Overall与Acceptance fields required；`mode: disabled`与absence、null、unavailable严格分开。

### BDH-003 — Overall membership is explicit

`metric_id`list是唯一membership authority；禁止selector与future automatic expansion。

### BDH-004 — Cross-Metric normalization must be bounded

v0只支持identity unit interval与bounded linear normalization，不支持implicit、ordinal或unbounded aggregation。

### BDH-005 — Missing and unavailable remain separate

OverallMetricContribution需要两个handling fields；system failure不能被semantic unavailable吞并。

### BDH-006 — Available weight coverage is required

Exclude-and-renormalize没有minimum coverage会让相同Overall value隐藏完全不同population，因此coverage threshold是required authority。

### BDH-007 — Fixed contribution is rejected in v0

它会把availability转换为performance；没有真实need，不加入。

### BDH-008 — Acceptance has only disabled and gate-based modes

`validity_only`重复Run validity，没有独立ordinary acceptance need，v0删除。

### BDH-009 — Acceptance Gate membership is propagation authority

Gate scope保持local authority；explicit participating Gate IDs决定whole-benchmark propagation。

### BDH-010 — Missing Gate Result is not INDETERMINATE Result

Acceptance可以把missing映射为overall indeterminate或blocked，但不得fabricate Gate Result。

### BDH-011 — External semantic resources require digest binding

Mutable path不足以形成Frozen closure。Inline、content-addressed ref或nested resource binding三选一。

### BDH-012 — Digest means complete content identity

所有schema-declared fields进入closure，包括name、description与source_ref；不混用semantic-subset digest。

### BDH-013 — Collection ordering is schema-profile authority

每个list field明确ordered或set-like；implementation不得猜测或静默deduplicate。

### BDH-014 — Closure profile is required

Canonicalization rules改变必须使用新profile ID，避免同一digest format承载不同byte semantics。

### BDH-015 — Digest is not a signature

SHA-256只提供content identity与drift detection，不提供publisher authentication。

---

## 41. Architecture Findings status

### AF-RR-001

```text
Status:
ARCHITECTURE_AUTHORITY_DEFINED_AND_VALIDATED

Resolution:
BenchmarkDefinition.overall_score_policy
```

Evidence：disabled/enabled union、explicit membership、normalization、weights、availability、coverage、canonical scale/precision与A–E controlled scenarios均得到deterministic result。

Not CLOSED：仍需Runtime Guide引用并完成Runtime real validation。

### AF-RR-002

```text
Status:
ARCHITECTURE_AUTHORITY_DEFINED_AND_VALIDATED

Resolution:
BenchmarkDefinition.acceptance_policy
```

Evidence：explicit participating Gates、TRIGGERED / INDETERMINATE / MISSING propagation、zero-Gate disabled、Run validity precedence与E–I scenarios均deterministic。

Not CLOSED：仍需Runtime Guide引用并完成Runtime real validation。

### AF-RR-003

```text
Status:
ARCHITECTURE_AUTHORITY_DEFINED_AND_VALIDATED

Resolution:
complete closure
+ semantic resource bindings
+ skill-eval-frozen-definition-closure-v0
+ canonical serialization
+ SHA-256
```

Evidence：J–O覆盖same-version drift、external content drift、set reorder、ordered sequence、decimal canonicalization与unknown-field rejection。

Not CLOSED：仍需Runtime Guide引用、digest implementation independent conformance validation与Runtime binding validation。

### Combined conclusion

```text
new Core Object required: NO
Concept Model reopen required: NO
Metric Guide reopen required: NO
Gate Guide reopen required: NO
Runtime Guide modified in this round: NO
Pydantic / implementation started: NO
```

---

## 42. Hardening readiness decision

Readiness conditions：

| Condition | Result |
|---|---|
| AF-RR-001 structurally expressible | PASS |
| AF-RR-002 structurally expressible | PASS |
| AF-RR-003 protocol deterministic | PASS |
| zero-Gate behavior clear | PASS |
| Run validity separate | PASS |
| Overall / Acceptance independent | PASS |
| canonical digest reproducible by rules | PASS |
| external semantic resources covered | PASS |
| no new Core Object | PASS |
| no Metric / Gate reopen | PASS |
| A–O controlled scenarios deterministic | PASS |
| new generic blocker | NONE |

Final decision：

```text
BENCHMARK_DEFINITION_HARDENING_READY:
YES
```

`YES`表示Benchmark Definition composition、nested policy authority与canonical digest protocol已经在architecture-level controlled validation范围内形成可冻结的Schema design。

它不表示：

- Runtime real validation完成；
- Runtime Guide已经hardening；
- Pydantic或calculator已实现；
- digest implementation已验证；
- 三个Architecture Findings已经CLOSED；
- 任何真实Subject evaluation PASS。

下一阶段必须先让Runtime / Result Guide显式消费本v0.2 authority，再进行Runtime validation subset；在此之前不得开始Pydantic。

---

## 43. Final validation checklist

### Composition

- [ ] all eight Definition object collections present
- [ ] existing object schemas imported, not rewritten
- [ ] overall policy present
- [ ] acceptance policy present
- [ ] resource binding list present

### Overall

- [ ] mode valid
- [ ] explicit Metric membership
- [ ] weights positive and finite
- [ ] normalization compatible
- [ ] unavailable and missing separate
- [ ] available weight threshold valid
- [ ] unit interval canonical scale
- [ ] precision in range
- [ ] no intermediate display rounding
- [ ] no formula DSL or fixed contribution

### Acceptance

- [ ] mode valid
- [ ] zero-Gate uses disabled
- [ ] gate-based membership non-empty
- [ ] Gate refs explicit and unique
- [ ] indeterminate handling explicit
- [ ] missing handling explicit
- [ ] no missing-to-OPEN
- [ ] actual trigger vs fail-closed explanation separate
- [ ] no Overall threshold
- [ ] no validity-only duplication

### Closure and resources

- [ ] all schema fields included
- [ ] external semantic resources inline, content-addressed or bound
- [ ] mutable resource path not accepted alone
- [ ] excluded artifacts remain non-authoritative
- [ ] digest and snapshot ref excluded from closure

### Canonicalization

- [ ] closure profile exact
- [ ] UTF-8 no BOM
- [ ] NFC and LF normalization
- [ ] keys deterministic
- [ ] every list classified
- [ ] absent and null distinct
- [ ] decimal canonical
- [ ] unknown fields rejected
- [ ] duplicate lists rejected before sorting

### Digest and version

- [ ] SHA-256 format valid
- [ ] digest computed over canonical bytes
- [ ] same closure produces same digest
- [ ] ordered semantic change produces different digest
- [ ] same-version drift blocked
- [ ] mismatch makes future Run invalid, not Gate-triggered

只有全部required checks通过，某个具体Benchmark Definition才可以`status=frozen`并产生freeze output metadata。
