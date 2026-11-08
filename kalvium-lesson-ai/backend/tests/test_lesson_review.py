from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_missing_lesson_edit_is_404_or_null():
    response = client.get('/lessons/999999/edit')
    assert response.status_code == 404


def test_edited_content_is_saved_and_retrieved():
    lessons = client.get('/lessons').json()
    if not lessons:
        return
    lesson = lessons[0]
    content = lesson['content']
    response = client.put(f"/lessons/{lesson['id']}/edit", json={"content": content, "note": "Verification save"})
    assert response.status_code == 200
    fetched = client.get(f"/lessons/{lesson['id']}/edit")
    assert fetched.status_code == 200
    assert fetched.json()['content'] == content


def test_markdown_export_includes_required_sections():
    lessons = client.get('/lessons').json()
    if not lessons:
        return
    lesson = lessons[0]
    response = client.get(f"/lessons/{lesson['id']}/export.markdown")
    assert response.status_code == 200
    text = response.text
    assert '# ' in text
    assert '## References' in text
    assert 'QC Agent 1' in text
    assert 'QC Agent 2' in text
