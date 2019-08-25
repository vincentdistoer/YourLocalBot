from utils.escapes import *


def pagify(text: str, delims=["\n"], *, escape_stuff=False, shorten_by=8,
           page_length=2000):
    """DOES NOT RESPECT MARKDOWN BOXES OR INLINE CODE"""
    in_text = text
    if escape:
        num_mentions = text.count("@here") + text.count("@everyone")
        shorten_by += num_mentions
    page_length -= shorten_by
    while len(str(in_text)) > page_length:
        closest_delim = max([in_text.rfind(d, 0, page_length)
                             for d in delims])
        closest_delim = closest_delim if closest_delim != -1 else page_length
        if escape:
            to_send = escape_mass_mentions(in_text[:closest_delim])
        else:
            to_send = in_text[:closest_delim]
        yield to_send
        in_text = in_text[closest_delim:]

    if escape_stuff:
        yield escape(in_text, mentions=True, mass_mentions=True, formatting=True)
    else:
        yield in_text


