# AGENTS.md

Spec for the `wfs` codebase. Machine-enforced rules live in tooling; rules that
cannot be machine-enforced live here and are upheld by agents and reviewers.

## Agent switches

Agents read these. Flip a value to turn an agent off.

| Agent | State |
|-------|-------|
| custodian | active |

`custodian: inactive` means the Custodian must exit immediately without reading
or changing anything.

## Enforcement tiers

A rule is encoded at the highest tier it fits. The Legislator picks the tier;
the Custodian enforces whatever exists.

1. **Lint** — `ruff` (`pyproject.toml` → `[tool.ruff.lint] select`).
2. **semgrep** — `.semgrep.yml`, for AST patterns ruff cannot express.
3. **This file** — for rules too semantic to express as a pattern. Enforced by
   agent review, not tooling.

## Ignore directives

A violation carrying one of these is *intentional*. Never "fix" it.

- `# noqa` / `# noqa: RULE` — ruff
- `# ruff: noqa` — file-level ruff
- `# pyright: ignore[rule]` / `# type: ignore` — basedpyright
- `# nosemgrep` / `# nosemgrep: rule-id` — semgrep
- `per-file-ignores` in `pyproject.toml`

---

# Rules

## R001 — Construct dicts with the `dict()` callable, not the `{}` literal

**Tier:** 3 (this file — unenforced by tooling)

Build dictionaries with the `dict()` builtin rather than a brace literal, wherever
the two are interchangeable.

```python
# good
out = dict()
cfg = dict(host="localhost", port=8080)

# bad
out = {}
cfg = {"host": "localhost", "port": 8080}
```

**Rationale:** Author preference — the `dict()` form is easier to write by hand
and easier to read. This is *not* a performance or correctness claim; `dict()` is
in fact marginally slower (a global name lookup). Stated by the repo owner.

**Why tier 3 (no tool enforces this):** No ruff rule enforces the `{}` → `dict()`
direction. Every related rule enforces the *inverse* and would rewrite the code
this rule mandates back into `{}` literals:

- `C408` unnecessary-collection-call — rewrites `dict()` / `dict(a=1)` → `{}` / `{"a": 1}`
- `C406` unnecessary-literal-dict — rewrites `dict([(1, 2)])` → `{1: 2}`
- `C418` unnecessary-literal-within-dict-call — rewrites `dict({"x": 1})` → `{"x": 1}`

(`PIE804` is *not* one of them — see the compatibility note below.)

Verified on fixtures with ruff 0.15.20: `dict(a=1)` is flagged by `C408`; the
`{"a": 1}` literal this rule wants is flagged by *no* ruff rule (`--select ALL`
returns only unrelated docstring lints). Because the only expressible tooling runs
counter to the rule, and the exceptions below are semantic (they depend on what a
call *binds to*, not on syntax), this rule cannot be reduced to a lint code or a
semgrep pattern without generating false positives on its own exception cases.

**The `C4` / flake8-comprehensions group may NEVER be enabled** in
`[tool.ruff.lint] select`. Enabling `C408` (or `C406`/`C418`) turns this rule
into its opposite and would flag every existing `dict()` call in the codebase.

**`PIE804` is compatible and may be enabled.** It targets `**`-unpacking of a
dict *literal* into a call — `f(**{"bar": 2})` → `f(bar=2)` — which removes a
`{}` literal in favor of kwargs, the same direction as this rule. Verified on
fixtures: `PIE804` flags `f(**{"bar": 2})` and `dict(**{"bar": 2})`, and does
not flag `dict(bar=1)` or a plain `{"bar": 1}` literal. It never rewrites a
`dict()` call into a literal.

**Exceptions** — cases where a `{}` literal is correct and must NOT be rewritten:

1. **`F.dict({...})` positional-mapping form** (load-bearing, `src/wfs/models/serializers.py`).
   `DictSerializer.__init__(self, fields=None, *, null, default, required, read_only,
   write_only, **field_kwargs)` takes its field map either positionally or as
   `**field_kwargs`. The keyword-only option names (`fields`, `null`, `default`,
   `required`, `read_only`, `write_only`) are reserved. To declare a *field*
   whose name collides with one of those options you MUST pass the map positionally
   as a `{}` literal:

   ```python
   F.dict({"required": F.string()})   # a field literally named "required"
   F.dict(required=F.string())        # sets the serializer's `required` OPTION
   ```

   Verified at runtime: the first yields `fields == {"required": ...}`; the second
   yields `fields == {}` and binds `required` to the option. Rewriting the `{}`
   away (to `F.dict(required=...)`) silently changes semantics. Any `{}` literal
   passed as the positional `fields` argument to `F.dict(...)` stays a literal.

2. **Non-string keys** — `{1: "x"}`, `{obj: "y"}`. Cannot be expressed as
   `dict(key=value)` keyword arguments. Stays a literal.

3. **Non-identifier string keys** — `{"content-type": v}`, `{"a b": v}`. Not
   valid Python identifiers, so not expressible as kwargs. Stays a literal.

4. **`**`-unpacking of a possibly non-string-keyed mapping** — `{**m, "k": v}` is
   only safely `dict(**m, k=v)` when `m` is guaranteed to have string keys; when
   that is not guaranteed, leave the literal.

Out of scope (this rule does not apply): **set literals** (`{"a", "b"}` — a set,
not a dict) and **dict comprehensions** (`{k: v for ...}` — no `dict()`-callable
equivalent that preserves the comprehension). Do not flag these.

## R002 — No explicit tests for drivers; drivers are tested implicitly

**Tier:** 3 (this file — unenforced by tooling)

Do not write tests whose *subject* is the driver layer (`src/wfs/drivers/`). No
dedicated driver test modules (e.g., `tests/test_s3_driver.py`) and no test
functions that construct a driver, mock the vendor SDK underneath it, and assert
on the driver's calls into that SDK. Drivers are covered *implicitly*: by
higher-layer tests (controller/endpoint tests that pass through the driver) and,
where real credentials are available, by exercising the app against a live
backend.

```python
# bad — the test's subject IS the driver: mocks the vendor SDK, asserts on it
def test_upload_file_sets_content_type():
    driver = S3Driver(settings)
    driver._client = MagicMock()          # mock boto3 under the driver
    driver.upload_file("k", b"data", content_type="text/plain")
    driver._client.upload_fileobj.assert_called_once()

# good — the test's subject is the ENDPOINT; the driver is a stubbed dependency
def test_upload_endpoint_stores_object():
    app = create_app()
    fake = MagicMock()
    app.dependency_overrides[get_driver] = lambda: fake
    resp = TestClient(app).put("/objects/k", content=b"data")
    assert resp.status_code == 201
    fake.upload_file.assert_called_once()
```

**Rationale:** The driver layer is a deliberately thin wrapper over a vendor API
(boto3/S3). An explicit unit test for it must mock the vendor SDK, at which point
the test asserts that the mock was called the way the implementation calls it —
it restates the implementation and verifies nothing about real behavior. The
driver's correctness is only meaningful against the real backend, which
higher-layer flows exercise. Stated by the repo owner. Precedent: an explicit
`tests/test_s3_driver.py` existed briefly and was deleted; the driver's
test-injection constructor seam (`client=None`) was removed at the same time —
do not reintroduce either.

**Why tier 3 (no tool enforces this):** No ruff rule can express "a test module
may not target this package." The plausible tier-2 encoding — a semgrep rule
flagging `from wfs.drivers... import ...` / `import wfs.drivers...` inside
`tests/` — is a false-positive generator, verified on fixtures: a *forbidden*
explicit driver test and an *allowed* endpoint test both contain the identical
line `from wfs.drivers.s3 import get_driver` (the allowed test needs the symbol
as the key for `app.dependency_overrides[get_driver]`). The rule turns on what a
test *exercises and asserts on*, not on what it imports — a semantic distinction
no import- or path-based pattern can draw. Filename-based patterns
(`tests/test_*driver*`) fail the same way in both directions: trivially evadable
by renaming, and wrong on a legitimately named higher-layer file.

**Allowed** — none of these are "explicit driver tests":

1. **Overriding the driver as a dependency** of the layer under test —
   `app.dependency_overrides[get_driver] = ...`,
   `monkeypatch.setattr("wfs.drivers.s3.get_driver", ...)`, or passing a stub
   driver into higher-layer code. Importing driver symbols (`get_driver`,
   `S3Driver`) for this purpose is fine.
2. **Higher-layer tests** (controllers, services) that pass through real driver
   code as a side effect of exercising their own subject.
3. **Asserting on a stub driver's received calls** from a higher-layer test
   (e.g., `fake.upload_file.assert_called_once()`) — the assertion's subject is
   the caller, not the driver.

## R003 — Do not comment what the code already says; comment only a non-obvious *why*

**Tier:** 3 (this file — unenforced by tooling)

A comment must carry information the code cannot. Do not write a comment that
restates what the adjacent line already says — a comment like that is noise, and
noise costs the next reader attention while teaching them nothing. A comment is
warranted in exactly two cases:

1. It explains a non-obvious **why** — a constraint, a gotcha, or the reason a
   surprising line is correct.
2. The repo owner **explicitly asked** for a comment.

Absent both, write no comment. The default is silence, not narration.

```python
# good — states an external constraint the code cannot (src/wfs/drivers/s3.py)
self._client = boto3.client(
    "s3",
    region_name=settings.s3_region,
    # R2 only accepts SigV4-signed requests.
    config=Config(signature_version="s3v4"),
)

# good — names the gotcha that makes a surprising line correct
# (src/wfs/models/serializers.py). Nothing in the code says why `bool` is
# singled out; the reader would otherwise read the check as redundant.
# bool is a subclass of int; reject it explicitly.
if isinstance(value, bool) or not isinstance(value, int):
    return False, f"expected an integer, got {type(value).__name__}"

# bad — restates the line verbatim
# Increment the counter by one.
counter += 1

# bad — restates the name and the annotation
# The bucket name.
bucket: str = "wfs"

# bad — narrates control flow the reader can already see
# Loop over the items.
for item in settings.items:
    ...

# bad — labels the mechanics without giving the reason. `type(self)` already
# says "class attribute"; the comment never says why class level is required.
# class attribute, not instance level
schema = type(self).schema
```

Compliance is not always deletion. When a redundant comment sits on a line that
*does* have a non-obvious reason behind it, the fix is to replace the restatement
with that reason. When there is no such reason, delete it.

**Rationale:** A comment that paraphrases its own line adds a second thing to
read and a second thing to keep true when the code changes — it decays into a
lie the moment the line is edited, and the reader must diff prose against code
to notice. Comments earn their place only by saying something the code cannot:
why a constraint exists, why an odd line is right. Stated by the repo owner ("do
not add comments to things that explain themselves or unless explicitly told").
This is a preference about what belongs in the source, not a correctness claim.

**Why tier 3 (no tool enforces this):** The predicate is "this prose is
redundant with the adjacent code," which requires reading English against Python
and judging whether the former adds information. No lint can do this, and the
second clause — "unless explicitly told" — is strictly worse: it turns on
whether the repo owner asked for the comment, a fact that exists nowhere in the
source tree and is unavailable to any checker in principle.

Verified against ruff 0.16.0 (the installed version; note R001's evidence was
gathered under 0.15.20). Searching all **968** rules — names, summaries, and
explanations — for "comment" returns nothing about redundancy. Every
comment-aware rule is lexical or syntactic:

- `ERA001` commented-out-code — commented-out *code*, not redundant prose
- `PLR2044` empty-comment — a `#` with nothing after it
- `E261`/`E262`/`E265`/`E266` — spacing and `#` count
- `RUF003` — ambiguous Unicode inside a comment
- `TD001`–`TD007`, `FIX001`–`FIX004` — `TODO`/`FIXME` tag hygiene

Run with `--select ALL` (all 968 rules) on a fixture holding six redundant
comments, ruff reports **zero** diagnostics against any comment — only unrelated
`D100`/`D103` (missing docstrings), `ANN001`/`ANN201`, `CPY001`, `INP001`, and
`F821`. Not one diagnostic points at a comment.

`ERA001` is the closest rule and is **not** a substitute: on fixtures it flags
`# client.timeout = 30` and `# return None` (commented-out code) while passing
clean over both `# Increment the counter by one.` and the legitimate `# R2 only
accepts SigV4-signed requests.`. The two rules are disjoint — R003 is about
prose that restates code, `ERA001` about code hiding in a comment.

Tier 2 is no better. Comments are not AST nodes, so a semgrep `pattern` cannot
address them at all; only `pattern-regex` over raw text can, and both candidate
encodings fail, verified by simulating them with `grep` over the real tree:

- **Flag every non-directive comment** — 7 matches in `src/` and `tests/`, of
  which 6 are load-bearing and legal under this rule. An ~86% false-positive
  rate on exactly the comments the rule exists to protect.
- **Blocklist English phrasings** (`# Create the`, `# Return the`, …) — catches
  4 of 6 redundant comments in the fixture, missing `# The bucket name.` and
  `# Skip empty items.`, and is evaded by rewording. It would also fire on a
  legitimate *why* that happens to open with a blocklisted verb.

`ERA001` **is compatible and may be enabled.** It targets a disjoint,
machine-checkable subset (commented-out code), does not overlap the currently
selected `E`/`W`/`F`/`I`/`UP`/`B`/`SIM`, and `ruff check --select ERA src tests`
passes clean on the tree today — so adopting it would add no violations. It
enforces a *neighbouring* rule, never this one.

**Exceptions** — must NOT be deleted or rewritten as R003 violations:

1. **Docstrings are out of scope.** A `"""..."""` is not a comment; R003 says
   nothing about docstring content, including docstrings that restate a
   signature. Present today in `src/wfs/main.py`,
   `src/wfs/models/serializers.py`, and `tests/externals/s3.py`.
2. **Functional directives are not explanatory prose.** `# noqa` /
   `# noqa: RULE`, `# ruff: noqa`, `# type: ignore`, `# pyright: ignore[...]`,
   `# nosemgrep`, and formatter pragmas (`# fmt: off`/`# fmt: on`) are
   instructions read by tools, not comments about code. They are already
   protected by the *Ignore directives* section above. (Currently zero occur in
   `src/` or `tests/`; this exception is forward-looking.)
3. **License and copyright headers in vendored third-party code** must be
   preserved verbatim for legal reasons, regardless of whether they explain
   anything. (No vendored directory exists in the repo today; forward-looking.)
4. **Comments that decode an opaque token** carry information the code cannot,
   even when they look like a restatement. `pyproject.toml`'s
   `# E/W pycodestyle, F pyflakes, I isort, UP pyupgrade, B bugbear, SIM simplify`
   expands lint codes that are meaningless on sight; the `extend-exclude` note
   above it explains why the formatter is kept out of the docs. Both are legal.
5. **The existing load-bearing comments in this repo**, cited by text rather
   than line number because they move:
   - `src/wfs/drivers/s3.py` — "R2 only accepts SigV4-signed requests."
     (external constraint; nothing in the code states it)
   - `src/wfs/models/serializers.py` — "bool is a subclass of int; reject it
     explicitly." (gotcha; the check reads as redundant without it)
   - `tests/externals/client.py` — "TestClient.`__exit__` overrides httpx's and
     never calls close(), so both teardown paths have to be hooked separately."
     (upstream behaviour that justifies a surprising teardown)
   - `tests/externals/s3.py` — "get_settings and get_driver are lru_cache'd, so
     a driver built under one test's env would otherwise outlive it." (explains
     why the cache clearing exists at all)
