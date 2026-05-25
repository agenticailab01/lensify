# Narrative Panel Prompt

When the scan runs without `--ast-only`, the narrative panel uses one LLM call to produce ~180 words of Day-1 onboarding prose.

## Inputs the model receives

The script writes `lens.json` first. Pass these fields ONLY (not the full file):

- `summary` (string)
- `entry_points` (list of {path, role})
- `modules` (list of {path, purpose})
- `languages` (dict)
- `hotspots` (list of {path, churn})
- `risks` (list)
- `conventions` (list)

Do not pass the full file tree, raw code, or git log. The capsule is the upper bound of what the narrative needs.

## Prompt template

```
You are writing a 180-word Day-1 narrative for a new joiner reading
this codebase for the first time. The reader may not be a developer —
write in plain English. No jargon, no acronyms without expansion.

Cover, in this order:
1. What the project IS (one sentence, no marketing).
2. The shape of it (how the modules fit together — pipeline? layered? hub?).
3. Where the action is (hotspots — which files change a lot and why).
4. What's brittle or unknown (one or two honest caveats).
5. The first thing the reader should open.

Hard rules:
- 180 words ±10. Hit the count.
- No bullet points. Flowing prose only.
- Do not invent. If the data doesn't support a claim, omit it.
- Preserve confidence tags from RISKS (mark inferences as "appears to" or
  "looks like" rather than stating as fact).
- End with one concrete next step: "Open <path> first."

Project data:
{lens_json_subset}
```

## Fallback if no LLM available

If the scan ran in `--ast-only` mode, the script emits a template-filled narrative using slots:

```
This project is a {project_kind} written in {primary_language}. It is
organized as {shape} across {n_modules} top-level modules. The most
active areas are {hotspot_1} and {hotspot_2}, which together account
for roughly {pct}% of recent changes. {primary_risk_phrase}. To get
oriented, open {entry_path} first — that's where the application
starts.
```

This template fallback is intentionally shorter (~80 words) and clearly less polished than the LLM version. Users running `--ast-only` accept that trade-off.

## Length enforcement

The skill should reject any narrative outside 150–210 words and re-prompt once with `"too long, trim to 180"` or `"too short, expand to 180"`. After one retry, accept whatever was produced.
