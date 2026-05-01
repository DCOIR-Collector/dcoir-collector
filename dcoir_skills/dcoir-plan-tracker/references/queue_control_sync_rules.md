# Queue Control sync rules

Use `Queue Control.active_plans` as the live branch pointer.

A plan-transition update is incomplete unless these agree:

1. `Queue Control.active_plans` links the active plan.
2. `Plans.plan_state` is `active` for the same plan.
3. `Plans.active_task_id` points to the active Work Item when known.
4. Work Items statuses and Queue Rank support the same next work order.

If the link is empty or stale, repair Queue Control before reporting a normal resume or closeout.
