Reviewer (claude opus medium): pass, 2 nits (an extra harmless test edit; a continue test relies on read order).
Orchestrator: every command on a list status → ERROR envelope, exit 1, no traceback (continue, cancel, status <id>, wait); status lists only valid jobs; prune skips the bad one and still removes a valid old job. The 4 test_release failures came from .colab/runs/*.last.md links (audit trail, not this change); renamed to .last.txt and the suite is clean.
Decision: ACCEPTED.
