# Evidence collection

Scope: incomplete or conflicting incident reports.

## Collect a current baseline

A report that an application is slow is a symptom, not a diagnosis. Ask which
host and service are affected, when the slowdown started, and whether it affects
one client or several. Collect current service, name-resolution, network, and
dependency observations. Record timestamps so the events can be correlated.

## Handle conflicting observations

If two observations report different states, check their timestamps, hostnames,
and collection method before treating either as the current state.
Preserve both observations and ask for a new check. Do not silently discard
contradictory evidence to make a familiar diagnosis fit.
