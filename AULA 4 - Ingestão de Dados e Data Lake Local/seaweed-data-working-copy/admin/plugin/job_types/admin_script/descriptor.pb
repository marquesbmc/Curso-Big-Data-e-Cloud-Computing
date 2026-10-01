
admin_scriptAdmin Script@Run custom admin shell scripts not covered by built-in job types"fas fa-terminal(2Ž
admin-script-adminAdmin Script Configuration)Define the admin shell script to execute."Š
scriptScript5Commands run sequentially by the admin script worker."Î
scriptScript/Admin shell commands to execute (one per line)."PLock/unlock are handled by the admin server; omit explicit lock/unlock commands.*3volume.balance -apply
volume.fix.replication -apply08@"p
run_interval_minutesRun Interval (minutes)6Minimum interval between successful admin script runs.08@Z*
run_interval_minutes*‡
script}"{fs.log.purge -daysAgo=7
volume.deleteEmpty -quietFor=24h -apply
volume.fix.replication -apply
s3.clean.uploads -timeAgo=24hB¬ (0@HˆPˆ