def normalize_query_label(label):
    """
    Match LF1 normalization:
    - lowercase
    - trim
    - collapse spaces
    """
    if not label:
        return None

    normalized = str(label).strip().lower()
    normalized = " ".join(normalized.split())

    return normalized if normalized else None


def build_single_label_query(label):
    """
    Search for photos containing one label.
    Example: dog
    """
    label = normalize_query_label(label)

    if not label:
        return {"query": {"match_none": {}}}

    return {
        "query": {
            "term": {
                "labels": label
            }
        }
    }


def build_group_label_query(labels, mode="and"):
    """
    Search for photos containing multiple labels.

    mode='and':
      photo must contain all labels.
      Useful for query: cats and dogs

    mode='or':
      photo can contain any label.
      Useful for broader search behavior.
    """
    normalized_labels = []

    for label in labels:
        normalized = normalize_query_label(label)
        if normalized and normalized not in normalized_labels:
            normalized_labels.append(normalized)

    if not normalized_labels:
        return {"query": {"match_none": {}}}

    clauses = [{"term": {"labels": label}} for label in normalized_labels]

    if mode == "or":
        return {
            "query": {
                "bool": {
                    "should": clauses,
                    "minimum_should_match": 1
                }
            }
        }

    return {
        "query": {
            "bool": {
                "must": clauses
            }
        }
    }


if __name__ == "__main__":
    print("Single label query:")
    print(build_single_label_query("Dog"))

    print("\nGroup AND query:")
    print(build_group_label_query(["Dog", "Park"], mode="and"))

    print("\nGroup OR query:")
    print(build_group_label_query(["Dog", "Park"], mode="or"))