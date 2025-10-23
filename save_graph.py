import osmnx as ox
G = ox.graph_from_place('Saint Petersburg, Russia', network_type='drive')
ox.save_graphml(G, "spb_drive.graphml")

