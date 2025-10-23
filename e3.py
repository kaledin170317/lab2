from __future__ import annotations
import osmnx as ox

import json

import re
import pymorphy3

morph = pymorphy3.MorphAnalyzer()
WORD = re.compile(r"[0-9A-Za-zА-Яа-яЁё\-]+")


def prepare_text(text: str) -> str:
    text = text.replace("\n", " ")
    text = lemmatize_text(text)
    return text


def strip_endings(text: str) -> str:
    suf = ("ого", "его", "ому", "ему", "ыми", "ими", "ых", "их", "ая", "яя", "ое", "ее", "ую", "юю",
           "ой", "ей", "ою", "ею", "ами", "ями", "ам", "ям", "ах", "ях", "ия", "ья", "ий", "ый", "ой",
           "а", "я", "у", "ю", "ы", "и", "е", "о", "ся", "сь", "им")
    res = []
    for w in re.findall(r"[A-Za-zА-Яа-яЁё0-9\-]+|.", text):
        lw = w.lower()
        for s in suf:
            if lw.endswith(s) and len(lw) > len(s) + 2:
                w = w[:-len(s)]
                break
        res.append(w)
    return "".join(res)


def lemmatize_text(text: str) -> str:
    text = text.replace("ё", "е")
    text = strip_endings(text)
    tokens = WORD.findall(text)
    return " ".join(morph.parse(t)[0].normal_form for t in tokens)


PATTERN = re.compile(
    rf"(?<!\S)({WORD})\s+({WORD})\s+(улица|проспект)\s+({WORD})\s+({WORD})(?!\S)",
    re.IGNORECASE
)


def lemmatize_name_safe(val):
    if isinstance(val, (list, tuple, set)):
        val = " ".join(val)
    val = str(val)
    return lemmatize_text(val)


def get_all_metro_from_graph():
    G = ox.load_graphml("spb_drive.graphml")
    nodes, _ = ox.graph_to_gdfs(G)
    poly = nodes.unary_union.convex_hull


    gdf = ox.features_from_polygon(poly, {
        "station": "subway",
        "railway": ["station", "subway_entrance"],
        "public_transport": "station"
    })
    if gdf.empty:
        return gdf


    is_station = (
            (gdf.get("station") == "subway") |
            ((gdf.get("railway") == "station") & (gdf.get("subway") == "yes")) |
            (gdf.get("public_transport") == "station")
    )
    is_entrance = (gdf.get("railway") == "subway_entrance")

    metro = gdf[is_station | is_entrance].copy()
    metro = metro[metro["name"].notna()]

    metro["lem_name"] = metro["name"].apply(lemmatize_name_safe)

    return metro


all_metro = get_all_metro_from_graph()


def get_all_streets():
    G = ox.load_graphml("spb_drive.graphml")
    streets = ox.graph_to_gdfs(G, nodes=False, edges=True)
    streets = streets[streets['name'].notna()]
    streets['lem_name'] = streets['name'].apply(lemmatize_name_safe)
    return streets


all_street = get_all_streets()


def windows_around_streets(text: str) -> list[list[str]]:
    words = ["улица", "проспект", "шосс"]
    text = "  " + text + "  "
    text = text.split(" ")
    res = []
    for i in range(len(text)):
        if text[i] in words:
            res.append([text[i - 2], text[i - 1], text[i], text[i + 1], text[i + 2]])
    return res


def windows_around_metro(text: str) -> list[list[str]]:
    words = ["метр"]
    text = "  " + text + "  "
    text = text.split(" ")
    res = []
    for i in range(len(text)):
        if text[i] in words:
            res.append([text[i - 2], text[i - 1], text[i], text[i + 1], text[i + 2]])

    return res


def validate_metro(streets: list[list[str]]) -> set[str]:
    res = set()

    for street in streets:
        new_streetss = [
            street[0] + " " + street[1],
            street[3] + " " + street[4],
            street[3],
            street[1],
        ]
        flag = False
        for new_street in new_streetss:
            for st in all_metro['lem_name']:
                if new_street == st:
                    res.add(new_street)
                    flag = True
                    break
            if flag:
                break
    return res


def validate_streets(streets: list[list[str]]) -> set[str]:
    res = set()
    for street in streets:
        new_streetss = [
            street[0] + " " + street[1] + " " + street[2],
            street[2] + " " + street[3] + " " + street[4],
            street[2] + " " + street[3],
            street[1] + " " + street[2],
        ]
        flag = False
        for new_street in new_streetss:
            for st in all_street['lem_name']:
                if new_street == st:
                    res.add(new_street)
                    flag = True
                    break
            if flag:
                break
    return res


def find_intersections(street1, street2, metro):
    if metro:
        metro_data = all_metro[all_metro['lem_name'].str.contains(metro, case=False, na=False)]

        if metro_data.crs is not None and not metro_data.crs.to_string().endswith("4326"):
            metro_data = metro_data.to_crs(4326)


        metro_data = metro_data.explode(index_parts=False, ignore_index=True)


        coords = list(zip(metro_data.geometry.y, metro_data.geometry.x))
        return coords


    street1_data = all_street[all_street['lem_name'].str.contains(street1, case=False, na=False)]
    street2_data = all_street[all_street['lem_name'].str.contains(street2, case=False, na=False)]


    if street1_data.empty or street2_data.empty:
        return set()

    street1_geometry = street1_data.geometry.union_all()
    street2_geometry = street2_data.geometry.union_all()


    intersections = street1_geometry.intersection(street2_geometry)

    coords = set()
    if not intersections.is_empty:
        if intersections.geom_type == 'Point':
            coords.add((intersections.y, intersections.x))
        elif intersections.geom_type == 'MultiPoint':
            pts = list(intersections.geoms)
            avg_y = sum(p.y for p in pts) / len(pts)
            avg_x = sum(p.x for p in pts) / len(pts)
            coords.add((avg_y, avg_x))

    return coords


with open("rta_texts.json", "r", encoding="utf-8") as f:
    data = json.load(f)


def locate(text: str):
    st = set()
    m = set()
    for sentance in text.split("."):
        sentance = prepare_text(sentance)
        val = validate_streets(windows_around_streets(sentance))
        metro = validate_metro(windows_around_metro(sentance))
        for mm in metro:
            m.add(mm)
        if len(val) == 2:
            st = val
            break

        for s in val:
            st.add(s)

    if len(st) == 2:
        return find_intersections(list(st)[0], list(st)[1], None)
    if len(m) == 1:
        return find_intersections(None, None, list(m)[0])

    return None
