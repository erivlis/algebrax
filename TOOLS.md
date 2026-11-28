# AI Tools Protocol

This document defines standard, executable one-liners for AI Agents to verify objective facts (Time, Math) instead of
hallucinating them.

## Usage Directive

When an Agent needs to perform a calculation or state the time, it should:

1. **Not Guess.**
2. **Propose** the command from this list.
3. **Wait** for the user to run it (or run it if the environment permits).

## Tools

### 1. Chronos (Time)

**Goal:** Get a rigorous, ISO-8601 timestamp.
**Command:**

```shell
python -c "import datetime; print(datetime.datetime.now().isoformat())"
```

### 2. Abacus (Simple Arithmetic)

**Goal:** Verify basic arithmetic to avoid token-prediction errors.
**Command:**

```shell
python -c "print({expression})"
```

*Example:* `python -c "print(123 * 456)"`

### 3. Calculator (Advanced Math)

**Goal:** Perform complex calculations (trig, log, exp) using the `math` module.
**Command:**

```shell
python -c "import math; print({expression})"
```

*Example:* `python -c "import math; print(math.sqrt(2) * math.pi)"`

### 4. Randomness (Entropy)

**Goal:** Generate a random seed or UUID.
**Command:**

```shell
python -c "import uuid; print(uuid.uuid4())"
```

### 5. Resource to Markdown

uses https://github.com/microsoft/markitdown

**Goal:** Convert a resource to Markdown format.
**Command:**

```shell
uvx --from 'markitdown[pdf]' markitdown {input_pdf} -o {output_md}
```

### 6. SonarQube CLI (Code Quality & Security)

**Goal:** Run instant local quality gate analysis against the active SonarCloud profile before committing.
**Command:**

```shell
sonar analyze --file {file_path}
```

*Examples:*
- Single file: `sonar analyze --file src/algebrax/analysis.py`
- Multiple files: `sonar analyze --file src/algebrax/matrix/core.py --file src/algebrax/transforms.py`
- Check authentication: `sonar auth status`

## Shell Execution Hygiene (Windows / PowerShell)

When running verification tools (`pytest`, `ruff`, `pyrefly`, `zensical`, `git`) on Windows PowerShell:

1. **One executable per `run_command` call:** Do not chain multiple tools with `;` (e.g., `ruff ...; pytest ...`), which can leave lingering ConPTY handles and zombie `RUNNING` background tasks.
2. **Keep fast checks synchronous:** Pass `WaitMsBeforeAsync=10000` for targeted tests, linters, type checks, and git queries so they return directly instead of registering background tasks.
3. **Set timeouts on long runs:** Reserve background execution for full-suite `pytest` or `zensical build` and always specify `NotificationTimeoutSeconds`.
4. **Handle zombie tasks early:** If `manage_task(list)` shows a finished task stuck as `RUNNING` even after `manage_task(kill)` and no OS process remains, finish the current milestone and advise rotating to a fresh conversation to reset the task registry.

