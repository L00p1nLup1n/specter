import pytest
from parser.diff import parse_diff, parse_file_as_hunk, Hunk

SIMPLE_DIFF = """\
diff --git a/src/auth.py b/src/auth.py
index abc..def 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -10,3 +10,5 @@
 def login():
+    user = request.args.get('user')
+    query = "SELECT * FROM users WHERE name = '" + user + "'"
 pass
"""

MULTI_HUNK_DIFF = """\
diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1,2 +1,3 @@
 x = 1
+y = 2
@@ -10,2 +11,3 @@
 z = 3
+w = 4
diff --git a/b.py b/b.py
--- a/b.py
+++ b/b.py
@@ -5,1 +5,2 @@
 pass
+return None
"""

NO_ADDITIONS_DIFF = """\
diff --git a/x.py b/x.py
--- a/x.py
+++ b/x.py
@@ -1,3 +1,2 @@
-removed line
 kept line
"""


def test_parse_diff_basic():
    hunks = parse_diff(SIMPLE_DIFF)
    assert len(hunks) == 1
    assert hunks[0].filename == "src/auth.py"
    assert hunks[0].start_line == 10
    assert len(hunks[0].added_lines) == 2
    assert "request.args" in hunks[0].added_lines[0]


def test_parse_diff_multi_hunk():
    hunks = parse_diff(MULTI_HUNK_DIFF)
    filenames = [h.filename for h in hunks]
    assert "a.py" in filenames
    assert "b.py" in filenames
    # a.py has two hunks
    a_hunks = [h for h in hunks if h.filename == "a.py"]
    assert len(a_hunks) == 2


@pytest.mark.parametrize("diff_text", [
    "",
    NO_ADDITIONS_DIFF,
])
def test_parse_diff_returns_empty(diff_text):
    assert parse_diff(diff_text) == []


def test_parse_diff_raw_contains_context_lines():
    hunks = parse_diff(SIMPLE_DIFF)
    assert hunks[0].raw != ""


@pytest.mark.parametrize("filename,content,expected_lines,expected_raw", [
    ("foo/bar.py", "line one\nline two\nline three", ["line one", "line two", "line three"], "+line one\n+line two\n+line three"),
    ("x.py",      "a\nb",                           ["a", "b"],                              "+a\n+b"),
    ("empty.py",  "",                                [],                                      ""),
])
def test_parse_file_as_hunk(filename, content, expected_lines, expected_raw):
    hunks = parse_file_as_hunk(filename, content)
    assert len(hunks) == 1
    assert hunks[0].filename == filename
    assert hunks[0].start_line == 1
    assert hunks[0].added_lines == expected_lines
    assert hunks[0].raw == expected_raw
