# AT Exchanger — ComfyUI Custom Node

프롬프트 내 특정 접두사를 감지하여 삭제·교체하거나, 접두사가 붙은 태그를 통째로 제거하는 텍스트 처리 노드입니다.  
기본판(`AT Exchanger`)과 확장판(`AT Exchanger (Advanced)`) 두 가지가 제공됩니다.

---

## 파일 구성

```
your_custom_node_folder/
├── __init__.py                  # ComfyUI 진입점
├── at_exchanger.py              # 기본 노드
└── at_exchanger__advanced_.py   # 확장 노드
```

---

## 공통 개념

### 태그(Token)란?
이 노드에서 "태그"는 **쉼표(`,`)로 구분된 하나의 단위**를 의미합니다.

```
masterpiece, @lora_style, (best quality:1.2), @bg_remove
  [태그1]      [태그2]          [태그3]           [태그4]
```

괄호 `()` `[]` 안에 있는 쉼표는 구분자로 취급하지 않습니다.  
예: `(best quality:1.2, ultra)` → 이 전체가 하나의 태그

### 접두사(Prefix)란?
태그 앞에 붙어서 "이 태그를 특별하게 처리해라"고 표시하는 기호입니다.  
기본값은 `@`이며 원하는 문자로 변경 가능합니다.

### 출력 단자
두 노드 모두 출력이 두 개입니다.

| 출력 | 설명 |
|---|---|
| `Original_text` | 입력받은 텍스트를 **아무 처리 없이** 그대로 출력 |
| `Exchanged_text` | 모든 처리가 적용된 결과 텍스트 출력 |

---

## AT Exchanger (기본)

### 입력 항목

| 항목 | 설명 |
|---|---|
| `text` | 처리할 원본 프롬프트 |
| `detect_prefix` | 감지할 접두사 (기본: `@`) |
| `mode` | 처리 방식 선택 (아래 참조) |
| `replacement_prefix` | `replace` 모드일 때 교체할 접두사 |
| `exceptions` | 처리에서 제외할 항목 목록 (쉼표 구분) |
| `additional_prompt` | main 처리 전에 먼저 찾아서 교체할 문자열 |
| `additional_exchang` | `additional_prompt`를 이것으로 교체 |

### mode 옵션

**`delete`** — 접두사만 제거, 나머지 태그 내용은 유지

```
입력: masterpiece, @lora_style, beautiful
결과: masterpiece, lora_style, beautiful
```

**`replace`** — 접두사를 다른 접두사로 교체

```
detect_prefix: @
replacement_prefix: $
입력: masterpiece, @lora_style, beautiful
결과: masterpiece, $lora_style, beautiful
```

**`power_delete`** — 접두사가 붙은 태그를 쉼표까지 포함해 통째로 제거

```
입력: masterpiece, @lora_style, beautiful
결과: masterpiece, beautiful
```

### exceptions (예외 처리)

예외로 등록한 항목은 접두사가 있어도 처리하지 않고 원문 그대로 유지합니다.

```
exceptions: @_@, @keep
입력: @lora_style, @_@, @keep_this
결과(delete 모드): lora_style, @_@, keep_this   ← @_@ 는 보존됨
```

여러 예외 항목이 겹칠 경우 **긴 것부터 우선 매칭**합니다.  
예: `@_@`와 `@_` 둘 다 등록 시 → `@_@`가 먼저 매칭됨

### additional_prompt / additional_exchang

main 처리(mode)보다 **반드시 먼저** 실행됩니다.  
특정 문자열을 다른 문자열로 치환하고 싶을 때 사용합니다.

```
additional_prompt: @old_tag
additional_exchang: @new_tag
입력: masterpiece, @old_tag, beautiful
→ (additional 치환 후) masterpiece, @new_tag, beautiful
→ (delete 모드 적용 후) masterpiece, new_tag, beautiful
```

---

## AT Exchanger (Advanced)

기본 노드의 모든 기능을 포함하며, 아래 기능이 추가됩니다.

### 처리 실행 순서

```
1. additional_prompt 치환   (항상 가장 먼저)
2. 조건부 체크              (main mode 실행 여부 결정)
3. main mode                (delete / replace / power_delete)
4. 태그 추가                (use_add)
5. 태그 이동                (use_move)
6. 인접 태그 수정           (use_neighbor)
```

---

### 추가 기능 1 — additional_prompt 개선 (태그 단위 시퀀스 매칭)

기본 노드와 달리 **태그 단위로 시퀀스 매칭**을 합니다.  
`@b`를 찾을 때 `@bc`가 잘못 매칭되는 오매칭이 발생하지 않습니다.  
또한 여러 태그 연속을 하나의 덩어리로 찾아서 교체할 수 있습니다.

```
additional_prompt: @setup_a, @setup_b    ← 태그 2개를 하나의 시퀀스로 검색
additional_exchang: @result_tag
입력: masterpiece, @setup_a, @setup_b, beautiful
결과: masterpiece, @result_tag, beautiful
```

---

### 추가 기능 2 — 조건부 처리 (use_condition)

특정 태그가 프롬프트에 존재하는지 여부에 따라 **main mode 실행 자체를 제어**합니다.

| 항목 | 설명 |
|---|---|
| `use_condition` | 활성화 여부 (기본: OFF) |
| `condition_tags` | 조건으로 사용할 태그 목록, `\|` 로 구분 |
| `condition_mode` | `run_if_present` 또는 `skip_if_present` |

`condition_tags`는 **파이프(`\|`)로 구분**합니다. 목록 중 하나라도 프롬프트에 있으면 조건 충족입니다.

```
condition_tags: lora_a | lora_b
condition_mode: run_if_present
```
→ 프롬프트에 `lora_a` 또는 `lora_b` 가 있을 때만 main mode 실행

```
condition_mode: skip_if_present
```
→ 프롬프트에 해당 태그가 있으면 main mode를 건너뜀

---

### 추가 기능 3 — 태그 추가 (use_add)

main mode 처리 이후 지정한 태그를 맨 앞 또는 맨 뒤에 추가합니다.  
독립적인 조건부(`use_conditional_add`)를 가집니다.

| 항목 | 설명 |
|---|---|
| `use_add` | 활성화 여부 (기본: OFF) |
| `add_tags` | 추가할 태그 (쉼표 구분) |
| `add_position` | `front`(맨 앞) 또는 `back`(맨 뒤) |
| `use_conditional_add` | 조건부 추가 활성화 여부 |
| `condition_add_tags` | 추가 실행 조건 태그, `\|` 로 구분 |

```
add_tags: high quality, detailed
add_position: front
입력: @lora_style, beautiful
결과(delete 후): high quality, detailed, lora_style, beautiful
```

`use_conditional_add`를 켜면 `condition_add_tags`에 지정한 태그가 있을 때만 추가합니다.

---

### 추가 기능 4 — 태그 이동 (use_move)

지정한 태그를 맨 앞 또는 맨 뒤로 이동시킵니다. 나머지 태그들의 순서는 유지됩니다.

| 항목 | 설명 |
|---|---|
| `use_move` | 활성화 여부 (기본: OFF) |
| `move_tags` | 이동할 태그 (쉼표 구분) |
| `move_to` | `front`(맨 앞) 또는 `back`(맨 뒤) |

```
move_tags: masterpiece, best quality
move_to: front
입력: beautiful, masterpiece, detailed, best quality
결과: masterpiece, best quality, beautiful, detailed
```

---

### 추가 기능 5 — 인접 태그 수정 (use_neighbor)

기준이 되는 태그를 찾고, 그 **앞 또는 뒤 인접 태그**에 텍스트를 붙입니다.

| 항목 | 설명 |
|---|---|
| `use_neighbor` | 활성화 여부 (기본: OFF) |
| `neighbor_target` | 기준 태그 (정확히 일치해야 함) |
| `neighbor_pos` | `after`(다음 태그) 또는 `before`(이전 태그) |
| `neighbor_add_pos` | `prefix`(앞에 붙임) 또는 `suffix`(뒤에 붙임) |
| `neighbor_text` | 추가할 텍스트 |

```
neighbor_target: @separator
neighbor_pos: after
neighbor_add_pos: prefix
neighbor_text: X_

입력: tag_a, @separator, tag_b, tag_c
결과: tag_a, @separator, X_tag_b, tag_c
```

기준 태그가 여러 번 나오면 모든 위치에 대해 적용됩니다.

---

## 입력 구분자 정리

| 용도 | 구분자 |
|---|---|
| 프롬프트 태그 간 구분 | `,` 쉼표 |
| `exceptions` 목록 | `,` 쉼표 |
| `add_tags` 목록 | `,` 쉼표 |
| `move_tags` 목록 | `,` 쉼표 |
| `condition_tags` 목록 | `\|` 파이프 |
| `condition_add_tags` 목록 | `\|` 파이프 |

---

## 설치

ComfyUI의 `custom_nodes` 폴더 안에 이 폴더를 통째로 넣고 ComfyUI를 재시작합니다.

```
ComfyUI/
└── custom_nodes/
    └── at_exchanger/
        ├── __init__.py
        ├── at_exchanger.py
        └── at_exchanger__advanced_.py
```

노드 검색창에서 `AT Exchanger` 또는 `AT Exchanger (Advanced)`로 검색하면 찾을 수 있습니다.  
카테고리 위치: `utils/text`
