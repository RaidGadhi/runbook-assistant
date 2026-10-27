# Oracle standby troubleshooting

Scope: Data Guard observations from a synthetic primary/standby environment.

## Separate transport and apply lag

Transport lag concerns redo receipt at the standby; apply lag concerns redo
replay. A stopped apply process and measurable lag require separate checks of
broker status, redo transport, and the standby alert log. Neither lag nor a
broker warning alone establishes data loss.

Read current database roles and lag measurements. Record the observation time.
Do not infer that a failover is safe from these observations.

## Preserve the role transition boundary

Failover and switchover are recovery decisions requiring the database owner's
review of roles, protection mode, observer state, and redo availability.
This assistant only proposes investigation checks. It cannot authorize or
execute a role transition.
