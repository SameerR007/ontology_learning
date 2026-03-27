abc = [
    { "start_label": "ImagingModality", "type": "COMBINED_WITH", "end_label": "ContrastAgent" },
    { "start_label": "ImagingModality", "type": "EVALUATES", "end_label": "Disease" },
    { "start_label": "ImagingModality", "type": "TARGETS", "end_label": "AnatomicalRegion" },
    { "start_label": "Disease", "type": "LOCATED_IN", "end_label": "AnatomicalRegion" }
]

print({ "start_label": "ImagingModality", "type": "COMBINED_WITH", "end_label": "ContrastAgent" } in abc)