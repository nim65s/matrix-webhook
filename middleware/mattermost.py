import re
import json
from typing import Optional, Sequence, Dict, Union

link_regexp = re.compile(r'<([^|]*)\|([^>]*)>')
link_template = r'<a href="\1">\2</a>'


def mattermost(data: dict):
    """Middleware to process a request to a mattermost webhook"""

    if 'payload' in data:  # data sent as application/x-www-form-urlencoded
        data = json.loads(data['payload'])
    attachments = '\n'.join(format_attachment(**a) for a in data.get('attachments', ()))
    fallback = data.get('fallback')
    text = '\n'.join(
        entry
        for entry in (link_regexp.sub(link_template, data.get('text', '')), attachments)
        if entry
    )
    if not text and fallback:
        text = link_regexp.sub(link_template, fallback)
    if data.get('text', '') == text:
        # Nothing has been formatted - dont prevent markdown formatting
        return data
    return {**data, 'formatted_text': text}


def format_attachment(
    title: Optional[str] = None,
    title_link: Optional[str] = None,
    author_name: Optional[str] = None,
    author_icon: Optional[str] = None,
    author_link: Optional[str] = None,
    fields: Sequence[Dict[str, Union[str, bool]]] = (),
    **_,
) -> str:
    """Formats a mattermost attachment to html"""
    author_icon = author_icon and f'<img src="{author_icon}" alt="author" width="20">'
    if author_name and author_link:
        author_name = f'<a href="{author_link}">{author_name}</a>'
    author_line = ' '.join(
        part for part in (author_icon, author_name) if part is not None
    )
    title = make_link(title or '', title_link)
    lines = [l for l in (author_line, title) if l] + list(format_fields(fields))
    return '\n'.join(lines)


def make_link(alt: str, link: Optional[str] = None):
    """Outputs a html a tag"""
    if link is None:
        return alt
    return f'<a href="{link}">{alt}</a>'


def format_fields(fields: Sequence[Dict[str, Union[str, bool]]]) -> Sequence[str]:
    """Formats fields inside a mattermost attachment"""
    if not fields:
        return ()
    entries = (
        (f['title'], link_regexp.sub(link_template, str(f['value']))) for f in fields
    )
    lines = [
        f'<tr><td><b>{title}</b></td><td>{value}</td></tr>' for title, value in entries
    ]
    return ['<table>'] + lines + ['</table>']


json_middlewares = [mattermost]
