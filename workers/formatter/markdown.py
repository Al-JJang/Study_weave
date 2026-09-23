"""
D — Markdown 본문 포맷터.

목차:
    개념 정리 → 코드 분석 → 흐름도 → 참조표
    → 이론-코드 연결 → Practice Notes → Quiz

토글:
    Quiz 정답 및 해설은 <details> 태그 사용

빈 섹션:
    config.EMPTY_SECTION_POLICY
    - "omit": 섹션 제목과 내용 모두 생략
    - "placeholder": 섹션 제목과 안내 문구 출력

연동:
    읽음 ← schemas.state.AgentState
    읽음 ← C 분석 산출 + quiz_items
    씀 → final_markdown
"""

from __future__ import annotations

import config
from schemas.state import AgentState


def _format_source_chunk_ids(
    source_chunk_ids: list[str],
) -> str:
    """근거 Chunk ID 목록을 일반 Markdown 문자열로 변환합니다.

    Args:
        source_chunk_ids: 항목의 근거 Chunk ID 목록.

    Returns:
        근거 Chunk ID를 표시하는 Markdown 문자열.
    """

    if not source_chunk_ids:
        return ""

    joined_ids = ", ".join(source_chunk_ids)

    return f"**근거 Chunk:** {joined_ids}"


def _append_section(
    sections: list[str],
    title: str,
    contents: list[str],
) -> None:
    """빈 섹션 정책에 따라 Markdown 섹션을 추가합니다.

    Args:
        sections: 완성된 Markdown 섹션을 저장할 목록.
        title: Markdown 섹션 제목.
        contents: 해당 섹션에 포함할 Markdown 블록 목록.
    """

    if contents:
        sections.append(
            "\n\n".join(
                [
                    f"## {title}",
                    *contents,
                ]
            )
        )
        return

    if config.EMPTY_SECTION_POLICY == "placeholder":
        sections.append(
            "\n\n".join(
                [
                    f"## {title}",
                    "_표시할 내용이 없습니다._",
                ]
            )
        )


def _format_concepts(
    state: AgentState,
) -> list[str]:
    """개념 분석 결과를 Markdown으로 변환합니다.

    Args:
        state: concepts가 포함된 AgentState.

    Returns:
        개념별 Markdown 블록 목록.
    """

    blocks: list[str] = []

    for concept in state.get("concepts", []):
        lines = [
            f"### {concept.title}",
            concept.summary,
        ]

        if concept.formula:
            lines.extend(
                [
                    "",
                    "$$",
                    concept.formula,
                    "$$",
                ]
            )

        if concept.related_code_refs:
            lines.extend(
                [
                    "",
                    "**관련 코드**",
                    *[f"- `{code_ref}`" for code_ref in concept.related_code_refs],
                ]
            )

        if concept.needs_verification:
            lines.extend(
                [
                    "",
                    "**확인 필요:** 이미지/비전 기반 추출 결과가 포함되어 있습니다.",
                ]
            )

        source_info = _format_source_chunk_ids(concept.source_chunk_ids)

        if source_info:
            lines.extend(
                [
                    "",
                    source_info,
                ]
            )

        blocks.append("\n".join(lines))

    return blocks


def _format_code_units(
    state: AgentState,
) -> list[str]:
    """코드 분석 결과를 Markdown으로 변환합니다.

    Args:
        state: code_units가 포함된 AgentState.

    Returns:
        코드 단위별 Markdown 블록 목록.
    """

    blocks: list[str] = []

    for unit in state.get("code_units", []):
        lines = [
            f"### `{unit.unit_name}`",
            f"- 유형: `{unit.unit_type}`",
            f"- 실행 흐름: {unit.execution_flow}",
        ]

        if unit.key_points:
            lines.extend(
                [
                    "",
                    "**핵심 포인트**",
                    *[f"- {point}" for point in unit.key_points],
                ]
            )

        source_info = _format_source_chunk_ids(unit.source_chunk_ids)

        if source_info:
            lines.extend(
                [
                    "",
                    source_info,
                ]
            )

        blocks.append("\n".join(lines))

    return blocks


def _format_flows(
    state: AgentState,
) -> list[str]:
    """흐름도 분석 결과를 Markdown으로 변환합니다.

    Args:
        state: flows가 포함된 AgentState.

    Returns:
        흐름도별 Markdown 블록 목록.
    """

    blocks: list[str] = []

    for flow in state.get("flows", []):
        lines = [
            f"### {flow.title}",
            f"- 범위: `{flow.scope}`",
            "",
            flow.description,
            "",
            "```text",
            flow.diagram,
            "```",
        ]

        if flow.needs_verification:
            lines.extend(
                [
                    "",
                    "**확인 필요:** 이미지/비전 기반 추출 결과가 포함되어 있습니다.",
                ]
            )

        source_info = _format_source_chunk_ids(flow.source_chunk_ids)

        if source_info:
            lines.extend(
                [
                    "",
                    source_info,
                ]
            )

        blocks.append("\n".join(lines))

    return blocks


def _escape_table_cell(
    value: str,
) -> str:
    """Markdown 표 안의 파이프 문자를 이스케이프합니다.

    Args:
        value: Markdown 표 셀에 들어갈 문자열.

    Returns:
        파이프 문자가 이스케이프된 문자열.
    """

    return value.replace("|", "\\|")


def _format_tables(
    state: AgentState,
) -> list[str]:
    """참조표 분석 결과를 Markdown 표로 변환합니다.

    Args:
        state: tables가 포함된 AgentState.

    Returns:
        참조표별 Markdown 블록 목록.
    """

    blocks: list[str] = []

    for table in state.get("tables", []):
        lines = [
            f"### {table.title}",
        ]

        if table.columns:
            header = (
                "| " + " | ".join(_escape_table_cell(column) for column in table.columns) + " |"
            )

            separator = "| " + " | ".join("---" for _ in table.columns) + " |"

            lines.extend(
                [
                    "",
                    header,
                    separator,
                ]
            )

            for row in table.rows:
                row_values = [_escape_table_cell(str(value)) for value in row]

                lines.append("| " + " | ".join(row_values) + " |")

        source_info = _format_source_chunk_ids(table.source_chunk_ids)

        if source_info:
            lines.extend(
                [
                    "",
                    source_info,
                ]
            )

        blocks.append("\n".join(lines))

    return blocks


def _format_cross_references(
    state: AgentState,
) -> list[str]:
    """이론과 코드의 교차 참조 결과를 Markdown으로 변환합니다.

    concept_ref는 가능한 경우 concept_id에 대응하는 개념 제목으로
    변환하여 사람이 읽기 쉬운 형태로 표시합니다.

    Args:
        state: concepts와 cross_references가 포함된 AgentState.

    Returns:
        교차 참조별 Markdown 블록 목록.
    """

    blocks: list[str] = []

    concept_titles = {concept.concept_id: concept.title for concept in state.get("concepts", [])}

    for reference in state.get(
        "cross_references",
        [],
    ):
        lines = [
            f"### `{reference.ref_type}`",
        ]

        if reference.concept_ref:
            concept_title = concept_titles.get(
                reference.concept_ref,
                reference.concept_ref,
            )

            lines.append(f"- 개념: {concept_title} (`{reference.concept_ref}`)")

        if reference.code_ref:
            lines.append(f"- 코드: `{reference.code_ref}`")

        lines.extend(
            [
                "",
                reference.explanation,
            ]
        )

        source_info = _format_source_chunk_ids(reference.source_chunk_ids)

        if source_info:
            lines.extend(
                [
                    "",
                    source_info,
                ]
            )

        blocks.append("\n".join(lines))

    return blocks


def _format_practice_notes(
    state: AgentState,
) -> list[str]:
    """Practice Note 분석 결과를 Markdown으로 변환합니다.

    Args:
        state: practice_notes가 포함된 AgentState.

    Returns:
        Practice Note별 Markdown 블록 목록.
    """

    blocks: list[str] = []

    for note in state.get(
        "practice_notes",
        [],
    ):
        lines = [
            f"### `{note.note_type}`",
            f"- 범위: `{note.scope}`",
            "",
            note.content,
        ]

        if note.caution:
            lines.extend(
                [
                    "",
                    f"**주의:** {note.caution}",
                ]
            )

        source_info = _format_source_chunk_ids(note.source_chunk_ids)

        if source_info:
            lines.extend(
                [
                    "",
                    source_info,
                ]
            )

        blocks.append("\n".join(lines))

    return blocks


def _format_quiz_items(
    state: AgentState,
) -> list[str]:
    """복습 퀴즈를 Markdown으로 변환합니다.

    객관식과 True/False 문제는 선택지를 표시하고,
    단답형은 문제만 표시합니다.
    정답과 해설은 details 태그 내부에 숨깁니다.

    Args:
        state: quiz_items가 포함된 AgentState.

    Returns:
        퀴즈별 Markdown 블록 목록.
    """

    blocks: list[str] = []

    for index, quiz in enumerate(
        state.get("quiz_items", []),
        start=1,
    ):
        lines = [
            f"### Q{index}. {quiz.question}",
        ]

        if quiz.quiz_type == "mcq":
            lines.append("")

            for option_index, option in enumerate(
                quiz.options,
            ):
                option_label = chr(ord("A") + option_index)

                lines.append(f"- {option_label}. {option}")

        elif quiz.quiz_type == "true_false":
            lines.extend(
                [
                    "",
                    *[f"- {option}" for option in quiz.options],
                ]
            )

        lines.extend(
            [
                "",
                "<details>",
                "<summary>정답 및 해설</summary>",
                "",
                f"**정답:** {quiz.answer}",
                "",
                quiz.explanation,
                "",
                "</details>",
            ]
        )

        source_info = _format_source_chunk_ids(quiz.source_chunk_ids)

        if source_info:
            lines.extend(
                [
                    "",
                    source_info,
                ]
            )

        blocks.append("\n".join(lines))

    return blocks


def format_markdown(
    state: AgentState,
) -> str:
    """C 분석 결과와 QuizItem을 최종 Markdown 문서로 변환합니다.

    Args:
        state: C 분석 결과와 quiz_items가 포함된 AgentState.

    Returns:
        각 분석 섹션이 포함된 최종 Markdown 문자열.
    """

    sections: list[str] = []

    _append_section(
        sections,
        "개념 정리",
        _format_concepts(state),
    )

    _append_section(
        sections,
        "코드 분석",
        _format_code_units(state),
    )

    _append_section(
        sections,
        "흐름도",
        _format_flows(state),
    )

    _append_section(
        sections,
        "참조표",
        _format_tables(state),
    )

    _append_section(
        sections,
        "이론-코드 연결",
        _format_cross_references(state),
    )

    _append_section(
        sections,
        "Practice Notes",
        _format_practice_notes(state),
    )

    _append_section(
        sections,
        "Quiz",
        _format_quiz_items(state),
    )

    markdown = "\n\n".join(sections).strip()

    if not markdown:
        return ""

    return markdown + "\n"
