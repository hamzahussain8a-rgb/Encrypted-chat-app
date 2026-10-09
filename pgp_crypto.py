"""
pgp_crypto.py — a simple word <-> number substitution cipher shared by
comm.py (server) and chat_app.py (client).

How it works:
  - WORD_TO_NUM maps common words to numbers (hardcoded dictionary,
    same copy on both sides).
  - encrypt_message() splits the text into words and swaps each
    known word for its number. Words not in the dictionary (names,
    typos, slang) are sent as their character codes instead, so any
    message still round-trips correctly.
  - decrypt_message() reverses it.

This is NOT real encryption — it's a substitution cipher. Anyone who
has this file (or guesses the pattern) can decode it instantly. It's
useful to see the client/server pipeline working end to end, not to
actually keep messages secret. See the earlier pgp_crypto.py version
for real RSA+AES encryption if you want that back.
"""

# ---- hardcoded word dictionary (same on client & server) ----
_WORDS = [
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "am",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her",
    "us", "them", "my", "your", "his", "its", "our", "their",
    "hello", "hi", "hey", "bye", "goodbye", "yes", "no", "ok", "okay",
    "please", "thanks", "thank", "sorry", "what", "when", "where",
    "why", "how", "who", "which", "this", "that", "these", "those",
    "and", "or", "but", "if", "so", "because", "not", "do", "does",
    "did", "can", "could", "will", "would", "should", "have", "has",
    "had", "to", "of", "in", "on", "at", "for", "with", "about",
    "like", "want", "need", "know", "think", "see", "look", "good",
    "bad", "great", "nice", "fine", "sure", "maybe", "now", "later",
    "today", "tomorrow", "chat", "message", "send", "hello!", "wait",
]
WORD_TO_NUM = {word: i for i, word in enumerate(_WORDS)}
NUM_TO_WORD = {i: word for word, i in WORD_TO_NUM.items()}

CHAR_MARK = "~"   # marks an unknown word encoded as character codes
SEP = ","         # separates tokens / char codes


def encrypt_message(plaintext: str) -> str:
    """Turn words into numbers. Unknown words fall back to char codes so nothing is lost."""
    tokens = []
    for word in plaintext.split(" "):
        key = word.lower()
        if key in WORD_TO_NUM:
            # keep track of original casing with a prefix: 'U' = word was uppercase-first
            prefix = "U" if word[:1].isupper() else "L"
            tokens.append(f"{prefix}{WORD_TO_NUM[key]}")
        else:
            codes = ".".join(str(ord(c)) for c in word)
            tokens.append(f"{CHAR_MARK}{codes}")
    return SEP.join(tokens)


def decrypt_message(blob: str) -> str:
    """Reverse of encrypt_message."""
    if blob == "":
        return ""
    words = []
    for token in blob.split(SEP):
        if token.startswith(CHAR_MARK):
            codes = token[len(CHAR_MARK):]
            word = "".join(chr(int(c)) for c in codes.split(".") if c != "")
            words.append(word)
        else:
            prefix, num = token[0], int(token[1:])
            word = NUM_TO_WORD[num]
            if prefix == "U":
                word = word[:1].upper() + word[1:]
            words.append(word)
    return " ".join(words)
