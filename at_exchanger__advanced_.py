# at_exchanger_(advanced) - ComfyUI Custom Node
#
# ▶ 처리 실행 순서
#   1. additional_prompt 치환  (태그 단위 시퀀스 매칭, 항상 먼저 실행)
#   2. 조건부 체크             (use_condition → main mode 실행 여부 결정)
#   3. main mode               (delete / replace / power_delete)
#   4. 태그 추가               (use_add, 독립 조건부 포함)
#   5. 태그 이동               (use_move)
#   6. 인접 태그 수정          (use_neighbor)

class ATExchangerAdvanced:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {

                # ── 기본 ─────────────────────────────────────────────────────
                "text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "처리할 원본 프롬프트 텍스트"
                }),
                "detect_prefix": ("STRING", {
                    "multiline": False,
                    "default": "@",
                    "tooltip": "감지할 접두사 (예: @)"
                }),
                "mode": (["delete", "replace", "power_delete"], {
                    "tooltip": "delete: 접두사만 삭제 / replace: 접두사 교체 / power_delete: 접두사 포함 토큰 전체 삭제"
                }),
                "replacement_prefix": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "replace 모드일 때 교체할 접두사 (공백 포함 그대로 입력)"
                }),
                "exceptions": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "처리 제외 항목, 쉼표 구분 (예: @_@, @keep) / 긴 항목 우선 매칭"
                }),

                # ── additional 치환 ──────────────────────────────────────────
                # main 처리 전에 먼저 실행됨
                # 태그 단위 시퀀스 매칭이므로 @b 검색 시 @bc 오매칭 없음
                "additional_prompt": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "이 태그 시퀀스를 먼저 찾아 additional_exchang으로 교체 / 비워두면 비활성화"
                }),
                "additional_exchang": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "additional_prompt와 매칭된 구간을 이 내용으로 교체"
                }),

                # ── 조건부 처리 ──────────────────────────────────────────────
                # main mode(3단계)의 실행 여부를 조건 태그로 제어
                "use_condition": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "활성화 시 condition_tags 조건을 만족할 때만 main mode 실행"
                }),
                "condition_tags": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "| 로 구분, 하나라도 존재하면 조건 충족 (예: lora_a | lora_b)"
                }),
                "condition_mode": (["run_if_present", "skip_if_present"], {
                    "tooltip": "run_if_present: 조건 태그 있으면 실행 / skip_if_present: 조건 태그 있으면 스킵"
                }),

                # ── 태그 추가 ────────────────────────────────────────────────
                # main mode 이후 실행, 독립적인 조건부 설정 가능
                "use_add": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "활성화 시 지정 태그를 맨 앞 또는 맨 뒤에 추가"
                }),
                "add_tags": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "추가할 태그 (쉼표 구분)"
                }),
                "add_position": (["front", "back"], {
                    "tooltip": "front: 맨 앞에 추가 / back: 맨 뒤에 추가"
                }),
                "use_conditional_add": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "활성화 시 condition_add_tags 조건 충족 시에만 추가 실행"
                }),
                "condition_add_tags": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "| 로 구분, 하나라도 있으면 추가 실행"
                }),

                # ── 태그 이동 ────────────────────────────────────────────────
                # 지정 태그를 맨 앞 또는 맨 뒤로 이동, 원래 순서는 유지
                "use_move": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "활성화 시 지정 태그를 앞 또는 뒤로 이동"
                }),
                "move_tags": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "이동할 태그 (쉼표 구분) / 지정 순서 유지"
                }),
                "move_to": (["front", "back"], {
                    "tooltip": "front: 맨 앞으로 / back: 맨 뒤로"
                }),

                # ── 인접 태그 수정 ───────────────────────────────────────────
                # 기준 태그를 찾고 그 앞/뒤 인접 태그에 텍스트를 붙임
                # 예: 기준=A, after, prefix, "X_" → A 다음 태그가 "B"이면 "X_B"로 변경
                "use_neighbor": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "활성화 시 기준 태그의 인접 태그에 텍스트 추가"
                }),
                "neighbor_target": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "기준이 되는 태그 (정확히 일치해야 함)"
                }),
                "neighbor_pos": (["after", "before"], {
                    "tooltip": "after: 기준 태그의 다음 태그 수정 / before: 이전 태그 수정"
                }),
                "neighbor_add_pos": (["prefix", "suffix"], {
                    "tooltip": "prefix: 인접 태그 앞에 붙임 / suffix: 인접 태그 뒤에 붙임"
                }),
                "neighbor_text": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "인접 태그에 추가할 텍스트 (공백 포함 그대로)"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("Original_text", "Exchanged_text")
    FUNCTION = "exchange"
    CATEGORY = "utils/text"
    OUTPUT_NODE = False

    def exchange(
        self, text, detect_prefix, mode, replacement_prefix, exceptions,
        additional_prompt, additional_exchang,
        use_condition, condition_tags, condition_mode,
        use_add, add_tags, add_position, use_conditional_add, condition_add_tags,
        use_move, move_tags, move_to,
        use_neighbor, neighbor_target, neighbor_pos, neighbor_add_pos, neighbor_text
    ):
        # Original_text: 항상 입력 그대로 출력
        original = text

        if not detect_prefix:
            return (original, text)

        # 예외 목록 파싱 & 길이 내림차순 정렬 (긴 항목 우선 매칭)
        exception_list = [e.strip() for e in exceptions.split(",") if e.strip()]
        exception_list.sort(key=len, reverse=True)

        working = text

        # ── Step 1: additional_prompt 치환 ──────────────────────────────────
        # 태그 단위 시퀀스 매칭 → @b 검색 시 @bc 오매칭 방지
        if additional_prompt.strip():
            working = self._apply_additional(working, additional_prompt, additional_exchang)

        # ── Step 2: 조건부 체크 (main mode 게이트) ──────────────────────────
        run_main = True
        if use_condition and condition_tags.strip():
            present = self._check_condition(working, condition_tags)
            run_main = present if condition_mode == "run_if_present" else not present

        # ── Step 3: main mode ────────────────────────────────────────────────
        if run_main:
            if mode == "delete":
                working = self._process(working, detect_prefix, "", exception_list)
            elif mode == "replace":
                working = self._process(working, detect_prefix, replacement_prefix, exception_list)
            elif mode == "power_delete":
                working = self._power_delete(working, detect_prefix, exception_list)

        # ── Step 4: 태그 추가 ────────────────────────────────────────────────
        if use_add and add_tags.strip():
            should_add = True
            if use_conditional_add and condition_add_tags.strip():
                should_add = self._check_condition(working, condition_add_tags)
            if should_add:
                working = self._add_tags(working, add_tags, add_position)

        # ── Step 5: 태그 이동 ────────────────────────────────────────────────
        if use_move and move_tags.strip():
            working = self._move_tags(working, move_tags, move_to)

        # ── Step 6: 인접 태그 수정 ───────────────────────────────────────────
        if use_neighbor and neighbor_target.strip() and neighbor_text:
            working = self._neighbor_modify(
                working, neighbor_target, neighbor_pos, neighbor_add_pos, neighbor_text
            )

        return (original, working)

    # ── 접두사 치환 (delete / replace 공용) ──────────────────────────────────

    def _process(self, text, prefix, replacement, exceptions):
        """문자 단위 순회로 접두사 감지 및 치환, 예외 항목은 원문 보존"""
        result = []
        i = 0
        prefix_len = len(prefix)

        while i < len(text):
            if text[i:i + prefix_len] == prefix:
                matched_exception = None
                for exc in exceptions:
                    if text[i:i + len(exc)] == exc:
                        matched_exception = exc
                        break

                if matched_exception is not None:
                    result.append(matched_exception)
                    i += len(matched_exception)
                else:
                    result.append(replacement)
                    i += prefix_len
            else:
                result.append(text[i])
                i += 1

        return "".join(result)

    # ── power_delete ─────────────────────────────────────────────────────────

    def _power_delete(self, text, prefix, exceptions):
        """접두사 포함 최상위 토큰 전체 제거, 빈 쉼표 없이 정리"""
        kept = []
        for token in self._split_top_level(text):
            stripped = token.strip()
            if stripped and not self._contains_active_prefix(stripped, prefix, exceptions):
                kept.append(stripped)
        return ", ".join(kept)

    def _contains_active_prefix(self, token, prefix, exceptions):
        """sentinel 치환 후 존재 여부로 예외 아닌 접두사 감지"""
        sentinel = "\x00"
        return sentinel in self._process(token, prefix, sentinel, exceptions)

    # ── additional_prompt 치환 ───────────────────────────────────────────────

    def _apply_additional(self, text, find_str, replace_str):
        """태그 단위 시퀀스 매칭으로 find_str → replace_str 교체"""
        find_tokens = [t.strip() for t in self._split_top_level(find_str) if t.strip()]
        replace_tokens = [t.strip() for t in self._split_top_level(replace_str) if t.strip()]

        if not find_tokens:
            return text

        text_tokens = [t.strip() for t in self._split_top_level(text) if t.strip()]
        m = len(find_tokens)
        result = []
        i = 0

        while i < len(text_tokens):
            if text_tokens[i:i + m] == find_tokens:
                result.extend(replace_tokens)
                i += m
            else:
                result.append(text_tokens[i])
                i += 1

        return ", ".join(result)

    # ── 조건부 체크 ──────────────────────────────────────────────────────────

    def _check_condition(self, text, condition_str):
        """| 구분 조건 태그 중 하나라도 텍스트 토큰에 존재하면 True"""
        tokens = {t.strip() for t in self._split_top_level(text) if t.strip()}
        cond_tags = [t.strip() for t in condition_str.split("|") if t.strip()]
        return any(ct in tokens for ct in cond_tags)

    # ── 태그 추가 ────────────────────────────────────────────────────────────

    def _add_tags(self, text, add_str, position):
        """지정 태그를 맨 앞 또는 맨 뒤에 추가"""
        new_tags = [t.strip() for t in self._split_top_level(add_str) if t.strip()]
        if not new_tags:
            return text

        existing = [t.strip() for t in self._split_top_level(text) if t.strip()]
        combined = new_tags + existing if position == "front" else existing + new_tags
        return ", ".join(combined)

    # ── 태그 이동 ────────────────────────────────────────────────────────────

    def _move_tags(self, text, move_str, direction):
        """지정 태그를 맨 앞 또는 맨 뒤로 이동, 나머지 순서 유지"""
        move_set = {t.strip() for t in self._split_top_level(move_str) if t.strip()}
        tokens = [t.strip() for t in self._split_top_level(text) if t.strip()]

        target = [t for t in tokens if t in move_set]
        other  = [t for t in tokens if t not in move_set]

        combined = target + other if direction == "front" else other + target
        return ", ".join(combined)

    # ── 인접 태그 수정 ───────────────────────────────────────────────────────

    def _neighbor_modify(self, text, target_tag, neighbor_pos, add_pos, add_text):
        """기준 태그를 찾고 그 앞/뒤 인접 태그에 텍스트를 prefix 또는 suffix로 추가"""
        tokens = [t.strip() for t in self._split_top_level(text) if t.strip()]
        result = tokens[:]
        target = target_tag.strip()

        modify_indices = set()
        for idx, tag in enumerate(tokens):
            if tag == target:
                n_idx = idx - 1 if neighbor_pos == "before" else idx + 1
                if 0 <= n_idx < len(tokens):
                    modify_indices.add(n_idx)

        for m_idx in modify_indices:
            orig = result[m_idx]
            result[m_idx] = (add_text + orig) if add_pos == "prefix" else (orig + add_text)

        return ", ".join(result)

    # ── 공통 유틸 ────────────────────────────────────────────────────────────

    def _split_top_level(self, text):
        """괄호/대괄호 깊이를 추적해 최상위 쉼표로만 분리"""
        tokens = []
        current = []
        depth = 0

        for ch in text:
            if ch in "([":
                depth += 1
                current.append(ch)
            elif ch in ")]":
                depth -= 1
                current.append(ch)
            elif ch == "," and depth == 0:
                tokens.append("".join(current))
                current = []
            else:
                current.append(ch)

        if current:
            tokens.append("".join(current))

        return tokens


# ── ComfyUI 등록 ──────────────────────────────────────────────────────────────

NODE_CLASS_MAPPINGS = {
    "ATExchangerAdvanced": ATExchangerAdvanced
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ATExchangerAdvanced": "AT Exchanger (Advanced)"
}
