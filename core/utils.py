def index_to_alpha(index: int) -> str:
    """
    Convert a 0-based index to a 3-letter alphabetic suffix.
    0 → 'aaa', 1 → 'aab', 25 → 'aaz', 26 → 'aba', ...
    Avoids sequential numeric names that editing software may detect as an image sequence.
    """
    chars = []
    for _ in range(3):
        chars.append(chr(ord('a') + (index % 26)))
        index //= 26
    return ''.join(reversed(chars))
