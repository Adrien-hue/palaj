import weakref
from collections import defaultdict
from datetime import datetime

class CacheManager:
    def __init__(self):
        self._objects = defaultdict(weakref.WeakSet)
        self.created_count = defaultdict(int)
        self.hits = defaultdict(int)
        self.misses = defaultdict(int)
        self.last_reset = datetime.now()

    def track(self, obj):
        cls = type(obj).__name__
        self._objects[cls].add(obj)
        self.created_count[cls] += 1

    def register_hit(self, cls_name):
        self.hits[cls_name] += 1

    def register_miss(self, cls_name):
        self.misses[cls_name] += 1

    def stats(self):
        total = sum(len(s) for s in self._objects.values())
        return {
            "total_instances": total,
            "by_class": {cls: len(instances) for cls, instances in self._objects.items()},
            "created_since_reset": dict(self.created_count),
            "hits": dict(self.hits),
            "misses": dict(self.misses),
            "last_reset": self.last_reset.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def report(self, verbose=False):
        stats = self.stats()
        print("\n===== CacheManager Report =====")
        print(f"Total instances vivantes : {stats['total_instances']}")
        print(f"Dernier reset : {stats['last_reset']}\n")

        print("Instances par classe :")
        for cls, count in stats["by_class"].items():
            print(f"  - {cls:<15}: {count}")

        print("\nCache hits/misses :")
        for cls in set(list(stats["hits"].keys()) + list(stats["misses"].keys())):
            h = stats["hits"].get(cls, 0)
            m = stats["misses"].get(cls, 0)
            ratio = h / (h + m) * 100 if (h + m) > 0 else 0
            print(f"  - {cls:<15}: hits={h}, misses={m}, hit_ratio={ratio:.1f}%")

        if verbose:
            print("\nObjets créés depuis le dernier reset :")
            for cls, count in stats["created_since_reset"].items():
                print(f"  - {cls:<15}: {count}")
        print("================================\n")

    def reset(self):
        self.created_count.clear()
        self.hits.clear()
        self.misses.clear()
        self.last_reset = datetime.now()