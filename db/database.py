# db/database.py
import json
import os
import time
from collections import defaultdict

class JsonDatabase:
    def __init__(self, base_dir="data", debug=False):
        self.base_dir = base_dir
        self.debug = debug

        # --- Stats globales ---
        self.stats = {
            "calls": 0,
            "time_total": 0.0,
            "operations": defaultdict(int),
            "objects_created": 0,
        }

    # --- Internal helper ---
    def _measure(self, op_name, func, *args, **kwargs):
        """Mesure le temps et enregistre les stats d'une opération DB."""
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start

        self.stats["calls"] += 1
        self.stats["time_total"] += duration
        self.stats["operations"][op_name] += 1

        if self.debug:
            print(f"[DB] {op_name.upper():<8} | {duration*1000:.2f} ms")

        return result

    # --- CRUD wrappers ---
    def create(self, collection, key, data):
        def _create():
            dir_path = os.path.join(self.base_dir, collection)
            os.makedirs(dir_path, exist_ok=True)
            path = os.path.join(dir_path, f"{key}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self.stats["objects_created"] += 1
            return True

        return self._measure("create", _create)

    def get(self, collection, key):
        def _get():
            path = os.path.join(self.base_dir, collection, f"{key}.json")
            if not os.path.exists(path):
                return None
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

        return self._measure("get", _get)

    def update(self, collection, key, data):
        def _update():
            path = os.path.join(self.base_dir, collection, f"{key}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True

        return self._measure("update", _update)

    def delete(self, collection, key):
        def _delete():
            path = os.path.join(self.base_dir, collection, f"{key}.json")
            if os.path.exists(path):
                os.remove(path)
                return True
            return False

        return self._measure("delete", _delete)

    def list_all(self, collection):
        def _list_all():
            dir_path = os.path.join(self.base_dir, collection)
            if not os.path.exists(dir_path):
                return {}

            data_dict = {}
            for file in os.listdir(dir_path):
                if file.endswith(".json"):
                    key = file[:-5]  # retire l'extension .json
                    with open(os.path.join(dir_path, file), "r", encoding="utf-8") as f:
                        data_dict[key] = json.load(f)
            return data_dict

        return self._measure("list_all", _list_all)

    # --- Stats display ---
    def summary(self):
        """Retourne un résumé des stats."""
        avg_time = (self.stats["time_total"] / self.stats["calls"]) if self.stats["calls"] else 0
        ops = ", ".join(f"{k}: {v}" for k, v in self.stats["operations"].items())
        return (
            f" /---------------------------------\\ \n"
            f"<======= JSON Database Stats =======>\n"
            f" \\---------------------------------/\n"
            f"Total calls: {self.stats['calls']}\n"
            f"Total time: {self.stats['time_total']:.4f}s\n"
            f"Average time per call: {avg_time*1000:.2f} ms\n"
            f"Operations breakdown: {ops}\n"
            f"Objects created: {self.stats['objects_created']}\n"
            f"Base directory: {self.base_dir}\n"
            f"-------------------------------------"
        )

    def print_summary(self):
        print(self.summary())