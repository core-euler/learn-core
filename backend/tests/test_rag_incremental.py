import json

from backend.app.retrieval import (
    compute_curriculum_content_signature,
    load_curriculum_chunks,
)


def _write_index(root, md_rel_path: str = 'content/m1/l1.md'):
    index = {
        'version': '1.0.0',
        'modules': [
            {
                'slug': 'm1',
                'title': 'M1',
                'order_index': 1,
                'full_chapter': 'content/m1/00_full_chapter.md',
                'lessons': [
                    {
                        'slug': 'l1',
                        'title': 'L1',
                        'order_index': 1,
                        'md_file_path': md_rel_path,
                        'type': 'theory',
                        'difficulty': 'beginner',
                        'prerequisites': [],
                        'tags': ['intro'],
                    }
                ],
            }
        ],
    }
    index_path = root / 'content' / 'index.json'
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index), encoding='utf-8')
    return index_path


def test_curriculum_signature_changes_when_markdown_changes(tmp_path):
    repo_root = tmp_path
    md_path = repo_root / 'content' / 'm1' / 'l1.md'
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text('First version of lesson', encoding='utf-8')
    (repo_root / 'content' / 'm1' / '00_full_chapter.md').write_text('chapter', encoding='utf-8')
    index_path = _write_index(repo_root)

    first = compute_curriculum_content_signature(
        index_path=index_path,
        repo_root=repo_root,
        chunk_size_chars=900,
        chunk_overlap_chars=120,
        embed_model='text-embedding-3-small',
    )

    md_path.write_text('Second version of lesson with updates', encoding='utf-8')
    second = compute_curriculum_content_signature(
        index_path=index_path,
        repo_root=repo_root,
        chunk_size_chars=900,
        chunk_overlap_chars=120,
        embed_model='text-embedding-3-small',
    )

    assert first != second


def test_load_curriculum_chunks_respects_chunking(tmp_path):
    repo_root = tmp_path
    md_path = repo_root / 'content' / 'm1' / 'l1.md'
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text('abcdef' * 20, encoding='utf-8')
    (repo_root / 'content' / 'm1' / '00_full_chapter.md').write_text('chapter', encoding='utf-8')
    index_path = _write_index(repo_root)

    chunks = load_curriculum_chunks(
        index_path=index_path,
        repo_root=repo_root,
        chunk_size_chars=30,
        chunk_overlap_chars=10,
    )

    assert len(chunks) >= 2
    assert chunks[0].metadata.chunk_id == 'm1:l1:1'
    assert chunks[0].metadata.source_path == 'content/m1/l1.md'
    assert chunks[0].metadata.start_char == 0
