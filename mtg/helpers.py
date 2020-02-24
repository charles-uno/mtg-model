def rmchars(text, chars):
    for c in chars:
        text = text.replace(c, "")
    return text

def slug(text):
    return rmchars(text, "',").lower().replace(" ", "_").replace("-", "_")


def highlight(text, color=None):
    if color == "green":
        return "\033[32m" + text + "\033[0m"
    if color == "blue":
        return "\033[36m" + text + "\033[0m"
    if color == "brown":
        return "\033[33m" + text + "\033[0m"
    if color == "red":
        return "\033[31m" + text + "\033[0m"
    if color == "magenta":
        return "\033[0;35m" + text + "\033[0m"
    return text
