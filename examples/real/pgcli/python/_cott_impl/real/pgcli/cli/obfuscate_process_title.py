import re


def obfuscate_process_title(title: str) -> str:
    if "://" in title:
        return re.sub(r":(.*):(.*)@", r":\1:xxxx@", title)
    if "=" in title:
        return re.sub(r"password=(.+?)((\s[a-zA-Z]+=)|$)", r"password=xxxx\2", title)
    return title
