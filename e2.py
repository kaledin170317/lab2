import osmnx as ox


def find_intersections(street1, street2):
    # Загрузка данных для Санкт-Петербурга
    G = ox.load_graphml("spb_drive.graphml")

    # Получение всех улиц в графе
    streets = ox.graph_to_gdfs(G, nodes=False, edges=True)

    streets = streets[streets['name'].notna()]

    # Фильтрация улиц по названиям
    street1_data = streets[streets['name'].str.contains(street1, case=False, na=False)]
    street2_data = streets[streets['name'].str.contains(street2, case=False, na=False)]

    # Если нет данных по одной из улиц, возвращаем пустое множество
    if street1_data.empty or street2_data.empty:
        return set()

    # Получение геометрии улиц с использованием union_all()
    street1_geometry = street1_data.geometry.union_all()
    street2_geometry = street2_data.geometry.union_all()

    # Нахождение пересечений
    intersections = street1_geometry.intersection(street2_geometry)

    # Получение координат точек пересечения
    coords = set()
    if not intersections.is_empty:
        if intersections.geom_type == 'Point':
            coords.add((intersections.y, intersections.x))
        elif intersections.geom_type == 'MultiPoint':
            for point in intersections.geoms:
                coords.add((point.y, point.x))

    return coords

if __name__ == "__main__":
    street_name1 = input("Введите название первой улицы: ")
    street_name2 = input("Введите название второй улицы: ")

    intersection_points = find_intersections(street_name1, street_name2)

    if intersection_points:
        print("Координаты точек пересечения:")
        for point in intersection_points:
            print(point)
    else:
        print("Пересечений не найдено.")