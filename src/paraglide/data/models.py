from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, RootModel, model_validator


class TextType(Enum):
    plain = "plain"
    list = "list"


class StructuredText(BaseModel):
    """Represents a structured text."""

    type: TextType = Field(description="Type of the text")
    text: str = Field(description="The text")
    guid: Optional[str] = Field(default=None, description="A unique ID for the text")
    reference: Optional[str] = Field(
        default=None, description="A reference of the text"
    )

    @model_validator(mode="after")
    def checks_when_type_is_list(self) -> "StructuredText":
        """Check that the guid and reference are filled if the type is list."""

        if self.type == TextType.list:
            for v in [self.guid, self.reference]:
                if v is None:
                    raise ValueError(
                        "guid and reference must be filled if type is list"
                    )
        return self


class StatuteSection(BaseModel):
    guid: str = Field(description="A unique ID for the section")
    reference: str = Field(description="A reference to this section")
    texts: List[StructuredText] = Field(
        default_factory=list, description="The texts of this section"
    )


class StatuteParagraph(BaseModel):
    guid: str = Field(description="A unique ID for the paragraph")
    id: str = Field(description="The ID of the paragraph")
    reference: str = Field(description="A reference to this paragraph")
    texts: List[StructuredText] = Field(
        default_factory=list, description="The texts of this paragraph"
    )
    sections: List[StatuteSection] = Field(
        default_factory=list, description="The sections of this paragraph"
    )


class StatuteChapter(BaseModel):
    number: int = Field(description="The number of the chapter")
    title: str = Field(description="The title of the chapter")
    guid: str = Field(description="A unique ID for the chapter")
    paragraphs: List[StatuteParagraph] = Field(
        default_factory=list, description="The paragraphs of this chapter"
    )


class Statute(BaseModel):
    number: int = Field(description="The number of the statute")
    date: datetime = Field(description="The date of the statute")
    title: str = Field(description="The title of the statute")
    chapters: List[StatuteChapter] = Field(
        default_factory=list, description="The chapters of this statute"
    )

    @classmethod
    def from_json_file(cls, statute_path: Path) -> "Statute":
        """Load a statute from a JSON file.

        Args:
            statute_path (Path): path to the JSON file.

        Returns:
            Statute: the statute.
        """
        with open(statute_path, "r") as f:
            json_data = f.read()
            return cls.model_validate_json(json_data=json_data)


class ParagraphRef(BaseModel):
    """Represents a paragraph reference."""

    guid: str = Field(description="A unique ID for the paragraph")
    id: str = Field(description="The ID of the paragraph")
    ref: str = Field(description="A reference to this paragraph")


class ParagraphRefList(RootModel[List[ParagraphRef]]):
    """Represents a list of paragraph references."""

    root: List[ParagraphRef] = Field(
        default_factory=list, description="The list of paragraph references"
    )

    @classmethod
    def from_json_path(cls, file_path: str) -> "ParagraphRefList":
        with open(file_path) as fp:
            return cls.model_validate_json(json_data=fp.read())
