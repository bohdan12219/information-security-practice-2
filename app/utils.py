import bleach

def sanitize_input(text: str | None) -> str | None:
    if not text:
        return text
    return bleach.clean(text, tags=[], attributes={}, strip=True)