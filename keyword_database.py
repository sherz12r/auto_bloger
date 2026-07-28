import json


def load_google_suggestions():

    with open(
        "google_suggestions.json",
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)

def flatten_keywords(data):

    keywords = []

    for seed, suggestions in data.items():

        keywords.append(seed)

        keywords.extend(suggestions)

    return keywords

def remove_duplicates(keywords):

    unique = []

    seen = set()

    for keyword in keywords:

        keyword = keyword.lower().strip()

        if keyword not in seen:

            seen.add(keyword)

            unique.append(keyword)

    return unique

def save_keywords(keywords):

    with open(
        "keyword_database.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            keywords,
            file,
            indent=4,
            ensure_ascii=False
        )


if __name__ == "__main__":

    data = load_google_suggestions()

    keywords = flatten_keywords(data)

    keywords = remove_duplicates(keywords)

    save_keywords(keywords)

    print(
        len(keywords),
        "keywords saved."
    )