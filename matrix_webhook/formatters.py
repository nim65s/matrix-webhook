"""Formatters for matrix webhook."""


def grafana(data, headers):
    """Pretty-print a grafana notification."""
    text = ""
    if "title" in data:
        text = "### " + data["title"] + "\n"
    if "message" in data:
        text = text + data["message"] + "\n\n"
    if "evalMatches" in data:
        for match in data["evalMatches"]:
            text = text + "* " + match["metric"] + ": " + str(match["value"]) + "\n"
    data["body"] = text
    return data
