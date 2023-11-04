import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup, NavigableString, Tag
from paraglide.data.models import (
    Statute,
    StatuteChapter,
    StatuteParagraph,
    StatuteSection,
    StructuredText,
    TextType,
)


class ParserError(Exception):
    pass


def get_cleaned_text(element: NavigableString | Tag) -> str:
    """Extracts the text from the given element and cleans it up.

    Args:
        element (Tag): The element to extract the text from

    Returns:
        str: The extracted text where all child tags are removed
        and any extra spaces or newlines are stripped.
    """
    if isinstance(element, NavigableString):
        raise ParserError(f"Element {element} is not a Tag.")

    # Remove all child tags within the element
    for child in element.find_all(True):
        child.extract()

    # Extracting the text and stripping any extra spaces or newlines
    return " ".join(element.get_text(strip=True).split())


def get_attr(tag: NavigableString | Tag, attr: str) -> str:
    """Get the value of the given attribute of the given tag.

    Args:
        tag (Tag): The tag to get the attribute value from.
        attr (str): The attribute to get the value of.

    Returns:
        str: The value of the attribute.

    Raises:
        ParserError: If the tag does not have the given attribute.
    """
    if isinstance(tag, NavigableString):
        raise ParserError(f"Tag {tag} does not have attribute {attr}")

    if attr in tag.attrs:
        return tag.attrs[attr]

    raise ParserError(f"Tag {tag} does not have attribute {attr}")


class RetsinformationStatuteParser:
    """A parser for parsing an HTML file from Retsinformation."""

    def __init__(self, file_path: Path) -> None:
        """Initializes the parser.

        Args:
            file_path (Path): The path to the HTML file to parse.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist")
        self._file_path = file_path

    def run(self) -> Statute:
        with open(self._file_path, "r") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
            return self._parse(soup)

    def _parse(self, soup: BeautifulSoup) -> Statute:
        id, date = self._extract_id_and_date(soup)
        title = self._extract_title(soup)
        chapters = self._parse_chapters(soup)

        return Statute(
            number=id,
            date=date,
            title=title,
            chapters=chapters,
        )

    def _extract_id_and_date(self, soup: BeautifulSoup) -> Tuple[int, datetime]:
        h5_elem = soup.find("h5", {"class": "d-sm-inline m-0 mr-sm-2"})
        if h5_elem is None:
            raise ParserError(
                'Could not find <h5> element with class "d-sm-inline m-0 mr-sm-2"'
            )

        id_date_str = h5_elem.text
        match = re.search(
            r"LBK\snr\s(\d{1,10})\saf\s(\d{2})\/(\d{2})\/(\d{4})", id_date_str
        )
        if match:
            number = int(match.group(1))
            date = datetime.strptime(
                match.group(2) + "/" + match.group(3) + "/" + match.group(4), "%d/%m/%Y"
            )
            return number, date

        raise ParserError(f'Could not extract ID and date from "{id_date_str}"')

    def _extract_title(self, soup: BeautifulSoup) -> str:
        p_element = soup.select_one("div.document-content p.Titel2")
        if p_element:
            return get_cleaned_text(p_element)

        raise ParserError(
            'Could not extract title. No <p> element with class "Titel2" found'
        )

    def _parse_chapters(self, soup: BeautifulSoup) -> List[StatuteChapter]:
        chapters: List[StatuteChapter] = []
        current_chapter: Optional[StatuteChapter] = None
        current_paragraph: Optional[StatuteParagraph] = None
        current_section: Optional[StatuteSection] = None

        p_elements = soup.select("div.document-content p")
        for p_elem in p_elements:
            if "Kapitel" in p_elem.get("class", []):
                current_chapter = self._parse_chapter(p_elem)
                chapters.append(current_chapter)
                current_paragraph = None
                current_section = None

            elif "Paragraf" in p_elem.get("class", []):
                if current_chapter is None:
                    raise ParserError("Found paragraph outside chapter")
                current_paragraph = self._parse_paragraph(p_elem)
                current_chapter.paragraphs.append(current_paragraph)
                current_section = None

            elif "Liste1" in p_elem.get("class", []):
                if current_paragraph is None:
                    raise ParserError("Found list outside paragraph")
                text_block = self._parse_list_block(p_elem=p_elem)

                # Text block always belongs to the leaf node.
                if current_section:
                    current_section.texts.append(text_block)
                else:
                    current_paragraph.texts.append(text_block)

            elif "Stk2" in p_elem.get("class", []):
                if current_paragraph is None:
                    raise ParserError("Found section outside paragraph")
                current_section = self._parse_section(p_elem=p_elem)
                current_paragraph.sections.append(current_section)

            elif "IkraftTekst" in p_elem.get("class", []):
                # We have reached the end of the document as the
                # "IkraftTekst" element describes other parts
                # of the statutory order.
                break

        return chapters

    def _parse_chapter(self, p_elem: Tag) -> StatuteChapter:
        guid = p_elem.get("id")
        span_chapter_elem = p_elem.find("span", id=lambda x: x and x.startswith("Kap"))
        if span_chapter_elem is None:
            raise ParserError(
                "Could not find <span> element with id starting with 'Kap'"
            )
        number = int(get_attr(span_chapter_elem, "id").replace("Kap", ""))

        next_p_elem = p_elem.find_next("p", class_="KapitelOverskrift2")
        if next_p_elem is None:
            raise ParserError(
                "Could not find <p> element with class 'KapitelOverskrift2'"
            )

        title = None

        if isinstance(next_p_elem, Tag):
            title_elem = next_p_elem.find("span")
            if title_elem is not None and isinstance(title_elem, Tag):
                title = get_cleaned_text(title_elem)

        if title is None:
            raise ParserError("Could not find title for chapter")

        return StatuteChapter(number=number, title=title, guid=guid, paragraphs=[])

    def _parse_paragraph(self, p_elem: Tag) -> StatuteParagraph:
        guid = p_elem.get("id")
        span_elem = p_elem.find("span", {"class": "ParagrafNr"})
        if span_elem is None:
            raise ParserError("Could not find <span> element with class 'ParagrafNr'")

        id = get_attr(span_elem, "id")
        text = get_cleaned_text(p_elem)
        reference = span_elem.get_text().replace(".", "")
        return StatuteParagraph(
            guid=guid,
            id=id,
            reference=reference,
            texts=[StructuredText(type=TextType.plain, text=text)],
            sections=[],
        )

    def _parse_list_block(self, p_elem: Tag) -> StructuredText:
        span_elem = p_elem.find("span", {"class": "Liste1Nr"})
        if span_elem is None:
            raise ParserError("Could not find <span> element with class 'Liste1Nr'")
        guid = get_attr(span_elem, "id")
        reference = span_elem.get_text()
        text = get_cleaned_text(p_elem)
        return StructuredText(
            type=TextType.list, text=text, guid=guid, reference=reference
        )

    def _parse_section(self, p_elem: Tag) -> StatuteSection:
        span_elem = p_elem.find("span", {"class": "StkNr"})
        if span_elem is None:
            raise ParserError("Could not find <span> element with class 'StkNr'")
        guid = get_attr(tag=span_elem, attr="id")
        reference = span_elem.get_text().strip()[:-1]
        text = get_cleaned_text(p_elem)
        return StatuteSection(
            guid=guid,
            reference=reference,
            texts=[StructuredText(type=TextType.plain, text=text)],
        )
