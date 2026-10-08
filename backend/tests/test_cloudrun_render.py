"""What the deploy hands Cloud Run, and where the traffic goes while it lands.

`deploy/cloudrun/render.py` is the one piece of Python with production traffic
on the other side of it, and it runs nowhere else — a mistake here is not found
by a failing request but by a deploy going sideways at the moment it is used.
So the two decisions are pinned: the image that was signed is the image that is
run, and a new revision serves nobody until somebody moves traffic to it.

The manifest is read from `deploy/cloudrun/service.yaml` itself rather than a
fixture, so a change to it that breaks the rendering fails here.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

ROOT = pathlib.Path(__file__).resolve().parents[2]
RENDER = ROOT / "deploy" / "cloudrun" / "render.py"


def _render_module() -> Any:
    """Load it by path: it is a script outside the backend package, and giving
    it an importable home would mean moving a file whose location is part of
    how the deploy workflow calls it."""
    spec = importlib.util.spec_from_file_location("cloudrun_render", RENDER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


render = _render_module()

IMAGE = "asia-northeast1-docker.pkg.dev/p/chummer/chummer-web@sha256:" + "ab" * 32


def _rendered(current: str = "") -> dict[str, Any]:
    return dict(yaml.safe_load(render.render(IMAGE, current)))


class TestTheImage:
    def test_the_placeholder_is_replaced_by_the_digest_that_was_signed(self) -> None:
        containers = _rendered()["spec"]["template"]["spec"]["containers"]
        assert [c["image"] for c in containers] == [IMAGE]

    def test_nothing_that_looks_like_a_placeholder_survives(self) -> None:
        """A renamed key in `service.yaml` would otherwise ship the literal
        string to Cloud Run, which fails with a message about the registry
        rather than about the manifest."""
        assert "PLACEHOLDER" not in render.render(IMAGE)


class TestPublicOrigin:
    def test_public_url_is_injected_without_losing_other_environment_settings(self) -> None:
        service = yaml.safe_load(render.render(IMAGE, "rev-1", "https://chummer.example/"))
        container = service["spec"]["template"]["spec"]["containers"][0]
        env = {row["name"]: row["value"] for row in container["env"]}
        assert env["PUBLIC_ORIGIN"] == "https://chummer.example"
        assert env["TRUST_CLOUDFLARE_IP"] == "1"
        assert container["image"] == IMAGE
        assert service["spec"]["traffic"][0] == {"revisionName": "rev-1", "percent": 100}

    def test_unset_public_url_keeps_the_template_environment(self) -> None:
        template = yaml.safe_load((RENDER.parent / "service.yaml").read_text())
        original = template["spec"]["template"]["spec"]["containers"][0]["env"]
        assert _rendered()["spec"]["template"]["spec"]["containers"][0]["env"] == original

    @pytest.mark.parametrize(
        "origin",
        [
            "not a url",
            "ftp://example.com",
            "https://user:pass@example.com",
            "https://example.com/path",
            "https://example.com?query=1",
            "https://example.com#fragment",
            "https://example.com:99999",
        ],
    )
    def test_invalid_public_urls_fail_before_deploying(self, origin: str) -> None:
        with pytest.raises(ValueError):
            render.render(IMAGE, "", origin)

    def test_the_workflow_passes_the_configured_public_url_to_the_renderer(self) -> None:
        workflow = yaml.safe_load((ROOT / ".github/workflows/deploy-cloudrun.yml").read_text())
        step = next(
            s for s in workflow["jobs"]["deploy"]["steps"] if s.get("name") == "Create the revision, serving nothing"
        )
        assert step["env"]["PUBLIC_ORIGIN"] == "${{ vars.PUBLIC_URL }}"
        assert 'render.py "$IMAGE" "$current" "$PUBLIC_ORIGIN"' in step["run"]


class TestWhereTrafficGoes:
    def test_the_first_deploy_has_nothing_to_hold_traffic_on(self) -> None:
        """With no revision serving, the file's own `latestRevision: true`
        stands and the new revision takes everything — there is no old one to
        keep it on."""
        assert _rendered()["spec"]["traffic"] == [{"latestRevision": True, "percent": 100}]

    def test_a_new_revision_serves_nobody_until_traffic_is_moved(self) -> None:
        """This is the safety of the whole deploy: `services replace` waits for
        the new revision to be Ready — its startup probe asks `/api/ready` —
        while every request keeps going to the revision that already works. A
        revision that cannot serve fails the deploy instead of the visitor."""
        traffic = _rendered("chummer-web-00007-abc")["spec"]["traffic"]
        assert traffic == [
            {"revisionName": "chummer-web-00007-abc", "percent": 100},
            {"latestRevision": True, "percent": 0, "tag": "candidate"},
        ]

    def test_the_candidate_is_reachable_by_name_before_it_serves(self) -> None:
        """Without the tag the new revision has no URL of its own, and the only
        way to look at it would be to give it live traffic first."""
        candidate = [t for t in _rendered("rev-1")["spec"]["traffic"] if t.get("tag")]
        assert [t["tag"] for t in candidate] == ["candidate"]

    def test_exactly_one_hundred_percent_is_handed_out(self) -> None:
        for current in ("", "rev-1"):
            assert sum(t["percent"] for t in _rendered(current)["spec"]["traffic"]) == 100


class TestTheRestOfTheManifestIsLeftAlone:
    def test_the_probes_and_the_scale_ceiling_survive_rendering(self) -> None:
        """`maxScale: 1` is not a cost setting — the rate limiter counts in
        process memory, so a second instance hands out a second allowance."""
        template = _rendered("rev-1")["spec"]["template"]
        assert template["metadata"]["annotations"]["autoscaling.knative.dev/maxScale"] == "1"
        container = template["spec"]["containers"][0]
        assert container["startupProbe"]["httpGet"]["path"] == "/api/ready"
        assert container["livenessProbe"]["httpGet"]["path"] == "/api/health"

    def test_the_rendering_is_still_a_service(self) -> None:
        rendered = _rendered("rev-1")
        assert rendered["kind"] == "Service"
        assert rendered["metadata"]["name"] == "chummer-web"
