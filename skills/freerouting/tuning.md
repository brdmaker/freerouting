# Tuning freerouting results

Always: fix one variable per run, keep the same `--router.autorouter.item_order_seed` when comparing,
and judge by KiCad DRC + your eyes. Settings sources by priority (high wins): API > GUI > CLI
(`--router.*`) > env (`FREEROUTING__ROUTER__*`) > .rules > SES > DSN > `freerouting.json` > defaults.
Full reference: docs/settings.md and docs/command_line_arguments.md in the freerouting repo.

## Vias too close to pads (tested)

Default via-to-pad gap is the board clearance (e.g. 0.3 mm). Raise it for via<->pad only:

1. In the DSN `(structure (rule ...))` block add (um):
   ```
   (clearance 600 (type smd_via))     ; via to SMD pad
   (clearance 600 (type pin_via))     ; via to through-hole pad
   ```
   Measured on a 2-layer 69-via board: vias under 0.4 mm from a pad 33 -> 14, median gap 0.50 -> 0.72 mm,
   still 0 unrouted, but the optimizer took ~4x longer. Vias on the same net as the pad may still touch it
   (same-net clearance does not apply).
2. Or keep it in KiCad: a custom rule in `board.kicad_dru`, passed with `-de board.dsn+board.kicad_dru`:
   ```
   (version 1)
   (rule "via_to_pad" (condition "A.Type == 'Via' && B.Pad_Type == 'SMD'") (constraint clearance (min 0.6mm)))
   ```
   (supported conditions: NetClass, NetName, Type, Pad_Type, Reference, Parent, Pad_Number,
   memberOfFootprint(), hasNetclass(), isPlated(); layer clauses). Not tested by me: verify in the log
   that the rule is reported as applied, then verify the gaps.
3. Larger via pad than drill also keeps vias away from pads: define a bigger via in KiCad.

## Fewer vias / cleaner traces

- `--router.via_costs=<n>` higher = fewer layer changes (try 100-300). `--router.start_ripup_costs`
  higher = less rip-up/reroute churn.
- Optimizer decides via elimination: `--router.optimizer.improvement_threshold=` 0.5-1.0 precision
  (long), 2.5 default, 3.5-5 fast. `0` runs to `max_passes`.
- `--router.optimizer.keep_increased_ripup_costs=true` often gives a better/faster tail.
- `--router.default_preferred_direction_trace_cost` / `--router.default_undesired_direction_trace_cost`
  and `--router.layers.preferred_direction_horizontal=true,false` steer layer directions.

## Unrouted nets remain

- More passes: `--router.autorouter.max_passes=60`, `--router.autorouter.stagnation_pass_limit=0`
  (never stop on stagnation), different `--router.autorouter.item_order_seed=1..N` (cheap multi-start;
  keep the best by unrouted count, then violations, then vias).
- Loosen: `--router.automatic_neckdown` (needs `.kicad_pro` min track width), smaller clearance only
  if the fab allows; add a via type in KiCad.
- Check the board: is a net blocked by keepouts or a missing layer? `--router.layers.routable=true,true`.

## Control what routes first / what is skipped

- `-inc GND,+5V` (`ignore_net_classes`): do not route these (route by hand or as planes).
- `--router.autorouter.priority_net_classes=DIFF,ANALOG`: routed first, not ripped up by others.
- Planes: `--router.plane_nets=GND` (or draw a zone in KiCad), `--router.autorouter.plane_as_priority=true`
  drops SMD pads into the plane through own vias; `--router.plane_via_costs=` prices them.

## Escape routing of dense SMD parts (fanout)

`--router.fanout.min_escape_length_mm`, `max_escape_length_mm`, `start_via_diameter_mm`,
`end_via_diameter_mm`, `pin_sorting_order=outer_first|inner_first|surroundings_density`,
`--router.fanout.enabled=false` to turn off.

## Speed / resources

`--router.max_threads=N` (each optimizer worker deep-copies the board: peak heap scales with N),
`--router.optimizer.enabled=false`, `--router.job_timeout=HH:MM:SS`. Give the JVM more heap with
`JAVA_TOOL_OPTIONS=-Xmx4g` for big boards.

## Workflow that works

1. Route with defaults, `-mp 30`. Render and DRC. 2. Fix rules (clearances, via sizes) at the source in
KiCad, not by hand-editing the SES. 3. Re-run with 3-5 seeds, pick the best. 4. Hand-finish the last
few connections in KiCad.
