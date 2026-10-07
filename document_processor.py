#!/usr/bin/env python3
"""
Document processing for RFP Studio.

Provides:
- Text extraction from PDF, DOCX, and TXT files
- Heuristic question extraction
- Retrieval-based answer extraction
- Dependency and capability reporting

Optional dependencies:
    pip install PyPDF2 python-docx

OCR is not implemented by this module.
"""

from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path
from typing import Any, Callable, TypedDict

from rfp_studio.vector import embed_text, search_knowledge_base

# Optional document dependencies.
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph
except ImportError:
    Document = None
    Table = None
    Paragraph = None

# Report OCR dependencies independently. They are not used for extraction.
try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import pytesseract
except ImportError:
    pytesseract = None


logger = logging.getLogger(__name__)

SearchResult = dict[str, Any]

DEFAULT_SEARCH_LIMIT = 3
DEFAULT_QUESTION_LIMIT = 50
DEFAULT_MAX_ANSWER_LENGTH = 500


class AnswerResult(TypedDict, total=False):
    """Dictionary returned by AnswerGenerator.generate_answer()."""

    success: bool
    question: str
    answer: str
    error: str
    retrieval_score: float
    confidence: float  # Legacy alias for retrieval_score, not a probability.
    sources: list[str]
    search_results: list[SearchResult]


class DocumentProcessor:
    """Extract text from supported document formats."""

    def __init__(self) -> None:
        self._extractors: dict[str, Callable[[Path], str]] = {
            ".pdf": self._extract_pdf_text,
            ".docx": self._extract_docx_text,
            ".txt": self._extract_txt_text,
        }

    @property
    def supported_formats(self) -> list[str]:
        """Formats whose required Python dependencies are installed."""
        dependencies = {
            ".pdf": PdfReader is not None,
            ".docx": Document is not None,
            ".txt": True,
        }
        return [
            extension
            for extension in self._extractors
            if dependencies[extension]
        ]

    def extract_text(self, file_path: str | Path) -> str:
        """Extract text, raising an exception if the file cannot be read."""
        path = self._validate_path(file_path)
        extractor = self._extractors.get(path.suffix.lower())

        if extractor is None:
            raise ValueError(
                f"Unsupported file format: {path.suffix or '(no extension)'}"
            )

        return extractor(path)

    def get_page_count(self, file_path: str | Path) -> int | None:
        """
        Return the PDF page count, or None if it cannot be determined.

        DOCX pagination depends on layout and rendering. Plain-text files
        do not have an intrinsic page count.
        """
        path = self._validate_path(file_path)

        if path.suffix.lower() != ".pdf" or PdfReader is None:
            return None

        try:
            with path.open("rb") as file:
                return len(PdfReader(file).pages)
        except Exception:
            logger.warning(
                "Could not determine page count for %s",
                path,
                exc_info=True,
            )
            return None

    @staticmethod
    def _validate_path(file_path: str | Path) -> Path:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if not path.is_file():
            raise ValueError(f"Not a regular file: {path}")

        return path

    @staticmethod
    def _extract_pdf_text(path: Path) -> str:
        """
        Extract embedded PDF text.

        Individual page failures are logged and skipped, allowing partial
        extraction. Image-only pages require OCR, which is not implemented.
        """
        if PdfReader is None:
            raise ImportError(
                "PDF processing requires PyPDF2. "
                "Install it with: pip install PyPDF2"
            )

        parts: list[str] = []

        with path.open("rb") as file:
            reader = PdfReader(file)

            for page_number, page in enumerate(reader.pages, start=1):
                try:
                    text = (page.extract_text() or "").strip()
                except Exception:
                    logger.warning(
                        "Could not extract page %d from %s",
                        page_number,
                        path,
                        exc_info=True,
                    )
                    continue

                if text:
                    parts.append(
                        f"--- Page {page_number} ---\n{text}"
                    )

        return "\n\n".join(parts)

    @staticmethod
    def _extract_docx_text(path: Path) -> str:
        """
        Extract body paragraphs and tables in document order.

        Headers, footers, text boxes, and nested tables are not included.
        """
        if Document is None:
            raise ImportError(
                "DOCX processing requires python-docx. "
                "Install it with: pip install python-docx"
            )

        document = Document(path)
        parts: list[str] = []

        # Walking body elements also supports python-docx versions that
        # predate Document.iter_inner_content().
        for element in document.element.body.iterchildren():
            tag = element.tag.rsplit("}", 1)[-1]

            if tag == "p":
                paragraph = Paragraph(element, document)
                text = paragraph.text.strip()

                if text:
                    parts.append(text)

            elif tag == "tbl":
                table = Table(element, document)

                for row in table.rows:
                    cells = [cell.text.strip() for cell in row.cells]

                    if any(cells):
                        # Keep empty cells to preserve column positions.
                        parts.append(" | ".join(cells))

        return "\n\n".join(parts)

    @staticmethod
    def _extract_txt_text(path: Path) -> str:
        """Read UTF-8 text, falling back to Latin-1."""
        try:
            # utf-8-sig also removes a UTF-8 BOM if one is present.
            return path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            logger.debug("Falling back to Latin-1 for %s", path)
            return path.read_text(encoding="latin-1")


class QuestionExtractor:
    """
    Extract likely questions and RFP instructions using regex heuristics.

    This is not a full sentence parser. Abbreviations, complex numbering,
    and questions wrapped across lines may require additional handling.
    """

    _PATTERN_TEXTS = (
        # A question at a line or sentence boundary, optionally numbered.
        r"(?:^|(?<=[.!?]))[ \t]*"
        r"(?:\d+[.)][ \t]*)?"
        r"[^.!?\n]*\?",

        # RFP instructions, including those without terminal punctuation.
        r"\b(?:Please[ \t]+)?"
        r"(?:describe|explain|provide|list|identify|specify|detail)\b"
        r"[ \t]+[^.!?\n]*(?:[.!?]|(?=\n|$))",

        # Questions that may follow headings or other text.
        r"\b(?:What|How|Where|When|Why|Who|Which)\b"
        r"[ \t]+[^.!?\n]*(?:[.!?]|(?=\n|$))",

        r"\b(?:Do|Does|Can|Could|Will|Would|Should|Is|Are)\b"
        r"[ \t]+[^.!?\n]*(?:[.!?]|(?=\n|$))",
    )

    _PATTERNS = tuple(
        re.compile(pattern, re.IGNORECASE | re.MULTILINE)
        for pattern in _PATTERN_TEXTS
    )

    _PAGE_MARKER = re.compile(
        r"^[ \t]*--- Page \d+ ---[ \t]*$",
        re.MULTILINE,
    )

    _LEADING_LABEL = re.compile(
        r"^\s*(?:[•·*-]\s*|\d+(?:\.\d+)*[.)]\s*)"
    )

    def __init__(
        self,
        max_questions: int = DEFAULT_QUESTION_LIMIT,
        min_question_length: int = 11,
    ) -> None:
        if max_questions < 1:
            raise ValueError("max_questions must be at least 1")

        if min_question_length < 1:
            raise ValueError("min_question_length must be at least 1")

        self.max_questions = max_questions
        self.min_question_length = min_question_length

    def extract_questions(self, text: str) -> list[str]:
        """Return unique questions in document order."""
        clean_text = self._clean_text(text)

        # For matches with the same start position, prefer the longest.
        matches = sorted(
            (
                match
                for pattern in self._PATTERNS
                for match in pattern.finditer(clean_text)
            ),
            key=lambda match: (match.start(), -match.end()),
        )

        questions: list[str] = []
        seen: set[str] = set()
        previous_end = -1

        for match in matches:
            # Avoid returning nested fragments of an accepted question.
            if match.start() < previous_end:
                continue

            question = self._clean_question(match.group())

            if len(question) < self.min_question_length:
                continue

            previous_end = match.end()

            # Ignore case and terminal punctuation when deduplicating.
            key = question.casefold().rstrip(".?!").strip()

            if key in seen:
                continue

            seen.add(key)
            questions.append(question)

            if len(questions) >= self.max_questions:
                break

        return questions

    @classmethod
    def _clean_text(cls, text: str) -> str:
        """Normalize whitespace without discarding line boundaries."""
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = cls._PAGE_MARKER.sub("\n", text)
        text = re.sub(r"[^\S\n]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @classmethod
    def _clean_question(cls, question: str) -> str:
        """Remove list labels and normalize question whitespace."""
        question = cls._LEADING_LABEL.sub("", question)
        question = re.sub(r"\s+", " ", question).strip()

        if question and not question.endswith((".", "?", "!")):
            question += "?"

        return question


class AnswerGenerator:
    """
    Retrieve supporting text and extract an answer from the top result.

    This class does not perform LLM synthesis.

    The score threshold assumes results are sorted best-first and that
    higher scores indicate greater relevance. Verify that contract with
    your search backend before using the default threshold.
    """

    def __init__(
        self,
        search_limit: int = DEFAULT_SEARCH_LIMIT,
        max_answer_length: int = DEFAULT_MAX_ANSWER_LENGTH,
    ) -> None:
        if search_limit < 1:
            raise ValueError("search_limit must be at least 1")

        if max_answer_length < 1:
            raise ValueError("max_answer_length must be at least 1")

        self.search_limit = search_limit
        self.max_answer_length = max_answer_length

    def generate_answer(
        self,
        question: str,
        confidence_threshold: float = 0.7,
    ) -> AnswerResult:
        """
        Extract an answer if the top result meets the score threshold.

        `confidence_threshold` retains its original name for compatibility;
        it is a retrieval-score threshold, not a confidence probability.
        """
        question = question.strip()

        if not question:
            return self._failure(question, "Question cannot be empty")

        try:
            embedding = embed_text(question)
            results = list(
                search_knowledge_base(
                    embedding,
                    limit=self.search_limit,
                )
                or []
            )

            if not results:
                return self._failure(
                    question,
                    "No relevant knowledge found",
                )

            top_result = results[0]
            raw_score = top_result.get("score")

            if raw_score is None:
                return self._failure(
                    question,
                    "Top search result has no retrieval score",
                    search_results=results,
                )

            score = float(raw_score)

            # NaN also fails this comparison rather than passing the gate.
            if not score >= confidence_threshold:
                return self._failure(
                    question,
                    (
                        f"Retrieval score does not meet threshold: "
                        f"{score:.3f} "
                        f"(required: {confidence_threshold:.3f})"
                    ),
                    search_results=results,
                    retrieval_score=score,
                )

            answer = self._extract_answer(top_result)

            if not answer:
                return self._failure(
                    question,
                    "Top search result contains no usable answer text",
                    search_results=results,
                    retrieval_score=score,
                )

            return {
                "success": True,
                "question": question,
                "answer": answer,
                "retrieval_score": score,
                "confidence": score,
                # Only cite the result actually used for the answer.
                "sources": self._extract_sources([top_result]),
                "search_results": results,
            }

        except Exception:
            # Keep this catch at the frontend-facing boundary. Log the
            # traceback without exposing backend details to the UI.
            logger.exception("Error generating answer")

            return self._failure(
                question,
                "Unable to generate an answer. Check application logs.",
            )

    def _extract_answer(self, result: SearchResult) -> str:
        """Extract the first answer section, or use the result's full text."""
        text = result.get("text")

        if not isinstance(text, str) or not text.strip():
            return ""

        text = text.strip()

        # Support sources formatted as "Q: ... A: ...".
        answer_marker = re.search(
            r"(?:^|\s)A:[ \t]*",
            text,
            re.IGNORECASE,
        )

        if answer_marker:
            text = text[answer_marker.end():].strip()

            # Avoid including a subsequent Q&A entry.
            next_question = re.search(
                r"^\s*Q:",
                text,
                re.IGNORECASE | re.MULTILINE,
            )

            if next_question:
                text = text[:next_question.start()].strip()

        return self._truncate_answer(text)

    def _truncate_answer(self, text: str) -> str:
        """Truncate long text, preferring a nearby sentence boundary."""
        if len(text) <= self.max_answer_length:
            return text

        # Reserve one character for the ellipsis if needed.
        prefix = text[: self.max_answer_length - 1].rstrip()

        sentence_ends = list(
            re.finditer(r"[.!?](?=\s|$)", prefix)
        )

        if sentence_ends:
            end = sentence_ends[-1].end()

            if end >= self.max_answer_length * 0.7:
                return prefix[:end]

        # Prefer a word boundary if it is near the cutoff.
        word_end = prefix.rfind(" ")

        if word_end >= self.max_answer_length * 0.7:
            prefix = prefix[:word_end]

        return prefix.rstrip() + "…"

    @staticmethod
    def _extract_sources(results: list[SearchResult]) -> list[str]:
        """Format source labels for the results used in an answer."""
        sources: list[str] = []

        for result in results:
            team = result.get("team_key") or "Unknown Team"
            topic = result.get("topic") or "General Knowledge"
            score = float(result.get("score") or 0.0)

            sources.append(
                f"{team} - {topic} (score: {score:.3f})"
            )

        return sources

    @staticmethod
    def _failure(
        question: str,
        error: str,
        *,
        search_results: list[SearchResult] | None = None,
        retrieval_score: float | None = None,
    ) -> AnswerResult:
        """Build a consistent failure response."""
        result: AnswerResult = {
            "success": False,
            "question": question,
            "error": error,
        }

        if search_results is not None:
            result["search_results"] = search_results

        if retrieval_score is not None:
            result["retrieval_score"] = retrieval_score
            result["confidence"] = retrieval_score

        return result


def validate_dependencies() -> dict[str, bool]:
    """Report which optional Python dependencies imported successfully."""
    return {
        "PyPDF2": PdfReader is not None,
        "python-docx": Document is not None,
        "PIL": Image is not None,
        "pytesseract": pytesseract is not None,
    }


def _tesseract_executable_found() -> bool:
    """Check PATH or pytesseract's configured executable location."""
    if pytesseract is None:
        return False

    command = pytesseract.pytesseract.tesseract_cmd
    return shutil.which(str(command)) is not None


def get_processing_capabilities() -> dict[str, Any]:
    """Describe available extraction features and optional dependencies."""
    dependencies = validate_dependencies()
    processor = DocumentProcessor()

    tesseract_found = _tesseract_executable_found()
    ocr_dependencies_available = (
        dependencies["PIL"]
        and dependencies["pytesseract"]
        and tesseract_found
    )

    return {
        "supported_formats": [
            extension.removeprefix(".")
            for extension in processor.supported_formats
        ],
        "dependencies": dependencies,
        "tesseract_executable_found": tesseract_found,
        # Dependency detection does not verify an operational OCR setup.
        "ocr_dependencies_available": ocr_dependencies_available,
        "ocr_implemented": False,
        "ocr_available": False,
    }


def main() -> None:
    """Print processing capabilities when executed directly."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    capabilities = get_processing_capabilities()

    print("Document Processing Capabilities:")
    print(
        "Supported formats: "
        + ", ".join(capabilities["supported_formats"])
    )
    print(f"Dependencies: {capabilities['dependencies']}")
    print(
        "Tesseract executable found: "
        f"{capabilities['tesseract_executable_found']}"
    )
    print("OCR available: False (not implemented)")


if __name__ == "__main__":
    main()
