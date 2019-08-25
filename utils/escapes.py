def escape(text, *, mass_mentions=True, formatting=True, invites=False, mentions=False, urls=False, markdown=False):
    if mass_mentions:
        text = text.replace("@everyone", "@\u200beveryone")
        text = text.replace("@here", "@\u200bhere")
    if formatting:
        text = (text.replace("`", "\\`")
                .replace("*", "\\*")
                .replace("_", "\\_")
                .replace("~", "\\~"))
    if invites:
        # invites are basically sub of urls, since urls do this to the https part
        text = text.replace('ord.gg', 'ord\u200b.gg')

    if mentions:
        text = text.replace('@', '@\u200b').replace('#', '#\u200b')

    if urls:
        text = text.replace('http', 'http\u200b')
    return text


def escape_mass_mentions(text):
    return escape(text, mass_mentions=True)


def escape_markdown(text):
    return escape(text, formatting=True)


def escape_urls(text):
    return escape(text, urls=True)


def escape_invites(text):
    return escape(text, invites=True)


def escape_all_mentions(text):
    return escape(text, mentions=True)