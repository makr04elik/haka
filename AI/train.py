import pandas as pd
from sklearn.model_selection import train_test_split
import lightgbm as lgb
from sklearn.metrics import mean_squared_error, r2_score

df = pd.read_csv("road_segments_features.csv")

if "target_speed" not in df.columns:
    raise SystemExit("Нет target_speed — добавь метрику (с датчиков/телеметрии) для supervised learning.")

feat_cols = ["length_m","num_coords","start_deg","end_deg","start_betw","end_betw"]
df = df.dropna(subset=feat_cols + ["target_speed"])
X = df[feat_cols]
y = df["target_speed"]

X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.2,random_state=42)
train_data = lgb.Dataset(X_train, label=y_train)
params = {"objective":"regression","metric":"rmse","verbosity":-1}
model = lgb.train(params, train_data, num_boost_round=100)
pred = model.predict(X_test)
print("RMSE:", mean_squared_error(y_test, pred, squared=False))
print("R2:", r2_score(y_test, pred))
model.save_model("lgb_road_speed_model.txt")