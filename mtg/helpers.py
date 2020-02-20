def rmchars(text, chars):
    for c in chars:
        text = text.replace(c, "")
    return text

def slug(text):
    return rmchars(text, "',").lower().replace(" ", "_").replace("-", "_")
