import re

def sanitize_filename(name: str) -> str:
    """
    Removes illegal characters from a string to make it a valid filename.
    """
    # Remove illegal characters
    name = re.sub(r'[\\/*?:"<>|]',"", name)
    # Replace spaces with underscores
    name = name.replace(" ", "_")
    return name