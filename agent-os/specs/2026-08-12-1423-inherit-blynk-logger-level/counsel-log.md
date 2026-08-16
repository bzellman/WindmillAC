# Fix Strategy Counsel — Respect Home Assistant Logger Configuration

**Bug Report**: https://github.com/bzellman/WindmillAC/issues/42
**Fix Plan**: `agent-os/specs/2026-08-12-1423-inherit-blynk-logger-level/fix-plan.md`
**Date**: 2026-08-12 14:23 CDT
**Iteration**: 1 of 2 (max)

---

## Round 1: Initial Reviews

### Reviewer A (Root Cause Validation)

**Disposition:** AMEND — the Blynk-service diagnosis is correct and the security fix is appropriately narrow, but the plan overstates integration-wide logger inheritance and needs executable, non-vacuous test criteria.

**Evidence reviewed:**

- Issue #42 describes the precise module and failure mode. Current `blynk_service.py:6-7` creates `custom_components.windmillac.blynk_service` and assigns it `DEBUG`; `async_get_pin_value` and `async_set_pin_value` then emit the complete token-bearing URLs at lines 39 and 66.
- The normal callers cover both operations: the coordinator reads pins directly and through `async_get_mode`, `async_get_fan`, and `async_get_power` (`coordinator.py:28-32`); entity actions reach the setters (`entity.py:82-113`). Removing only the two debug statements neither changes URL construction nor the `requests.get` calls.
- History shows the forced level and URL messages were introduced together in the original POC commit `e7535e4` and carried forward unchanged when the integration was renamed in `8ff3a0d`; no later history changes this path. There is no existing test configuration or test suite.

**Independent reproduction (current production source):**

- The checkout lacks Home Assistant and `requests`, so I loaded the unmodified production file under its real module name with import-only doubles, attached a root capture handler, and configured `custom_components.windmillac` to `WARNING`.
- Import set the child explicit/effective levels to `DEBUG`. Exercising one get and one set produced nine records from `custom_components.windmillac.blynk_service`, including both complete URLs and the sentinel token. Setting only that child logger to `NOTSET` changed its effective level to `WARNING`; repeating the same operations produced zero Blynk-service debug records. This validates the Python logging root cause without claiming a live Home Assistant runtime verification.

**Findings:**

1. **[P1 — scope statement must be resolved]** The plan's Blynk-specific security remedy is minimal and warranted: the token must remain in the request URL for the API, but there is no functional need to log that URL, and the existing get/set operation messages retain useful diagnostics. However, `entity.py:10-11` and `climate.py:12-13` also set their child loggers to `DEBUG`. Consequently, a `custom_components.windmillac: warning` setting will still not suppress all integration debug logging after the proposed Blynk-only change. `entity.py` has no direct token log, and `climate.py` has no logging calls, so these do not extend the demonstrated credential-exposure path; they do invalidate the plan's broad claim that the integration's child logger(s) will inherit user configuration.

2. **[P2 — root-cause test must prove behavior, not only state]** A fresh import with the parent set to `WARNING`, `child.level == NOTSET`, and `child.getEffectiveLevel() == WARNING` is the right regression assertion. Also assert `not child.isEnabledFor(logging.DEBUG)` or capture zero records whose logger name is the Blynk-service logger after one operation. This protects against a future explicit child level and proves the expected suppression. The test must reset the named logger/module state between cases because Python's logger registry outlives a module reload.

3. **[P2 — token test needs an enabled debug path]** The get/set token test must set the integration parent to `DEBUG`, assert that safe Blynk debug records were actually captured, and then assert the sentinel is absent from every captured `record.getMessage()`. Otherwise, a `WARNING` configuration or disabled logger could make the test pass vacuously. Its fake executor/request function should also assert both expected requests were made, preserving the current API behavior while proving no request URL reaches the component logger.

4. **[P2 — standard-library test harness is underspecified]** `python -m unittest discover` cannot import this module in the present checkout because neither Home Assistant nor `requests` is installed. A dependency-free test is feasible, but the plan must specify import-only `sys.modules` doubles for `homeassistant.components.climate.const` and `requests` (or an equivalent isolated loader), plus cleanup of logging and module globals. Merely adding a test file that imports the module normally will not be runnable under the stated verification command.

**Required amendments:**

- Choose and state one scope: (a) keep the minimal security fix to `blynk_service.py`, retain the prohibition on unrelated logging changes, and narrow the blast-radius language to the Blynk logger; or (b) make integration-wide logger inheritance the objective, remove all three explicit `DEBUG` assignments, and cover them. I recommend (a) for issue #42 because only the Blynk logger emits the credential-bearing URLs.
- Make the two proposed tests non-vacuous as described above, including an isolated standard-library import harness and request-call assertions. The token test should exercise both public get/set paths at effective `DEBUG`; the inheritance test should exercise effective `WARNING`.

**Root-cause confidence:** High (0.98). The explicit child `DEBUG` level is both necessary for the observed override and sufficient to explain why the token-bearing debug messages are emitted despite the configured parent level; the direct source-to-caller path and isolated execution agree with the report.

**Summary:** Remove Blynk's explicit logger level and its two full-URL debug messages. Do not silently treat that as an integration-wide logger-config fix while `entity.py` and `climate.py` retain their own explicit levels; either narrow the claim (recommended) or intentionally broaden the patch and its tests.

### Reviewer B (Regression Risk)

**Disposition:** AMEND — deleting the Blynk module's explicit `DEBUG` level and its two full-URL messages is a low functional-risk, high-value security fix, but the plan needs a precise Blynk-only scope, an isolated and discoverable standard-library test harness, and an automated execution path before it can be considered regression prevention.

**Evidence reviewed:**

- Issue #42, the fix plan, Reviewer A's findings, all production callers, repository history, and all current GitHub Actions. There is no production-code diff yet; the only on-disk candidates are the plan and counsel log. The expected production change is limited to `blynk_service.py:7`, `:39`, and `:66`.
- A dependency-free execution of the unmodified source, using import-only doubles and the real module name, set `custom_components.windmillac` to `WARNING` yet produced `child_level=DEBUG` and `child_effective=DEBUG`. One primitive get and one primitive set made the unchanged URLs `.../get?token=SENTINEL_TOKEN&V1` and `.../update?token=SENTINEL_TOKEN&V2=72`, and emitted the sentinel in two of nine Blynk records. This confirms both the logging defect and the request behavior that must remain unchanged.
- `BlynkService` is constructed only in `__init__.py:18`. The coordinator calls direct reads plus `async_get_mode`, `async_get_fan`, and `async_get_power` (`coordinator.py:28-32`); entity actions reach target-temperature, mode, fan, and power setters (`entity.py:82-113`). `async_set_current_temp` has no in-repository caller but remains a public wrapper over the same primitive setter.
- `entity.py:10-11` and `climate.py:12-13` also force `DEBUG`. The former has debug calls but no direct token log; the latter has no log calls. No other module calls `requests.get` or constructs the Blynk URLs. History shows the Blynk forced level and URL messages originated together in `e7535e4` and were only renamed with the integration in `8ff3a0d`.
- The checkout has neither Home Assistant nor `requests` installed. `python` is unavailable; `python3 -m unittest discover -v` currently finds zero tests and exits 5, while `python3 -m compileall -q custom_components` succeeds. The only workflows run HACS and hassfest validation/release packaging; none invokes a Python unit suite.

**Blast radius:**

| Surface | Regression risk | Required preservation / evidence |
|---|---|---|
| `blynk_service.py` primitive get/set | Low if the patch deletes only the level assignment and the two log calls; URL construction, executor use, response parsing, and errors are otherwise untouched. | Fake `requests.get` must receive the exact get and update URLs, in order; assert get still returns its existing converted value and set still returns stripped response text. |
| Coordinator refresh reads | Low indirect risk: direct reads plus mode/fan/power wrappers all terminate in `async_get_pin_value`. | Primitive-get coverage proves the unchanged transport path; no coordinator refactor is warranted. |
| Entity control actions and unreferenced raw temperature setter | Low indirect risk: target temperature, HVAC mode, fan, and power each terminate in `async_set_pin_value`; `async_set_current_temp` does too despite having no in-repo caller. | Primitive-set URL and response assertions preserve the shared implementation; do not alter wrapper mappings or refresh behavior. |
| Home Assistant logger configuration | Intended behavioral change for the Blynk child only: it will obey the configured effective parent level. Users at `WARNING` lose Blynk debug diagnostics; users can enable the parent at `DEBUG` to retain the safe messages. | Fresh-import test: child is `NOTSET`, effective level is parent `WARNING`, and it is not enabled for `DEBUG`. |
| Other integration child loggers | Material scope/expectation risk: `entity` and `climate` retain explicit `DEBUG`, so the patch does not make every `custom_components.windmillac.*` logger inherit. | State the scope as Blynk logger/token path, or deliberately broaden and test all three modules. Keep the former for this issue. |
| Unit-test and CI environment | High risk of false-green or non-execution without careful doubles, restoration, discovery, and a runner. | Import source with local doubles; restore `sys.modules` and logger state; use a discoverable command and add it to an existing PR workflow. |

**Findings:**

1. **[P1 — preserve Blynk-only scope and API behavior]** I agree with Reviewer A: removing the three Blynk lines is the appropriately narrow fix, and the plan must not call it integration-wide logger inheritance while `entity.py` and `climate.py` keep their explicit levels. The two URL log deletions must not be accompanied by URL-construction, `requests.get`, executor, parsing, wrapper, or error-path edits. The regression test should assert exact URLs and normal get/set return values, not merely that a fake was called; this protects the shared primitive operations used by every production caller.

2. **[P2 — make the secret test non-vacuous and define its guarantee]** I agree with Reviewer A that the token test must run at effective `DEBUG`, capture at least one safe Blynk record, and check every exact-child `record.getMessage()` for the sentinel. Use safe fake response bodies such as `"1"` and `"ok"`: the current retained `Response Text` messages intentionally log the response body, so making a fake response echo the sentinel would fail even after the proposed two-line URL-log removal. If the intended claim is instead that the credential can never appear in any Blynk debug record regardless of a server response, response-body logging must be redacted or removed as an explicitly broader security change; the current plan only establishes that request construction does not leak it.

3. **[P2 — dependency-free import and logging cleanup are global-state sensitive]** A normal import cannot work in this checkout because `__init__.py` imports additional Home Assistant APIs and the two direct dependencies are absent. The test should load `blynk_service.py` with `importlib.util.spec_from_file_location` under the real module name after supplying only `requests` and `homeassistant.components.climate.const` (plus its package parents) in `sys.modules`. Snapshot and restore every inserted/replaced module key, the target module, parent/child logger levels, `disabled`, `propagate`, and the test handler in `addCleanup`/`try-finally`; do not clear `logging.Logger.manager.loggerDict`, root handlers, or unrelated handlers. `logging` and `sys.modules` are process-global, so a future same-process parallel runner would race unless these tests are serialized or protected by a module lock. The fake `hass.async_add_executor_job` should synchronously execute the supplied function, avoiding a real thread and making captured records deterministic.

4. **[P2 — test discovery and automation are currently incomplete]** The plan's literal `python -m unittest discover` is not executable here (`python` is absent), and default `unittest` discovery will not recurse into a new `tests/` directory without `tests/__init__.py` under the installed Python 3.14 loader. Use either `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` or add `tests/__init__.py` and retain default discovery. The existing HACS and hassfest workflows do not run the suite, so the proposed regression test remains manual unless the hassfest workflow (which already checks out the repository) gains that dependency-free command. This is the smallest reliable PR gate and introduces no package or framework dependency.

5. **[P2 — reload transition must be explicit]** Removal gives a clean Home Assistant process the default `NOTSET` child level. It cannot clear a `DEBUG` level already held by that named logger if old and new source are re-executed in the same interpreter, because Python's logger registry survives module reload. Do not replace the deletion with `setLevel(NOTSET)`: that would still overwrite a user's specific child-level choice on each import. Require the normal Home Assistant restart after installing the update (already part of the repository's HACS installation guidance), and reset the child level only inside the isolated test setup.

**Required amendments:**

- Narrow the plan's logger-inheritance and blast-radius language to `custom_components.windmillac.blynk_service`; leave the two adjacent forced levels untouched in this issue and list them as follow-up debt rather than silently claiming they are fixed.
- Define the two tests as dependency-free, fresh-import tests with exact request URL/order and response-value assertions, enabled debug capture, a non-vacuous safe-record assertion, and complete global cleanup.
- Make test discovery executable with `python3` and an explicit `-s tests` start directory (or a test package), then add that same command to the existing PR workflow. Treat a clean process restart after HACS update as the deployment transition condition.

**Verification required after implementation:**

1. Run the new suite first against the unfixed source and confirm the inheritance/token assertions fail for the intended reasons; then run `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` after the targeted deletion.
2. Confirm the capture contains safe Blynk debug records at parent `DEBUG`, no captured exact-child message contains the sentinel, and the fake received precisely the existing get and update URLs while returning the expected values.
3. Run `python3 -m compileall -q custom_components` in a disposable/CI workspace (it creates `__pycache__` artifacts), `git diff --check`, and `git status --short` to ensure only the targeted source, tests, and intended workflow/spec changes remain.
4. Obtain the existing exact-head HACS and hassfest checks after the new unit-test workflow step passes. This is not a live Home Assistant runtime proof; no Home Assistant environment or real Blynk credential was available in the checkout.

**Reviewer A agreement:** I agree with all four of Reviewer A's substantive amendments: the minimal Blynk-only scope, behavior-level inheritance assertion, enabled non-vacuous token capture with request assertions, and import-only standard-library doubles. My additions are the precise `unittest` discovery/CI gap, safe restoration of the global logger and module state, the stale-level reload transition, and the boundary created by retained response-body logging.

**Summary:** The planned three-line Blynk deletion preserves the network/API path across coordinator and entity consumers and removes the demonstrated token exposure. Approve it only as a Blynk-scoped change, with an isolated standard-library regression suite that actually runs in CI and a documented restart transition; do not expand into the other forced loggers without a separate compatibility review.

### Reviewer C (GPT-5.6 Terra xhigh — Deep Reasoning)

**Disposition:** AMEND — the three Blynk-line deletion fixes the demonstrated *normal-path* request-URL debug leak for a fresh Home Assistant process, but it is not an honest general “credential cannot reach logs” guarantee. In particular, the current exception path can turn a token-bearing transport error into an `ERROR` record even when the user has configured the integration at `WARNING`. Resolve that same-path failure mode now; make the retained raw-response logging an explicit, limited contract (or remove it); and strengthen the test/CI design so it cannot make the inheritance assertion pass by changing the logger under test.

**Evidence reviewed:**

- Issue #42, the fix plan, both prior reviews, every Blynk caller, the workflow files, README installation/reload guidance, and the complete history of `blynk_service.py`. The forced Blynk child level and the two request-URL log calls originated together in `e7535e4` and were only moved by `8ff3a0d`.
- Independent dependency-free execution of the unmodified source under its real module name, with `custom_components.windmillac` set to `WARNING`, resulted in Blynk child explicit/effective levels of `DEBUG` and `isEnabledFor(DEBUG) == True`. One primitive get and set made two requests and produced four sentinel-bearing Blynk records: one `Request URL` and one `Response Text` for each operation when the fake server body reflected the sentinel. This is source-level evidence, not a Home Assistant or live-Blynk proof.
- `async_get_pin_value` and `async_set_pin_value` call `requests.get(url)` without a request-exception boundary (`blynk_service.py:42,69`). The coordinator catches every resulting `Exception`, interpolates `err` into an `ERROR` record, then interpolates it again into `UpdateFailed` (`coordinator.py:35-37`). Therefore any transport exception whose representation contains the request target can cross the `WARNING` clamp as an error. The source does not sanitize it before the coordinator sees it.
- The proposed URL deletion leaves `Response Text` in both primitive methods and `Response RAW` in the get path (`blynk_service.py:44,47,71`); several wrappers and the coordinator also log response-derived values. Consequently a test with safe fake bodies can demonstrate only that this component does not log the *outbound constructed URL*, not that arbitrary server-controlled content cannot contain the token.
- This checkout has Python 3.14.6 but neither `python` nor the declared `requests` dependency installed. `python3 -m unittest discover -v` finds no tests and exits 5, while `python3 -m compileall -q custom_components` exits 0. The two existing PR workflows run HACS validation and hassfest only. `README.md:37-40` already directs users to restart Home Assistant after a HACS download.

**Findings:**

1. **[P1 — close the `WARNING`-level transport-error leak in this fix]** Reviewers A and B are right that deleting Blynk’s explicit `DEBUG` and the two direct URL messages is the minimal correction for the reproduced success path. I disagree with B’s instruction to preserve the error path unchanged: that path is part of the same credential-bearing request operation and can log an arbitrary raw exception at `ERROR`, which remains enabled at the user’s documented `WARNING` clamp. A common request/connection failure is allowed to include its target in its text; the code explicitly republishes whatever text it receives twice. Catch `requests.exceptions.RequestException` at the Blynk request boundary and raise a stable token-free operation error with exception chaining suppressed before it reaches the coordinator (or otherwise ensure both the raised and logged messages cannot contain the URL). Add a sentinel-bearing fake request exception test that proves the public operation’s surfaced error and all captured component/coordinator records omit the sentinel. This is a security correction within issue #42’s Blynk path, not unrelated error refactoring.

2. **[P1 — state the precise guarantee; raw response logging defeats an absolute one]** After the three deletions, a clean process with `custom_components.windmillac: warning` will suppress Blynk `DEBUG` records, and a component-only `DEBUG` setting will no longer directly emit the constructed request URL. That is the supported claim. It does *not* mean a token can never reach any Home Assistant log: retained response/body/value logs can emit server-reflected data, request-library/global-debug loggers are outside this component logger hierarchy, and unsanitized errors are presently a direct counterexample. The independent reflected-body probe proves that `Response Text` is an actual raw-data log, not a hypothetical one. Either remove the three raw-response logs now as defensible privacy hardening, or retain them deliberately and rename the test/plan assertion to “constructed request URLs are not logged”; use safe fake bodies in the latter case. Do not claim universal token redaction without a broader data-classification/logging review.

3. **[P1 — a restart is required for the corrected inherited level]** Deleting `setLevel(DEBUG)` does not mutate an existing `logging.Logger` object. Named logger objects live in Python’s logging registry across source re-execution and `importlib.reload`, so a process that previously executed the old module can retain its explicit `DEBUG` level even after the new source is executed. Do not add `setLevel(NOTSET)` as a migration workaround: it would again override a user’s deliberately configured exact-child logger level. The honest transition is install the update, preserve the user’s parent `logger:` configuration, and fully restart Home Assistant, consistent with the existing HACS instructions. The fresh-import test must reset only its isolated child logger to `NOTSET`; it must not present an integration reload as a proof of the deployed transition.

4. **[P2 — make isolated tests observant rather than state-changing]** Do not use `unittest.TestCase.assertLogs` for either central assertion: it adjusts the named logger’s level/handlers, which can conceal a future forced level and make the inheritance test self-fulfilling. Attach a purpose-built handler without changing the Blynk child level, set the integration parent to the intended level, and inspect exact-child `record.getMessage()` values. For the `DEBUG` test, prove the handler captured at least one safe Blynk record and that the fake received the exact existing get/update URLs; for the `WARNING` test, prove `child.level == NOTSET`, effective level is `WARNING`, `isEnabledFor(DEBUG)` is false, and no Blynk debug record is emitted. Test source must be loaded with import-only `requests` and Home Assistant climate-constant doubles; snapshot/restore each substituted `sys.modules` key, the target module entry, parent/child `level`, `disabled`, and `propagate`, and remove only the test handler in `addCleanup`/`finally`. Do not clear the process-wide logger registry, root handlers, or unrelated module entries. Default `unittest` execution is serial; document that this harness is not safe for concurrent same-process execution without a lock.

5. **[P2 — put the dependency-free suite on the existing PR gate]** A test file alone is not regression prevention here. Add a small, explicit unit-test step to the checked-out `hassfest.yml` PR/push workflow before hassfest (or an equivalent job in that workflow), using a declared supported Python version and `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`. This is proportionate: it adds no runtime package or test framework, executes the exact isolated contract in hosted CI, and leaves HACS/release behavior unchanged. Default `python -m unittest discover` is both unavailable in this checkout and insufficiently explicit about the test start directory.

6. **[P2 — keep adjacent logging and credential-persistence debt as follow-up work]** Keep `entity.py` and `climate.py`’s forced levels out of this patch unless the objective is intentionally broadened and compatibility-tested; they do not create the demonstrated request-URL leak, so the release claim must remain Blynk-child scoped. Separately, `entity.py:23,47` embeds the device token in the entity unique ID and then in the device identifier. That is a credential-persistence concern, not a logger-level fix; changing it can alter entity-registry identity and needs a migration/compatibility plan. Track it as a high-priority follow-up rather than silently mixing it with this focused correction.

**Required amendments:**

- Narrow the plan’s primary success claim to the Blynk child and a clean Home Assistant process, while documenting full restart after update as the required transition.
- Add a token-safe `requests` failure boundary and a non-vacuous sentinel-exception regression test; do not retain raw exception interpolation to an `ERROR` record.
- Explicitly choose whether raw response bodies are retained. If retained, scope the token test to outbound request-URL logging and use safe response bodies; if removed, add a reflected-body assertion for the chosen no-raw-body contract.
- Use a custom capture handler and complete `sys.modules`/logger cleanup instead of `assertLogs`, then run its explicit `python3` command in the existing checked-out PR workflow.

**Reviewer A/B agreement and challenge:** I agree with A/B on Blynk-only inheritance scope, clean-process behavior, exact request/return assertions, module/logger cleanup, test discoverability, CI coverage, and the need to preserve the normal request API. I amplify B’s response-body and reload boundaries. I challenge the recommendation to leave error handling untouched: `coordinator.py` already formats all Blynk failures into an enabled error record, so the stated `WARNING`-level protection is incomplete until request-error text is made token-safe.

**Summary:** Approve a Blynk-scoped security fix only after it removes the forced level and direct URL logs, prevents token-bearing request exceptions from becoming coordinator `ERROR` messages, and makes its remaining response/global-logger limits explicit. Use a clean-process, dependency-free custom-capture test suite on the existing PR workflow; require a Home Assistant restart for users upgrading from the forced-DEBUG release. Leave the other forced child loggers and token-derived entity IDs to separately planned follow-up work.

---

## Round 2: Orchestrator Synthesis

**Synthesized**: 2026-08-12 14:58 CDT

### Why Questions

1. **Why remove the request URL logs as well as the forced level?** Because a user may legitimately enable Blynk debug logging; logger inheritance alone would still disclose the credential in that supported mode.
2. **Why change request-error handling when the reporter proposed a one-line deletion?** Because a request-library exception can contain the same token-bearing URL and the coordinator republishes it at `ERROR`, which remains enabled under the reporter's `WARNING` clamp. This is the same credential path, not unrelated hardening.
3. **Why not remove the other forced child levels now?** Neither adjacent module emits the demonstrated URL, while broadening logger behavior needs compatibility tests. The Blynk logger can be fixed independently and honestly described as Blynk-scoped.
4. **Why add a unit step to CI in a repository without a test framework?** A regression file that hosted validation never executes is not durable protection. The proposed suite is standard-library-only and fits the already checked-out hassfest job.

### Agreements (Reviewers Align)

1. The explicit Blynk child `DEBUG` assignment is the confirmed cause of the parent-level override. **Action**: remove it and require a clean-process/restart transition.
2. Full request URLs must not be logged, even when debug is intentionally enabled. **Action**: delete both URL messages and verify exact request behavior separately.
3. The scope must remain the Blynk request path. **Action**: leave `entity.py`, `climate.py`, and token-derived entity identity unchanged and name them as follow-up debt.
4. Tests must be dependency-free, non-vacuous, state-clean, and discoverable. **Action**: use import-only doubles, a custom handler, exact request/return assertions, and explicit `python3` discovery in CI.

### Conflicts (Reviewers Disagree)

1. **Topic**: Preserve the existing request-exception path.
   - **Reviewer A/B**: keep normal request behavior unchanged and avoid adjacent error refactoring.
   - **Reviewer C**: sanitize `RequestException` before the coordinator can log its raw token-bearing text.
   - **Orchestrator Decision**: accept Reviewer C.
   - **Rationale**: the unsanitized exception is a concrete second route from the same URL to Home Assistant logs at a level the documented clamp permits. A narrow boundary around the two request calls closes it without changing successful requests.
2. **Topic**: Retain raw response-body diagnostics with a limited security claim, or remove them.
   - **Reviewer B**: retaining them is acceptable if tests use safe bodies and the claim is limited to outbound URLs.
   - **Reviewer C**: raw server-controlled content defeats a broader credential/privacy claim.
   - **Orchestrator Decision**: remove raw response text and raw response-object logging while keeping operation/status diagnostics.
   - **Rationale**: raw bodies are not needed for the integration's behavior, can contain sensitive server data, and can be removed with zero transport impact.

### Gaps (Nobody Caught Initially)

1. A same-process source reload does not clear a logger object's old explicit level. **Action**: document the already-required full Home Assistant restart and avoid a new forced `NOTSET` assignment.
2. The existing test workflow did not exist. **Action**: run the dependency-free suite in the current hassfest validation job before hassfest.

### Root Cause Verdict

- **Confirmed root cause**: the Blynk module explicitly forces `DEBUG` and logs credential-bearing request data; raw request exceptions provide a related enabled error-level path.
- **Confidence**: High (0.98)
- **Supporting evidence**: source trace, caller map, history, and three independent isolated reproductions all agree.
- **Rejected alternatives**: parent logger misconfiguration and handler filtering do not explain the child's observed explicit/effective `DEBUG`; changing adjacent loggers is unnecessary to close this Blynk credential path.

## Refined Fix Amendments

1. Narrow every inheritance claim to `custom_components.windmillac.blynk_service` in a clean process.
2. Remove full request URL, response text, and raw response-object logging while retaining safe operation/status messages.
3. Convert `requests.exceptions.RequestException` into token-free operation failures with exception chaining suppressed.
4. Require exact request/return preservation, non-mutating logger capture, reflected-body and exception sentinels, and complete global-state cleanup in tests.
5. Run the new suite through explicit `python3` discovery in the existing hassfest workflow.
6. Document full restart as the upgrade transition and record adjacent logger/token-identity concerns as follow-up debt.

## Final Verdict

**APPROVED**

**Root Cause Confidence**: High

**Conditions**:
- Production edits remain within `blynk_service.py`; adjacent logger and identity debt is not mixed into this patch.
- Successful request URLs, response parsing, executor use, and return values remain byte-for-byte behaviorally equivalent.
- Request exceptions surface only stable token-free operation text and suppress the raw request exception context.
- The hosted PR gate runs the dependency-free suite.

**Required Regression Tests**:
- Fresh-import Blynk logger inheritance and suppressed debug under parent `WARNING`.
- Exact get/set requests and returns at parent `DEBUG` with no request or reflected-response sentinel in records.
- Token-bearing request exceptions yield only stable token-free surfaced/loggable text.

**Iteration**: 1 of 2 max
