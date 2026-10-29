"""
ARIA Egyptian Arabic Polisher
Converts common Modern Standard Arabic (MSA) phrases to Egyptian colloquial.
Acts as a safety net when the AI slips into MSA.
"""

import re


# MSA → Egyptian dictionary (most common slips)
MSA_TO_EGYPTIAN = [
    # Question words
    (r'\bماذا\b',          'ايه'),
    (r'\bكيف\b',           'ازاي'),
    (r'\bلماذا\b',         'ليه'),
    (r'\bأين\b',           'فين'),
    (r'\bمتى\b',           'امتى'),
    (r'\bمن\s+أين\b',      'منين'),
    (r'\bإلى\s+أين\b',     'فين'),
    # Pronouns / demonstratives
    (r'\bهذا\b',           'ده'),
    (r'\bهذه\b',           'دي'),
    (r'\bهؤلاء\b',         'دول'),
    (r'\bذلك\b',           'ده'),
    (r'\bتلك\b',           'دي'),
    # Temporal
    (r'\bالآن\b',          'دلوقتي'),
    (r'\bالأن\b',          'دلوقتي'),
    (r'\bحالياً\b',        'دلوقتي'),
    (r'\bالحاضر\b',        'دلوقتي'),
    (r'\bاليوم\b',         'النهاردة'),
    (r'\bغداً\b',          'بكرة'),
    (r'\bأمس\b',           'امبارح'),
    # Verbs / wants
    (r'\bأريد\b',          'عايز'),
    (r'\bتريد\b',          'عايز'),
    (r'\bتريدين\b',        'عايزة'),
    (r'\bنريد\b',          'عايزين'),
    # Negation
    (r'\bليس\b',           'مش'),
    (r'\bلست\b',           'مش'),
    (r'\bلسنا\b',          'مش'),
    # Yes/No
    (r'\bنعم\b',           'آه'),
    (r'\bأجل\b',           'آه'),
    (r'\bبلى\b',           'أيوه'),
    # Common nouns
    (r'\bشيء\b',           'حاجة'),
    (r'\bشيئاً\b',          'حاجة'),
    (r'\bأشياء\b',         'حاجات'),
    (r'\bأمر\b',           'موضوع'),
    (r'\bخاصتي\b',         'بتاعي'),
    (r'\bخاصتك\b',         'بتاعك'),
    (r'\bخاصتها\b',        'بتاعها'),
    # Connectives
    (r'\bلكن\b',           'بس'),
    (r'\bأيضاً\b',         'كمان'),
    (r'\bأيضا\b',          'كمان'),
    (r'\bكذلك\b',          'كمان'),
    (r'\bهكذا\b',          'كده'),
    (r'\bبينما\b',         'في الوقت ده'),
    # Common phrases
    (r'\bحسناً\b',         'تمام'),
    (r'\bحسنا\b',          'تمام'),
    (r'\bجداً\b',          'قوي'),
    (r'\bجدا\b',           'قوي'),
    (r'\bمن\s+فضلك\b',     'لو سمحت'),
    (r'\bأنا\s+بخير\b',    'أنا كويس'),
    (r'\bكيف\s+حالك\b',    'ازيك'),
    (r'\bلا\s+بأس\b',      'مفيش مشكلة'),
    # Conjugated verbs (common)
    (r'\bأحب\b',           'بحب'),
    (r'\bأكره\b',          'بكره'),
    (r'\bأفهم\b',          'فاهم'),
    (r'\bأعرف\b',          'عارف'),
    (r'\bسأفعل\b',         'هاعمل'),
    (r'\bسأقول\b',         'هاقول'),
    (r'\bسنذهب\b',         'هنروح'),
    # Greetings / common
    (r'\bمرحباً\b',        'أهلاً'),
    (r'\bمرحبا\b',         'أهلا'),
    (r'\bالسلام\s+عليكم\b','أهلاً'),
    (r'\bحيث\b',           'فين ما'),
    (r'\bعندما\b',         'لما'),
    (r'\bإذا\b',           'لو'),
]


# Compile regex patterns once
_compiled = [(re.compile(pat), repl) for pat, repl in MSA_TO_EGYPTIAN]


def polish_to_egyptian(text: str) -> str:
    """Convert MSA phrases to Egyptian colloquial. Safe to run on Egyptian text too."""
    if not text:
        return text
    result = text
    for pattern, replacement in _compiled:
        result = pattern.sub(replacement, result)
    return result


def is_likely_msa(text: str) -> bool:
    """Heuristic: detect if text leans toward MSA based on signature words."""
    if not text:
        return False
    msa_markers = [
        'ماذا', 'كيف', 'لماذا', 'هذا', 'هذه', 'الآن',
        'أريد', 'ليس', 'نعم', 'شيء', 'حسناً', 'حسنا',
        'جداً', 'جدا', 'أحب', 'أكره', 'سأفعل', 'مرحباً',
    ]
    count = sum(1 for marker in msa_markers if marker in text)
    return count >= 2  # 2+ MSA markers = likely MSA
