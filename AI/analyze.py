import pandas as pd
import networkx as nx
from sklearn.cluster import DBSCAN
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point
import geopandas as gpd
from pyproj import Transformer
import contextily as ctx

FEATURES_CSV = "road_segments_features.csv"
OUT_GPKG = "road_segments_with_hotspots.gpkg"
df = pd.read_csv(FEATURES_CSV)


df = df.dropna(subset=["start_lon","start_lat","end_lon","end_lat"])


def node_key(lon, lat):
    return (round(lon,6), round(lat,6))

edges = []
for idx,row in df.iterrows():
    s = node_key(row.start_lon, row.start_lat)
    e = node_key(row.end_lon, row.end_lat)
    edges.append((s,e,{"edge_id": idx, "length_m": row.length_m}))

G = nx.DiGraph()
G.add_edges_from(edges)


deg = dict(G.degree())
betw = nx.betweenness_centrality(G, weight="length_m", normalized=True)


start_deg = []
end_deg = []
start_betw = []
end_betw = []
for idx, row in df.iterrows():
    s = node_key(row.start_lon, row.start_lat)
    e = node_key(row.end_lon, row.end_lat)
    start_deg.append(deg.get(s, 0))
    end_deg.append(deg.get(e, 0))
    start_betw.append(betw.get(s, 0))
    end_betw.append(betw.get(e, 0))

df["start_deg"] = start_deg
df["end_deg"] = end_deg
df["start_betw"] = start_betw
df["end_betw"] = end_betw


from sklearn.preprocessing import StandardScaler
X = df[["length_m","num_coords","start_deg","end_deg","start_betw","end_betw"]].fillna(0).values
sc = StandardScaler()
Xs = sc.fit_transform(X)


db = DBSCAN(eps=0.8, min_samples=10).fit(Xs)
df["cluster"] = db.labels_


gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.start_lon, df.start_lat), crs="EPSG:4326")

hotspots = gdf[gdf.cluster != -1].dissolve(by="cluster", as_index=False)

gdf.to_file(OUT_GPKG, layer="segments_points", driver="GPKG")
hotspots.to_file(OUT_GPKG, layer="hotspots", driver="GPKG")

print("Сохранено в", OUT_GPKG)

