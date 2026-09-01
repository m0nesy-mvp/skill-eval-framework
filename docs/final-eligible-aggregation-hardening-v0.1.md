# Final-Eligible 聚合加固 v0.1

状态：`AUDIT_002_DESIGN_HARDENING_FREEZE_READY`

> [!IMPORTANT]
> **文档角色：历史设计加固快照。** 上述状态以及正文中的 “当前接受非法组合”“IMPLEMENTATION_STATUS: OPEN”“BLOCKING_BEFORE_CLI: YES” 记录的是本文冻结时的历史状态，不是当前仓库状态。
>
> **当前状态（2026-09-01）：`AUDIT-002 = CLOSED`。** `MetricSpecificationV03` 已在 Definition-time 拒绝同一派生 aggregation unit 包含多个 `MetricInputs` 的 `final_eligible` 组合；`tests/test_definition_v03_schema.py` 覆盖合法与非法的三种 aggregation-unit modes，`tests/test_evaluation_services.py` 覆盖 selection、eligibility、trace、coverage 与确定性顺序。当前 CLI blocker 已移除。当前统一状态见 `docs/audit-status-v0.1.md`。

目标：Benchmark Definition schema v0.3

范围：当显式 Metric inputs 派生到 aggregation units 时，`final_eligible` unit reduction 在 Definition-time 的合法性。

本文是带版本的加固附录。它不重写历史 Benchmark Definition v0.2 设计，也不重写现有 v0.3 可执行策略设计；它只冻结 Full Design-to-Code Conformance Audit 发现的最小缺失合法性不变量。本文不实现该不变量。

## 1. 问题

当前 `BenchmarkDefinitionV03` 接受以下 `MetricSpecificationV03`：

```text
multiple MetricInputs
-> the same derived aggregation unit
-> unit_reduction.mode = final_eligible
```

确定性 evaluator 无法执行该组合。它会在每个 MetricInput 内保留 `Episode.attempt_index` 顺序，但 Frozen Definition 没有定义派生到同一 unit 的不同 MetricInputs 之间的全序。

不同 MetricInputs 没有以下 Frozen authority：

- 全局 attempt timeline；
- 跨 input attempt ordering；
- Test Case 顺序 权威；
- Contract ordering authority；
- local attempt indexes 相等时的 tie-break rule。

因此，当前 evaluator 会用防御性错误拒绝该组合，而不是生成 Result。Definition 层必须在执行前拒绝这个未定义组合。

## 2. 现有权威

现有可执行 v0.3 设计冻结了以下规则：

1. `Episode.attempt_index` 是唯一 attempt ordering authority。Timestamp、arrival order、Result ID、filesystem order 和 list construction order 都不是 ordering authority。
2. 对一个 MetricInput 关联的不同 Grader Results，attempt selection 独立执行。
3. `final_eligible` 不是 attempt selector，而是 eligibility 之后的 unit-reduction mode，并要求 `all_distinct` selection。
4. Aggregation-unit identity 只从显式 MetricInput identity 派生：
   - `per_target` -> `(test_case_id, contract_id)`；
   - `per_contract` -> `contract_id`；
   - `per_test_case` -> `test_case_id`。
5. 每个 MetricInput 只属于一个派生 aggregation unit。
6. 实现不得用 implementation-specific convention 补充未定义的高级排序或分组行为。

Metric Specification Guide 同时固定了以下语义 pipeline：

```text
resolve explicit MetricInput population
-> associate and validate logical Grader Results
-> select attempts for each MetricInput
-> apply eligibility
-> map contributions
-> derive aggregation units
-> apply unit reduction
-> apply weighting and final aggregation
```

该 pipeline 区分 final raw selection 与 final eligible reduction，也不赋予 MetricInput list order 任何语义权威。

## 3. 权威审查决定

### 3.1 与现有权威的兼容性

最小限制与现有权威兼容。

当一个派生 unit 恰好包含一个 MetricInput 时，该 unit 的全部 eligible contributions 都属于同一个 attempt sequence。现有 `Episode.attempt_index` authority 足以识别 final eligible contribution。

当一个派生 unit 包含多个 MetricInputs 时，现有权威只提供多个局部 attempt sequences，没有将它们合并为全序的规则。拒绝该组合可维持“executor 禁止虚构 ordering authority”的规则。

### 3.2 对现有合法语义的影响

该限制不改变任何已经定义且可执行的语义场景：

- 唯一 MetricInput pairs 的 `per_target + final_eligible` specification 仍然合法；
- 每个 Contract unit 只有一个 MetricInput 时，`per_contract + final_eligible` 仍然合法；
- 每个 Test Case unit 只有一个 MetricInput 时，`per_test_case + final_eligible` 仍然合法；
- `single` 与 `mean` 保持现有语义；
- attempt selection、eligibility、contribution mapping、weighting、completeness 与 final aggregation 均不变。

该限制只关闭尚未冻结跨 input ordering 语义、且当前 evaluator 无法生成权威 Result 的组合。

### 3.3 版本决定

该决定是带版本的 v0.3 加固附录，不要求 Benchmark Definition schema v0.4，原因如下：

- 没有新增、删除、重命名或重新定型字段；
- 没有可执行 enum value 改变含义；
- 没有已经定义的可执行行为发生变化；
- 没有规范 Definition field 或 collection classification 发生变化；
- digest byte protocol 不变；
- `skill-eval-frozen-definition-closure-v1` 仍是正确 closure profile；
- 附录拒绝的是未定义且当前无法执行的策略组合，没有引入新语义。

未来若设计跨 MetricInput ordering，则属于语义扩展，必须单独进行版本审查。本文不授权该扩展。

## 4. 冻结决定

对每个满足以下条件的 `MetricSpecificationV03`：

```text
execution_policy.unit_reduction.mode == final_eligible
```

使用 `execution_policy.aggregation_unit`，为每个显式 MetricInput 派生一个逻辑 aggregation-unit key。

每个派生 aggregation-unit key 在 `MetricSpecificationV03.inputs` 中必须（MUST）恰好出现一次。

只要任一派生 aggregation-unit key 出现多次，Benchmark Definition 即无效。

该规则是在以下现有不变量之外追加的规则：

```text
final_eligible requires selection.mode == all_distinct
```

两个不变量必须同时成立。

## 5. 可由机器实现的合法性不变量

定义：

```text
I = MetricSpecificationV03.inputs
U = MetricSpecificationV03.execution_policy.aggregation_unit
R = MetricSpecificationV03.execution_policy.unit_reduction.mode
```

对 `I` 中每个 input `i`，按下列方式派生 `unit_key(U, i)`：

```text
unit_key(per_target, i)    = (i.test_case_id, i.contract_id)
unit_key(per_contract, i)  = i.contract_id
unit_key(per_test_case, i) = i.test_case_id
```

合法性规则：

```text
if R == final_eligible:
    for every distinct key K derived from I:
        count(i in I where unit_key(U, i) == K) MUST equal 1
```

等价的可执行谓词：

```text
R != final_eligible
OR
len([unit_key(U, i) for i in I])
    == len(set(unit_key(U, i) for i in I))
```

该规则只依赖：

- `MetricSpecificationV03.inputs`；
- `execution_policy.aggregation_unit`；
- `execution_policy.unit_reduction.mode`。

它不依赖 Benchmark-wide references、Runtime Episodes、实际 GraderResults、timestamps、Result IDs、input list order 或 implementation state。

## 6. 排序理由

只有一个 unit 中的全部 eligible contributions 共享同一个 Frozen attempt sequence 时，`final_eligible` 才有明确含义。

每个 unit 恰好一个 MetricInput 时：

```text
one MetricInput
-> one local distinct-attempt sequence
-> Episode.attempt_index ascending
-> final eligible contribution
```

每个 unit 有多个 MetricInputs 时：

```text
MetricInput A -> local attempt sequence A
MetricInput B -> local attempt sequence B
```

没有任何 Frozen authority 能决定 A 的 attempt 位于 B 的 attempt 之前、之后或与其并列。MetricInput list order、Test Case ID、Contract ID、Result ID、timestamp 与 arrival order 禁止（MUST NOT）填补该空白。

因此，v0.3 的最小安全行为是在 Definition validation 时拒绝，而不是虚构 merge order。

## 7. 合法示例

### A. Per-target，一个显式 input

```text
inputs:
- TC1/C1

aggregation_unit: per_target
unit_reduction: final_eligible
```

派生 unit：

```text
(TC1, C1) -> one MetricInput
```

结果：`VALID`

### B. Per-contract，不同 Contract units

```text
inputs:
- TC1/C1
- TC2/C2

aggregation_unit: per_contract
unit_reduction: final_eligible
```

在 `C1 != C2` 时，派生 units 为：

```text
C1 -> one MetricInput
C2 -> one MetricInput
```

结果：`VALID`

### C. Per-contract，同一个 Test Case、不同 Contract units

```text
inputs:
- TC1/C1
- TC1/C2

aggregation_unit: per_contract
unit_reduction: final_eligible
```

在 `C1 != C2` 时，派生 units 为：

```text
C1 -> one MetricInput
C2 -> one MetricInput
```

结果：`VALID`。共享 Test Case 不会合并 Contract aggregation units。

### 附加合法边界：Per-test-case，不同 Test Cases

```text
inputs:
- TC1/C1
- TC2/C1

aggregation_unit: per_test_case
unit_reduction: final_eligible
```

在 `TC1 != TC2` 时，每个 Test Case unit 只有一个 MetricInput。

结果：`VALID`

## 8. 非法示例

### D. Per-contract，一个 Contract unit 中有多个 inputs

```text
inputs:
- TC1/C1
- TC2/C1

aggregation_unit: per_contract
unit_reduction: final_eligible
```

派生 unit：

```text
C1 -> two MetricInputs
```

结果：`INVALID`

两个 MetricInputs 拥有不同的局部 attempt sequences，没有跨 input 全序的 Frozen authority。

### E. Per-test-case，一个 Test Case unit 中有多个 inputs

```text
inputs:
- TC1/C1
- TC1/C2

aggregation_unit: per_test_case
unit_reduction: final_eligible
```

派生 unit：

```text
TC1 -> two MetricInputs
```

结果：`INVALID`

Contract ID 不提供 Test Case unit 内部的排序规则。

## 9. 其他 reducers

该限制只适用于：

```text
unit_reduction.mode == final_eligible
```

它不改变 `single` 或 `mean`：

- `single` 继续要求一个 unit 恰好有一个 eligible contribution；
- `mean` 继续对一个 unit 中的全部 eligible contributions 取算术平均。

同一 unit 包含多个 inputs 的 `single` 或 `mean` Definition 继续受其现有语义和 validation boundary 约束。本文不会扩大或缩小这两种 reducer。

## 10. 归属

权威合法性检查属于 `MetricSpecificationV03` local/cross-field validation，理由如下：

- 所需数据全部位于一个 MetricSpecification 内；
- 不变量不需要 Benchmark-wide object resolution；
- 在消费 digest 或规划执行前即可检测无效性；
- 保持一条 Definition-time 合法性事实，可防止 Schema、cross-object validator、evaluator 与 CLI 分叉。

该检查主要不属于：Benchmark-wide cross-object Definition validator、Runtime validation、Metric evaluator、CLI / orchestration 或新 execution stage。

只有在复用同一 legality helper 或以其他方式保证不会分叉时，cross-object Definition validator 才可以保留防御性 assertion。禁止（MUST NOT）维护第二套独立规则解释。

## 11. Schema 影响

后续 implementation migration 必须扩展 `MetricSpecificationV03` local/cross-field validation：

1. 检查 `execution_policy.unit_reduction.mode`；
2. 当其为 `final_eligible` 时，使用 `execution_policy.aggregation_unit` 为每个显式 input 派生 aggregation-unit key；
3. 任一 key 重复时拒绝 specification；
4. 保留现有 `final_eligible requires all_distinct` 不变量；
5. 保持 `single` 和 `mean` 行为不变。

Definition invalidity 必须在 Evaluation Services 执行前报告。

本文不选择 implementation helper 名称、error-code 名称或 Pydantic error-message 文案；只要保持上述唯一不变量，这些都属于实现细节。

## 12. Evaluator 影响

当前 evaluator error：

```text
final_eligible cannot merge multiple MetricInputs into one aggregation unit
```

可以保留为防御性完整性检查。完成 Schema migration 后，对于正常验证过的 `MetricSpecificationV03`，该分支禁止（MUST NOT）成为常规控制路径；evaluator 也禁止增加跨 input ordering fallback。

本文属于纯设计任务，不授权 evaluator 修改。

## 13. 回归要求

后续 implementation migration 必须增加测试，证明：

1. 示例 A 合法。
2. Contract IDs 不同时，示例 B 合法。
3. Contract IDs 不同时，示例 C 合法。
4. 示例 D 在 Definition validation 阶段被拒绝。
5. 示例 E 在 Definition validation 阶段被拒绝。
6. 所有 Test Case unit keys 不同时，`per_test_case + final_eligible` 合法。
7. 多个唯一 target pairs 的 `per_target + final_eligible` 仍合法。
8. `final_eligible` 仍要求 `all_distinct` selection。
9. `single` 的同 unit 多 input 行为不变。
10. `mean` 的同 unit 多 input 行为不变。
11. 正常验证的 Definition 无法到达 evaluator 的防御性多 input `final_eligible` error。
12. Digest v1 canonicalization 与 closure-profile selection 不变。

测试必须覆盖三种 aggregation-unit mode 的合法性组合，不能只覆盖单 input fixture。

## 14. 非目标

本文不引入或授权：跨 MetricInput 全序、Test Case ordering、Contract ordering、tie-break rule、global attempt timeline、按 timestamp / Result ID / input list order / arrival order 排序、新 Core Object、新 execution stage、新 reducer、修改 `single` 或 `mean`、修改 weighting / completeness / final aggregation、implementation 修改、CLI / Packaging / Public API 工作。

## 15. 发现项状态

### 15.1 本文冻结时的历史状态

冻结本附录后：

```text
AUDIT-002: DESIGN_HARDENING_FREEZE_READY

AUDIT-002:
  SEVERITY: P1
  DESIGN_HARDENING_REQUIRED: YES
  DESIGN_STATUS: DESIGN_HARDENING_FREEZE_READY
  IMPLEMENTATION_STATUS: OPEN
  BLOCKING_BEFORE_CLI: YES
```

本文在冻结时只提供设计，不会修复或完全关闭 `AUDIT-002`。当时只有实现并独立验证该 Definition-time 合法性不变量及其回归后，才能移除 CLI blocker。

历史发现项状态：

```text
IMP-EVAL-METRIC-POLICY-001:
  DESIGN_LAYER: CLOSED_STILL_VALID
  IMPLEMENTATION_LAYER: OPEN_PENDING_SCHEMA_VALIDATION_AND_TESTS
```

在本文冻结时，关闭未定义组合后，原始类型化策略设计仍然有效；完整 implementation closure 仍需要 Schema/validator migration 与 regression evidence。

### 15.2 当前 resolution

后续实现已经完成本文要求的最小不变量：

- `src/skill_eval_framework/schemas/definition_v03.py` 在 Definition-time 执行每个派生 aggregation unit 恰好一个 `MetricInput` 的校验；
- `src/skill_eval_framework/evaluation/metric.py` 保留防御性拒绝，不把实现顺序伪造成跨 input authority；
- `tests/test_definition_v03_schema.py` 验证合法单 input、非法同 unit 多 input，以及 `single` / `mean` 不受影响；
- `tests/test_evaluation_services.py` 验证 `final_eligible`、coverage、trace ordering 和 set-like input determinism。

因此当前状态为：

```text
AUDIT-002:
  CURRENT_STATUS: CLOSED
  CLI_BLOCKER: REMOVED
  HISTORICAL_DESIGN_STATUS: AUDIT_002_DESIGN_HARDENING_FREEZE_READY
```

## 16. 冻结决定

```text
AUDIT_002_DESIGN_HARDENING_FREEZE_READY: YES
```

该最小限制与现有权威兼容，保留全部已经定义的合法语义，只拒绝未定义的可执行组合；它不要求 v0.4 schema 或新 digest profile，并把唯一可由机器实现的合法性事实归属于 `MetricSpecificationV03` local/cross-field validation。
