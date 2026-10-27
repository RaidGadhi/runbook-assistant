# DNS troubleshooting

Scope: Linux clients and application dependencies. These notes are for a synthetic
lab. Commands are reviewed separately in commands.json.

## Isolate name resolution

A successful direct HTTP check alongside a failed lookup supports investigating
name resolution before application restarts. It does not prove that a DNS record
is missing. A resolver timeout differs from NXDOMAIN: one means the query did not
receive a usable response in time; the other is a negative answer for the name.

Inspect the active resolver configuration, query the same hostname against the
configured resolver, and compare the result with an application health check.
An active systemd service alone does not establish end-to-end application health.

## Verify the affected user path

After an approved change, repeat the hostname lookup and the application request
from an affected client. A successful direct backend request only checks part of
the path. Record the time of each observation and confirm that the result is
repeatable. Do not report recovery merely because a process is running.
