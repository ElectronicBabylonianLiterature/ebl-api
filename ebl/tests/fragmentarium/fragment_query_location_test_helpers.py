MALFORMED_MARKERS: tuple[dict[str, object], ...] = (
    {"type": []},
    {"type": {}},
    {"type": None},
    {"type": "ObjectAtLine"},
    {"type": "ColumnAtLine", "column_label": {"status": [], "column": -1}},
    {"type": "ColumnAtLine", "column_label": {"status": [], "column": 400000}},
    {
        "type": "SurfaceAtLine",
        "surface_label": {"status": [], "surface": "OBVERSE"},
    },
    {
        "type": "SurfaceAtLine",
        "surface_label": {"status": [], "surface": "OBVERSE", "text": "invalid"},
    },
    {
        "type": "SurfaceAtLine",
        "surface_label": {
            "status": ["UNCERTAIN", "UNCERTAIN"],
            "surface": "OBVERSE",
            "text": "",
        },
    },
    {
        "type": "SurfaceAtLine",
        "surface_label": {"status": [], "surface": "REVERSE", "text": ""},
        "storedOnly": 1,
    },
)

MALFORMED_MARKER_IDS = (
    "array-type",
    "object-type",
    "missing-type",
    "missing-object-label",
    "negative-column",
    "large-column",
    "sparse-surface-label",
    "invalid-domain-text",
    "duplicate-status",
    "unknown-field",
)
