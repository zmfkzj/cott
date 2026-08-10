from curriculum.textfile_analysis import extract_casefolded_words
from curriculum.textfile_analysis_types import TextAnalysis


def analyze_text(text: str) -> TextAnalysis:
    words = extract_casefolded_words(text)
    seen: set[str] = set()
    seen.update(words)
    return TextAnalysis(
        total_lines=text.count("\n") + (1 if text else 0),
        total_characters=sum(1 for character in text if not character.isspace()),
        total_words=len(words),
        unique_words=len(seen),
        special_characters=sum(
            1
            for character in text
            if not character.isalnum() and not character.isspace()
        ),
    )
