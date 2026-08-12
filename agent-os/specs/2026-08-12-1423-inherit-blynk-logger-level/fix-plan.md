# Fix Plan — Respect Home Assistant Logger Configuration

**Bug Report**: https://github.com/bzellman/WindmillAC/issues/42  
**Root Cause**: `blynk_service.py` assigns `DEBUG` directly to its module logger at import time, so the Blynk child logger does not inherit Home Assistant's configured integration level. The same request path logs token-bearing URLs and republishes raw transport details that can contain the URL.  
**Confidence**: High

## Root Cause Analysis

`logging.Logger.setLevel(logging.DEBUG)` sets an explicit child-logger level. Python logging therefore stops walking to the `custom_components.windmillac` parent when it computes the effective level. The module then emits request URLs whose `token` query parameter contains the credential. Separately, a `requests` transport exception may include that URL and is currently allowed to reach coordinator `ERROR` logging unchanged.

### Execution Path

1. Home Assistant imports `custom_components.windmillac.blynk_service` while loading or reloading the integration.
2. Module initialization gets the child logger and explicitly assigns `DEBUG`.
3. `async_get_pin_value` or `async_set_pin_value` builds a URL containing the Blynk token and logs the complete URL at debug level.
4. The explicit child level allows the message even when the parent integration logger is configured as `WARNING`.
5. On transport failure, an unsanitized request exception can carry the same URL into an enabled coordinator error record.

### Reproduction Evidence

An isolated import with `custom_components.windmillac` configured at `WARNING` reports both the child logger's explicit and effective levels as `DEBUG`. The assertion that the child remains at `NOTSET` fails.

### Why This Wasn't Caught

The repository has no automated test suite for logger configuration or secret-bearing log messages.

## Proposed Fix

### Changes Required

| File | Change Type | Description |
|------|-------------|-------------|
| `custom_components/windmillac/blynk_service.py` | MODIFY | Remove the explicit `DEBUG` level, stop logging request URLs/raw response data, and convert request-library failures into stable token-free operation errors. |
| `tests/test_blynk_service_logging.py` | ADD | Verify Blynk logger inheritance, exact get/set behavior without secret-bearing logs, and token-safe transport failures. |
| `.github/workflows/hassfest.yml` | MODIFY | Run the dependency-free unit suite in the existing checked-out PR validation job. |

### What NOT to Change

- Do not change request construction or Blynk API behavior.
- Do not change logger levels in `entity.py` or `climate.py`; they do not emit the demonstrated request URL and need a separate compatibility review.
- Do not change token-derived entity identifiers; correcting that persistence concern requires an entity-registry migration plan.
- Do not add dependencies or a new test framework; use the Python standard library.
- Do not refactor unrelated style or control flow.

## Regression Prevention

### Tests to Add

1. `test_module_logger_inherits_parent_level`: fresh-import the module beneath a parent logger configured to `WARNING`; the Blynk child must remain `NOTSET`, inherit `WARNING`, reject debug records, and remain unmodified by the capture harness.
2. `test_pin_operations_do_not_log_request_or_response_secrets`: run get and set paths at effective `DEBUG`; assert safe records exist, exact request URLs/order and return values are preserved, and neither the request token nor a reflected response sentinel is logged.
3. `test_request_exceptions_are_token_safe`: make the request double raise a token-bearing `RequestException`; assert the public operation surfaces a stable token-free error with suppressed chaining and no captured message contains the token.

The suite uses only the standard library, import-only doubles for unavailable `requests` and Home Assistant modules, a custom non-mutating log handler, and complete cleanup of substituted module/logger state. It runs serially with `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`.

### Tests to Verify (Existing)

The repository has no existing automated tests. Run the new standard-library suite, compile every Python source file, and obtain the exact-head HACS and hassfest checks.

## Blast Radius

| Component | Impact | Verification |
|-----------|--------|-------------|
| Home Assistant logging | The Blynk child follows its configured parent level in a clean process. Other explicit integration child levels are unchanged. | Fresh-import inheritance regression test. |
| Blynk get/set requests | Network URLs, executor behavior, response parsing, and successful return values remain unchanged. | Exact fake request and return-value assertions. |
| Blynk request failures | Raw request-library text is replaced by the existing operation-level failure shape without exposing the URL. | Sentinel-bearing request-exception test. |
| Debug diagnostics | Safe operation/status messages remain; full request URLs and raw response data are removed. | Non-vacuous debug capture with request and reflected-response sentinels. |
| PR validation | The dependency-free unit suite runs before hassfest. | Exact-head GitHub Actions result. |

## Implementation Waves

1. **Regression test first**: add the two tests and confirm they fail on the current code.
2. **Targeted implementation**: remove the forced level and secret-bearing raw-data logs, add the token-safe request-error boundary, and confirm the tests pass.
3. **Blast-radius verification**: run all tests and compile all Python files.
4. **`/simplify` pass**: review only the new fix and regression-test code, then rerun verification.
5. **`/pr-handoff-to-codex` handoff**: perform adversarial PR review and apply verified findings.

## Rollback Plan

Revert the fix commit. No data, schema, API, configuration, or dependency changes are involved.

## Upgrade Transition

Users must fully restart Home Assistant after installing the update, as the existing HACS instructions already require. Re-executing the module in a process that previously ran the old source can retain the named logger object's stale explicit `DEBUG` level; the fix intentionally does not force `NOTSET`, because doing so would overwrite a user's exact-child logger choice.

## Follow-up Debt (Not This PR)

- `entity.py` and `climate.py` also force child logger levels and need a separate compatibility-scoped correction.
- `entity.py` derives entity/device identifiers from the token; changing that security-sensitive persistence requires an explicit entity-registry migration plan.
