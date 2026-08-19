"""
Embeds (`![[Title]]`) need no backend changes -- they reuse the existing
[[Title]] wiki-link extraction (backend/utils/wiki_parser.py's regex
doesn't care what precedes "[[", so a leading "!" doesn't stop a match),
which means an embed also creates a real backlink, same as a plain
link. This test exists to pin that behavior down explicitly rather than
leave it as an unstated assumption the frontend embeds feature depends
on.
"""


def test_embed_syntax_creates_a_real_backlink(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    target = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "Target"}).json()
    client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "Source", "content": "See ![[Target]] below."})

    backlinks = client.get(f"/api/notebooks/chapters/{target['id']}/backlinks").json()
    assert any(b["title"] == "Source" for b in backlinks)
