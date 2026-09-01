# Runtime 评估

## 三层模型

```text
Definition -> Runtime -> Result
```

- Definition 冻结测试内容、所需 Evidence，以及确定性结果的派生方式。
- Runtime 记录一个 Run、计划 attempts、Episodes、trace facts、Artifacts、合格 Evidence、GraderResults 和 diagnostics。
- Result 包含 Framework 派生的 MetricResults、GateResults、Overall、Acceptance 和最终 Scorecard。

一个 Run 只绑定一个 Frozen Definition 和一个 Subject identity。Episode 是该 Run 中一次计划的 Test Case attempt。

## 受支持的评估边界

CLI input 可以包含确定性的 identity/timestamp 字段、Run plan、已完成的 Runtime facts、Artifacts、合格 Evidence、GraderResults、diagnostics，以及 Framework 将创建的 results 对应 IDs。禁止包含调用方生成的 MetricResults、GateResults、OverallScoreOutcome 或 AcceptanceEvaluation。

确定性流程为：

```text
GraderResults
-> MetricResults
-> GateResults
-> OverallScoreOutcome
-> AcceptanceEvaluation
-> Scorecard
```

Scorecard inventory 区分 expected、actual 与 missing applications。GraderResult 缺失可以使 Metric unavailable、Gate indeterminate，但不会因此让 Runtime graph 在结构上无效。

## Identity 与最终确认规则

- 绑定 benchmark ID、Definition version、closure profile 和精确 digest。
- v0.3 只使用 closure profile v1。
- 即使 attempt 被 blocked 或失败，也要保留分配的 attempt indexes。
- input 使用确定性 IDs 和 timestamps；CLI 不生成随机 ID 或当前时间戳。
- digest/profile 不匹配属于 identity error，不是 warning。
- 保留原始 Run。Definition 改变后生成新的 digest 和 Run，禁止覆盖 Evidence。

## 文档角色

- 当前操作边界：本文与 `references/cli.md`。
- 历史设计与 pseudo-schema：`docs/guides/runtime-result-design-guide-v0.md`。该 Guide 保留设计阶段的“未实现”与 readiness 结论，不能覆盖当前代码和测试状态。
- 当前 Audit 状态：`docs/audit-status-v0.1.md`。
