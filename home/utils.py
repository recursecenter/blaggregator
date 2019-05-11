import bs4


def is_medium_comment(entry):
    """Check if a link is a medium comment."""

    link = entry.link or ""
    if "medium.com" not in link:
        return False

    content = entry.summary or ""
    title = entry.title or ""
    soup = bs4.BeautifulSoup(content, "lxml")
    # Medium comments set their title from the content of the comment. So, we
    # verify if the content starts with the content.
    text_content = soup.text.encode("ascii", "replace").replace("?", " ")
    title = title.encode("ascii", "replace").replace("?", " ").strip()
    is_comment = text_content.startswith(title)
    return is_comment
