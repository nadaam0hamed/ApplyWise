from enum import Enum


class KnowledgeSource(str, Enum):
    STATIC = "static"
    APPLICATION = "application"


class DocumentSourceType(str, Enum):
    PDF = "pdf"
    TEXT = "text"
    URL = "url"
