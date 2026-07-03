import re


def clean_text(text):

    if not isinstance(text, str):
        return ""

    text = text.lower()

    text = re.sub(r"http\S+", "", text)

    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_dataframe(df):

    df["content"] = df["content"].apply(clean_text)

    return df
