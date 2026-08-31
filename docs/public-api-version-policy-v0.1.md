# Public API 与 Definition 版本策略 v0.1

## 状态

`AUDIT-006: CLOSED`

Public version 边界是显式的：

| Definition | 角色 | Closure profile |
|---|---|---|
| `BenchmarkDefinitionV03` | 当前可执行 Definition | `skill-eval-frozen-definition-closure-v1` |
| `BenchmarkDefinitionV02` | 历史兼容 Definition | `skill-eval-frozen-definition-closure-v0` |

`skill-eval` CLI 只接受 `BenchmarkDefinitionV03`。

## 导入策略

当前可执行代码使用聚合 schema API：

```python
from skill_eval_framework.schemas import BenchmarkDefinition
```

无版本后缀的聚合 Definition、Metric 与 Gate 名称解析到 v0.3 可执行形式。带版本模块只发布带版本名称：

```python
from skill_eval_framework.schemas.definition_v03 import BenchmarkDefinitionV03
from skill_eval_framework.schemas.definition_v02 import BenchmarkDefinitionV02
```

旧的 `skill_eval_framework.schemas.definition` 模块继续用于历史 v0.2 兼容。其无版本后缀名称属于历史 API，禁止解释为当前可执行 API。该兼容模块尚未声明 removal schedule。

## 版本感知 helpers

通用 Definition validation、digest 与 Run-binding helpers 根据具体 Definition root type 分派。调用方需要固定 protocol 时，也可以使用显式带版本 helper：

- `validate_benchmark_definition_v02` / `validate_benchmark_definition_v03`；
- `compute_definition_digest_v02` / `compute_definition_digest_v03`；
- `verify_run_definition_binding_v02` / `verify_run_definition_binding_v03`。

跨版本 Definition/profile 配对会被拒绝。v0.2 自由文本 Metric 或 Gate 策略字段不会进入 v0.3 可执行路径。

## 兼容边界

历史 v0.2 parsing 与 closure-v0 digest 行为继续支持显式兼容用途。新的可执行 definitions 和所有受支持 CLI 工作流使用 v0.3 与 closure profile v1。
