Reviewer (claude opus medium): pass; F1 minor, F2 minor, F3 nit, F4 nit.
Orchestrator: pytest 78 passed. But CI runs `python -m unittest discover -s tests -v` on a clean setup-python (no pytest installed).
O1 [blocker] VALID — own finding, upgrades F4: tests/test_duration.py is pytest-style (`import pytest`, parametrize, plain functions).
  - With pytest installed: `python3 -m unittest discover -s tests` → "Ran 64 tests ... OK": the 14 new tests silently never run.
  - Without pytest (CI): discover → errors=1, `unittest.loader._FailedTest.test_duration` → CI fails.
  Root cause shared with the orchestrator: the handoff said "run with pytest" and did not name the CI runner.
F1 [minor] INVALID as a defect — `d` for wait is an intended consequence of the shared parser.
F2 [minor] VALID — no test that `wait --timeout 0s` still says "--timeout must be positive".
F3 [nit] VALID, pre-existing behavior; not required.
Decision: REWORK round 2 (O1, F2), same Codex executor via --resume.
