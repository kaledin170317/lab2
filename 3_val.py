# -*- coding: utf-8 -*-
import json
import math
from typing import Iterable, Tuple, Optional, Set

from labs.lab_2.e3 import locate

DATA_FILE = "rta_texts.json"

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def first_point(obj) -> Optional[Tuple[float, float]]:
    if obj is None:
        return None
    if isinstance(obj, tuple) and len(obj) == 2 and all(isinstance(v, (int, float)) for v in obj):
        return obj
    if isinstance(obj, (set, list, tuple)) and len(obj) > 0:
        any_el = next(iter(obj))
        if isinstance(any_el, tuple) and len(any_el) == 2:
            return any_el
    return None

def google_link(lat: float, lon: float) -> str:
    return f"https://www.google.com/maps?q={lat:.6f},{lon:.6f}"

def short(text: str, n: int = 120) -> str:
    t = " ".join(text.split())
    return t if len(t) <= n else t[:n] + "…"

def run_eval(data_file: str = DATA_FILE):
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("text_list", []) if isinstance(data, dict) else data

    distances = []
    ok = 0
    total = 0

    for idx, item in enumerate(items, start=1):
        text = item["text"]
        gt_lat, gt_lon = item["rta_coords"]

        pred_res = locate(text)  # <-- твоя функция
        pred = first_point(pred_res)

        print(f"=== Случай #{idx} ===")
        print(short(text, 200))
        print()

        print(f"Эталон:        {gt_lat:.6f}, {gt_lon:.6f}")
        print(f"Google Maps (gt):   {google_link(gt_lat, gt_lon)}")

        if pred is None:
            print("Предсказание:  — (нет координат)")
            print()
            total += 1
            continue

        pred_lat, pred_lon = pred
        dist = haversine(pred_lat, pred_lon, gt_lat, gt_lon)
        distances.append(dist)
        total += 1
        if dist <= 200:
            ok += 1

        print(f"Предсказание:  {pred_lat:.6f}, {pred_lon:.6f}")
        print(f"Google Maps (pred): {google_link(pred_lat, pred_lon)}")
        print(f"Расстояние:    {int(round(dist))} м")
        print()

    # Сводка
    print("=== Сводка ===")
    if total > 0:
        if distances:
            avg = sum(distances) / len(distances)
            med = sorted(distances)[len(distances)//2] if len(distances) % 2 == 1 else \
                  0.5 * (sorted(distances)[len(distances)//2 - 1] + sorted(distances)[len(distances)//2])
            print(f"Всего кейсов:        {total}")
            print(f"Есть предсказания:   {len(distances)}/{total}")
            print(f"Точность (<=200 м):  {ok}/{total} = {ok/total:.1%}")
            print(f"Среднее откл.:       {avg:.1f} м")
            print(f"Медиана откл.:       {med:.1f} м")
        else:
            print(f"Всего кейсов:        {total}")
            print("Ни для одного кейса не удалось получить предсказание координат.")

if __name__ == "__main__":
    run_eval(DATA_FILE)
