

REPLACEMENTS = {
    "'": "\"", 
    "True": ''' "True" ''',
      "False": ''' "False" ''', 
      "None": ''' "None" '''}

def clean_string(string: str) -> str:
    """
    Cleans a string returned from the API so that it is properly formed JSON.
    """
    for old, new in REPLACEMENTS.items():
        string = string.replace(old, new)
    return string

def remove_base_url(string: str, base_url: str = "https://openalex.org/") -> str:
    """
    Removes the base URL from a string.
    """
    return string.replace(base_url, "")