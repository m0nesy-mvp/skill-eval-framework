# 《Metric Specification Design Guide v0》

Status: Design Guide

本文定义从Grader Results到Metric Specification与future Metric Result的通用聚合设计方法。它适用于tool-use、coding、browser、conversational、research、structured-output、qualitative与workflow evaluation，不绑定特定Skill、平台、工具、Artifact、业务领域或aggregation implementation。

本文提出最小MetricSpecification Schema Proposal，但不修改已经冻结的Requirement、Contract、Test Case、Evidence Specification、Grader Specification、Concept Model或其他Schema，不设计Gate，不实现Runtime、concrete aggregation code、Scorecard或Overall Score。

---

## 1. Metric Specification 的角色

Metric Specification回答：

> How should a defined population of Grader Results be aggregated into one interpretable evaluation measure?

它是Definition-time first-class object，预先冻结：

- Metric semantic identity；
- aggregation population；
- Definition-time membership；
- distinct Result / attempt selection；
- accepted Grader Result semantics；
- eligibility与denominator policy；
- contribution mapping；
- aggregation unit；
- repeated-result / unit-level reduction；
- aggregation rule；
- weighting policy；
- input completeness与empty-denominator policy；
- future Metric Result的meaning、direction、scale与denominator interpretation。

Metric Specification不负责：

- 修改Contract judgment；
- 重新解释Evidence；
- 覆盖或重写Grader Result；
- 把多个Graders重新组合成单个Contract verdict；
- 定义Gate blocking；
- 宣布Benchmark PASS / FAIL；
- 设计Scorecard或Overall Score；
- 保存actual Metric value、counts、included Result IDs或Runtime status；
- 编写Python、SQL、statistics-library call或aggregation engine。

---

## 2. Metric Specification 与 Metric Result

```text
Metric Specification
= Definition-time aggregation policy

Metric Result
= Runtime application of that policy to one Run's actual inputs
```

Metric Specification描述：

- 哪些Definition targets构成expected population；
- future Grader Results如何获得membership；
- 哪些result meanings可贡献；
- non-substantive与unavailable inputs如何处理；
- contributions如何按unit归并、加权与聚合；
- 结果在语义上代表什么。

Metric Result未来描述：

- 某个Run中实际使用了哪个Metric Specification；
- expected population与actual input availability；
- 实际eligible、excluded、insufficient、not-exercised与unavailable数量；
- 实际included Grader Results；
- actual value或unavailable / undefined状态；
- denominator与coverage metadata；
- 与其他Run的comparison compatibility。

因此Metric Specification禁止保存：

- Run ID；
- Subject ID；
- actual Grader Result ID；
- actual count或sample size；
- actual numerator / denominator；
- actual Metric value；
- actual Metric Result status；
- actual comparison result。

---

## 3. Grader、Metric、Gate 与 Scorecard Boundary

### 3.1 Grader vs Metric

```text
Grader
→ judges one target-specific evaluation observation

Metric
→ aggregates already-established Grader Results
```

Metric不得重新决定某个Contract是否满足。如果一个atomic Contract的必要条件为A、B、C，它们必须已经在一个authoritative Grader Specification中形成target-level judgment。

禁止：

```text
Grader A judges condition A
+ Grader B judges condition B
→ Metric AND
→ claims one Contract satisfied
```

Metric可以聚合同一Contract在不同Cases / Episodes中的performance observations，但这不是重写任何一次Contract-specific Grader Result。

### 3.2 Metric vs Gate

```text
Metric
→ describes measured performance

Gate
→ later decides whether defined results block the Benchmark
```

Metric value低、critical target violated或insufficient比例高，都不能由Metric Specification直接宣布Benchmark FAIL。Gate Definition与Gate Result属于后续阶段。

### 3.3 Metric vs Scorecard / Overall Score

Metric必须具有独立可解释意义。它可以在未来参与Overall Score，但不得为了提前实现Scorecard而创建一个没有独立Benchmark meaning的`overall_score` Metric。

```text
Metric Result
→ one interpretable measure

Overall Score
→ future Scorecard-derived value across selected Metric Results
```

本Guide不设计Metric→Metric→Overall Score graph、Scorecard layout或reporting UI。

---

## 4. Authoritative Inputs 与 Entry Gate

### 4.1 Production inputs

Production Metric Specification Design必须消费：

1. authoritative Benchmark Definition context；
2. authoritative Frozen Requirements；
3. validated Contract Set；
4. validated Test Case Set与ExpectedAssertions；
5. validated Evidence Specification Set；
6. validated Grader Specification Set；
7. ExpectedAssertion → authoritative Grader Coverage Mapping；
8. Contract evaluation type与criticality；
9. Grader result semantics与applicable Rubric / local-value semantics；
10. relevant Definition version与staleness information。

Design Audits可以帮助理解既有rationale，但不得成为Metric membership或aggregation的第二套authority。

### 4.2 Production Entry Gate

只有以下条件全部满足，才能开始production Metric Specification Design：

- Grader Specification Design Status为`GRADERS_READY`；
- upstream Definition objects当前有效；
- 每个proposed Metric input pair都能解析到唯一ExpectedAssertion与唯一authoritative Grader coverage；
- 没有unresolved population、result-semantics或aggregation blocker；
- inputs属于同一个有效Benchmark Definition version。

否则输出：

```text
METRICS_BLOCKED
```

并回退相关upstream lifecycle，不得通过Metric临时发明membership或verdict。

### 4.3 Method Validation Subset

允许使用明确限定、internally consistent的validation subset验证本方法，但必须同时满足：

- upstream statuses完整写为`*_READY for validation subset`；
- target pairs与Grader coverage在subset内闭合；
- 不把validation-only IDs或status混入production；
- 保留benchmark-wide blocker；
- 最终状态只能是：

```text
METRICS_READY for validation subset
```

或：

```text
METRICS_BLOCKED for validation subset
```

---

## 5. Metric Semantic Identity

每个Metric必须回答：

- What does this Metric measure?
- Which evaluation population does it summarize?
- What receives one conceptual contribution?
- What does a higher, lower or equal value mean?
- What is included in the denominator or count universe?

以下定义不充分：

```text
metric_id: M001
name: quality
aggregation: average
```

较稳定的定义应说明：

> 在被实际exercise且形成substantive judgment的目标population中，按Contract等权汇总satisfied contribution的比例；higher表示更广泛的Contract-level compliance。

Metric name提供简洁identity；完整meaning由`result_semantics`与其他policy fields共同冻结，不另加重复description字段。

---

## 6. Population Authority

Metric population回答：

> Which Definition targets are expected to supply future Grader Results to this Metric?

v0采用explicit target membership，不采用semantic selector或query DSL。

允许的authoritative membership unit是：

```text
MetricInput:
- test_case_id
- contract_id
```

该pair唯一定位ExpectedAssertion，并通过authoritative Grader Coverage Mapping解析到唯一GraderTarget。

不使用以下多套filters共同决定membership：

- grader IDs；
- Contract IDs；
- Test Case IDs；
- evaluation type selector；
- criticality selector；
- runtime-discovered Results。

这些信息可以在authoring时帮助生成explicit inputs或进入Audit rationale，但不能成为与`inputs`并行的第二套population authority。

### Why explicit membership first

- Definition membership deterministic；
- future Graders不会被自动纳入；
- shared Grader的target ambiguity被消除；
- Benchmark version语义稳定；
- Cross-object validation可直接执行；
- reviewer能审计每一个included target。

未来只有真实规模或maintenance evidence证明explicit membership不可持续时，才重新评估selector language；本轮不预留query字段。

同一个target pair可以进入多个具有不同、独立meaning的Metric Specifications；这不构成重复计分。对单个Metric而言，同一个pair只能在`inputs`中出现一次，也不能通过第二套membership authority再次纳入。

---

## 7. MetricInput 与 Shared Grader

不在`MetricInput`中保存`grader_id`。

理由：

- `(test_case_id, contract_id)`已唯一定位ExpectedAssertion；
- 每个ExpectedAssertion已被当前Grader v0规则限制为恰好一个authoritative Grader coverage；
- GraderTarget与MetricInput使用同一pair identity；
- 再存`grader_id`会产生pair与ID不一致的双authority风险；
- shared Grader包含多个targets，单独引用Grader ID会产生“全部targets还是部分targets”的歧义。

Cross-object validation必须确认：

```text
MetricInput pair
→ one ExpectedAssertion
→ exactly one authoritative GraderTarget
```

如果authoritative Grader coverage改变，应更新Benchmark Definition version与相关Metric validation，而不是在MetricInput保留stale grader ID。

---

## 8. Grader Result Input Semantics

Grader Result是最小可聚合evaluation observation。Metric Specification只声明接受哪些semantic meanings，不冻结完整GraderResult Schema。

当前已知meaning包括：

- satisfied；
- violated；
- insufficient evidence；
- not exercised；
- future ordinal anchor；
- future local scalar。

未来Runtime还可能存在：

- no Result because Episode not run；
- execution blocked；
- environment failure；
- Grader execution failure。

这些availability / lifecycle states不能被Metric Specification伪装成Grader verdict，但Metric必须预先说明它们对computation availability的影响。

---

## 8.1 Result Selection Policy

`result_selection_policy`回答：

> Given the distinct Grader Results associated with one MetricInput within the current Run, which Result observations are selected for this Metric before eligibility and contribution mapping?

它是Definition-time Metric semantics，定义selection intent，不保存actual Episode、attempt或Grader Result identity。Future Runtime负责提供足够actual identity与ordering，以区分same logical Result、duplicate record、distinct Episodes / attempts以及current Run association。

Metric processing的conceptual semantic order固定为：

```text
1. Resolve explicit MetricInput population
2. Associate available Grader Results from the current Run
3. Deduplicate duplicate records of the same logical Grader Result
4. Apply result_selection_policy
5. Apply eligibility_policy
6. Apply contribution_mapping
7. Map selected contributions to aggregation units
8. Apply unit_reduction
9. Apply weighting_policy
10. Apply aggregation_rule
11. Apply completeness / empty-denominator policy
12. Interpret Metric Result
```

这是方法语义顺序，不是Runtime engine设计。Duplicate logical Result records必须在selection前去重；author不能选择把同一logical Result的重复记录计数两次。Metric Specification不新增`duplicate_handling`字段，Runtime以后必须提供执行该invariant所需的identity evidence。

`result_selection_policy`必须明确：

- selection population；
- selection basis；
- 需要ordering时的ordering basis；
- selected cardinality；
- required identity或ordering不可用时的behavior；
- unexpected attempt multiplicity如何处理；
- selected Result为insufficient、not-exercised或unavailable时是否禁止fallback。

允许的deterministic patterns例如：

```text
Select all distinct attempt-level Grader Results associated with each MetricInput in the current Run after duplicate logical Result records are removed.

Select the first distinct attempt-level Grader Result for each MetricInput according to the Runtime-provided attempt order.

Select the final distinct attempt-level Grader Result for each MetricInput according to the Runtime-provided attempt order. Do not fall back to an earlier Result when the selected final Result is non-substantive or unavailable.
```

对于预期只有一个distinct Result的Metric，也必须明确：

> Use the sole distinct Grader Result associated with each MetricInput; if multiple distinct attempts exist, the Metric Definition is not satisfied unless this policy explicitly defines their selection.

禁止模糊selection：

- `use the most relevant attempt`；
- `use the best result`；
- `use the final valid result`；

除非`relevant`、`best`或`valid`已有完整、deterministic且不循环依赖Metric judgment的semantics。本轮不设计selector language或concrete selection code。

### Final raw attempt vs final eligible contribution

两者是不同Metric policies：

```text
Final raw attempt:
select final distinct raw Result
→ eligibility
→ contribution
```

如果final raw Result是`insufficient_evidence`，不得为了得到数值而回退到earlier satisfied Result。它之后按eligibility与completeness处理。

```text
Final eligible contribution:
select all distinct attempts
→ eligibility
→ contribution mapping
→ unit_reduction selects final eligible contribution using preserved attempt order
```

两种policy可能产生相同numeric value，但contributing-unit count、denominator、coverage与availability可能不同，不能互换。

---

## 9. Aggregation Unit

Aggregation Unit定义：

> The unit that receives one conceptual contribution before the final Metric aggregation.

它不同于最小Runtime input：

```text
Runtime input observation
= Grader Result

Aggregation Unit
= Definition grouping that receives one reduced contribution
```

常见可由当前Definition identity确定的units：

- per-target：每个MetricInput pair一个unit；
- per-contract：同一`contract_id`下的inputs形成一个unit；
- per-test-case：同一`test_case_id`下的inputs形成一个unit。

v0不冻结`aggregation_unit` enum。Spec必须用human-readable但deterministic的规则明确：

- unit identity如何从inputs派生；
- 一个input属于哪个unit；
- 一个input是否只能贡献给一个unit；
- unit之间如何进入final aggregation。

无法从现有Definition identity确定的custom semantic group不能只写在Audit中作为authority。若真实Metric需要稳定custom grouping，应记录Schema Finding，而不是临时用模糊label分组。

---

## 10. Unit-Level Reduction 与 Selected Contributions

`unit_reduction`只处理已经经过deduplication、Result Selection、eligibility与contribution mapping的selected eligible contributions。它不得重新隐式决定first raw attempt或final raw attempt；这属于`result_selection_policy`。

`unit_reduction`至少回答：

- 同一Contract多个Cases如何reduce；
- 同一aggregation unit内多个selected eligible contributions如何reduce；
- reduction是mean、worst-case、all-satisfied、proportion还是其他明确规则；
- unit没有eligible observation时如何处理。

不得默认：

```text
Every produced Grader Result
= one independent equal sample
```

例如`worst substantive attempt`更稳定的decomposition是：

```text
result_selection_policy:
select all distinct attempts

eligibility + contribution mapping

unit_reduction:
select the worst eligible contribution
```

如果Benchmark真正要求按raw Result semantic value选择attempt，必须特别审查selection是否与judgment semantics产生循环或隐式耦合，不得临时发明复杂selector language。

重复执行可能测量stability，也可能是replacement retry或其他sample semantics。哪些distinct Results进入后续processing由Result Selection冻结；selected contributions怎样形成unit contribution由Unit Reduction冻结。

### Attempt / Episode Multiplicity Review

Case数量与Episode数量是不同multiplicity dimensions。每个Metric Design至少检查：

1. 每个MetricInput是否可能产生多个distinct Results；
2. 预期单Result时，policy如何处理unexpected multiplicity；
3. 多Result时，selection basis与selected cardinality是什么；
4. selection是否明确发生在eligibility之前；
5. ordering依据是否由future Runtime提供；
6. duplicate logical Results是否在selection前去重；
7. selected Result为insufficient、not-exercised或unavailable时是否允许fallback；
8. retries代表replacement、samples、stability observations还是其他semantics；
9. Result selection如何影响denominator、coverage与completeness interpretation。

Attempt / Episode Multiplicity Review属于Design Audit与Semantic Review，不是Core Object，也不保存actual Runtime IDs。

---

## 11. Eligibility Policy

Eligibility Policy决定actual Grader Results是否可以形成Metric contribution。

它必须区分：

### Eligible substantive meanings

例如binary compliance Metric通常选择：

- satisfied；
- violated。

### Non-substantive meanings

例如：

- insufficient evidence；
- not exercised。

### Unavailable input states

例如：

- no Grader Result；
- Episode not run；
- execution blocked；
- environment failure；
- Grader execution failure。

这些不是全局enum。本层只要求每个Metric Specification用当前可用semantic vocabulary明确policy。

不存在安全的全局隐式default。即使最常见的binary compliance rule是只让satisfied / violated进入substantive denominator，Metric实例仍必须显式声明。

---

## 12. Denominator Semantics

对于rate、proportion或mean，denominator不是“所有Cases”的机械计数，而是Metric semantic identity的一部分。

Binary compliance Metric的典型结构：

```text
eligible substantive contributions
= satisfied + violated

compliance rate
= satisfied contributions / eligible substantive contributions
```

但只有在Spec明确以下内容时才合法：

- expected population是什么；
- 每个MetricInput经过`result_selection_policy`选择了哪些distinct Results；
- unit是什么；
- 哪些actual Results eligible；
- unit-level reduction何时发生；
- not-exercised、insufficient与unavailable如何处理；
- weights作用在哪些units；
- empty denominator怎么处理。

禁止把not-exercised、insufficient、blocked、not-run与missing Result全部机械记为0。

---

## 13. Insufficient Evidence Handling

默认原则：

```text
insufficient evidence
≠ violated
≠ contribution 0 in a compliance rate
```

Metric-specific policy可以选择：

- exclude from substantive denominator and report separately；
- exclude but make Metric unavailable if completeness requirement不满足；
- 对专门的evidence-availability Metric作为被统计对象。

如果Benchmark明确需要把“未获得verified compliance”作为availability/yield penalty，必须创建语义诚实的Metric：其result meaning是verified-yield或availability-adjusted measure，而不能仍命名为Contract compliance并暗示insufficient等于violation。

Metric永远不能修改原Grader Result meaning。

---

## 14. Not-Exercised Handling

```text
not exercised
≠ satisfied
≠ violated
```

处理方式由Metric purpose决定：

- “compliance among exercised responsibilities”通常exclude并单独透明报告；
- “exercise rate”可以把exercised vs not-exercised作为Metric自身统计对象；
- “scenario coverage”可以把not-exercised视为coverage signal，但不能把它改写成Contract FAIL。

同一个Grader Result可以按不同冻结Metric Specifications服务不同目的，但每个Metric的contribution meaning必须独立清楚，不能在Runtime临时改变。

---

## 15. Missing Result vs Insufficient Evidence

必须保持：

```text
Grader Result exists with insufficient-evidence meaning
≠ no Grader Result exists
```

前者说明grading operation形成了Result，但qualified inputs不足。后者可能来自Case未运行、Episode blocked、environment failure或Grader execution failure。

Metric Specification不设计这些Runtime状态字段，但`unavailable_input_handling`必须声明：

- expected input没有Result时是否允许partial computation；
- 哪些availability gaps阻止Metric；
- unavailable population必须如何透明说明；
- 不得把no Result当作violated或insufficient，除非未来Runtime Result明确产生了相应meaning。

---

## 16. Metric Completeness 与 Partial Result

Metric completeness回答：

> Is the actual input coverage sufficient for this Metric Result to retain its declared interpretation?

Spec必须定义：

- Result selection之后的selected population如何计入coverage；
- minimum eligible observation requirement；
- minimum unit coverage；
- insufficient / not-exercised / unavailable对coverage的影响；
- partial computation是否允许；
- partial value如何保持honest interpretation；
- 哪些gap使Metric unavailable。

Selection完成后，selected Result可能是substantive、not-exercised、insufficient-evidence或unavailable；之后才适用eligibility与completeness。Final raw Result为insufficient时不得隐式fallback到earlier satisfied Result。只有明确选择all distinct attempts并在post-eligibility `unit_reduction`中定义final eligible contribution的Metric，才具有该另一种semantics。

不同Metrics可以选择不同policy：

### Strict completeness

任何required unit缺少eligible contribution，Metric Result unavailable。

### Threshold completeness

达到明确minimum unit count或coverage proportion时允许partial value，并强制报告coverage。

### Eligible-only descriptive result

始终汇总当前eligible units，但result semantics明确限定为“among eligible observations”，且不得隐藏coverage不足。

本Guide不设计statistical confidence interval、imputation或复杂missing-data model。

---

## 17. Empty Denominator

如果rate / mean的eligible denominator为零：

```text
Metric value
→ unavailable / undefined meaning
```

不得默认：

- 0；
- 1；
- 100%；
- PASS；
- FAIL。

Count Metric是例外：如果expected population与observation surface完整，规则确实是在完整population中计数某事件，那么count 0可以是合法substantive value。它不是division-by-zero fallback。

`empty_denominator_policy`必须明确rate/mean与count语义的区别，但本轮不冻结Runtime status enum。

---

## 18. Contribution Mapping

Contribution Mapping把eligible Grader Result meaning转换为Metric-local contribution。

例如binary compliance Metric可以定义：

```text
satisfied → contribution 1
violated  → contribution 0
```

这只是该Metric的aggregation mapping：

```text
satisfied is not inherently the number 1
violated is not inherently the number 0
```

另一Metric可以统计violation count、exercise rate或diagnostic frequency，并使用不同contribution semantics。

每条mapping必须说明：

- source Grader Result semantics；
- produced contribution meaning；
- contribution scale或unit；
- 为什么没有改变原judgment。

禁止写implementation branch、code function或library call。

---

## 19. Binary、Ordinal 与 Scalar Inputs

### 19.1 Binary

当前最稳定的输入是satisfied / violated。Rate、proportion、count、all-satisfied或worst-case等rules都可以表达，但必须明确unit、denominator与mapping。

### 19.2 Ordinal

不得机械执行：

```text
Poor = 1
Fair = 2
Good = 3
```

除非Metric Specification明确冻结：

- anchors有order；
- numeric mapping的semantic distance是否有意义；
- aggregation对ordinal scale是否合法；
- result interpretation如何避免把ordinal伪装成interval scale。

没有real validation前，不为ordinal新增special Schema字段。

### 19.3 Local scalar

聚合local scalar前必须确认：

- scale compatible；
- direction consistent；
- normalization已定义；
- units有共同meaning；
- range与out-of-range handling清楚；
- missing与non-substantive policy明确。

不同scale或不同unit不能直接average。当前scalar path属于future method validation coverage。

---

## 20. Aggregation Rule

Metric aggregation应尽可能deterministic。Spec必须让两个conforming implementations在相同qualified inputs上得到相同conceptual result。

允许使用：

- human-readable exact rule；
- mathematical expression；
- explicit numerator / denominator definition；
- rate / proportion；
- count / sum；
- mean；
- min / max；
- weighted mean；
- clearly bounded unit-level reduction。

不冻结`aggregation_method` enum，因为真实needs可能组合unit reduction与final aggregation，简单enum会掩盖semantics。

禁止：

> 综合评估整体表现。

较稳定：

> For each Contract unit, compute the proportion of eligible target contributions mapped to satisfied; then take the equal-weight mean of all Contract units that meet the unit completeness rule.

本Guide不写concrete aggregation code。

---

## 21. Weighting Policy

每个Metric必须显式写`weighting_policy`，不得依赖隐含default。

最简单且推荐的起点是：

```text
equal weight per declared aggregation unit
```

如果采用unequal weighting，policy必须说明：

- weight附着于哪个aggregation unit；
- exact weight如何确定；
- weight是否在unit reduction前或后应用；
- weights是否需要normalization；
- omitted unit如何处理；
- 为什么weight与Metric purpose一致。

明确禁止：

```text
criticality automatically becomes weight
failure-mode severity automatically becomes weight
Gate importance automatically becomes weight
number of Cases silently becomes weight
```

`criticality`只有在Metric policy显式选择并解释derived weighting时才可能参与；这仍不产生Gate blocking semantics。

v0使用human-readable deterministic`weighting_policy`，不新增Contract weight字段，也不创建Weight Core Object。真实unequal-weight authoring若证明需要结构化unit-weight mapping，再记录Schema Finding。

---

## 22. Case Multiplicity 与 Duplicate Weighting

同一Contract可以出现在多个Test Cases：

```text
Contract A → 5 inputs
Contract B → 1 input
```

按per-target equal weighting聚合时，Contract A自然占5/6。这个结果可能合理，也可能只是Case数量意外变成importance。

每个Metric必须执行Case Multiplicity Review：

1. 多Case Contract是否应该获得更高影响；
2. Case数量是否代表sample diversity还是importance；
3. Metric goal是per-target、per-case还是per-contract performance；
4. duplicate/retry是否被误计为independent sample；
5. 新增Case是否会静默改变历史Metric meaning；
6. Benchmark version变化是否需要重新验证comparability。

如果multiplicity是intentional，`aggregation_unit`、`unit_reduction`与`weighting_policy`必须明确表达；如果不是，应采用例如per-contract normalization。

---

## 23. Contract-Level Normalization

对于“average Contract compliance”类Metric，可定义两阶段semantic aggregation：

```text
Stage 1:
multiple eligible target contributions for one Contract
→ one Contract unit contribution

Stage 2:
Contract unit contributions
→ final Metric Result
```

这属于一个Metric Specification内部的unit reduction + final aggregation，不是重新判定某次Episode中的Contract verdict。

例如：

> 对每个Contract，先计算其eligible Cases中satisfied contribution的比例；再对满足minimum coverage的Contracts进行等权平均。

Contract-level normalization防止Case count无意中成为Contract importance，但不是所有Metric的全局default。Stability Metric或input-space performance Metric可能有意按target / Episode计权。

---

## 24. Outcome、Workflow 与 Mixed Population

Metric可以分别总结Outcome或Workflow targets，也可以在有清楚semantic basis时混合。

不硬编码固定的“Outcome Metric”和“Workflow Metric”，但author必须检查：

- included evaluation types是否共享同一contribution meaning；
- direction与scale是否兼容；
- unit reduction是否一致；
- 混合后Metric name与interpretation是否仍诚实；
- 一个type是否因Case数量主导结果。

直接把Outcome quality与Workflow compliance平均为一个数字通常缺少语义基础。如果只是为了形成Overall Score，应停止在Scorecard / Overall Aggregation concern，而不是创建模糊mixed Metric。

---

## 25. Hierarchical Aggregation Boundary

v0 Metric Specification只消费Grader Results，不消费其他Metric Results。

禁止：

```text
Metric Result A
+ Metric Result B
→ Metric Specification C
```

否则会引入：

- Metric dependency graph；
- topological execution；
- cycle validation；
- nested completeness propagation；
- repeated weighting；
- comparison compatibility complexity。

当前需要的two-stage aggregation通过`aggregation_unit + unit_reduction + aggregation_rule`在一个Metric内表达。跨多个独立Metrics的汇总留给future Overall Score / Scorecard policy。

---

## 26. Failure-Mode-Derived Metrics

Failure modes主要属于Grader Result diagnosis。统计supported failure-mode frequency可以形成有意义的diagnostic Metric，但它必须：

- 只消费实际supported attribution；
- 不把unknown diagnosis当该mode不存在；
- 不替代Contract satisfied / violated judgment；
- 明确denominator是violated Results、all substantive Results还是其他population；
- 不将failure-mode severity升级为Gate。

由于Grader Result diagnosis Schema尚未冻结，本Guide不为failure-mode Metric增加专用字段。当前`eligibility_policy + contribution_mapping + aggregation_rule`原则上可表达；真实validation前保留为future coverage。

---

## 27. Metric Result Semantics

Metric Specification必须定义future Result代表什么，至少包括：

- `interpretation`：完整自然语言meaning；
- `direction`：higher / lower / neutral分别表示什么；
- `scale`：count、rate、range、unit或其他semantic scale；
- `denominator_meaning`：rate / mean的denominator，或count Metric的population universe。

例如：

> 该Result表示被实际exercise、具有substantive binary judgment且满足minimum Contract-unit coverage的Workflow Contracts中，等权Contract satisfaction rate；range为0–1，higher表示更高compliance。

Metric不等于score。合法Metric Result可以是：

- count；
- rate / proportion；
- mean local scalar；
- coverage rate；
- diagnostic frequency；
- unavailable / undefined with coverage metadata。

---

## 28. Denominator Transparency

即使non-substantive与unavailable inputs不进入main value，也不得静默消失。

Metric Specification的`completeness_policy.transparency_requirements`必须要求future Metric Result能够说明与本Metric相关的：

- expected population size；
- actual Grader Results available；
- distinct Results remaining after duplicate removal；
- Results selected by `result_selection_policy`与selection coverage；
- eligible substantive count；
- excluded not-exercised count；
- insufficient-evidence count；
- unavailable count where known；
- included aggregation units；
- units failing minimum completeness；
- partial / unavailable interpretation；
- included Cases或target identities的traceability。

Future Result metadata必须使reviewer能够区分：expected MetricInputs、available raw Results、deduplicated distinct Results、selected Results、eligible contributions与contributing units。相同numeric value但selection coverage不同的Results不具有相同完整语义。

这些是future Metric Result concept metadata requirements，不是Specification中的actual counts，也不意味着自动创建companion Metrics。

---

## 29. Metric Specification Candidate / Working Stage

v0不引入mandatory Metric Specification Candidate对象或Candidate lifecycle。

复杂authoring可以使用temporary Working Metric Drafts比较：

- alternate populations；
- alternate Result selection与Attempt multiplicity semantics；
- per-target vs per-contract units；
- eligibility与denominator policies；
- strict vs partial completeness；
- equal vs explicit weighting；
- contribution mappings；
- result interpretations。

Working Draft：

- 不是Core Object；
- 不进入Frozen Metric Specification Set；
- 不算Metric coverage；
- 不占用正式`Mxxx` ID；
- resolved后由正式Spec或Metric Design Issue取代。

只有真实authoring出现稳定alternate lineage、multi-reviewer reconciliation或长期draft dependency时，才重新评估Candidate lifecycle。

---

## 30. Metric Specification Design Audit

v0引入轻量、非Core、非authoritative的Metric Specification Design Audit，建议至少记录：

| 字段 | 含义 |
|---|---|
| `metric_id` | 正式Metric ID；draft可用temporary label |
| `purpose_rationale` | 为什么该Metric具有独立Benchmark meaning |
| `population_rationale` | 为什么选择这些MetricInputs |
| `membership_exclusions` | 明确排除哪些相似targets及原因 |
| `result_selection_rationale` | 哪些distinct Results被选择、selection basis与cardinality为何匹配Metric purpose |
| `aggregation_unit_rationale` | 为什么选择per-target / contract / case或其他derivable unit |
| `unit_reduction_rationale` | selected eligible contributions与multi-Case unit如何reduce |
| `eligibility_rationale` | 为什么某些meanings进入或退出contribution |
| `denominator_rationale` | denominator为何匹配Metric interpretation |
| `contribution_rationale` | mapping为何不改写Grader judgment |
| `weighting_rationale` | equal / unequal weighting与unit alignment |
| `case_multiplicity_rationale` | Case count影响是否intentional |
| `attempt_multiplicity_rationale` | Episode / retry semantics、duplicate invariant、ordering与fallback policy |
| `completeness_rationale` | partial / unavailable policy为何仍保持解释诚实 |
| `result_semantics_rationale` | direction、scale与meaning选择 |
| `comparison_concern` | Benchmark version或Run comparability concern |
| `downstream_gate_concern` | 只记录future Gate concern，不定义blocking |
| `downstream_scorecard_concern` | 只记录future presentation / Overall concern |
| `implementation_concern` | future aggregation implementation concern |

Audit：

- 不替代Metric Specification；
- 不成为population第二套authority；
- 不保存actual Grader Results或Metric Result；
- 不定义Gate或Overall Score；
- 不用rationale弥补ambiguous policy field；
- 必须与Spec Set、Coverage Review与upstream Definition一致。

---

## 31. Minimal MetricSpecification Schema Proposal

### 31.1 MetricSpecification

```text
MetricSpecification:
- metric_id
- name
- inputs: list[MetricInput]
- result_selection_policy: str
- aggregation_unit: str
- eligibility_policy: MetricEligibilityPolicy
- contribution_mapping: list[MetricContributionRule]
- unit_reduction: str
- aggregation_rule: str
- weighting_policy: str
- completeness_policy: MetricCompletenessPolicy
- result_semantics: MetricResultSemantics
```

### 31.2 MetricInput

```text
MetricInput:
- test_case_id
- contract_id
```

### 31.3 MetricEligibilityPolicy

```text
MetricEligibilityPolicy:
- eligible_result_semantics: list[str]
- non_substantive_handling: list[str]
- unavailable_input_handling: list[str]
```

### 31.4 MetricContributionRule

```text
MetricContributionRule:
- source_semantics
- contribution_semantics
```

### 31.5 MetricCompletenessPolicy

```text
MetricCompletenessPolicy:
- minimum_input_requirement
- partial_result_policy
- empty_denominator_policy
- transparency_requirements: list[str]
```

### 31.6 MetricResultSemantics

```text
MetricResultSemantics:
- interpretation
- direction
- scale
- denominator_meaning
```

这是Definition-time Schema Proposal，不规定YAML、JSON、Pydantic、storage、formula parser、aggregation engine或Runtime MetricResult serialization。

---

## 32. Schema Field Decisions

| 候选字段 | v0决定 | 理由 |
|---|---|---|
| `metric_id` | 必填 | Metric Specification是一等Definition object |
| `name` | 必填 | 提供human-facing stable identity，但不替代完整semantics |
| `inputs` | 非空 | explicit population唯一authority |
| `test_case_id + contract_id` | nested MetricInput | pair定位ExpectedAssertion与authoritative GraderTarget |
| `grader_id` | 不进入MetricInput | pair可解析Grader；加入会形成双authority并使shared Grader歧义 |
| selector / query | 不进入v0 | 防止future objects自动加入与query ambiguity |
| `result_selection_policy` | 必填string | 在eligibility前冻结distinct attempt-level Results的selection intent与cardinality |
| nested ResultSelectionPolicy / selection enum | 不进入v0 | 当前all / first / final patterns可由exact required string稳定表达；没有证据支持提前冻结enum |
| Episode / attempt / Result ID或ordering字段 | 禁止 | 属于future Runtime actual identity，不是Metric Definition identity |
| `duplicate_handling` | 不进入v0 | Duplicate logical Result必须在selection前去重，是correctness invariant，不是author option |
| `aggregation_unit` | 必填string | unit是Case multiplicity与weighting解释基础；暂不冻结enum |
| `eligibility_policy` | 必填nested | 必须分开substantive、non-substantive与unavailable inputs |
| `contribution_mapping` | 非空nested rules | 冻结judgment-to-contribution semantics，不等同checker code |
| `unit_reduction` | 必填string | 处理selected eligible contributions、multi-Case与同unit多contributions，不重新选择raw attempts |
| `aggregation_rule` | 必填string | 冻结deterministic final rule，不用过早enum |
| `weighting_policy` | 必填string | 禁止implicit Case-count或criticality weighting |
| `completeness_policy` | 必填nested | 决定partial、unavailable与empty denominator |
| `result_semantics` | 必填nested | Metric Result必须独立可解释 |
| `description` | 不单独进入 | `name + result_semantics.interpretation`已承载identity，避免重复 |
| `metric_type` / `aggregation_method` | 不进入v0 | 单一enum不足以表达unit reduction + final aggregation |
| per-Contract weight | 不进入Contract | weight属于Metric policy，不改upstream object |
| actual value / counts | 禁止 | 属于Metric Result |
| Metric Result ref | 禁止 | Runtime object尚未产生 |
| Gate / threshold | 禁止 | 属于Gate Design |
| Overall Score / Scorecard | 禁止 | 属于downstream derived result/presentation |
| Metric input refs | 禁止 | v0不支持Metric→Metric graph |

### ID Rules

推荐形式：

```text
M001
M002
M003
```

规则：

- 在一个Benchmark Definition中唯一；
- 使用`M`加至少三位十进制数字；
- 不要求跨Benchmarks全局唯一；
- population、unit、eligibility、mapping、aggregation、weighting、completeness或result semantics重大变化时，应分配新ID；
- 被删除ID不应在同一Benchmark lineage复用于不同Metric meaning。

---

## 33. Schema Field Semantics

### 33.1 metric_id

非空string，表示Definition-time Metric Specification identity，不是Runtime Metric Result ID。

### 33.2 name

非空、human-readable、meaningful name。禁止只有`quality`、`score`、`metric`等无法区分population与purpose的名称。

### 33.3 inputs

必填非空`list[MetricInput]`，pair不得重复。它冻结expected Definition population，不保存Episode或Grader Result IDs。

### 33.4 result_selection_policy

必填非空deterministic string。它在duplicate logical Result records去重后、eligibility之前，定义每个MetricInput选择哪些distinct Results。

Policy必须说明selection population、basis、需要时的ordering basis、selected cardinality以及identity / ordering不可用时的behavior。它不得保存actual Episode、attempt或Result IDs，不得引用`grader_id`，也不得依赖`best`、`relevant`、`valid`等未定义判断。

### 33.5 aggregation_unit

非空string，明确unit identity如何从inputs确定。必须足够deterministic，不能只写`appropriate unit`。

### 33.6 eligibility_policy

必填nested structure：

- `eligible_result_semantics`非空，说明哪些meanings可以产生contribution；
- `non_substantive_handling`非空，说明insufficient / not-exercised等如何处理；
- `unavailable_input_handling`非空，说明no Result与execution gaps如何影响Metric availability。

它不冻结全局Result enum，也不保存actual counts。

### 33.7 contribution_mapping

必填非空rules。每个`source_semantics`在同一Metric中不得存在冲突mapping；`contribution_semantics`必须明确value、unit或category meaning。

### 33.8 unit_reduction

非空deterministic semantic rule。它只处理selection、eligibility与contribution mapping之后的contributions，必须说明同一unit的多个eligible contributions如何形成一个unit contribution以及无eligible contribution时如何处理。它不得再次决定first / final raw attempt。

### 33.9 aggregation_rule

非空、可复核、deterministic。必须说明unit contributions如何形成one Metric Result，并与result semantics一致。

### 33.10 weighting_policy

非空。必须说明equal或unequal、weight attachment unit、normalization与omitted units。不得只写`weighted as appropriate`。

### 33.11 completeness_policy

四个必填semantics：minimum requirement、partial policy、empty denominator、transparency requirements。它定义availability policy，不保存actual coverage。

### 33.12 result_semantics

四个非空strings共同定义future Result meaning。对于count Metric，`denominator_meaning`说明count universe或明确denominator不适用，而不能留空。

---

## 34. Three-Layer Metric Specification Validation

### 34.1 A. Structural / Field Validation

未来可deterministic检查：

- `metric_id`符合`M`+至少三位数字；
- Metric IDs在Definition中唯一；
- `name`非空；
- `inputs`至少一项；
- 每个MetricInput包含非空`test_case_id`与`contract_id`；
- input pairs不重复；
- `result_selection_policy`非空；
- `aggregation_unit`非空；
- eligibility三组fields均非空；
- contribution mapping至少一项；
- source semantics无duplicate conflict；
- `unit_reduction`、`aggregation_rule`、`weighting_policy`非空；
- completeness四组fields均非空；
- transparency requirements非空；
- result semantics四组fields均非空；
- 不存在actual value、counts、Result ref、Gate、Overall Score或Metric input ref字段。

### 34.2 B. Cross-object Validation

需要完整Definition context：

- 每个input `test_case_id`存在且validated；
- 每个input `contract_id`存在且validated；
- pair实际出现在Test Case ExpectedAssertions中；
- pair恰好由一个authoritative GraderTarget覆盖；
- referenced Grader Specification validated且current；
- inputs属于同一个Benchmark Definition version；
- 没有dangling、stale、cross-Benchmark或validation-only-to-production refs；
- population没有duplicate entries；
- result selection policy与MetricInput population兼容；
- selection policy不保存actual Runtime IDs或引入grader ID authority；
- selection basis可由future Runtime提供的Result identity、Episode identity、attempt ordering与Run association执行；
- aggregation units可从inputs deterministic派生；
- weighting attachment units存在且与aggregation unit一致；
- Metric Set、Population Review与Audit双向一致；
- 没有Metric→Metric、Gate或Scorecard refs。

### 34.3 C. Semantic Metric Review

逐Metric至少检查：

- name与result interpretation是否清楚；
- population是否匹配Metric purpose；
- explicit inputs是否完整且minimum；
- evaluation types是否兼容；
- repeated Episode / retry semantics是否明确；
- duplicate logical Result records是否在selection前去重且不双计；
- selection是否明确发生在eligibility之前；
- selection population、basis、cardinality与ordering是否deterministic；
- selected Result为non-substantive或unavailable时是否没有implicit fallback；
- eligibility是否不篡改Grader meanings；
- insufficient evidence是否没有自动变violated / zero；
- not-exercised handling是否符合Metric purpose；
- no Result与insufficient是否分开；
- denominator是否与interpretation一致；
- empty denominator是否不会默认0 / 100%；
- partial policy是否保持honest interpretation；
- contribution mapping是否清楚；
- aggregation unit是否有semantic意义；
- unit reduction是否只处理selected eligible contributions，没有重新选择raw attempts；
- Case multiplicity是否intentional；
- Attempt / Episode multiplicity是否intentional；
- weighting是否显式且unit-aligned；
- criticality是否没有自动变weight或Gate；
- binary / ordinal / scalar inputs是否scale-compatible；
- aggregation rule是否足够deterministic；
- denominator exclusions是否transparent；
- denominator、coverage与completeness是否与result selection semantics一致；
- 是否重新组合单一Contract judgment；
- 是否泄漏Gate、Overall Score、Scorecard或implementation。

Semantic Review需要Agent / Human judgment，不能伪装成Schema validation。

---

## 35. Metric Population 与 Coverage Review

不像上游层，每个ExpectedAssertion不需要出现在每一个Metric中，也不应该强制all targets进入一个Metric。

Metric Population Review至少记录：

| 字段 | 含义 |
|---|---|
| `metric_id` | Metric identity |
| `intended_dimension` | 该Metric要summarize的能力/表现维度 |
| `included_inputs` | 从Spec派生的MetricInput pairs |
| `excluded_relevant_inputs` | 看似相关但被排除的pairs及理由 |
| `population_status` | `POPULATION_VALID`或`POPULATION_BLOCKED` |
| `rationale` | population是否足以支持Metric interpretation |

只有满足以下条件才能`POPULATION_VALID`：

- inputs与Metric purpose一致；
- required population没有semantic gap；
- exclusion有清楚rationale；
- pair均有authoritative Grader coverage；
- result selection与Attempt / Episode multiplicity semantics明确；
- aggregation unit、multiplicity与weights不会歪曲population；
- validation通过。

Benchmark Definition整体需要哪些evaluation dimensions以及是否所有relevant responsibilities被某个Metric总结，属于required Metric Set / Benchmark coverage concern。Metric Design必须记录gap，但不凭空发明Benchmark dimensions，也不创建一个all-target Metric掩盖它。

Population Review是working artifact，不是Core Object，也不成为membership authority。

---

## 36. Metric Design Issues 与 Rollback

至少区分：

- metric-purpose ambiguity；
- population / membership issue；
- input-reference issue；
- Grader Result semantic incompatibility；
- eligibility / denominator issue；
- insufficient / not-exercised handling issue；
- unavailable-input issue；
- completeness / partial-result issue；
- empty-denominator issue；
- contribution-mapping issue；
- aggregation-unit issue；
- result-selection / attempt-multiplicity issue；
- repeat / retry / duplicate issue；
- Case multiplicity issue；
- weighting issue；
- ordinal / scalar compatibility issue；
- result-semantics issue；
- Schema insufficiency；
- downstream Gate concern；
- downstream Scorecard / Overall concern；
- implementation concern。

Rollback：

```text
Individual target judgment unclear
→ Grader Specification lifecycle

Target Evidence or Contract semantics unclear
→ appropriate upstream lifecycle

Expected population or capability dimension unclear
→ Benchmark Definition / Metric Design issue

Population clear but Result selection, denominator or aggregation unclear
→ Metric Specification Design

Metric value clear but blocking consequence unclear
→ downstream Gate Design concern

Metric Results clear but overall presentation/score unclear
→ downstream Scorecard / Overall concern

Metric rule clear but executable calculation unknown
→ downstream Metric implementation concern
```

不得为方便aggregation、Gate或presentation而改变upstream Grader Results。

---

## 37. Metric Specification Design Workflow

### Step 1 — Verify Inputs

- 验证upstream Definitions、Grader coverage、statuses与versions；
- production Entry Gate不满足时立即BLOCK；
- validation subset保留限定边界。

### Step 2 — Define Metric Meaning

- 写清measure、population、unit、direction与denominator meaning；
- 确认它是独立Metric，不是伪装的Overall Score或Gate。

### Step 3 — Freeze Explicit Population

- 列出MetricInput pairs；
- 通过Coverage Mapping解析authoritative GraderTargets；
- 删除future-convenience或无关inputs；
- 不写selector DSL。

### Step 4 — Define Result Selection

- 明确每个MetricInput选择all、first、final或其他deterministic subset；
- duplicate logical Results在selection前必须去重；
- 明确ordering basis、selected cardinality与missing identity / ordering behavior；
- 明确selected insufficient / unavailable Result是否禁止fallback；
- 执行Attempt / Episode Multiplicity Review；
- 不保存actual Runtime IDs，不写selector implementation。

### Step 5 — Define Eligibility and Contribution

- 对selected Results分开substantive、non-substantive与unavailable；
- 写contribution mappings；
- 不改变Grader Result meaning；
- 不把insufficient自动映射为violation；
- 不在eligibility阶段回退到earlier unselected Result。

### Step 6 — Choose Aggregation Unit

- 决定per-target、per-contract、per-case或其他可derivable unit；
- 执行Case Multiplicity Review；
- 明确新增Case是否改变weight。

### Step 7 — Define Unit Reduction

- 只处理selected eligible contributions；
- 写exact unit-level reduction；
- 不重新决定first / final raw attempt；
- 不引入Metric→Metric graph。

### Step 8 — Define Weighting

- 显式写equal / unequal policy；
- 保持weight与unit对齐。

### Step 9 — Define Final Aggregation

- 写exact final aggregation rule；
- 明确result scale、direction与denominator meaning；
- 不引入Metric→Metric graph。

### Step 10 — Define Completeness and Interpretation

- 写minimum input、partial、empty-denominator与transparency policy；
- 确认selection改变的coverage与denominator被诚实报告；
- 明确unavailable与zero value的区别。

### Step 11 — Write Metric Specifications

- 分配`Mxxx`；
- 使用Proposed Schema；
- 不写actual value、Gate、Overall Score或implementation。

### Step 12 — Build Population Review and Audit

- 记录included / excluded rationale；
- 记录Result selection、Case multiplicity、Attempt multiplicity、unit、weight与completeness rationale；
- 保留downstream concerns。

### Step 13 — Validate and Determine Status

- Structural / Field Validation；
- Cross-object Validation；
- Semantic Metric Review；
- unresolved issue进入Metric Design Issues；
- required Metric Set有效时READY，否则BLOCKED；
- 停止，不进入Gate或Runtime implementation。

---

## 38. Metric Specification Design Status

Production状态只保留：

```text
METRICS_READY
METRICS_BLOCKED
```

### 38.1 METRICS_READY

只有同时满足：

- authoritative upstream Definition current；
- Grader Specification Design为`GRADERS_READY`；
- required Metric Set已定义；
- 每个Metric具有独立可解释meaning；
- population explicit且validated；
- input pairs均解析到authoritative Grader coverage；
- result selection policy明确且deterministic；
- Attempt / Episode multiplicity semantics明确；
- duplicate handling invariant可由future Runtime identity满足；
- selection → eligibility → contribution → unit reduction processing order唯一；
- 没有unresolved retry semantics；
- eligibility与denominator明确；
- contribution mapping明确；
- aggregation unit与unit reduction明确；
- Case multiplicity intentional；
- aggregation deterministic；
- weighting显式且unit-aligned；
- completeness、partial与empty-denominator policy明确；
- result semantics清楚；
- denominator transparency充分；
- 所有Metrics通过三层validation；
- Spec Set、Population Review与Audit一致；
- 没有unresolved blocker；
- 没有Gate、Scorecard、Overall或Runtime implementation leakage。

### 38.2 METRICS_BLOCKED

例如：

- required Metric dimension未定义；
- population模糊或依赖Runtime discovery；
- target pair没有authoritative Grader coverage；
- result selection population、basis、ordering或cardinality不清；
- duplicate logical Result可能被双计；
- final raw attempt与final eligible contribution混淆；
- selection / eligibility / unit reduction顺序不唯一；
- denominator无法解释；
- insufficient被自动当FAIL / 0；
- no Result与insufficient混淆；
- Case multiplicity产生unintended weighting；
- unit reduction或Attempt / Episode multiplicity policy不清；
- weights与unit不一致；
- empty denominator默认0 / 100%；
- ordinal / scalar scales不兼容；
- aggregation rule无法deterministic实现；
- Metric重新决定Contract verdict；
- Metric泄漏Gate或Overall Score。

状态不是Metric value，也不是Benchmark PASS / FAIL。

---

## 39. Required Outputs

Metric Specification Design至少产生：

1. **Metric Specification Set**：使用Proposed Schema的Definition-time policies；
2. **Metric Population / Coverage Review**：每个Metric的intended dimension、included / excluded population与status；
3. **Metric Specification Design Audit**：unit、denominator、mapping、weighting、multiplicity与completeness rationale；
4. **Metric Design Issues**：blocking issues与downstream concerns；
5. **Metric Specification Validation Summary**：Structural、Cross-object、Semantic三层结果；
6. **Metric Specification Design Status**：`METRICS_READY`或`METRICS_BLOCKED`；
7. **Schema Design Findings**：只记录真实design暴露的schema need。

Working Metric Drafts不是必需final output，也不算Metric coverage。

---

## 40. Metric Result Boundary

本轮不设计完整Metric Result Schema，但必须保持：

```text
Specification:
how the defined population should be aggregated

Result:
what this Run actually aggregated and obtained
```

Future Metric Result在概念上至少需要关联或表达：

- Metric Specification；
- Run与Subject；
- expected population；
- actual Grader Results；
- included / excluded inputs；
- actual unit contributions；
- actual value或unavailable meaning；
- actual denominator与coverage metadata；
- comparison compatibility。

为执行duplicate invariant与`result_selection_policy`，future Runtime还必须提供足够actual identity与ordering，以区分same logical Result、duplicate record、distinct Episodes / attempts、attempt order与current Run association。Metric Specification不保存`episode_id`、`attempt_id`、`grader_result_id`、sequence number或timestamp；这些是downstream Runtime evidence，不是Definition identity。

一个Metric Result只对应一个Run与一个Subject。参与该Result的actual Grader Results必须属于同一Run；跨Run比较可以消费多个已有Metric Results，但不得把不同Runs的Grader Results混成一个Metric Result。

这些actual data都不得写入Metric Specification实例。即使没有eligible inputs，也应产生可追踪的future Result state，而不是让Metric静默消失。

---

## 41. Gate、Scorecard 与 Overall Boundary

### 41.1 Gate

Metric描述表现，Gate决定阻断。Metric Specification不得包含：

- threshold causing Benchmark FAIL；
- critical violation blocker；
- non-offsettable failure；
- Gate pass / fail；
- Gate Result。

Gate Specification未来可以Definition-time引用Metric Specification，再在Run中定位Metric Result；Metric不反向引用Gate。

### 41.2 Scorecard

Scorecard未来组织Grader summaries、Metric Results、Gate Results、Overall Score与diagnostics。Metric不负责layout、report formatting或final Benchmark conclusion。

### 41.3 Overall Score

多个Metric Results如何形成Overall Score属于future Overall Aggregation / Scorecard policy。Metric-level `weighting_policy`只处理本Metric内部aggregation units，不是Metrics之间的Overall weight。

---

## 42. Schema Design Findings

### 42.1 Explicit MetricInput pair is the membership authority

`(test_case_id, contract_id)`在当前Definition内唯一定位ExpectedAssertion与authoritative GraderTarget，避免query drift与shared Grader ambiguity。

### 42.2 No grader_id in MetricInput

Pair与grader ID同时存在会形成双authority。Grader coverage由Cross-object Validation解析，不在MetricInput重复冻结。

### 42.3 Aggregation unit is first-class policy, not Core Object

Unit必须进入Metric Specification，但不创建AggregationUnit Core Object。当前用deterministic string表达派生规则，不冻结enum。

### 42.4 Result selection is first-class and precedes eligibility

`result_selection_policy`在duplicate logical Results去重后、eligibility之前，冻结每个MetricInput选择哪些distinct attempt-level Results。它关闭final raw attempt与final eligible contribution混淆，但不保存Runtime IDs，也不引入selector language。

当前真实validation只证明需要一个required deterministic string；没有证据要求nested ResultSelectionPolicy或selection enum。Future implementation evidence若证明string无法稳定执行，再重新评估结构化representation。

### 42.5 Unit reduction is distinct from Result selection and final aggregation

Unit reduction只处理selection、eligibility与contribution mapping之后的selected eligible contributions；它不再选择first / final raw Result。Multi-Case Contract与同unit多contributions需要先形成unit contribution，随后final aggregation形成Metric Result。

### 42.6 Eligibility separates substantive, non-substantive and unavailable

三类inputs具有不同语义，不能靠一个included-status list或全局default处理。

### 42.7 Completeness requires explicit nested policy

Minimum input、partial、empty denominator与transparency共同决定Metric Result是否仍可解释，不能只放Audit。

### 42.8 No aggregation-method enum

真实method需要unit reduction + final rule组合。Human-readable exact rule比不成熟enum更忠实；未来implementation validation可重新评估structured formula representation。

### 42.9 Weighting is explicit but not an upstream field

每个Metric必须声明weighting policy。Criticality、Case count与failure severity都不自动成为weight。

真实unequal-weight authoring可能需要future structured unit-weight mapping；当前validation subset不依赖它，因此不在本轮扩Schema。

### 42.10 Completeness threshold structure remains future hardening

Strict、eligible-only与简单partial policy可由current nested strings表达。多个threshold units、operators与logical combinations可能需要future structured clauses；当前validation subset不依赖它，因此不是当前generic blocker。

### 42.11 No Metric-to-Metric inputs

Hierarchical needs通过unit reduction表达；跨Metrics汇总留Overall Score，避免metric graph。

### 42.12 No actual Result fields

Actual value、counts、denominator、included IDs与status属于future Metric Result。

---

## 43. Method Self-Review

| 检查问题 | v0结论 |
|---|---|
| 1. Grader vs Metric边界是否清楚？ | 是。Grader形成target judgment；Metric只聚合已成立Results，不重组单一Contract verdict。 |
| 2. Metric vs Gate边界是否清楚？ | 是。Metric描述表现；Gate以后决定阻断。 |
| 3. Metric vs Overall Score是否清楚？ | 是。Metric有独立meaning；Overall是future Scorecard-derived value。 |
| 4. population authority是否清楚？ | 是。`inputs`中的explicit MetricInput pairs是唯一authority。 |
| 5. target membership是否无歧义？ | 是。pair定位ExpectedAssertion与authoritative GraderTarget，不存grader ID。 |
| 6. denominator semantics是否明确？ | 是。Eligibility、unit reduction、weights与empty policy共同定义。 |
| 7. insufficient evidence是否不会变FAIL？ | 是。默认非substantive；特殊yield Metric必须诚实改名和interpretation。 |
| 8. not-exercised是否可Metric-specific处理？ | 是。Compliance、exercise rate与coverage可有不同冻结policy。 |
| 9. missing result是否区分？ | 是。No Result不等于insufficient-evidence Result。 |
| 10. empty denominator是否处理？ | 是。Rate/mean undefined；完整population中的count 0可合法。 |
| 11. aggregation unit是否必要？ | 是。它决定conceptual contribution、multiplicity与weight attachment。 |
| 12. Case multiplicity是否显式处理？ | 是。每个Metric必须审查Case count是否intentional weight。 |
| 13. Attempt / Episode multiplicity是否显式处理？ | 是。Result Selection在eligibility前冻结all / first / final等distinct Result subset，Review检查ordering、fallback与coverage影响。 |
| 14. Duplicate处理是否可配置？ | 否。Same logical Result的duplicate record必须在selection前去重，这是evaluation correctness invariant。 |
| 15. Contract normalization是否可表达？ | 是。per-contract unit reduction + final aggregation，不重判Episode verdict。 |
| 16. weighting是否与criticality分离？ | 是。Criticality不自动产生weight或Gate。 |
| 17. weighting unit是否明确？ | 是。Required `weighting_policy`必须与aggregation unit对齐。 |
| 18. contribution mapping是否清楚？ | 是。Metric-local mapping不改变Grader meaning。 |
| 19. binary aggregation是否支持？ | 是。支持明确mapping、rate、count、mean、worst-case等semantic rules。 |
| 20. ordinal/scalar future边界是否清楚？ | 是。必须scale-compatible；当前不增加专用字段。 |
| 21. shared Grader target membership是否清楚？ | 是。引用target pair，不引用ambiguous shared grader ID。 |
| 22. Metric是否足够deterministic？ | 是，要求exact population、Result selection、eligibility、unit、mapping、reduction、weight与rule，并固定processing order。 |
| 23. Metric Result meaning是否清楚？ | 是。Interpretation、direction、scale、denominator四项必填。 |
| 24. denominator transparency是否要求？ | 是。Future Result必须说明expected、selected、eligible、excluded、insufficient与unavailable。 |
| 25. Candidate是否需要？ | 当前不需要mandatory Candidate；Working Draft + Audit足够。 |
| 26. Audit是否需要？ | 需要非Core Audit保存population、Result selection、Case / Attempt multiplicity、weight与completeness rationale。 |
| 27. Schema最小字段是什么？ | M ID、name、inputs、result selection、unit、eligibility、mapping、reduction、aggregation、weighting、completeness与result semantics。 |
| 28. 是否泄漏Gate？ | 未泄漏。没有threshold、blocking或Benchmark PASS / FAIL。 |
| 29. 是否泄漏Scorecard？ | 未泄漏。没有Overall Score、Metric-to-Metric graph或presentation。 |
| 30. 哪些问题仍需future validation？ | Structured unequal weights、multi-threshold completeness、ordinal/scalar与large-scale implementation determinism。 |

### 43.1 Self-review corrections incorporated

本轮自审已在正文处理：

- 为防止Runtime自动纳入全部Results，采用explicit MetricInput population；
- 为防止shared Grader引用歧义，target pair不存grader ID；
- 为防止Case count隐式变importance，强制aggregation unit与Multiplicity Review；
- 为防止final raw attempt与final eligible contribution混淆，新增required `result_selection_policy`并固定selection-before-eligibility；
- 为防止duplicate logical Result重复计分，将deduplication冻结为selection前invariant；
- 为防止Case与Episode multiplicity混淆，分开Case Multiplicity Review与Attempt / Episode Multiplicity Review；
- 为防止unit reduction重新选择raw attempts，将其限定为selected eligible contributions的reduction；
- 为防止insufficient变FAIL，分开substantive、non-substantive与unavailable；
- 为防止no Result与insufficient混淆，单独定义availability handling；
- 为防止empty denominator伪造0 / 100%，要求explicit policy；
- 为防止criticality变weight / Gate，要求explicit unit-aligned weighting；
- 为防止Metric重判Contract，禁止multi-Grader verdict composition；
- 为防止metric graph，v0只消费Grader Results；
- 为防止Scorecard leakage，Overall Score留downstream；
- 为防止actual data进入Definition，分开Metric Result semantics与actual value / counts。

### 43.2 Future Method Validation Coverage

在freeze MetricSpecification Schema前，至少需要真实validation检查：

- binary per-target compliance rate；
- per-contract normalization with unequal Case multiplicity；
- additional repeated Episode semantics beyond all / first / final / worst eligible probes；
- insufficient / not-exercised exclusions；
- missing Result与partial Metric；
- empty denominator；
- strict vs threshold completeness；
- shared Grader的target-level membership；
- equal per-unit weighting；
- explicit unequal weighting；
- mixed Outcome / Workflow rejection或合法正例；
- ordinal mapping；
- compatible local scalar aggregation；
- diagnostic failure-mode Metric；
- denominator transparency与comparison compatibility。

这些是future method validation，不是Runtime execution、Metric Result、Gate或Scorecard PASS。

---

## 44. Final Decision Checklist

### Inputs

- [ ] Upstream Grader Specification Design为`GRADERS_READY`
- [ ] Inputs属于同一current Benchmark Definition version
- [ ] Method validation subset保留限定status与benchmark-wide blocker

### Identity and Population

- [ ] Metric name与result interpretation清楚
- [ ] Metric具有独立meaning，不是伪装Overall Score
- [ ] `inputs`是唯一membership authority
- [ ] 每个pair解析到ExpectedAssertion与唯一authoritative GraderTarget
- [ ] 没有grader ID、selector或Runtime discovery双authority
- [ ] Included / excluded population通过review

### Eligibility and Denominator

- [ ] Substantive、non-substantive与unavailable分开
- [ ] Insufficient没有自动变violated / 0
- [ ] Not-exercised处理符合Metric purpose
- [ ] No Result没有混成insufficient
- [ ] Denominator与Metric interpretation一致
- [ ] Empty denominator没有默认0 / 100%
- [ ] Exclusions必须透明报告

### Result Selection and Attempt Multiplicity

- [ ] `result_selection_policy`必填、非空且deterministic
- [ ] Duplicate logical Result records在selection前去重
- [ ] Selection population、basis、cardinality与ordering basis明确
- [ ] Selection明确发生在eligibility之前
- [ ] Selected non-substantive / unavailable Result没有implicit fallback
- [ ] Attempt / Episode multiplicity semantics与unexpected multiplicity behavior明确
- [ ] Future Runtime identity / ordering dependency已记录但没有写入Specification IDs
- [ ] Result selection对denominator、coverage与completeness的影响透明

### Unit、Case Multiplicity and Weighting

- [ ] Aggregation unit可deterministic派生
- [ ] Unit reduction只处理selected eligible contributions，不重新选择raw attempts
- [ ] Unit reduction处理multi-Case与同unit多contributions
- [ ] Case multiplicity影响是intentional
- [ ] Weighting policy显式且与unit对齐
- [ ] Criticality没有自动变weight或Gate

### Contribution and Aggregation

- [ ] Contribution mapping不改写Grader semantics
- [ ] Aggregation rule足够deterministic
- [ ] Binary / ordinal / scalar scales兼容
- [ ] Metric没有重组单一Contract verdict
- [ ] 没有Metric→Metric dependency

### Completeness and Result Meaning

- [ ] Minimum input requirement明确
- [ ] Partial result policy明确
- [ ] Transparency requirements明确
- [ ] Result interpretation、direction、scale、denominator meaning完整
- [ ] 没有actual value、counts或Result IDs

### Boundaries and Validation

- [ ] 没有Gate threshold、blocking或Benchmark PASS / FAIL
- [ ] 没有Overall Score、Scorecard layout或presentation
- [ ] 没有aggregation code、formula parser或library implementation
- [ ] Structural / Cross-object / Semantic Validation完成
- [ ] Selection → eligibility → contribution → unit reduction order唯一
- [ ] 没有unresolved retry semantics
- [ ] Spec Set、Population Review与Audit一致
- [ ] 无unresolved Metric Design Issue

全部必需检查通过时，production Metric Specification Design才可输出：

```text
METRICS_READY
```

否则输出：

```text
METRICS_BLOCKED
```

并停止在Metric Specification Design边界，不开始Gate、Metric implementation、Scorecard或Overall Score Design。
