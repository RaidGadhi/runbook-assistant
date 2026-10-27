# Shared storage troubleshooting

Scope: Linux device-mapper multipath and shared storage. Read-only investigation.

## Inspect path redundancy

One active path out of four expected paths indicates degraded redundancy.
It does not establish a failed SAN controller. Compare multipath output across
hosts, correlate path failures with kernel events, and review the array's events.
Elevated I/O wait can accompany degraded paths, but one latency sample cannot
establish causality.

Do not clear persistent reservations, remove multipath devices, deactivate shared
volumes, or repair a clustered filesystem as part of this investigation.

## Correlate latency with the event window

Collect several device latency samples and inspect kernel events from the same
time window. A busy guest, host queueing, an array issue, or a path problem can
produce similar symptoms. Ask for the peer host and storage array observations
before selecting a recovery action.
