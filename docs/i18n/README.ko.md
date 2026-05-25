# ProjectLens

> 모든 코드베이스를 위한 단일 스캔 적응형 프로젝트 렌즈 + 토큰 최적화 컨텍스트 캡슐. AI 코딩 에이전트를 위한 오리엔테이션 토큰 70-90% 절감.

[English](../../README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · **한국어**

## 무엇입니까

ProjectLens는 **단일 스캔** (50-150ms)으로 모든 코드베이스를 다음으로 변환하는 플러그인입니다:

1. **`LENS.html`** — 사람이 30초 만에 읽을 수 있는 한 페이지 요약
2. **`LENS.capsule.md`** — 800-3,600 토큰 컨텍스트 블록. AI 에이전트가 30개 이상의 원본 파일을 읽는 **대신** 흡수합니다
3. **30개 프레임워크 어댑터** — 8개 생태계 팩 (AI 앱, AI UI, ML 코어, 서빙, 벡터 DB, 실험 추적, 엔터프라이즈, 노트북)

## 설치

```bash
# Claude Code / Cowork — projectlens.plugin을 채팅에 드래그&드롭
# Cursor / VS Code / Codex / Gemini CLI — MCP 서버
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / 스크립트 / CI — CLI
pip install projectlens
# 컨텍스트 파일을 읽는 도구 — AGENTS.md 모드
projectlens . --install-agents-md
```

## 주요 기능

- **적응형 깊이** (T1/T2/T3 자동 선택)
- **30개 프레임워크 어댑터** — PyTorch, LangChain, FastAPI, Pinecone 등
- **5개 세션 후크** (Claude Code) — 읽기 중복 제거, 활동 추적, 선택적 주입, 출력 압축, 메모리
- **대화 컴팩터** — 세션 중간에 8-25k 토큰 회수
- **순수 표준 라이브러리** — 런타임 종속성 없음

## 토큰 경제학

| 단계 | 절감 |
|---|---|
| 오리엔테이션 | **70-90%** |
| 재읽기 | **~25%** (긴 세션) |
| 프롬프트별 재주입 | **~60%** |
| 중간 압축 | **8-25k** 토큰 |

## 라이센스

MIT.
