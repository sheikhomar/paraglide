from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pytest
from paraglide.data.models import (
    ParagraphRefList,
    Statute,
    StatuteChapter,
    StatuteParagraph,
    TextType,
)
from paraglide.parsers.retsinformation import RetsinformationStatuteParser


def find_chapter_by_number(
    chapters: List[StatuteChapter], number: int
) -> StatuteChapter:
    for chapter in chapters:
        if chapter.number == number:
            return chapter
    assert False, f"Expected chapter {number} to be present, but it was not"


@pytest.fixture(scope="session")
def parsed_status_order() -> Statute:
    file_input = Path("data/eli-lta-2023-1180.html")
    parser = RetsinformationStatuteParser(
        file_path=file_input,
    )
    return parser.run()


@pytest.fixture(scope="session")
def parsed_1180_paragraphs(parsed_status_order: Statute) -> Dict[str, StatuteParagraph]:
    output: Dict[str, StatuteParagraph] = dict()
    for chapter in parsed_status_order.chapters:
        for paragraph in chapter.paragraphs:
            output[paragraph.id] = paragraph
    return output


def test_id(parsed_status_order: Statute) -> None:
    assert parsed_status_order.number == 1180


def test_date(parsed_status_order: Statute) -> None:
    assert parsed_status_order.date == datetime(2023, 9, 21, 0, 0)


def test_title(parsed_status_order: Statute) -> None:
    assert (
        parsed_status_order.title
        == "Bekendtgørelse af lov om ret til orlov og dagpenge ved barsel (barselsloven)"
    )


def test_number_of_chapters(parsed_status_order: Statute) -> None:
    assert (
        len(parsed_status_order.chapters) == 14
    ), f"Expected 14 chapters, but got {len(parsed_status_order.chapters)}"


@pytest.mark.parametrize(
    "expected_number,expected_title",
    [
        (1, "Formål"),
        (
            2,
            "Afgrænsning af personkredsen, der har ret til fravær og barselsdagpenge efter denne lov",
        ),
        (3, "Ophold og beskatning her i landet"),
        (4, "Ret til fravær i forbindelse med graviditet, fødsel og adoption m.v."),
        (5, "Ret til barselsdagpenge og ret til overdragelse af orlov m.v."),
        (6, "Beskæftigelseskrav"),
        (7, "Den dagpengeberettigedes ansøgning om barselsdagpenge"),
        (8, "Beregningsgrundlaget for barselsdagpenge"),
        (9, "Barselsdagpengenes størrelse"),
        (10, "Refusion og finansiering m.v."),
        (
            11,
            "Indbetaling m.v. til Arbejdsmarkedets Tillægspension og den obligatoriske pensionsordning",
        ),
        (12, "Administration m.v."),
        (13, "Klageregler"),
        (14, "Ikrafttrædelses- og overgangsbestemmelser"),
    ],
)
def test_chapter_numbers_and_titles(
    expected_number: int, expected_title: str, parsed_status_order: Statute
) -> None:
    chapter = find_chapter_by_number(parsed_status_order.chapters, expected_number)
    assert (
        chapter.title == expected_title
    ), f"Expected chapter {expected_number} title to be '{expected_title}', but got '{chapter.title}'"


@pytest.mark.parametrize(
    "expected_number,expected_guid",
    [
        (1, "id99994932-66a2-41d8-9cfd-2afba1db881f"),
        (2, "id3cbe62ea-e69f-4a95-a5aa-cca6e2c35710"),
        (3, "idf004e9a0-6301-4bf9-8d27-374dd6754f85"),
        (4, "id17228e7c-6fad-4fd1-87ca-3254b9246836"),
        (5, "idac3c39b9-2487-4ceb-9d26-b954c0d3dd1a"),
        (6, "id59128810-2edd-45c9-bb5d-67c4cd0dd5e8"),
        (7, "ide8c0d607-35e8-4732-8ef8-c59c91906fc1"),
        (8, "id28d52d67-959f-4870-96db-e24c982f30f5"),
        (9, "idad1bd018-ccac-44f4-abb3-e951209b1323"),
        (10, "idd9c3015d-9820-4a9d-9f85-a3c54b36895d"),
        (11, "id464c8587-409f-4b1f-844d-8d75b8f4eb2a"),
        (12, "id9dc8081d-78cd-4368-9535-54ac62468801"),
        (13, "idb60344a5-f07f-46c1-974a-f116508796b5"),
        (14, "id14f0ceb5-c3f6-46e5-913d-9a1b6abfceee"),
    ],
)
def test_chapter_numbers_and_guids(
    expected_number: int, expected_guid: str, parsed_status_order: Statute
) -> None:
    chapter = find_chapter_by_number(parsed_status_order.chapters, expected_number)
    assert (
        chapter.guid == expected_guid
    ), f"Expected chapter {expected_number} guid to be '{expected_guid}', but got '{chapter.guid}'"


@pytest.mark.parametrize(
    "chapter_number,expected_number_of_paragraphs",
    [
        (1, 1),
        (2, 1),
        (3, 3),
        (4, 15),
        (5, 19),
        (6, 3),
        (7, 2),
        (8, 3),
        (9, 5),
        (10, 8),
        (11, 6),
        (12, 12),
        (13, 1),
        (14, 3),
    ],
)
def test_chapter_has_correct_number_of_paragraphs(
    chapter_number: int,
    expected_number_of_paragraphs: int,
    parsed_status_order: Statute,
) -> None:
    chapter = find_chapter_by_number(parsed_status_order.chapters, chapter_number)
    assert (
        len(chapter.paragraphs) == expected_number_of_paragraphs
    ), f"Expected chapter {chapter_number} to have {expected_number_of_paragraphs} paragraphs, but got {len(chapter.paragraphs)}"


def test_all_paragraph_references_are_extracted_correctly(
    parsed_1180_paragraphs: Dict[str, StatuteParagraph],
) -> None:
    known_paragraph_refs = ParagraphRefList.from_json_path(
        file_path="data/eli-lta-2023-1180-paragraph-refs.json"
    ).root
    for expected_ref in known_paragraph_refs:
        parsed_paragraph = parsed_1180_paragraphs.get(expected_ref.id)
        assert (
            parsed_paragraph is not None
        ), f"Expected paragraph '{expected_ref.id}' to have been parsed, but was not the case. Got None."
        assert (
            parsed_paragraph.id == expected_ref.id
        ), f"Mismatched ID. Expected '{expected_ref.id}', but got '{parsed_paragraph.id}'."
        assert (
            parsed_paragraph.guid == expected_ref.guid
        ), f"Mismatched Guid. Expected '{expected_ref.guid}', but got '{parsed_paragraph.guid}'."
        assert (
            parsed_paragraph.reference == expected_ref.ref
        ), f"Mismatched Ref. Expected '{expected_ref.ref}', but got '{parsed_paragraph.reference}'."


@pytest.mark.parametrize(
    "paragraph_id,intro_text",
    [
        (
            "Par5",
            """
        Personer med ophold her i landet
        eller indkomst omfattet af § 4, stk. 1, kan ikke opnå barselsdagpenge, hvis de efter
        et andet lands lovgivning eller efter lovgivningen for Færøerne eller Grønland har
        ret til dagpenge eller anden erstatning for tab af indtægt eller de efter
        EF-forordninger om koordinering af de sociale sikringsordninger er omfattet af en
        anden medlemsstats lovgivning om social sikring.
        """,
        ),
        (
            "Par21",
            """
        Ved fravær efter §§ 9 og 10 har en
        mor ret til barselsdagpenge i 14 uger, og en far eller medmor har ret til
        barselsdagpenge i 22 uger indtil 1 år efter barnets fødsel eller modtagelse, jf. dog
        §§ 21 a-21 c. Begge adoptanter har hver ret til barselsdagpenge i 18 uger indtil 1
        år efter barnets modtagelse, jf. dog §§ 21 a-21 c.
        """,
        ),
    ],
)
def test_paragraph_introductory_text_is_parsed_correctly(
    paragraph_id: str,
    intro_text: str,
    parsed_1180_paragraphs: Dict[str, StatuteParagraph],
) -> None:
    parsed_paragraph = parsed_1180_paragraphs.get(paragraph_id)
    assert (
        parsed_paragraph is not None
    ), f"Expected paragraph '{paragraph_id}' to have been parsed, but was not the case. Got None."
    cleaned_intro_text = " ".join(intro_text.split())
    assert parsed_paragraph.texts[0].text == cleaned_intro_text, "Wrong text parsed."


def test_each_paragraph_has_at_least_one_text_block(
    parsed_1180_paragraphs: Dict[str, StatuteParagraph],
) -> None:
    for paragraph in parsed_1180_paragraphs.values():
        assert (
            len(paragraph.texts) >= 1
        ), f"Expected paragraph '{paragraph.id}' to have at least one text block, but it has {len(paragraph.texts)}."


def test_each_paragraph_texts_are_not_empty(
    parsed_1180_paragraphs: Dict[str, StatuteParagraph],
) -> None:
    for paragraph in parsed_1180_paragraphs.values():
        for text_block in paragraph.texts:
            assert (
                len(text_block.text.strip()) >= 1
            ), f"Expected texts of '{paragraph.id}' to be not empty, but got '{text_block.text}'"


def test_paragraph_1_has_three_text_blocks(
    parsed_1180_paragraphs: Dict[str, StatuteParagraph],
) -> None:
    paragraph = parsed_1180_paragraphs.get("Par1")
    assert (
        paragraph is not None
    ), "Expected paragraph 'Par1' to have been parsed, but was not the case. Got None."
    assert (
        len(paragraph.texts) == 3
    ), f"Expected paragraph 'Par1' to have 3 text blocks, but it has {len(paragraph.texts)}."


@pytest.mark.parametrize(
    "paragraph_id,text_index,expected_ref,expected_guid",
    [
        ("Par1", 1, "1)", "id72049405-e25c-48e4-b368-fcfdef747c9d"),
        ("Par1", 2, "2)", "id7b58a518-2f13-48ca-8732-fa497e0634bb"),
        ("Par49b", 6, "6)", "ida2c8b090-09b9-4da2-b251-31b1aa2450c8"),
    ],
)
def test_paragraph_list_block_is_parsed_correctly(
    paragraph_id: str,
    text_index: int,
    expected_ref: str,
    expected_guid: str,
    parsed_1180_paragraphs: Dict[str, StatuteParagraph],
) -> None:
    paragraph = parsed_1180_paragraphs.get(paragraph_id)
    assert (
        paragraph is not None
    ), f"Expected paragraph '{paragraph_id}' to have been parsed, but was not the case. Got None."
    list_block = paragraph.texts[text_index]
    assert (
        list_block.type == TextType.list
    ), f"Expected list type, but got {list_block.type}"
    assert (
        list_block.guid == expected_guid
    ), f"Expected GUID '{expected_guid}' but got {list_block.guid}."
    assert (
        list_block.reference == expected_ref
    ), f"Expected reference '{expected_ref}' but got {list_block.reference}."


def test_paragraph_4_has_no_list_blocks(
    parsed_1180_paragraphs: Dict[str, StatuteParagraph],
) -> None:
    paragraph = parsed_1180_paragraphs.get("Par4")
    assert (
        paragraph is not None
    ), "Expected paragraph 'Par4' to have been parsed, but was not the case. Got None."
    assert (
        len(paragraph.texts) == 1
    ), f"Expected paragraph 'Par4' to have 1 text block, but it has {len(paragraph.texts)}."
    assert (
        paragraph.texts[0].type == TextType.plain
    ), f"Expected paragraph 'Par4' to have plain text, but it has {paragraph.texts[0].type}."


@pytest.mark.parametrize(
    "paragraph_id,section_index,expected_ref,expected_guid",
    [
        ("Par49b", 1, "Stk. 3", "ide70570a2-6ab6-43f6-bd4b-f06944d0aebd"),
        ("Par55", 0, "Stk. 2", "id08a6a8d8-917d-4a4b-ae98-39c1ec4fbe73"),
        ("Par53a", 0, "Stk. 2", "id4ba46852-23b1-487d-8b24-8fc899e83408"),
    ],
)
def test_paragraph_has_correct_section(
    paragraph_id: str,
    section_index: int,
    expected_ref: str,
    expected_guid: str,
    parsed_1180_paragraphs: Dict[str, StatuteParagraph],
) -> None:
    paragraph = parsed_1180_paragraphs.get(paragraph_id)
    assert (
        paragraph is not None
    ), f"Expected paragraph '{paragraph_id}' to have been parsed, but was not the case. Got None."
    section = paragraph.sections[section_index]
    assert (
        section.guid == expected_guid
    ), f"Expected GUID '{expected_guid}' but got {section.guid}."
    assert (
        section.reference == expected_ref
    ), f"Expected reference '{expected_ref}' but got {section.reference}."


@pytest.mark.parametrize(
    "paragraph_id,text_index,list_text",
    [
        (
            "Par49b",
            2,
            """
        Sygedagpenge fra kommunen efter lov om sygedagpenge.
        """,
        ),
        (
            "Par49b",
            7,
            """
        Integrationsydelse, selvforsørgelses- og hjemrejseydelse, overgangsydelse,
        uddannelseshjælp, kontanthjælp, revalideringsydelse, ressourceforløbsydelse i
        ressourceforløb, ressourceforløbsydelse i jobafklaringsforløb eller ledighedsydelse
        efter lov om aktiv socialpolitik.
        """,
        ),
        (
            "Par47a",
            2,
            """
        Fra den 4. januar 2021 med 0,6 pct.
        """,
        ),
        (
            "Par47a",
            11,
            """
        Fra den 7. januar 2030 med 3,3 pct.
        """,
        ),
    ],
)
def test_paragraph_list_text_is_parsed_correctly(
    paragraph_id: str,
    text_index: int,
    list_text: str,
    parsed_1180_paragraphs: Dict[str, StatuteParagraph],
) -> None:
    parsed_paragraph = parsed_1180_paragraphs.get(paragraph_id)
    assert (
        parsed_paragraph is not None
    ), f"Expected paragraph '{paragraph_id}' to have been parsed, but was not the case. Got None."

    list_block = parsed_paragraph.texts[text_index]
    cleaned_text = " ".join(list_text.split())
    assert (
        list_block.type == TextType.list
    ), f"Expected list type, but got {list_block.type}"
    assert list_block.text == cleaned_text, "Wrong text is parsed."


@pytest.mark.parametrize(
    "paragraph_id,section_ref,text_index,list_text",
    [
        (
            "Par33",
            "Stk. 2",
            1,
            """
        opgørelse af timefortjenesten efter stk. 1, herunder placeringen af indberettede
        løntimer og indkomst, omregning af indkomst m.v.,
        """,
        ),
        (
            "Par33",
            "Stk. 2",
            7,
            """
        fravigelse af § 35, stk. 1, for lønmodtagere med skiftende arbejdstid.
        """,
        ),
        (
            "Par27",
            "Stk. 2",
            6,
            """
        modtaget godtgørelse i en opsigelsesperiode fra Lønmodtagernes Garantifond.
        """,
        ),
    ],
)
def test_section_list_text_is_parsed_correctly(
    paragraph_id: str,
    section_ref: str,
    text_index: int,
    list_text: str,
    parsed_1180_paragraphs: Dict[str, StatuteParagraph],
) -> None:
    parsed_paragraph = parsed_1180_paragraphs.get(paragraph_id)
    assert (
        parsed_paragraph is not None
    ), f"Expected paragraph '{paragraph_id}' to have been parsed, but was not the case. Got None."

    parsed_section = [
        section
        for section in parsed_paragraph.sections
        if section.reference == section_ref
    ][0]

    assert (
        parsed_section is not None
    ), f"Expected section '{section_ref}' in paragraph '{paragraph_id}' to have been parsed, but was not the case. Got None."

    list_block = parsed_section.texts[text_index]
    cleaned_text = " ".join(list_text.split())
    assert (
        list_block.type == TextType.list
    ), f"Expected list type, but got {list_block.type}"
    assert list_block.text == cleaned_text, "Wrong text is parsed."
