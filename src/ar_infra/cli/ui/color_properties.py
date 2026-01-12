from questionary import Style


PRIMARY = "#6d66c8"
SECONDARY = "#9d97d9"

CLR = "fg:#673ab7"
PROMPT_STYLE = Style(
    [
        ("qmark", f"{CLR} bold"),
        ("question", "bold"),
        ("answer", "fg:#f44336 bold"),
        ("pointer", f"{CLR} bold"),
        ("highlighted", f"{CLR} bold"),
        ("selected", "fg:#cc5454"),
        ("separator", "fg:#cc5454"),
        ("instruction", ""),
        ("text", ""),
    ]
)
