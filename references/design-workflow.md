# 基准设计工作流（Benchmark Design Workflow）

当 benchmark 尚未形成冻结的可执行 Definition 时，使用本参考。权威设计链为：

```text
Target Skill
-> Requirement
-> Contract
-> Test Case
-> Evidence Specification
-> Grader Specification
-> Metric Specification
-> Gate Specification
-> BenchmarkDefinitionV03
```

## 使用规则

1. 阅读 Target Skill 入口及其明确委派的资源，把规范性需求与实现事实、假设分开。
2. 在把 Contracts 视为权威前冻结 Requirements。每个 Contract 必须说明可观察的成功、失败和失败模式。
3. 为每个 expected assertion 提供 Test Case 与 Contract identity；根据需要设计正常、负向、缺少前置条件和边界用例。
4. 执行用例前，先规定 Evidence 所需的 observation、provenance、context 与 qualification。
5. 显式声明每个 Grader target 和 result semantics。在受支持的 CLI 工作流中，GraderResult 是最后一个由外部提供的语义产物。
6. 执行前定义类型化 Metric 与 Gate 策略；禁止把可执行行为编码在普通说明文字中。
7. 验证全部引用和覆盖，冻结 Definition，然后计算 digest。看到结果后禁止原地修改 Frozen Definition。

## 详细设计参考

| 设计阶段 | 仓库权威文档 |
|---|---|
| 端到端流程 | `docs/universal-skill-eval-design-process-v1.1-scope-frozen.md` |
| 需求（Requirement） | `docs/guides/requirement-extraction-guide-v0.1.md` |
| 契约（Contract） | `docs/guides/contract-design-guide-v0.md` |
| 测试用例（Test Case） | `docs/guides/test-case-design-guide-v0.md` |
| 证据（Evidence） | `docs/guides/evidence-specification-guide-v0.md` |
| 评分器（Grader） | `docs/guides/grader-specification-guide-v0.md` |
| 指标（Metric） | `docs/guides/metric-specification-guide-v0.md` |
| 门禁（Gate） | `docs/guides/gate-specification-guide-v0.md` |

这些详细文档保留设计历史与冻结决定。其历史 readiness 标签不能覆盖当前可执行 v0.3 Public API 或当前仓库测试结果。
