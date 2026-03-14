from pathlib import Path

ASSETS_DIR = Path(__file__).parent / "assets"
FREQ_FILE = ASSETS_DIR / "kontext-freq_download-2026-03-14.txt"

WORD_LEN = 5
MIN_FREQ = 17


def load_word_list() -> list[str]:
    """Parse the KonText frequency file and return 5-letter lowercase Czech words.

    Filters:
    - Frequency >= MIN_FREQ
    - Starts with a lowercase letter (excludes proper nouns and place names)
    """
    words: list[str] = []
    with FREQ_FILE.open(encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            if lineno <= 2:  # skip header lines
                continue
            line = raw.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            word = parts[0]
            try:
                freq = int(parts[1])
            except ValueError:
                continue
            if freq < MIN_FREQ:
                continue
            if word[0].isupper():
                continue
            words.append(word.lower())

    return words


WORD_LIST: list[str] = load_word_list()
