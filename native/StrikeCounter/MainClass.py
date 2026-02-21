from collections import defaultdict

class StrikeCounter:
    def __init__(self, limits: dict[int, int]):
        self.limits = limits
        self.counts = defaultdict(int)

    def hit(self, level: int, source: str) -> bool:
        limit = self.limits.get(level)
        if not limit:
            return False

        key = (level, source)
        self.counts[key] += 1

        if self.counts[key] >= limit:
            del self.counts[key]
            return True

        return False
