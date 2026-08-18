# UI-D1.5 Cockpit Fix Attestation v1.0

**STATUS: FROZEN**

## Defect

`templates/cockpit.html` line 53 originally used:

```
{% for item in snapshot.panels.attention.data.items %}
```

Jinja2 resolved `.items` as `dict.items` (method), not the `"items"` list key. Non-empty attention queues raised:

`TypeError: 'builtin_function_or_method' object is not iterable`

## Frozen correction

```
{% for item in snapshot.panels.attention.data['items'] %}
```

Read-model shape in `cockpit_read_model.py` is unchanged: `data={"items": attention_items, "count": ...}`.

Empty / unavailable panel states still skip the loop.

## Proof

`tests/test_ui_d1_5_live_demo_baseline_freeze.py::test_cockpit_attention_items_regression`  
`tests/test_ui_d1_founder_demo.py::test_cockpit_renders_with_attention_items`
