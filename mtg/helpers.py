
def rmchars(text, chars):
    for c in chars:
        text = text.replace(c, "")
    return text
