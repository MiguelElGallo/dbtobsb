"""Closed v1 native-status vocabulary."""

RUN_STATUSES = ("error", "no-op", "partial success", "skipped", "success")
TEST_STATUSES = ("error", "fail", "pass", "skipped", "warn")
NATIVE_STATUSES = tuple(sorted(set(RUN_STATUSES) | set(TEST_STATUSES)))
