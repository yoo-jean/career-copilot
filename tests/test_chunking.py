from rag.chunking import chunk_text


def test_chunk_text_empty_returns_empty_list():
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []


def test_chunk_text_packs_small_paragraphs_together():
    text = "문단 하나.\n\n문단 둘.\n\n문단 셋."
    chunks = chunk_text(text, max_chars=900)
    assert len(chunks) == 1
    assert "문단 하나." in chunks[0]
    assert "문단 셋." in chunks[0]


def test_chunk_text_splits_when_exceeding_max_chars():
    para_a = "가" * 100
    para_b = "나" * 100
    chunks = chunk_text(f"{para_a}\n\n{para_b}", max_chars=150)
    assert len(chunks) == 2
    assert chunks[0] == para_a
    assert chunks[1] == para_b


def test_chunk_text_hard_splits_oversized_single_paragraph():
    long_para = "가" * 500
    chunks = chunk_text(long_para, max_chars=200)
    assert len(chunks) == 3
    assert all(len(c) <= 200 for c in chunks)
    assert "".join(chunks) == long_para
