import re

def split_sentences(text: str, max_len: int = 120) -> list:
    """
    Split long text into smaller sentences (~max_len chars) for readability.
    """
    sentences = re.split(r'(?<=[.!?]) +', text)
    lines = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        # If sentence is too long, split further by comma
        if len(sentence) > max_len:
            sub_sentences = [s.strip() for s in sentence.split(',')]
            lines.extend(sub_sentences)
        else:
            lines.append(sentence)
    return lines

def emphasize_keywords(text: str) -> str:
    """
    Bold important words dynamically (capitalized / technical terms).
    Frontend can render bold via CSS; here we just keep plain text for history.
    """
    # Detect CamelCase or ALLCAPS words
    return re.sub(r'\b([A-Z][a-zA-Z0-9]+|[A-Z]{2,})\b', lambda m: f"{m.group(0)}", text)

def format_text(text: str) -> str:
    """
    Formats PDF text into human-readable, professional LLM-style output:
    - Headings/subheadings plain
    - Bullets clean
    - Numbered lists clean
    - Important words dynamically emphasized
    - Each bullet broken into readable 2-3 sentence points
    - No Markdown or HTML tags in history
    """
    if not text or not text.strip():
        return "No answer generated."

    lines = text.splitlines()
    formatted_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Remove Markdown-style bold
        line = line.replace("**", "")

        # Detect heading (short line or ends with ":")
        if len(line.split()) <= 6 or line.endswith(":"):
            formatted_lines.append(line)
            continue

        # Bullet points
        if line.startswith("- ") or line.startswith("• "):
            content = line[2:].strip() if line.startswith("- ") else line[1:].strip()
            content = emphasize_keywords(content)
            # Split long sentences into readable lines
            sub_lines = split_sentences(content)
            for sub in sub_lines:
                formatted_lines.append(f"• {sub}")
            continue

        # Numbered points
        match_numbered = re.match(r'^(\d+)\.\s*(.*)', line)
        if match_numbered:
            num, rest = match_numbered.groups()
            rest = emphasize_keywords(rest)
            sub_lines = split_sentences(rest)
            for sub in sub_lines:
                formatted_lines.append(f"{num}. {sub}")
            continue

        # Normal text
        line = emphasize_keywords(line)
        sub_lines = split_sentences(line)
        formatted_lines.extend(sub_lines)

    return "\n".join(formatted_lines)
