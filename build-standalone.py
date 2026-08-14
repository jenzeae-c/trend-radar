#!/usr/bin/env python3
"""index.html -> standalone.html

index.html은 Pretendard를 jsDelivr에서 불러온다(가볍고 웹 배포용).
standalone.html은 그 폰트를 파일 안에 통째로 넣어 인터넷 없이도 동일하게 보이게 한다.

사용법:  python3 build-standalone.py
"""

import base64
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "index.html"
DST = ROOT / "standalone.html"
CACHE = ROOT / ".pretendard.woff2"          # .gitignore 처리됨

FONT_URL = (
    "https://cdn.jsdelivr.net/npm/pretendard@1.3.9"
    "/dist/web/variable/woff2/PretendardVariable.woff2"
)

# index.html 안의 CDN @import 한 줄
IMPORT_RE = re.compile(
    r'^[ \t]*@import url\("https://cdn\.jsdelivr\.net/gh/orioncactus/pretendard[^"]*"\);[ \t]*\n',
    re.MULTILINE,
)


def fetch_font() -> bytes:
    """폰트를 내려받아 캐시한다.

    macOS 기본 파이썬에는 CA 인증서가 없는 경우가 많아 urllib 대신 curl을 쓴다.
    """
    if CACHE.exists() and CACHE.stat().st_size > 1_000_000:
        return CACHE.read_bytes()

    if shutil.which("curl") is None:
        sys.exit("curl 을 찾을 수 없습니다.")

    print(f"폰트 내려받는 중… {FONT_URL}")
    try:
        subprocess.run(
            ["curl", "-fsSL", "--max-time", "180", "-o", str(CACHE), FONT_URL],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        sys.exit(f"폰트 다운로드 실패 (curl 종료 코드 {e.returncode}).")

    data = CACHE.read_bytes()
    if len(data) < 1_000_000 or data[:4] != b"wOF2":
        CACHE.unlink(missing_ok=True)
        sys.exit(f"폰트 파일이 이상합니다 ({len(data)} bytes). URL을 확인하세요.")
    return data


def main() -> None:
    if not SRC.exists():
        sys.exit(f"{SRC} 가 없습니다.")

    html = SRC.read_text(encoding="utf-8")
    if not IMPORT_RE.search(html):
        sys.exit(
            "index.html에서 Pretendard @import 줄을 찾지 못했습니다.\n"
            "폰트 로딩 방식을 바꿨다면 이 스크립트의 IMPORT_RE도 같이 고쳐 주세요."
        )

    b64 = base64.b64encode(fetch_font()).decode("ascii")
    face = (
        "  @font-face {\n"
        '    font-family: "Pretendard Variable";\n'
        f'    src: url(data:font/woff2;base64,{b64}) format("woff2-variations");\n'
        "    font-weight: 45 920;\n"
        "    font-style: normal;\n"
        "    font-display: swap;\n"
        "  }\n"
    )

    DST.write_text(IMPORT_RE.sub(lambda _: face, html, count=1), encoding="utf-8")
    print(f"완료: {DST.name}  ({DST.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
