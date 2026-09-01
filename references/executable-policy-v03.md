# 可执行策略 v0.3

`BenchmarkDefinitionV03` 使用封闭的类型化策略对象，替代历史 v0.2 中可执行的自由文本 Metric 策略与 direct-Grader Gate 策略。

## Metric 边界

确定性 pipeline 为：

```text
resolve inputs
-> select attempts
-> apply eligibility
-> map contributions
-> derive aggregation units
-> reduce each unit
-> apply weights
-> aggregate
-> apply completeness
```

v0.3 刻意只支持较窄的选择：显式 attempt selectors、类型化 eligible semantics、精确 Decimal contributions、`per_target` / `per_contract` / `per_test_case` 单元、`single` / `mean` / `final_eligible` reduction、逐单元等权、mean aggregation，以及空分母为 unavailable 的 strict completeness。

`final_eligible` 要求 `all_distinct` selection，且每个派生 aggregation unit 恰好包含一个 MetricInput。Framework 禁止虚构跨 input attempt ordering。

## Gate 边界

Metric-threshold 与 availability conditions 保持类型化。Direct-Grader Gates 复用类型化 attempt-selection 策略、显式 trigger semantics，以及 `any` 或 `all` quantifier。Gate unavailable handling 必须在完整条件评估后应用；单个 unknown input 不能自动覆盖本来已经确定的条件。

## 版本与兼容性

- v0.3 可执行 root：`BenchmarkDefinitionV03`；
- v0.3 digest profile：`skill-eval-frozen-definition-closure-v1`；
- v0.2 兼容 root：`BenchmarkDefinitionV02`；
- v0.2 历史 profile：`skill-eval-frozen-definition-closure-v0`。

CLI 禁止把 v0.2 自由文本策略作为可执行 input。高级 formula DSL、自定义 weighting、statistical estimators、嵌套 boolean/count Gates 和自动 v0.2 migration 均不属于 v0.3。

## 文档角色与当前状态

| 文档 | 角色 / 当前状态 |
|---|---|
| `docs/executable-evaluation-policy-hardening-design-v0.1.md` | 历史设计权威；正文中的“未实现”是冻结时状态，typed policies 当前已进入 v0.3 实现 |
| `docs/final-eligible-aggregation-hardening-v0.1.md` | 历史 `AUDIT-002` 设计加固记录；当前 `AUDIT-002 = CLOSED` |
| `docs/public-api-version-policy-v0.1.md` | 当前 v0.3/v0.2 Public API 与 closure-profile 边界 |
| `docs/audit-status-v0.1.md` | 当前 `AUDIT-001`～`AUDIT-006` 状态权威 |
