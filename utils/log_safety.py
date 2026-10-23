"""Encode untrusted text before it reaches plain-text logging sinks."""


def safe_log_value(value: object) -> str:
    text = str(value).replace("\r", "\\r").replace("\n", "\\n")
    return "".join(
        f"\\x{ord(character):02x}"
        if ord(character) < 32 or 127 <= ord(character) <= 159
        else f"\\u{ord(character):04x}"
        if character in "\u2028\u2029"
        else character
        for character in text
    )
