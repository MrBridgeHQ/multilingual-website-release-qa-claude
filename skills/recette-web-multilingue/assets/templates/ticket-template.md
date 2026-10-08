# <ID> - [LANG][device] <where>: <what is wrong>

- Status: OPEN | FIXED_VERIFIED | STILL_FAILING | NOT_RETESTED
- Severity: BLOCKER | MAJOR | MINOR | COSMETIC - Rationale: <who is affected, what they cannot do, workaround or not>
- Confidence: HIGH | MEDIUM | LOW
- Impact: <user-facing consequence in one or two sentences>
- Observed scope: languages <..>, devices <..>, pages <..>
- Preconditions: <state before step 1>
- Test data: <non-sensitive values only>

## Steps to reproduce

1. Open <absolute URL> on <device profile / viewport>.
2. <action>
3. <action>

## Expected

<from the config, the specification or an explicit assumption>

## Observed

<factual, with the site's text quoted verbatim in its original language>

- Reproduction: reproduced <k>/<n>
- Evidence: evidence/<case_id>/<file>
- Linked cases: <case ids>

## Fix hypothesis

Hypothesis: <likely cause and where to look> (state "Proven:" only if the cause is demonstrated)

## Acceptance criteria

- [ ] <observable check 1>
- [ ] <observable check 2>
- [ ] The linked cases pass on re-run and no other case regresses.

## Retest procedure

<runner command with --journeys/--languages, then the manual steps above>
