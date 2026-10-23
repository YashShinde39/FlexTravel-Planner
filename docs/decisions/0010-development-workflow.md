# ADR-0010: Ownership split, small PRs, restart from scratch

- Status: Accepted
- Date: 2026-10-23

## Context

The project is built with an AI assistant (Claude) and will be presented in interviews.
The owner needs genuine authorship of the critical parts and the ability to defend every
major decision. An initial scaffold (FastAPI, a McA\* engine, a React UI) was generated
before these decisions were made.

## Decision

**Who builds what:**

| Part | Mode |
| --- | --- |
| RAPTOR / McRAPTOR | **Guided build**: Claude explains with a worked example and provides a skeleton and failing tests; the owner implements the core and Claude reviews |
| GTFS import pipeline | **Claude writes, owner extends**: the owner reviews, owns the data-quality decisions, and implements one stage (transfer linking between agencies) |
| API, data model, frontend | **Claude writes, owner reviews and modifies** |

**How:**

- Small pull requests, one concept each, each explaining what changed and why. The owner
  reviews and merges on GitHub; Claude never merges.
- Every significant decision gets an ADR with a *Why (in my words)* section written by the
  owner.
- **Restart from scratch.** The earlier scaffold is kept on a local `archive/initial-scaffold`
  branch for reference only and is not merged.
- **Data before code.** The first technical PR inspects the real Delhi feeds before any
  application skeleton is built.

## Alternatives considered

- **Owner writes everything.** Maximum ownership, but slow.
- **Claude writes everything, owner reviews.** Fast, but weak ownership of the parts an
  interviewer will probe.
- **Merge the existing scaffold as one PR.** Faster, but too much code to review properly.

## Consequences

- The routing milestone takes longer and depends on the owner's time.
- The git history and PR reviews become evidence of the owner's involvement.

## Why (in my words)

> _To fill in: how do you describe your role in this project, honestly, in one paragraph?_

## Questions an interviewer might ask

- What did you build yourself, and what did the AI build?
- Tell me about a time you disagreed with a generated design and changed it.
