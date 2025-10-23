import fiona
import os
import csv
from shapely.geometry import shape, LineString, mapping
from pyproj import Transformer
import math
from tqdm import tqdm

DATA_DIR = ".\data"
OUT_CSV = "road_segments_features.csv"

def compute_bearing_coords(a, b):

    import math
    x1,y1 = a
    x2,y2 = b

    angle = math.degrees(math.atan2(y2-y1, x2-x1))
    return angle


transformer = Transformer.from_crs("epsg:4326","epsg:3857", always_xy=True)

fieldnames = ["source_file","feature_id","geom_type","length_m","num_coords","bearing_deg","start_lon","start_lat","end_lon","end_lat","tags"]

with open(OUT_CSV, "w", newline='', encoding='utf-8') as fout:
    writer = csv.DictWriter(fout, fieldnames=fieldnames)
    writer.writeheader()


    for root, dirs, files in os.walk(DATA_DIR):
        for fname in files:
                    if not fname.lower().endswith(".geojson"):
                        continue
                    fp = os.path.join(root, fname)
                    try:
                        with fiona.open(fp, 'r', encoding='utf-8') as src:
                            for i, feat in enumerate(tqdm(src, desc=fname, leave=False)):
                                try:
                                    geom = feat.get('geometry')
                                    if geom is None:
                                        continue
                                    geom_obj = shape(geom)
                                    if geom_obj.is_empty:
                                        continue
                                    
                                    if geom_obj.geom_type == "MultiLineString":
                                        
                                        lines = list(geom_obj)
                                    elif geom_obj.geom_type == "LineString":
                                        lines = [geom_obj]
                                    else:
                                        continue

                                    props = feat.get('properties') or {}
                                    tags = {k:v for k,v in props.items() if v is not None}
                                    for line in lines:
                                        coords = list(line.coords)
                                        if len(coords) < 2:
                                            continue
                                        
                                        a0 = transformer.transform(coords[0][0], coords[0][1])
                                        a1 = transformer.transform(coords[-1][0], coords[-1][1])
                                        
                                        length_m = 0.0
                                        for j in range(len(coords)-1):
                                            x0,y0 = transformer.transform(coords[j][0], coords[j][1])
                                            x1,y1 = transformer.transform(coords[j+1][0], coords[j+1][1])
                                            seg_len = ((x1-x0)2 + (y1-y0)2)**0.5
                                            length_m += seg_len 
                                        bearing = compute_bearing_coords(coords[0], coords[-1])
                                        row = {
                                            "source_file": fname,
                                            "feature_id": feat.get('id', f"{i}"),
                                            "geom_type": line.geom_type,
                                            "length_m": round(length_m,3),
                                            "num_coords": len(coords),
                                            "bearing_deg": round(bearing,3) if bearing is not None else None,
                                            "start_lon": coords[0][0],
                                            "start_lat": coords[0][1],
                                            "end_lon": coords[-1][0],
                                            "end_lat": coords[-1][1],
                                            "tags": str(tags)
                                        }
                                        writer.writerow(row)
                                except Exception as e:
                                    
                                    print("skip feature in", fp, "err:", e)
                    except Exception as e:
                        print("Ошибка чтения файла", fp, ":", e)

        print("Готово. Сохранил:", OUT_CSV)