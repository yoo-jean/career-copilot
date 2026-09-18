def chunk_text(text: str, max_chars: int = 900) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    def flush() -> None:
        nonlocal current
        if current:
            chunks.append(current)
            current = ""

    for para in paragraphs:
        if len(para) > max_chars:
            flush()
            for i in range(0, len(para), max_chars):
                chunks.append(para[i : i + max_chars])
            continue

        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) > max_chars:
            flush()
            current = para
        else:
            current = candidate

    flush()
    return chunks
