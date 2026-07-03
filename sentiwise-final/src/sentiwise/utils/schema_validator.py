REQUIRED_COLUMNS = [
    "sr_no",
    "content",
    "timestamp",
    "location",
    "category"
]


def validate_schema(df):

    missing = []

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            missing.append(col)

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    return True
