"""
Platform registry — import and list all enabled platforms here.
To add a new platform: create its module, import it, and append an instance.
"""

from src.platforms.codeforces import CodeforcesClient
from src.platforms.atcoder import AtCoderClient
from src.platforms.codechef import CodeChefClient
from src.platforms.leetcode import LeetCodeClient

ALL_PLATFORMS = [
    CodeforcesClient(),
    AtCoderClient(),
    CodeChefClient(),
    LeetCodeClient(),
]
