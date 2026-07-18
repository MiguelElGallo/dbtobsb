# Commands

Run lifecycle commands from the release checkout and the macOS account that
performed installation.

## Product lifecycle

| Command | Result | Approval | Final App state |
| --- | --- | --- | --- |
| `dbtobsb bootstrap` | Install or safely resume | Exact resource and permission preview | `STOPPED` |
| `dbtobsb start` | Start the read-only App | App compute acknowledgement | `ACTIVE` |
| `dbtobsb stop` | Stop App compute and pause reconciliation | None | `STOPPED` |
| `dbtobsb uninstall --retain` | Remove runtime and keep evidence | Type `RETAIN` | Removed |
| `dbtobsb uninstall --delete` | Remove runtime and all nine product objects | Two destructive acknowledgements | Removed |

From the repository source environment, use:

```console
uv run --project installer --no-sync dbtobsb <command>
```

An interrupted operation keeps a protected local state file. Resume by running the
same command and mode. Do not delete the state file or switch uninstall modes.

## Project onboarding

`dbtobsb bootstrap` performs supported project onboarding. It derives connection
fields from authenticated preflight, generates the sealed project snapshot, and
deploys the observed Job only after the attended preview is approved.

`dbtobsb-onboard-dbt-project` is an internal implementation entry point. It is not
a supported operator workflow, and its internal target document must not be used to
bypass bootstrap discovery and approval.

## Local artifact inspection

```text
dbtobsb-capture inspect-artifact-pair \
  --manifest PATH \
  --run-results PATH \
  [--json] \
  [--no-color]
```

| Exit code | Meaning |
| ---: | --- |
| `0` | Inspection completed and the pair is valid. |
| `10` | Inspection completed and the pair is invalid. |
| `2` | The command arguments are invalid. |
| `3` | An input could not be read safely. |
| `4` | The inspector had an internal error. |

The inspector accepts closed regular files up to 128 MiB each. It does not upload,
copy, delete, or retain them.

## Commands that operators do not supply

The installed Jobs generate their own IDs, paths, selector, dbt flags, task
coordinates, and destination values. Do not add caller-supplied SQL, run IDs, Job
IDs, log paths, artifact paths, or task overrides.
