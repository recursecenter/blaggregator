import bs4


def is_medium_comment(entry):
    """Check if a link is a medium comment."""

    link = getattr(entry, "link", getattr(entry, "url", ""))
    if "medium.com" not in link:
        return False

    content = getattr(entry, "summary", getattr(entry, "content", ""))
    title = entry.title or ""
    soup = bs4.BeautifulSoup(content, "lxml")
    # Medium comments set their title from the content of the comment. So, we
    # verify if the content starts with the content.
    text_content = soup.text.strip()
    is_comment = text_content.startswith(title.strip())
    return is_comment
