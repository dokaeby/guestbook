"""외부 API 없이 설정 파일을 읽는 금지어 검사. 설정 변경 후 서버를 재시작합니다."""
import json
import re
import unicodedata
from pathlib import Path

POLICY_MESSAGE = "비속어·욕설 또는 성적인 표현이 포함되어 등록할 수 없습니다. 내용을 수정해 주세요."


def normalized(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    return "".join(char for char in text if unicodedata.category(char) not in {"Cf", "Mn", "Me"})


def compact(text: str) -> str:
    return unicodedata.normalize("NFKC", "".join(char for char in normalized(text) if char.isalnum()))


class TextPolicy:
    def __init__(self, path: Path):
        config = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(config, dict) or not config:
            raise ValueError("금지어 설정에는 하나 이상의 분류가 필요합니다.")
        self.fragments = []
        self.patterns = []
        for rules in config.values():
            if not isinstance(rules, dict) or set(rules) != {"contains", "words"}:
                raise ValueError("금지어 분류에는 contains와 words 목록이 필요합니다.")
            for kind, terms in rules.items():
                if not isinstance(terms, list):
                    raise ValueError("금지어는 문자열 목록이어야 합니다.")
                for term in terms:
                    if not isinstance(term, str) or not term.strip() or len(term) > 80:
                        raise ValueError("금지어는 비어 있지 않은 80자 이하 문자열이어야 합니다.")
                    cleaned = compact(term)
                    if not cleaned:
                        raise ValueError("금지어에는 문자나 숫자가 있어야 합니다.")
                    if kind == "contains":
                        self.fragments.append(cleaned)
                    else:
                        # 문자열을 정규식으로 실행하지 않고 문자별로 이스케이프합니다.
                        letters = r"[\W_]*".join(re.escape(char) for char in normalized(term))
                        boundary = r"a-z0-9" if cleaned.isascii() else r"\w"
                        self.patterns.append(re.compile("(?<![" + boundary + "])" + letters + "(?![" + boundary + "])"))

    def blocked(self, value: str) -> bool:
        text = normalized(value)
        joined = compact(value)
        # '씨1발' 같은 숫자 삽입도 contains 규칙에서 검사합니다.
        no_digits = "".join(char for char in joined if not char.isdecimal())
        if any(term in joined or term in no_digits for term in self.fragments):
            return True
        english_leet = text.translate(str.maketrans("013457", "oieast"))
        return any(pattern.search(text) or pattern.search(english_leet) for pattern in self.patterns)


POLICY = TextPolicy(Path(__file__).with_name("moderation.json"))


def validate_text(value: str) -> str:
    if POLICY.blocked(value):
        raise ValueError(POLICY_MESSAGE)
    return value
