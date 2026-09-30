# StudyWeave AI

팀원끼리 쓰는 학습 노트 도구. 수업 PDF와 코드를 올리면 개념·코드 흐름·퀴즈 노트로 묶습니다.

이 브랜치(WEAVE-28)는 **React + FastAPI UI 뼈대**입니다. 기존 LangGraph 워커(`workers/`, `graph/` 로직)는 그대로 두고, API는 헬스체크·업로드·노트/작업 목록만 얇게 감쌉니다. 그래프가 mock이거나 없어도 placeholder로 화면이 동작합니다.

인증, 결제, 앱스토어, 실시간 전사는 없습니다.

## 로컬 실행

Python 3.11, [uv](https://docs.astral.sh/uv/), Node.js 필요.

```bash
git clone https://github.com/Al-JJang/Study_weave.git
cd Study_weave
git checkout feature/WEAVE-28-ui-skeleton
uv sync
```

터미널 1 — API (포트 `43181`):

```bash
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 43181
```

터미널 2 — 프론트 (포트 `43180`):

```bash
cd frontend
npm install
npm run dev
```

브라우저에서 [http://127.0.0.1:43180](http://127.0.0.1:43180) 을 엽니다. Vite가 `/api` 요청을 FastAPI로 프록시합니다.

기존 Streamlit 스텁은 `streamlit run app.py` 그대로이며, 이번 UI와는 별개입니다.

## 화면

| 경로 | 내용 |
| --- | --- |
| `/` | 대시보드. 인사, StudyWeave가 학습에 도움이 되는 방식, 소스 업로드 / 새 노트 / 노트 열기 카드, 검색 |
| `/sources` | 업로드한 소스 목록 (empty / loading / error) |
| `/notes` | 학습 노트 목록 |
| `/notes/:id` | 노트 본문 |

## API

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| GET | `/api/health` | 헬스체크. `graph_available` 포함 |
| GET/POST | `/api/sources` | 소스 목록 / 파일 업로드 |
| GET/POST | `/api/notes` | 노트 목록 / 빈 노트 생성 |
| GET | `/api/notes/{id}` | 노트 상세 |
| GET | `/api/jobs` | 업로드·노트 생성 작업 목록 |

업로드 시 `graph.supervisor.run_pipeline(use_mock=True)` 를 호출해 보고, 실패하면 placeholder 노트를 만듭니다. 그래프 파일은 수정하지 않습니다.

## 테스트 · 린트

```bash
uv run ruff check .
uv run ruff format .
uv run pytest
cd frontend && npm test
```

의존성 추가: `fastapi`, `uvicorn[standard]`, `python-multipart` (HTTP API). 개발: `httpx` (TestClient).
