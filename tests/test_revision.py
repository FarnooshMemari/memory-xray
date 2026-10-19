import json
import re
from pathlib import Path

import pytest

import run_feasibility
from mxr import scoring
from mxr.scoring import (PINNED_MODEL, PINNED_REVISION, RevisionError, resolve_revision,
                         verify_revision_in_cache)

ROOT = Path(__file__).parents[1]
SHA = "f39ac1d28e925b323eae81227eaba4464caced4e"


def test_pinned_constants():
    assert PINNED_MODEL == "microsoft/Phi-3-mini-4k-instruct"
    assert re.fullmatch(r"[0-9a-f]{40}", PINNED_REVISION) and PINNED_REVISION == SHA


def test_runner_defaults_are_pinned():
    args = run_feasibility.parse_args([])
    assert args.model == PINNED_MODEL and args.revision == PINNED_REVISION
    assert args.compute_dtype == "float32"


def test_notebook_pins_the_same_commit():
    nb = json.loads((ROOT / "colab" / "feasibility_s_single.ipynb").read_text())
    src = "".join("".join(c["source"]) for c in nb["cells"])
    assert PINNED_REVISION in src and "--compute-dtype float32" in src


def test_sha_passes_through_without_network():
    r = resolve_revision("org/model", SHA)
    assert r == {"sha": SHA, "source": "pinned_sha", "requested": SHA}


def test_local_path_has_no_commit(tmp_path):
    assert resolve_revision(str(tmp_path), SHA)["source"] == "local_path"


def test_branch_is_resolved_to_sha(monkeypatch):
    class Info:
        sha = SHA

    class Api:
        def model_info(self, repo, revision=None):
            assert revision == "main"
            return Info()

    import huggingface_hub
    monkeypatch.setattr(huggingface_hub, "HfApi", Api)
    assert resolve_revision("org/model", None) == {"sha": SHA, "source": "resolved_from:main", "requested": None}


def test_unresolvable_revision_aborts(monkeypatch):
    class Api:
        def model_info(self, repo, revision=None):
            raise OSError("offline")

    import huggingface_hub
    monkeypatch.setattr(huggingface_hub, "HfApi", Api)
    with pytest.raises(RevisionError):
        resolve_revision("org/model", "main")


def test_runner_aborts_when_commit_cannot_be_pinned(monkeypatch, tmp_path):
    def boom(args, scenario):
        raise RevisionError("offline")

    monkeypatch.setattr(run_feasibility, "make_scorer", boom)
    assert run_feasibility.main(["--out", str(tmp_path)]) == 3
    assert not any(tmp_path.iterdir())


def test_cache_verification(tmp_path):
    snap = tmp_path / "models--org--model" / "snapshots" / SHA
    snap.mkdir(parents=True)
    (snap / "config.json").write_text("{}")
    (tmp_path / "models--org--model" / "refs").mkdir()
    (tmp_path / "models--org--model" / "refs" / "main").write_text(SHA)
    assert verify_revision_in_cache("org/model", SHA, cache_dir=str(tmp_path))
    assert not verify_revision_in_cache("org/model", "0" * 40, cache_dir=str(tmp_path))
