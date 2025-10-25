"""Text comparison utilities for checking user answers."""
import re


def normalize_text(text: str, strictness: str = "normal") -> str:
    """
    Normalize text for comparison.
    
    Args:
        text: The text to normalize
        strictness: How strict to be - "strict" (exact), "normal" (case-insensitive), "lenient" (ignore punctuation)
    
    Returns:
        Normalized text
    """
    if strictness == "strict":
        return text.strip()
    
    # For normal and lenient: lowercase and trim
    normalized = text.lower().strip()
    
    if strictness == "lenient":
        # Remove punctuation and extra whitespace
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized


def check_answer(user_answer: str, correct_answer: str, strictness: str = "normal") -> bool:
    """
    Check if the user's answer matches the correct answer.
    
    Args:
        user_answer: The user's typed answer
        correct_answer: The correct answer
        strictness: How strict to be - "strict", "normal" (default), or "lenient"
    
    Returns:
        True if the answer is correct, False otherwise
    
    Examples:
        >>> check_answer("hello", "Hello", "normal")
        True
        >>> check_answer("hello", "Hello", "strict")
        False
        >>> check_answer("hello!", "hello", "lenient")
        True
    """
    if not user_answer or not correct_answer:
        return False
    
    user_normalized = normalize_text(user_answer, strictness)
    correct_normalized = normalize_text(correct_answer, strictness)
    
    return user_normalized == correct_normalized


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts (0.0 to 1.0).
    Uses simple character-based comparison.
    
    Args:
        text1: First text
        text2: Second text
    
    Returns:
        Similarity score between 0.0 and 1.0
    """
    if not text1 or not text2:
        return 0.0
    
    # Normalize both texts
    text1 = normalize_text(text1, "lenient")
    text2 = normalize_text(text2, "lenient")
    
    if text1 == text2:
        return 1.0
    
    # Simple character-level similarity
    max_len = max(len(text1), len(text2))
    if max_len == 0:
        return 0.0
    
    # Count matching characters at same positions
    matches = sum(1 for a, b in zip(text1, text2) if a == b)
    return matches / max_len
