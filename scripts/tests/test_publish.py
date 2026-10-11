"""Exercise publication against local git and a fake gh, never a live service."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
MERGE = "b" * 40
GH = r"""#!/usr/bin/env python3
import json, os, pathlib, subprocess, sys
args = sys.argv[1:]
with open(os.environ['CALLS'], 'a') as f:
    f.write(json.dumps(args) + '\n')
def option(name):
    return args[args.index(name) + 1]
if args[:2] == ['auth', 'status']:
    pass
elif args[:2] == ['repo', 'view']:
    print('example/project' if option('--jq') == '.nameWithOwner' else 'main')
elif args[:2] == ['pr', 'list']:
    print('https://github.com/example/project/pull/1')
elif args[:2] == ['pr', 'view']:
    field = option('--json')
    if field == 'state':
        print('MERGED' if pathlib.Path(os.environ['MERGED']).exists() else 'OPEN')
    elif field == 'headRefOid':
        print(subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip())
    elif field == 'mergeCommit':
        print('b' * 40)
elif args[:2] == ['pr', 'checks']:
    sys.exit(1 if os.environ.get('FAIL_CHECKS') else 0)
elif args[:2] == ['pr', 'merge']:
    pathlib.Path(os.environ['MERGED']).touch()
elif args[:2] == ['run', 'list']:
    print('101')
elif args[:2] == ['run', 'watch']:
    sys.exit(1 if os.environ.get('FAIL_DEPLOY') and args[2] == '202' else 0)
elif args[:2] == ['run', 'view']:
    if '--json' in args:
        print(json.dumps([{'conclusion': 'skipped' if os.environ.get('SKIPPED') else 'success'}]))
    elif args[2] == '101':
        print('published image: registry.example/app@sha256:' + 'd' * 64)
    else:
        print('revision: deployed, traffic 100%')
elif args[:2] == ['workflow', 'run']:
    if not os.environ.get('NO_URL'):
        print('https://github.com/example/project/actions/runs/202')
elif args[0] == 'api':
    if 'check-runs' in args[1]:
        print('1')
    elif 'git/ref/' in args[1]:
        print(('c' if os.environ.get('ADVANCED') else 'b') * 40)
    else:
        print(json.dumps({'head_sha': 'b' * 40, 'event': 'workflow_dispatch',
                          'path': '.github/workflows/' + ('wrong.yml' if os.environ.get('WRONG_RUN') else 'deploy.yml')}))
else:
    sys.exit('unexpected fake gh call: ' + repr(args))
"""


class PublishTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Test")
        (self.repo / "code").write_text("base")
        self.git("add", ".")
        self.git("commit", "-m", "base")
        subprocess.run(
            ["git", "init", "--bare", str(self.root / "remote")],
            check=True,
            capture_output=True,
        )
        self.git("remote", "add", "origin", str(self.root / "remote"))
        self.git("push", "origin", "main")
        self.git("switch", "-c", "feature")
        (self.repo / "code").write_text("feature")
        self.git("commit", "-am", "feature")
        self.bin = self.root / "bin"
        self.bin.mkdir()
        (self.bin / "gh").write_text(GH)
        (self.bin / "gh").chmod(0o755)
        self.body = self.root / "body.md"
        self.body.write_text("Description")
        self.calls = self.root / "calls"
        self.state = self.root / "state.json"
        self.env = {
            **os.environ,
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            "CALLS": str(self.calls),
            "MERGED": str(self.root / "merged"),
        }

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, check=True, text=True, capture_output=True).stdout.strip()

    def publish(self, mode="--existing-commit", extra=(), **env):
        return subprocess.run(
            [
                "bash",
                str(SCRIPTS / "publish.sh"),
                *([mode] if isinstance(mode, str) else mode),
                "--title",
                "Feature",
                "--body-file",
                str(self.body),
                "--ci-workflow",
                "ci.yml",
                "--deploy-workflow",
                "deploy.yml",
                "--deploy-input",
                "image",
                "--artifact-pattern",
                r"published image: (registry\.example/app@sha256:[0-9a-f]{64})",
                "--state-file",
                str(self.state),
                *extra,
            ],
            cwd=self.repo,
            env={**self.env, "HEAD_SHA": self.git("rev-parse", "HEAD"), **env},
            text=True,
            capture_output=True,
            check=False,
        )

    def count(self, *prefix):
        return sum(row[: len(prefix)] == list(prefix) for row in map(json.loads, self.calls.read_text().splitlines()))

    def test_existing_commit_and_resume_do_not_redeploy(self):
        result = self.publish()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Deployment status: succeeded", result.stdout)
        self.assertNotIn("revision: deployed", result.stdout)
        self.assertTrue(Path(str(self.state) + ".logs/deploy-details.log").exists())
        result = self.publish("--resume")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.count("workflow", "run"), 1)
        self.assertEqual(self.count("pr", "merge"), 1)

    def test_failed_checks_allow_fix_commit_and_resume(self):
        self.assertNotEqual(self.publish(FAIL_CHECKS="1").returncode, 0)
        self.assertEqual(self.count("workflow", "run"), 0)
        (self.repo / "code").write_text("fixed")
        self.git("commit", "-am", "fix")
        result = self.publish("--resume")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(self.state.read_text())["head_sha"],
            self.git("rev-parse", "HEAD"),
        )

    def test_preflight_stops_before_push_and_can_resume(self):
        marker = self.root / "ready"
        options = ("--preflight", f'test -f "{marker}"')
        self.assertNotEqual(self.publish(extra=options).returncode, 0)
        self.assertFalse(Path(str(self.state) + ".logs/push.log").exists())
        marker.touch()
        self.assertEqual(self.publish("--resume", extra=options).returncode, 0)

    def test_dispatch_without_url_requires_explicit_recovery(self):
        self.assertNotEqual(self.publish(NO_URL="1").returncode, 0)
        self.assertNotEqual(self.publish("--resume").returncode, 0)
        self.assertEqual(self.count("workflow", "run"), 1)
        result = self.publish("--resume", extra=("--deploy-run", "202"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.count("workflow", "run"), 1)

    def test_advanced_base_stops_before_dispatch(self):
        self.assertNotEqual(self.publish(ADVANCED="1").returncode, 0)
        self.assertEqual(self.count("workflow", "run"), 0)

    def test_failed_or_skipped_deployment_cannot_report_success(self):
        result = self.publish(FAIL_DEPLOY="1")
        self.assertNotEqual(result.returncode, 0)
        result = self.publish("--resume", SKIPPED="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Deployment status: succeeded", result.stdout)
        self.assertEqual(self.count("workflow", "run"), 1)

    def test_wrong_run_metadata_stops_before_watch(self):
        self.assertNotEqual(self.publish(WRONG_RUN="1").returncode, 0)
        self.assertEqual(self.count("run", "watch", "202"), 0)

    def test_public_challenge_and_failure_are_distinct(self):
        options = ("--verify-command", 'exit "${VERIFY_RESULT:-2}"')
        result = self.publish(extra=options)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Public verification: incomplete", result.stdout)
        result = self.publish("--resume", extra=options, VERIFY_RESULT="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Deployment status: succeeded", result.stdout)
        self.assertIn("Public verification: failed", result.stdout)
        self.assertEqual(self.count("workflow", "run"), 1)

    def test_staged_mode_and_changed_head_after_merge(self):
        (self.repo / "code").write_text("staged")
        self.git("add", "code")
        result = self.publish(["--message", "Commit staged changes"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git("log", "-1", "--format=%s"), "Commit staged changes")
        (self.repo / "code").write_text("next feature")
        self.git("commit", "-am", "next")
        result = self.publish("--resume")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("HEAD changed after merging", result.stderr)

    def test_resume_after_merge_before_checkpoint(self):
        self.assertEqual(self.publish().returncode, 0)
        state = json.loads(self.state.read_text())
        state["merge_sha"] = ""
        self.state.write_text(json.dumps(state))
        result = self.publish("--resume")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.count("pr", "merge"), 1)
        self.assertEqual(self.count("workflow", "run"), 1)

    def test_dirty_tree_or_mismatched_options_stop(self):
        (self.repo / "code").write_text("uncommitted")
        self.assertNotEqual(self.publish().returncode, 0)
        self.assertEqual(self.count("workflow", "run"), 0)
        self.git("checkout", "--", "code")
        self.assertEqual(self.publish().returncode, 0)
        self.assertNotEqual(self.publish("--resume", extra=("--deploy-input", "other")).returncode, 0)


class PublicProbeTest(unittest.TestCase):
    def test_content_status_and_challenge(self):
        with tempfile.TemporaryDirectory() as directory:
            fake = Path(directory) / "curl"
            fake.write_text("""#!/usr/bin/env python3
import os, pathlib, sys
args = sys.argv
mode = os.environ['PROBE_MODE']
ready = args[-1].endswith('/api/ready')
challenge = mode == 'challenge' or (mode == 'challenge_then_failure' and ready)
pathlib.Path(args[args.index('-D') + 1]).write_text('cf-mitigated: challenge\\n' if challenge else '')
body = '{"ready":true}' if ready else '<html></html>'
pathlib.Path(args[args.index('-o') + 1]).write_text('wrong' if mode == 'bad_content' else body)
print('403' if challenge else ('503' if mode in ('http_failure', 'challenge_then_failure') else '200'), end='')
""")
            fake.chmod(0o755)
            for mode, expected in (
                ("ok", 0),
                ("challenge", 2),
                ("bad_content", 1),
                ("http_failure", 1),
                ("challenge_then_failure", 1),
            ):
                with self.subTest(mode=mode):
                    result = subprocess.run(
                        [
                            "bash",
                            str(SCRIPTS / "verify-public.sh"),
                            "https://example.invalid",
                        ],
                        env={
                            **os.environ,
                            "PATH": directory + os.pathsep + os.environ["PATH"],
                            "PROBE_MODE": mode,
                        },
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(result.returncode, expected, result.stderr)


if __name__ == "__main__":
    unittest.main()
