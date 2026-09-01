# 当前 Audit 状态 v0.1

状态：`CURRENT_STATUS_AUTHORITY`

核对日期：2026-09-01

适用范围：当前 `main` 上的 Framework 实现、受支持 CLI 路径与 Public API 边界。

## 1. 如何使用本文

本文是 `AUDIT-001`～`AUDIT-006` 的当前状态入口。历史设计文档中的 `OPEN`、`BLOCKED`、`FREEZE_READY` 或“未开始实现”等标签仍保留为当时阶段证据，但不得覆盖本文的当前状态。

状态含义：

- `ACCEPTED_RISK`：风险仍存在，当前版本明确接受并记录；不得写成 `FIXED` 或 `CLOSED`。
- `CLOSED`：对应问题已经实现修复，并有当前代码与回归测试证据。
- 历史 commit 只用于追踪引入变更的位置；当前结论仍必须以当前 checkout 的代码和测试结果复核。

## 2. 当前状态表

| Audit | 当前状态 | 当前结论 | 主要实现证据 | 主要回归证据 |
|---|---|---|---|---|
| `AUDIT-001` | `ACCEPTED_RISK` | 受支持 CLI 拒绝调用方提供派生 Results，并由 Framework 派生 Metric/Gate/Overall/Acceptance；直接 Python caller 仍可绕过该受支持路径，残余语义完整性风险未被消除 | `src/skill_eval_framework/cli.py`、`docs/known-risks-v0.1.md` | `tests/test_cli.py` |
| `AUDIT-002` | `CLOSED` | Definition-time 拒绝同一派生 aggregation unit 包含多个 `MetricInputs` 的 `final_eligible` 未定义组合 | `src/skill_eval_framework/schemas/definition_v03.py` | `tests/test_definition_v03_schema.py` |
| `AUDIT-003` | `CLOSED` | 权威 Runtime/Result snapshots 拒绝顶层和嵌套原地修改；copy/transition/finalization 返回 detached immutable snapshots | `src/skill_eval_framework/schemas/common.py`、`src/skill_eval_framework/schemas/runtime.py`、`src/skill_eval_framework/schemas/results.py` | `tests/test_runtime_result_immutability.py` |
| `AUDIT-004` | `CLOSED` | Metric selection、eligibility、unit reduction、coverage counts 与 trace ordering 使用显式 stage-aware authority，并保持确定性 | `src/skill_eval_framework/evaluation/metric.py` | `tests/test_evaluation_services.py` |
| `AUDIT-005` | `CLOSED` | set-like Metric input ordering 不改变 digest 或 evaluation result；输出 trace 使用 canonical order | `src/skill_eval_framework/evaluation/metric.py`、`src/skill_eval_framework/digest/` | `tests/test_evaluation_services.py`、`tests/test_digest_v1.py` |
| `AUDIT-006` | `CLOSED` | 无后缀 Public API 指向当前 v0.3；v0.2 只通过显式 `*V02` 名称保留历史兼容；CLI 只接受 v0.3 | `src/skill_eval_framework/schemas/__init__.py`、`src/skill_eval_framework/digest/definition.py` | `tests/test_public_api.py`、`tests/test_digest_v1.py` |

## 3. 版本与执行边界

- 当前可执行 Definition：`BenchmarkDefinitionV03`。
- 当前 digest profile：`skill-eval-frozen-definition-closure-v1`。
- 历史兼容 Definition：`BenchmarkDefinitionV02`。
- 历史兼容 digest profile：`skill-eval-frozen-definition-closure-v0`。
- 当前 CLI 只接受 v0.3。
- 当前 CLI 不执行 Subject、不收集外部 Evidence、不托管 semantic Grader，也不提供 Baseline/Candidate comparison engine。
- 当前 CLI 消费已完成的 Runtime facts 与 `GraderResults`，然后确定性派生 Metric、Gate、Overall、Acceptance 和 Scorecard。

## 4. 历史追踪

| Audit | 历史变更入口 | 说明 |
|---|---|---|
| `AUDIT-001` | `b22f2d6` | 记录并接受残余语义完整性风险 |
| `AUDIT-002` / `AUDIT-004` / `AUDIT-005` | `399e3c8` | 加固 Metric schema 与 evaluation semantics |
| `AUDIT-003` | `3ab94e0` | 强制 Runtime/Result immutability |
| `AUDIT-006` | `c512be1` | 明确 v0.3 current API 与 v0.2 historical compatibility |

这些 commit 不是当前 PASS 的替代证据。修改相关边界后，至少重新运行对应回归文件和完整质量门禁。

## 5. 状态维护规则

1. 新 Audit 必须在本文增加一行，并链接到具体实现和回归证据。
2. `CLOSED` 只有在修复已进入当前 checkout 且回归通过时才能使用。
3. 历史文档不得无痕改写旧状态；应增加 current-resolution block，并链接本文。
4. `AUDIT-001` 在残余绕过路径消失并完成独立验证前必须保持 `ACCEPTED_RISK`。
5. CLI、Public API、Definition version 或 digest profile 变化时，必须同步更新本文、根入口和相应 policy 文档。

## 6. 验证命令

```powershell
.venv\Scripts\pytest.exe -q
.venv\Scripts\ruff.exe check .
.venv\Scripts\ruff.exe format --check .
.venv\Scripts\mypy.exe src
git diff --check
```

通过这些检查只能证明当前实现满足仓库内冻结的确定性契约；不能证明外部 Evidence 或 Grader judgment 在语义上正确，也不能证明 benchmark 具有科学代表性。
