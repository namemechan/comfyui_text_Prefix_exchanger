# at_exchanger - ComfyUI Custom Node
# 특정 접두사를 감지하여 삭제/교체하거나, 접두사가 달린 프롬프트를 통째로 제거하는 노드
# additional_prompt 기능으로 특정 문자열을 다른 문자열로 먼저 치환할 수 있음
# 예외처리 목록에 등록된 항목은 모든 처리에서 제외됨

class ATExchanger:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # 처리할 원본 텍스트 (프롬프트 연결 또는 직접 입력)
                "text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "처리할 원본 프롬프트 텍스트"
                }),
                # 감지할 접두사 (예: @)
                "detect_prefix": ("STRING", {
                    "multiline": False,
                    "default": "@",
                    "tooltip": "감지할 접두사를 입력하세요 (예: @)"
                }),
                # 처리 방식 선택
                "mode": (["delete", "replace", "power_delete"], {
                    "tooltip": (
                        "delete: 접두사만 삭제 / "
                        "replace: 다른 접두사로 교체 / "
                        "power_delete: 접두사가 포함된 토큰 전체 삭제"
                    )
                }),
                # 교체할 접두사 (replace 모드일 때만 사용, 나머지 모드에서는 무시)
                "replacement_prefix": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "mode가 replace일 때 교체할 접두사 (공백 포함 그대로 입력)"
                }),
                # 예외처리 목록 (쉼표로 구분, 여기 등록된 항목은 모든 처리에서 제외)
                "exceptions": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "처리에서 제외할 항목을 쉼표로 구분하여 입력 (예: @_@, @keep)"
                }),
                # additional: 찾을 문자열 (main 처리보다 먼저 실행됨)
                "additional_prompt": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "이 문자열을 먼저 찾아서 additional_exchang으로 교체한 뒤 main 처리를 진행 / 비워두면 이 기능 비활성화"
                }),
                # additional: 교체할 문자열
                "additional_exchang": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "additional_prompt를 이 문자열로 교체 (공백 포함 그대로 입력)"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("Original_text", "Exchanged_text")
    FUNCTION = "exchange"
    CATEGORY = "utils/text"
    OUTPUT_NODE = False

    def exchange(self, text, detect_prefix, mode, replacement_prefix="", exceptions="",
                 additional_prompt="", additional_exchang=""):

        # Original_text: 입력받은 텍스트를 항상 그대로 출력
        original = text

        # 감지할 접두사가 비어있으면 그대로 반환
        if not detect_prefix:
            return (original, text)

        # 예외처리 목록 파싱 (쉼표 구분, 공백 trim)
        exception_list = []
        if exceptions.strip():
            exception_list = [e.strip() for e in exceptions.split(",") if e.strip()]

        # 예외 항목은 길이 내림차순 정렬 → 긴 것부터 먼저 매칭 (탐욕적 매칭)
        # 예: "@_@"와 "@_" 둘 다 있을 경우 "@_@"를 우선 매칭
        exception_list.sort(key=len, reverse=True)

        working = text

        # ── Step 1: additional_prompt 치환 (main 처리보다 반드시 먼저 실행) ──
        if additional_prompt.strip():
            working = working.replace(additional_prompt, additional_exchang)

        # ── Step 2: main mode 처리 ──────────────────────────────────────────
        if mode == "delete":
            result = self._process(working, detect_prefix, "", exception_list)

        elif mode == "replace":
            result = self._process(working, detect_prefix, replacement_prefix, exception_list)

        elif mode == "power_delete":
            result = self._power_delete(working, detect_prefix, exception_list)

        else:
            result = working

        return (original, result)

    # ── 접두사 치환 (delete / replace 공용) ──────────────────────────────────

    def _process(self, text, prefix, replacement, exceptions):
        """
        텍스트를 문자 단위로 순회하며 접두사를 감지하고 처리합니다.
        예외 목록에 해당하는 구간은 그대로 보존합니다.
        """
        result = []
        i = 0
        prefix_len = len(prefix)

        while i < len(text):
            if text[i:i + prefix_len] == prefix:
                # 예외 목록 중 현재 위치와 일치하는 항목 탐색 (길이 내림차순)
                matched_exception = None
                for exc in exceptions:
                    if text[i:i + len(exc)] == exc:
                        matched_exception = exc
                        break

                if matched_exception is not None:
                    # 예외 항목 → 원문 그대로 유지, 해당 길이만큼 건너뜀
                    result.append(matched_exception)
                    i += len(matched_exception)
                else:
                    # 접두사를 replacement로 교체 (삭제 시 빈 문자열)
                    result.append(replacement)
                    i += prefix_len
            else:
                result.append(text[i])
                i += 1

        return "".join(result)

    # ── power_delete: 접두사가 포함된 최상위 토큰 통째로 제거 ─────────────────

    def _power_delete(self, text, prefix, exceptions):
        """
        최상위 레벨 쉼표 기준으로 토큰을 분리한 뒤,
        예외 처리 후에도 접두사가 남아있는 토큰은 통째로 제거합니다.
        빈 쉼표가 남지 않도록 정리하여 재조합합니다.
        """
        tokens = self._split_top_level(text)
        kept = []

        for token in tokens:
            stripped = token.strip()
            if not stripped:
                continue
            # 예외를 고려한 뒤에도 접두사가 존재하면 토큰 전체 제거
            if self._contains_active_prefix(stripped, prefix, exceptions):
                continue
            kept.append(stripped)

        return ", ".join(kept)

    def _contains_active_prefix(self, token, prefix, exceptions):
        """
        sentinel 문자(\x00)로 치환 후 결과에 sentinel이 포함되어 있으면
        예외가 아닌 접두사가 존재한다고 판단합니다.
        """
        sentinel = "\x00"
        processed = self._process(token, prefix, sentinel, exceptions)
        return sentinel in processed

    def _split_top_level(self, text):
        """
        괄호/대괄호 깊이를 추적하여 최상위 레벨 쉼표로만 분리합니다.
        예: "a, (b, c), d" → ["a", " (b, c)", " d"]
        """
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
    "ATExchanger": ATExchanger
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ATExchanger": "AT Exchanger"
}
