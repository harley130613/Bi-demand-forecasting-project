"""
ML — Demand Forecasting theo Ngày x Khu Vực (BUTL 2025, dữ liệu thật).

Bài toán pivot từ đề xuất ban đầu ("dự đoán khách hàng rời bỏ") vì fact_trip
không có user_id hợp lệ để làm churn prediction ở cấp khách hàng (xem
01_data_audit.py). Thay vào đó: dự báo SỐ BOOKING theo ngày, theo tỉnh/thành
cho 6 khu vực có khối lượng lớn nhất — phục vụ phân bổ tài xế.

Feature engineering CHỈ dùng dữ liệu quá khứ (lag_1, lag_7, rolling mean 7/14
ngày) để tránh rò rỉ thông tin tương lai. Train/test split THEO THỜI GIAN
(không random-split): Train = 01/01-31/10/2025, Test = 01/11-31/12/2025.

Không có số tiền VND trong bài toán này -> không cần bước ẩn danh hóa.
"""
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

DP = "/home/claude/bi_demand_forecasting_project/data_private"
OUT = "/home/claude/bi_demand_forecasting_project/output"

daily = pd.read_pickle(f"{DP}/daily_city.pkl")

cities = sorted(daily["city_raw"].unique())
city_map = {i: c for i, c in enumerate(cities)}
city_code = {c: i for i, c in city_map.items()}
daily["city_code"] = daily["city_raw"].map(city_code)

FEATURES = ["city_code", "dow", "month", "is_weekend", "day_of_year", "lag_7", "lag_1", "roll_mean_7", "roll_mean_14"]
TARGET = "bookings"

daily = daily.dropna(subset=FEATURES).reset_index(drop=True)

split_date = pd.Timestamp("2025-11-01")
train = daily[daily["trip_date"] < split_date]
test = daily[daily["trip_date"] >= split_date]
print(f"Train: {len(train)} dòng (01/01 - 31/10) | Test: {len(test)} dòng (01/11 - 31/12)")

X_train, y_train = train[FEATURES], train[TARGET]
X_test, y_test = test[FEATURES], test[TARGET]


def mape(y_true, y_pred):
    mask = y_true > 0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


results = {}

# ---- naive baseline: booking cùng thứ tuần trước (lag_7) ----
baseline_pred = X_test["lag_7"].values
results["NaiveBaseline_lag7"] = {
    "MAE": round(mean_absolute_error(y_test, baseline_pred), 2),
    "RMSE": round(mean_squared_error(y_test, baseline_pred) ** 0.5, 2),
    "MAPE_%": round(mape(y_test.values, baseline_pred), 2),
}

models = {
    "LinearRegression": LinearRegression(),
    "RandomForest": RandomForestRegressor(n_estimators=300, max_depth=8, random_state=42, n_jobs=-1),
    "GradientBoosting": GradientBoostingRegressor(n_estimators=300, max_depth=3, learning_rate=0.05, random_state=42),
}

feature_importance = {}
for name, model in models.items():
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    results[name] = {
        "MAE": round(mean_absolute_error(y_test, pred), 2),
        "RMSE": round(mean_squared_error(y_test, pred) ** 0.5, 2),
        "MAPE_%": round(mape(y_test.values, pred), 2),
    }
    if hasattr(model, "feature_importances_"):
        feature_importance[name] = dict(zip(FEATURES, [round(float(v), 4) for v in model.feature_importances_]))

print("\nSo sánh model trên tập test (2 tháng cuối năm, giữ nguyên trạng, không nhìn thấy lúc train):")
for name, m in results.items():
    print(f"  {name:<20s} MAE={m['MAE']:>6.2f}  RMSE={m['RMSE']:>6.2f}  MAPE={m['MAPE_%']:>6.2f}%")

best_model = min(
    (n for n in results if n != "NaiveBaseline_lag7"),
    key=lambda n: results[n]["MAPE_%"],
)
print(f"\nModel được chọn (MAPE thấp nhất): {best_model}")
print(f"Feature importance ({best_model}): {feature_importance.get(best_model)}")

output = {
    "problem": "Dự báo số booking theo ngày x tỉnh/thành (6 khu vực lớn nhất) — regression theo chuỗi thời gian",
    "train_period": "2025-01-01 to 2025-10-31",
    "test_period": "2025-11-01 to 2025-12-31",
    "features": FEATURES,
    "model_comparison": results,
    "selected_model": best_model,
    "feature_importance": feature_importance,
    "cities": cities,
}
with open(f"{OUT}/ml_model_comparison.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("\nSaved output/ml_model_comparison.json (không chứa số tiền -> không cần ẩn danh hóa)")
