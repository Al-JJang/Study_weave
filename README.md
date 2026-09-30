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
| `/` | 공용 대시보드. `StudyWeave AI` 제목과 한 줄 설명, 업로드/노트 카드, 수업 내용 검색 |
| `/u/:userId` | 개인 작업 공간. 섹션 추가·이름 변경·삭제, 노트/업로드를 섹션으로 옮기기, 학습 도우미 |
| `/sources` | 선택한 사용자의 `user_id/YYYY-MM-DD` 폴더 트리 |
| `/notes` | 선택한 사용자의 학습 노트 목록 |
| `/notes/:id` | 노트 본문 |

사이드바에서 서영·송주·새결·동규를 고르면 `/u/{user_id}` 개인 책상으로 이동합니다. 선택은 `localStorage`에 남고, 노트/소스는 그 사용자만 보입니다.

챗봇(학습 도우미)은 개인 작업 공간에 있습니다. 키는 `config.get_chat_model`이 쓰는 `GEMINI_API_KEY`입니다. 없으면 챗봇이 안내 문구를 보여 줍니다.

## API

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| GET | `/api/health` | 헬스체크. `graph_available` 포함 |
| GET | `/api/users` | 팀원 목록 (서영, 송주, 새결, 동규) |
| GET/POST | `/api/sources` | 소스 목록 / 파일 업로드 (`user_id` 필수). 저장 경로 `data/uploads/{user_id}/{YYYY-MM-DD}/{filename}` |
| GET/POST | `/api/notes` | 노트 목록 / 빈 노트 생성. 노트 파일은 `data/notes/{user_id}/{YYYY-MM-DD}/` |
| GET | `/api/notes/{id}` | 노트 상세 |
| GET | `/api/jobs` | 업로드·노트 생성 작업 목록 |
| GET | `/api/desk` | 개인 책상 (`user_id` 필수). `data/desks/{user_id}/desk.json` |
| POST | `/api/desk/sections` | 섹션 추가 |
| PATCH | `/api/desk/sections/{id}` | 섹션 이름 변경 |
| DELETE | `/api/desk/sections/{id}` | 섹션 삭제 (항목은 미분류로) |
| POST | `/api/desk/move` | 노트/소스를 섹션으로 옮기거나 미분류로 |
| POST | `/api/chat` | 학습 도우미. SSE 스트림. 본문 `{ user_id, message, history }` |

업로드 시 `graph.supervisor.run_pipeline(use_mock=True)` 를 호출해 보고, 실패하면 placeholder 노트를 만듭니다. 그래프 파일은 수정하지 않습니다.

챗봇을 쓰려면 프로젝트 루트 `.env`에 `GEMINI_API_KEY`를 넣으세요. 모델 이름은 기존 `GEMINI_MODEL`(기본 `gemini-3.7-flash`)입니다.

## 테스트 · 린트

```bash
uv run ruff check .
uv run ruff format .
uv run pytest
cd frontend && npm test
```

의존성 추가: `fastapi`, `uvicorn[standard]`, `python-multipart` (HTTP API). 개발: `httpx` (TestClient).
