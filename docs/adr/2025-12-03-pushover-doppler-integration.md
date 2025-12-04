---
status: accepted
date: 2025-12-03
decision-maker: Terry Li
consulted: [Explore-Agent-Pushover, Explore-Agent-Doppler]
research-method: single-agent
clarification-iterations: 3
perspectives: [UpstreamIntegration, SecurityBoundary, OperationalService]
---

# ADR: Pushover Doppler Integration for crypto-marketcap-rank

**Design Spec**: [Implementation Spec](/docs/design/2025-12-03-pushover-doppler-integration/spec.md)

## Context and Problem Statement

The crypto-marketcap-rank repository currently uses Pushover notifications via the shared `notifications` Doppler project. This creates coupling between repositories and prevents repository-specific notification identity (app icon/name in Pushover). We need a dedicated Doppler project with new Pushover credentials for proper separation of concerns.

### Before/After

```
                     🔄 Doppler Project Migration

┌−−−−−−−−−−−−−−−−−−−−−−−┐            ┌−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−┐
╎ Before:               ╎            ╎ After:                        ╎
╎                       ╎            ╎                               ╎
╎ ┌───────────────────┐ ╎            ╎ ┌───────────────────────────┐ ╎
╎ │ notifications/dev │ ╎  migrate   ╎ │ crypto-marketcap-rank/prd │ ╎
╎ │     (shared)      │ ╎ ─────────> ╎ │        (dedicated)        │ ╎
╎ └───────────────────┘ ╎            ╎ └───────────────────────────┘ ╎
╎                       ╎            ╎                               ╎
└−−−−−−−−−−−−−−−−−−−−−−−┘            └−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−┘
```

<details>
<summary>graph-easy source</summary>

```
graph { label: "🔄 Doppler Project Migration"; flow: east; }
( Before:
  [notifications/dev] { label: "notifications/dev\n(shared)"; }
)
( After:
  [cmr/prd] { label: "crypto-marketcap-rank/prd\n(dedicated)"; }
)
[notifications/dev] -- migrate --> [cmr/prd]
```

</details>

## Research Summary

| Agent Perspective      | Key Finding                                                   | Confidence |
| ---------------------- | ------------------------------------------------------------- | ---------- |
| Explore-Agent-Pushover | Two workflows use Pushover: monitor-collection, test-pushover | High       |
| Explore-Agent-Pushover | Current config: `--project notifications --config dev`        | High       |
| Explore-Agent-Doppler  | Secrets: PUSHOVER_APP_TOKEN, PUSHOVER_USER_KEY                | High       |
| Explore-Agent-Doppler  | GitHub secret: DOPPLER_TOKEN scoped to notifications/dev      | High       |

## Decision Log

| Decision Area  | Options Evaluated              | Chosen     | Rationale                                      |
| -------------- | ------------------------------ | ---------- | ---------------------------------------------- |
| Doppler Config | dev, prd                       | prd        | Production environment for daily automation    |
| GitHub Secret  | Replace DOPPLER_TOKEN, New one | New secret | Avoid breaking other workflows using old token |
| Service Token  | Manual, CLI                    | CLI        | Agent has Doppler CLI access                   |

### Trade-offs Accepted

| Trade-off               | Choice     | Accepted Cost                      |
| ----------------------- | ---------- | ---------------------------------- |
| Multiple GitHub secrets | New secret | Slightly more secrets to manage    |
| prd vs dev config       | prd        | No staging environment for testing |

## Decision Drivers

- Separation of concerns: Each repo should have its own notification identity
- New Pushover app credentials provided by user (distinct logo/name)
- Minimize disruption to existing `notifications` project consumers
- Production-grade setup (using `prd` config)

## Considered Options

- **Option A**: Continue using shared `notifications` project
- **Option B**: Create dedicated `crypto-marketcap-rank` Doppler project with `prd` config <- Selected
- **Option C**: Use environment variables directly in GitHub Actions (no Doppler)

## Decision Outcome

Chosen option: **Option B**, because it provides proper separation of concerns with a dedicated Doppler project per repository, enabling unique notification identity while maintaining centralized secrets management via Doppler.

## Synthesis

**Convergent findings**: Both exploration agents confirmed the current architecture uses `notifications/dev` Doppler project with two workflow files needing updates.

**Divergent findings**: Initial plan used `dev` config; user clarified `prd` is preferred.

**Resolution**: User specified `prd` config for production environment and new GitHub secret to avoid breaking existing workflows.

## Consequences

### Positive

- Repository has dedicated notification identity (unique Pushover app icon/name)
- Decoupled from shared `notifications` project
- Production-grade secrets management via Doppler

### Negative

- Additional GitHub secret to maintain (`DOPPLER_TOKEN_CMR`)
- Doppler project sprawl (one more project to manage)

## Architecture

```
🏗️ Pushover Notification Architecture

                              secrets
  ┌──────────────────────────────────────────────────┐
  │                                                  ∨
╔═══════════════════════════╗                      ╭─────────────────╮
║          Doppler          ║  DOPPLER_TOKEN_CMR   │ GitHub Actions  │
║ crypto-marketcap-rank/prd ║ <─────────────────── │   (workflows)   │
╚═══════════════════════════╝                      ╰─────────────────╯
                                                     │
                                                     │ HTTP POST
                                                     ∨
                                                   ┌─────────────────┐
                                                   │  Pushover API   │
                                                   │ (notifications) │
                                                   └─────────────────┘
                                                     │
                                                     │ push
                                                     ∨
                                                   ╭─────────────────╮
                                                   │  Mobile Device  │
                                                   ╰─────────────────╯
```

<details>
<summary>graph-easy source</summary>

```
graph { label: "🏗️ Pushover Notification Architecture"; flow: south; }
[gha] { label: "GitHub Actions\n(workflows)"; shape: rounded; }
[doppler] { label: "Doppler\ncrypto-marketcap-rank/prd"; border: double; }
[pushover] { label: "Pushover API\n(notifications)"; }
[device] { label: "Mobile Device"; shape: rounded; }
[gha] -- DOPPLER_TOKEN_CMR --> [doppler]
[doppler] -- secrets --> [gha]
[gha] -- HTTP POST --> [pushover]
[pushover] -- push --> [device]
```

</details>

## References

- [Doppler Documentation](https://docs.doppler.com/)
- [Pushover API](https://pushover.net/api)
- [ADR-0009: Documentation Rectification](/docs/adr/0009-documentation-rectification.md)
