# 可执行评估策略加固设计 v0.1

状态：`EXECUTABLE_EVALUATION_POLICY_DESIGN_V0_FREEZE_READY: YES`

范围：针对实现阶段发现的 Metric 与 direct-Grader Gate 执行阻断项，提供后继设计。

本文不实现 Python services，只定义后续实现可消费的最小机器可读策略表面。历史 v0.2 Definition 设计及其证据保持不变。

## 1. 基线与阻断项

实现基线为：

```text
dfbca2870e73da9fbfdb8794b24caa950db78e9e
feat: implement frozen definition digest
```

此前的 Evaluation Services 尝试确认了两个真实阻断项：

1. `MetricSpecification` 把多项执行权威保存为不受约束的字符串。
2. `GraderResultGateCondition.result_selection_policy` 保存了同类不受约束的 selection authority。

问题不在于字符串难以解析，而在于两个合规实现没有冻结规则可判断哪种解释才是权威。substring test、regular expression、NLP interpretation、隐藏约定短语、expression parser 或 `eval` 都会创建 implementation-specific authority。

因此，加固目标为：

```text
Definition-time policy = typed machine-readable authority
human-readable explanation = separate descriptive field
```

## 2. 权威与版本决定

权威顺序保持不变：

```text
Frozen Design
> Pydantic schema
> validator/runtime implementation
> implementation convenience
```

现有 v0.2 文档是历史 Frozen baseline，禁止无痕改写。

后继版本为：

```text
Benchmark Definition schema v0.3
Executable Evaluation Policy hardening
```

Closure profile 同时改为：

```text
skill-eval-frozen-definition-closure-v1
```

原因是 v0.3 改变了 Definition policy fields 的类型化结构与规范含义。继续使用 `skill-eval-frozen-definition-closure-v0` 会让同一个 profile identifier 表示两种不同的规范对象结构和 byte protocol。新 profile 是最小安全 identity boundary，不是 algorithm negotiation 或 fallback。

现有 v0.2 Definitions、v0 closure digests 与 v0 conformance vectors 仍是有效历史证据。Evaluator 禁止自动迁移。未来显式 migration tool 可以构造 v0.3 Definition 并生成新的 v1 digest，但 migration 不属于本文，也不是自动兼容路径。

## 3. 可执行性审计

### 3.1 保留为文本的描述性字段

以下字段不直接选择、分组、归约、加权或聚合值，继续保持为人类可读文本：

- `MetricSpecification.name`
- `MetricCompletenessPolicy.transparency_requirements`
- `MetricResultSemantics.interpretation`
- `MetricResultSemantics.direction`（需要时验证其与 executable scale 的兼容性，但仍是解释性含义）
- `MetricResultSemantics.scale`（兼容性标签，不是 executor operator）
- `MetricResultSemantics.denominator_meaning`
- `GateSpecification.name`
- `GateSpecification.scope`
- `GateResultSemantics.open_meaning`
- `GateResultSemantics.triggered_meaning`
- `GateResultSemantics.indeterminate_meaning`
- `GateResultSemantics.blocking_effect`
- `GateSpecification.explanation_requirements`
- design rationale、purpose rationale 与 semantic review prose

描述性字段可以解释可执行策略，但 calculator 禁止从中推断策略。

### 3.2 可执行权威字段

以下内容改为类型化 structures 或 enums：

- result selection；
- eligibility handling；
- numeric contribution mapping；
- aggregation unit；
- unit reduction；
- final aggregation；
- weighting；
- completeness 与 empty-denominator behavior；
- 直接-Grader Gate 结果 选择；
- 直接-Grader Gate trigger 语义。

### 3.3 拆分权威与说明的混合字段

当前 `contribution_semantics` 字符串混合了贡献含义与 calculator 使用的数值。v0.3 将其拆分为：

```text
ContributionRule:
- source_semantic: ResultSemantic
- numeric_value: finite Decimal
- contribution_unit: ContributionUnit
- explanation: NonEmptyStr
```

`explanation` 保持描述性；`numeric_value` 是唯一数值权威。Grader judgment 本身不天然等于某个数值，映射由 Metric-local rule 提供。

当前 eligibility handling strings 同样是混合字段。其机器行为改为类型化 variants，人类理由保留在独立 explanation/rationale field 中。

## 4. 共享的 Result selection 权威

Metric 与 direct-Grader Gate 共用一个 Definition-time policy type：

```text
AttemptSelectionPolicy:
- mode: all_distinct | sole_distinct | first_distinct | final_distinct_raw
- order: attempt_index_ascending (required for first/final)
```

`attempt_index` 是唯一排序权威。Timestamp、arrival order、Result ID、filesystem order 与 list construction order 都不是 ordering authority。

语义如下：

| mode | 行为 |
|---|---|
| `all_distinct` | 完成 logical-duplicate validation 后，选择全部不同的 logical attempt-level Result |
| `sole_distinct` | 要求恰好一个不同 Result；零个时为 unavailable，多重性属于 policy execution failure |
| `first_distinct` | 按 `Episode.attempt_index` 升序选择第一个不同 Result |
| `final_distinct_raw` | 按 `Episode.attempt_index` 升序选择最后一个不同 Result；该 Result 为 non-substantive 或 unavailable 时禁止 fallback |

Selector 不包含 `final_eligible`。Final eligible 是 eligibility 之后的 unit-reduction mode，刻意与 final raw selection 分离。

Selection 始终在 logical identity integrity 之后、eligibility 之前执行：

```text
associate same-Run Results
→ validate logical uniqueness
→ apply AttemptSelectionPolicy
→ apply eligibility
```

共享 type 防止 Metric 与 direct-Grader Gate 形成两套略有差异的 selector authority。

## 5. Result 语义词汇

Definition policy vocabulary 只使用以下小写 tokens：

```text
satisfied
violated
insufficient_evidence
not_exercised
```

它们是面向 Definition 的语义词汇，与现有 Runtime `GraderJudgment` values 一一对应。未来实现可以把共享词汇放进 common schema module，但 Definition policy 禁止依赖 Runtime Result object 或 Runtime ID。

以下边界保持固定：

- `insufficient_evidence` 不是 `violated`；
- `not_exercised` 不是 `violated`；
- Grader Result 缺失不是 `insufficient_evidence`；
- engine failure 不产生语义 Grader Result；
- eligibility 禁止改写原始 Grader judgment。

## 6. Metric 可执行策略

v0.3 Metric policy 是封闭的最小结构：

```text
MetricExecutionPolicy:
- selection: AttemptSelectionPolicy
- eligibility: EligibilityPolicy
- contribution_mapping: list[ContributionRule]
- aggregation_unit: per_target | per_contract | per_test_case
- unit_reduction: UnitReductionPolicy
- weighting: equal_per_unit
- aggregation: mean
- completeness: CompletenessPolicy
```

现有描述性 `MetricSpecification` fields 只保留为说明，或在 v0.3 schema 中由上述类型化字段替换。没有 `custom: str` 逃生口，也没有 arbitrary expression field。

### 技术主题：6.1 EligibilityPolicy

```text
EligibilityPolicy:
- eligible_semantics: non-empty set[ResultSemantic]
- non_substantive: exclude_and_trace
- missing_input: unavailable
```

`eligible_semantics` 必须显式声明。常规 binary compliance Metric 使用 `{satisfied, violated}`。`insufficient_evidence` 与 `not_exercised` 被排除，并在 Result trace 中单独计数。Missing inputs 保持 unavailable，禁止转换为语义 judgment。

`exclude_and_trace` 不表示 Metric 一定 available。Completeness 仍决定剩余 eligible population 是否保留声明的 Metric 含义。

### 技术主题：6.2 ContributionRule

```text
ContributionRule:
- source_semantic: ResultSemantic
- numeric_value: finite Decimal
- contribution_unit: unit_interval
- explanation: NonEmptyStr
```

Binary compliance Metric 的映射为：

```text
satisfied → 1, unit_interval
violated  → 0, unit_interval
```

数值是显式 Definition authority。Calculator 禁止从 `full contribution`、`zero contribution`、`pass`、`fail` 或其他短语推导。每个 eligible semantic 必须恰好有一个 mapping；non-eligible semantic 的 mapping 会被拒绝。

v0.3 正式支持 `unit_interval` contributions。Count 与任意 scalar contribution units 暂缓；在独立方法验证冻结其 scale 和 aggregation semantics 前，不能成为可执行 v0.3 values。

### 技术主题：6.3 Aggregation units

v0.3 enum 刻意保持较小：

```text
per_target
per_contract
per_test_case
```

派生方式固定：

- `per_target`：`(test_case_id, contract_id)`；
- `per_contract`：`contract_id`；
- `per_test_case`：`test_case_id`。

每个 input 恰好属于一个 unit。禁止使用 `custom` label、name selector、tag selector 或 Runtime-discovered group。

### 技术主题：6.4 UnitReductionPolicy

最小支持集合为：

```text
UnitReductionPolicy:
- mode: single | mean | final_eligible
```

- `single`：每个 unit 必须恰好有一个 eligible contribution；禁止静默折叠多重性。
- `mean`：对 unit 中全部 eligible contributions 取算术平均。
- `final_eligible`：保留 `all_distinct` 的 attempt order，在 eligibility 与 mapping 后选择最后一个 eligible contribution。它不能与 `first_distinct`、`final_distinct_raw` 或其他已归约为一个 raw Result 的 selector 组合。

`final_eligible` 是 v0.3 唯一在 eligibility 后对 attempt 敏感的 reducer。`worst`、`best`、ordinal distance、median、percentile 与 arbitrary reducers 均暂缓。

空 unit 没有 contribution。在 v0.3 strict completeness policy 下，它使 Metric unavailable，不产生 synthetic zero。

### 6.5 最终聚合

v0.3 只支持一条 final rule：

```text
mean
```

它在 unit reduction 后，对纳入的 unit contributions 计算算术平均。这足以覆盖已经验证的 binary per-target 与 per-contract 方法场景。`rate`、`count`、`sum`、`min`、`max`、weighted mean、formulas 与 statistical estimators 均暂缓，直到真实验证证明需要并提供精确语义。

### 6.6 加权

v0.3 只支持：

```text
equal_per_unit
```

每个参与贡献的 aggregation unit 权重相等。Case count、Contract criticality、Gate importance、failure severity、display order 与 Metric-internal weights 禁止成为隐式权重。

Unequal weights 暂缓；它需要结构化 unit-weight mapping、normalization rule、omitted-unit behavior 与新的 semantic validation。继续保留 `weighting_policy: str` 会重建原阻断项。

### 6.7 完整性与空分母

v0.3 支持的策略为：

```text
CompletenessPolicy:
- mode: strict
- empty_denominator: unavailable
```

Strict 表示经过 selection、eligibility 与 reduction 后，每个 expected aggregation unit 都必须有 eligible contribution。任一必需 input 缺失、空 unit 或零 eligible denominator，都会生成正常的 `MetricResult(status=unavailable)`，并附带类型化 reason 与完整 trace。

Partial-threshold completeness 与 eligible-only descriptive Metrics 暂不进入可执行 v0.3 vocabulary。历史 Guide 有相关讨论，但当前仓库尚未冻结两个实现可一致执行的 threshold operator、coverage denominator 或 interpretation。

Count-zero semantics 同样暂缓。只有具备显式 complete-population authority 时才能增加 count Metric；zero 禁止作为 rate 或 mean 的 division-by-zero fallback。

## 7. Direct-Grader Gate 设计

`GraderResultGateCondition` 使用与 Metric 相同的 `AttemptSelectionPolicy`：

```text
DirectGraderGatePolicy:
- selection: AttemptSelectionPolicy
- trigger_result_semantics: non-empty set[ResultSemantic]
- quantifier: any | all
```

固定处理顺序为：

```text
resolve explicit target pairs
→ associate same-Run Results
→ validate logical uniqueness
→ shared attempt selection
→ classify MATCH / NON_MATCH / UNKNOWN
→ apply one Gate-level quantifier
→ apply unavailable_handling only to UNKNOWN
```

分类规则固定：

- 选中 semantic 位于 `trigger_result_semantics` 中 → `MATCH`；
- 已知选中 semantic 不在 trigger set 中 → `NON_MATCH`；
- 必需的选中 Result 缺失，或 selection identity/order 不可用 → `UNKNOWN`；
- `insufficient_evidence` 与 `not_exercised` 是已知 `NON_MATCH`，除非显式包含在 trigger set 中。

现有 `any | all` quantifier 与三值 truth table 保持不变。不增加 nested boolean DSL、count Gate、ratio Gate、逐 target 隐藏 quantifier 或跨 target 第二 quantifier。

本加固不改变 Metric threshold 与 Metric availability Gate variants 的语义。

## 8. Digest 影响

v0.3 可执行策略属于完整 Frozen Definition closure。以下内容进入新 closure：structured selection policy、类型化 eligibility policy、类型化 numeric contribution mappings、aggregation unit、unit reduction、weighting policy、final aggregation、completeness 与 empty-denominator policy、structured direct-Grader Gate selection 与 trigger semantics。

以下内容继续排除：Runtime IDs 与 timestamps；实际 Results、Evidence、Episodes 与 Scorecards；implementation traces 与 diagnostics；source formatting、comments 与 rationale prose；`definition_snapshot_ref` 与 `definition_digest` 本身。

Collection classification：

- 已标识的 Metric policy collections 继续按 IDs 视为 set-like；
- `eligible_semantics`、`trigger_result_semantics` 与 contribution rules 按稳定 semantic/source identity 视为 set-like；
- `interaction_steps`、Rubric dimensions、Rubric anchors 与 attempt-ordered runtime observations 保持 ordered；
- selector mode 与 policy object keys 使用新的 v1 canonical profile rules。

因此 closure profile 必须为 `skill-eval-frozen-definition-closure-v1`。v0 vectors 属于历史记录，禁止在 v1 semantics 下重算。Implementation freeze 前必须增加新的 v1 conformance vectors。

## 9. Validator migration 影响

后续实现必须更新三层 validation。

### 结构 / Pydantic

- 用 discriminated typed policies 替换 executable free-text fields；
- 验证 enum membership 与 finite Decimal contribution values；
- 拒绝 duplicate semantic mappings 与 duplicate set-like members；
- 强制 `final_eligible` 要求 `all_distinct`；
- 强制 strict completeness 与 empty-denominator shape；
- 拒绝 unknown policy fields 与 arbitrary expression escape hatches。

### 跨对象 Definition validation

- 把类型化 Metric inputs 解析到唯一权威 Grader target；
- 验证每个 eligible semantic 恰好有一个 contribution mapping；
- 验证 source semantics 属于已知 Result vocabulary；
- 验证每个 input 都能派生 aggregation unit；
- 验证引用的 Metric 与 Gate IDs；
- 验证 direct-Grader Gate targets 可解析且不形成重复权威；
- 验证 normalization、contribution unit 与 Result semantics 兼容。

### 技术主题：Runtime / Result validation

- 保持同一 Run 与 logical Result identity；
- 显式提供 Episode attempt ordering；
- 区分 missing Result、insufficient evidence 与 unavailable Metric；
- 拒绝 duplicate logical Result records，禁止静默去重；
- 验证 Metric 与 Gate traces 符合类型化策略路径；
- engine failure 保持在 semantic Result objects 之外。

## 10. Evaluation service migration 影响

后续 Evaluation Services 只能实现类型化 v0.3 vocabulary：

1. Metric service 消费结构化策略，生成完整 `MetricCoverageSummary` 与 `MetricInputTrace`。
2. Direct-Grader Gate 消费共享 selector，再应用现有三值 quantifier。
3. Metric threshold Gate 只消费规范 Decimal Metric values。
4. Overall 继续使用现有结构化策略中的显式跨 Metric weights 与 normalization。
5. Acceptance 继续只消费显式 participating Gate Results 与现有 fail-closed handling。

任何 service 都禁止把 legacy free-form executable string 当成隐式兼容模式。v0.2 Definition 只能保留为历史 artifact，或在 evaluation 前显式迁移到 v0.3。

## 10.1 v0.2 到 v0.3 字段迁移映射

后继版本禁止原地重新解释旧值。概念映射为：

| v0.2 字段 | v0.3 权威 | 处理方式 |
|---|---|---|
| `result_selection_policy: str` | `execution_policy.selection` | 替换为共享 `AttemptSelectionPolicy` |
| `eligibility_policy.eligible_result_semantics` | `execution_policy.eligibility.eligible_semantics` | 替换为类型化 semantic set |
| `eligibility_policy.non_substantive_handling` | `execution_policy.eligibility.non_substantive` | 替换为类型化 variant |
| `eligibility_policy.unavailable_input_handling` | `execution_policy.eligibility.missing_input` | 替换为类型化 variant |
| `contribution_mapping[].source_semantics` | `ContributionRule.source_semantic` | 替换为类型化 semantic |
| `contribution_mapping[].contribution_semantics` | `ContributionRule.numeric_value` + `contribution_unit` + `explanation` | 拆分混合权威 |
| `aggregation_unit: str` | `execution_policy.aggregation_unit` | 替换为封闭 enum |
| `unit_reduction: str` | `execution_policy.unit_reduction` | 替换为封闭 reducer |
| `aggregation_rule: str` | `execution_policy.aggregation` | 替换为 `mean` |
| `weighting_policy: str` | `execution_policy.weighting` | 替换为 `equal_per_unit` |
| completeness string fields | `execution_policy.completeness` | 替换为 strict typed policy |
| `GraderResultGateCondition.result_selection_policy: str` | `DirectGraderGatePolicy.selection` | 复用共享 selector |
| `trigger_result_semantics: list[str]` | `DirectGraderGatePolicy.trigger_result_semantics` | 类型化 ResultSemantic set |

`name`、`scope`、interpretation prose、transparency、explanation requirements 与 rationale fields 继续保持描述性。无法显式映射的 v0.2 value 属于 migration error，不能据此保留 free-text executor fallback。

## 11. 受控方法回归

以下示例是设计一致性目标，不是 implementation output。

### A. 技术主题：All distinct、binary、eligible mean

```text
selection: all_distinct
eligible: satisfied, violated
mapping: satisfied=1, violated=0
unit: per_target
reduction: mean
weighting: equal_per_unit
aggregation: mean
completeness: strict
```

两个 eligible contributions `1` 与 `0` 产生规范 Metric value `0.5`。

### B. Final raw，不 fallback

```text
selection: final_distinct_raw
```

若 final attempt 为 `insufficient_evidence`，它会被选中、由 eligibility 排除，strict Metric 变为 unavailable；禁止回看更早的 `satisfied` Result。

### C. 技术主题：Final eligible

```text
selection: all_distinct
reduction: final_eligible
```

Evaluator 检查全部 attempts，应用 eligibility 与 contribution mapping，再使用保留的 `attempt_index` 顺序选择最后一个 eligible contribution。这不等价于 final raw。

### D. Per-target 聚合

每个 `(test_case_id, contract_id)` 获得一个 unit contribution；多个 target units 等权平均。

### E. Per-contract 聚合

共享 `contract_id` 的 inputs 先归约到一个 Contract unit，再对 Contract units 等权平均。Case multiplicity 禁止静默变成 Contract weight。

### F. 技术主题：Strict completeness

任一 expected unit 没有 eligible contribution 时，Metric 带 completeness reason 与显式 trace 变为 unavailable；禁止插入 zero。

### G. Partial / eligible-only 边界

由于当前权威尚未冻结唯一 threshold operator 或 coverage interpretation，这些模式继续在 v0.3 暂缓，且不会保留为 free text。

### H. 技术主题：Direct-Grader Gate

共享 selector 支持 all、sole、first 与 final raw selection。现有 ANY/ALL 与 MATCH/NON_MATCH/UNKNOWN rules 适用，不增加第二 quantifier。

### I. 技术主题：Metric threshold Gate

规范 Metric value `0.8995` 与 `lt 0.90` 比较结果为 `TRUE`，因此 Gate 为 `TRIGGERED`；显示值 `0.90` 不影响结果。

### J. Overall 与 Acceptance

Overall 与 Acceptance 保持独立。即使 Overall 很高，participating Gate 触发也会阻断 Acceptance；全部 participating Gates 为 OPEN 时可以产生 `ACCEPTABLE`，且不消费 Overall。

## 12. 三层设计验证

### 结构验证

- 不保留 executable free-text policy fields；
- 全部 executable policies 都有封闭 discriminated vocabularies；
- 不存在重复权威或 arbitrary expression escape hatch；
- Decimal mappings 有限且精确；
- ordered 与 set-like collections 已显式区分。

### 跨对象验证

- Metric input pairs 解析到权威 Grader coverage；
- policy references 解析到当前 Definition IDs；
- contribution source semantics 已知且完整；
- aggregation units 从显式 input identity 派生；
- direct-Grader Gate targets 可解析，且没有 `grader_id` 双重权威；
- v0.3 policy references 不能无痕指向 v0.2 closure content。

### 语义验证

- selection 先于 eligibility；
- final raw 禁止 fallback；
- final eligible 是 eligibility 后的 reduction；
- missing、unavailable、insufficient 与 not-exercised 保持不同；
- 不引入 implicit zero 或 vacuous truth；
- 两个合规实现使用相同 selector、units、reducer、weights 与 final mean；
- Gate、Overall 与 Acceptance 边界保持独立。

## 13. 暂缓的高级策略

明确暂缓：arbitrary formula / expression DSL、custom aggregation groups、unequal / derived weights、worst/best/median/percentile reducers、ordinal distance arithmetic、heterogeneous scalar normalization、statistical estimators / confidence intervals、partial threshold completeness、eligible-only descriptive completeness、缺少 complete population contract 的 count-zero semantics、nested boolean / count Gates，以及自动 v0.2-to-v0.3 migration。

暂缓行为不能用 executable free-form string 表示。在单独验证并确定版本前，它不属于受支持的 v0.3 vocabulary。

## 14. 新发现项

用上述封闭设计替换两处 free-text authorities 后，没有发现新的通用阻断项。

原发现项由本设计关闭：

- `IMP-EVAL-METRIC-POLICY-001`：由类型化 selection、eligibility、contribution、unit、reduction、weighting、aggregation 与 completeness policies 关闭；
- `IMP-EVAL-GATE-GRADER-SELECTION-001`：由共享 `AttemptSelectionPolicy` 关闭。

这里的关闭只发生在设计层，不表示后续 Pydantic、validator、digest 与 Evaluation Service migrations 已实现。

## 15. 冻结决定

```text
EXECUTABLE_EVALUATION_POLICY_DESIGN_V0_FREEZE_READY: YES
```

后继 schema 与 closure profile 必须作为一次协调迁移处理。只有保留 v0.2 历史 baseline 并增加 v1 digest conformance vectors 后，才能开始实现。

## 16. 架构问题答复

1. **哪些现有 string fields 保持描述性？** Names、scopes、result interpretations、denominator explanations、transparency requirements、explanation requirements 与 rationale prose。Executor 禁止解析它们。
2. **哪些变成可执行结构化字段？** Selection、eligibility、contribution mapping、aggregation unit、unit reduction、final aggregation、weighting、completeness、empty-denominator behavior，以及 direct-Grader Gate trigger/selection policy。
3. **精确 selection vocabulary 是什么？** `all_distinct`、`sole_distinct`、`first_distinct`、`final_distinct_raw`；需要排序时使用 `attempt_index_ascending`。
4. **Selection 是否共享？** 是。Metric 与 direct-Grader Gate 使用同一个 `AttemptSelectionPolicy`。
5. **Final raw 与 final eligible 如何区分？** Final raw 是 eligibility 前的 selector；final eligible 是 `all_distinct` 后执行 eligibility/mapping，再进行 `final_eligible` unit reduction。
6. **v0 aggregation units 是什么？** `per_target`、`per_contract`、`per_test_case`。
7. **支持哪些 unit reductions？** `single`、`mean`、`final_eligible`；worst/best/ordinal/statistical reducers 暂缓。
8. **支持哪些 final aggregation rules？** 只支持 `mean`。
9. **支持哪些 weighting policies？** 只支持 `equal_per_unit`。
10. **如何表示 numeric contribution？** 类型化 finite Decimal `numeric_value` 与类型化 source semantic 配对；禁止 prose-to-number conversion。
11. **如何处理 insufficient、not-exercised 与 missing？** 显式声明 eligible semantics；排除并追踪 non-substantive Results；missing Results 为 unavailable；均禁止改写为 violated。
12. **哪些 completeness policies 可执行？** `strict` 加 `empty_denominator: unavailable`；partial-threshold 与 eligible-only modes 暂缓。
13. **哪些高级场景暂缓？** Custom groups、arbitrary formulas、unequal weights、count/scalar/ordinal arithmetic、statistical estimators、nested boolean/count Gates 与自动 migration。
14. **Definition schema version 是否变化？** 是，后继版本为 `v0.3`；历史 v0.2 不变。
15. **Closure profile 是否变化？** 是，使用 `skill-eval-frozen-definition-closure-v1`，因为类型化策略结构与规范含义发生变化。
16. **哪些代码模块必须迁移？** Pydantic schemas、local/cross-object validators、Runtime identity/ordering checks、Digest canonicalizer/vectors 与 Evaluation Services；本文不包含实现。
