"""
Enum definitions for InfoPilot Explorer
"""
from enum import Enum


class DocumentType(str, Enum):
    INFORMATIVE_PHD = "Informative Ph.D"
    INFORMATIVE = "Informative"
    NEWS_ARTICLE = "News Article"
    BLOG = "Blog"
    FORUM = "Forum"
    PERSONAL_REPORT_ORGANIC = "Personal Report (Organic)"
    PERSONAL_REPORT_COLLECTED = "Personal Report (Collected)"
    INFOPILOT_EXCLUSIVE = "InfoPilot Exclusive"


class ReactionType(str, Enum):
    LIKE = "Like"
    LOVE = "Love"
    FUNNY = "Funny"
    SAD = "Sad"
    CAUTION = "Caution"
    SPAM = "Spam"
    BEST = "Best"


class SearchAggregation(str, Enum):
    AND_OR = "and_or"
    AND = "and"
    OR = "or"
