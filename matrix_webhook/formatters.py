"""Formatters for matrix webhook."""

import re
from . import utils


def grafana(data, headers):
    """Pretty-print a Grafana (version 8 and older) notification."""
    text = ""
    if "ruleName" not in data and "alerts" in data:
        return grafana_9x(data, headers)
    if "title" in data:
        text = "#### " + data["title"] + "\n"
    if "message" in data:
        text = text + data["message"] + "\n\n"
    if "evalMatches" in data:
        for match in data["evalMatches"]:
            text = text + "* " + match["metric"] + ": " + str(match["value"]) + "\n"
    data["body"] = text
    return data


def grafana_9x(data, headers):
    """Pretty-print a Grafana newer than v9.x notification."""
    text = ""
    if "title" in data:
        text = "#### " + data["title"] + "\n"
    if "message" in data:
        text = text + data["message"].replace("\n", "\n\n") + "\n\n"
    data["body"] = text
    return data


def github(data, headers):
    """Pretty-print a github notification."""
    # TODO: Write nice useful formatters. This is only an example.
    if headers["X-GitHub-Event"] == "push":
        pusher, ref, a, b, c = (
            data[k] for k in ["pusher", "ref", "after", "before", "compare"]
        )
        pusher = f"[@{pusher['name']}](https://github.com/{pusher['name']})"
        data["body"] = f"{pusher} pushed on {ref}: [{b} → {a}]({c}):\n\n"
        for commit in data["commits"]:
            data["body"] += f"- [{commit['message']}]({commit['url']})\n"
    else:
        data["body"] = "notification from github"
    data["digest"] = headers["X-Hub-Signature-256"].replace("sha256=", "")
    return data


def gitlab_gchat(data, headers):
    """Pretty-print a gitlab notification preformatted for Google Chat."""
    data["body"] = re.sub(
        "<(.*?)\\|(.*?)>",
        "[\\2](\\1)",
        data["body"],
        flags=re.MULTILINE,
    )
    return data


def gitlab_teams(data, headers):
    """Pretty-print a gitlab notification preformatted for Microsoft Teams."""
    body = []
    for section in data["sections"]:
        if "text" in section.keys():
            text = section["text"].split("\n\n")
            text = ["* " + t for t in text]
            body.append("\n" + "  \n".join(text))
        elif all(
            k in section.keys()
            for k in ("activityTitle", "activitySubtitle", "activityText")
        ):
            text = section["activityTitle"] + " " + section["activitySubtitle"] + " → "
            text += section["activityText"]
            body.append(text)

    data["body"] = "  \n".join(body)
    return data


def gitlab_webhook(data, headers):
    """Pretty-print a gitlab notification.

    NB: This is a work-in-progress minimal example for now
    """
    body = []

    event_name = data["event_name"]
    user_name = data["user_name"]
    project = data["project"]

    body.append(f"New {event_name} event")
    body.append(f"on [{project['name']}]({project['web_url']})")
    body.append(f"by {user_name}.")

    data["body"] = " ".join(body)
    if "X-Gitlab-Token" in headers:
        data["key"] = headers["X-Gitlab-Token"]
    return data


def grn(data, headers):
    """Pretty-print a github release notifier (grn) notification."""
    version, title, author, package = (
        data[k] for k in ["version", "title", "author", "package_name"]
    )
    data["body"] = (
        f"### {package} - {version}\n\n{title}\n\n"
        f"[{author} released new version **{version}** for **{package}**]"
        f"(https://github.com/{package}/releases/tag/{version}).\n\n"
    )

    return data


def slack(data, headers):
    """Pretty-print a slack notification."""
    text = ""
    if "text" in data:
        text = text + "<div>" + utils.format_url(data["text"]) + "</div>\n"
    if "attachments" in data and len(data["attachments"]):
        for attachment in data["attachments"]:
            text = text + "<div>"
            if "title_link" in attachment and "title" in attachment:
                text = text + "<h4><a href=\"" + attachment["title_link"] + "\">" + attachment["title"] + "</a></h4>\n"
            elif "title" in attachment:
                text = text + "<h4>" + utils.format_url(attachment["title"]) + "</h4>\n"
            if "text" in attachment:
                text = text + utils.format_url(attachment["text"]) + "\n"

            if "fields" in attachment and len(attachment["fields"]):
                for field in attachment["fields"]:
                    text = text + "<div>"
                    if "title" in field:
                        text = text + "<h5>" + utils.format_url(field["title"]) + "</h5>\n"
                    if "value" in field:
                        text = text + utils.format_url(str(field["value"])) + "\n"
                    text = text + "</div>"
            text = text + "</div>"
    data["body"] = text
    return data

