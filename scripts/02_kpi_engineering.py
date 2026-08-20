"""
PHẦN B/C — KPI Engineering trên dữ liệu THẬT (BUTL, 2025).

Tính các KPI đã xác nhận khả thi trong Data Audit (xem 01_data_audit.py và
docs/02_kpi_dictionary_semantic_model.md): Total Booking, Completion/
Cancellation/No-Driver-Found Rate, Net Revenue, AOV, Discount Usage Rate,
Failure Rate theo tỉnh/thành & theo khung giờ x ngày trong tuần.

Ghi 2 output:
  output/kpi_summary_private.json  -> số VND thật, CHỈ dùng nội bộ, KHÔNG
                                       nằm trong bản public trên GitHub.
  output/kpi_summary_public.json   -> bản ẨN DANH HÓA: mọi số tiền tuyệt đối
                                       (net revenue, AOV, discount) được
                                       chuyển thành % / index; số lượng
                                       chuyến, tỷ lệ (%), MAPE... không phải
                                       tiền nên giữ nguyên số thật.
"""
import json
import numpy as np
import pandas as pd

DP = "/home/claude/bi_demand_forecasting_project/data_private"
OUT = "/home/claude/bi_demand_forecasting_project/output"

trip = pd.read_pickle(f"{DP}/fact_trip.pkl")
notfound = pd.read_pickle(f"{DP}/fact_notfound.pkl")
user = pd.read_pickle(f"{DP}/dim_user.pkl")

# ---------- headline KPIs ----------
total_booking = len(trip)
completed = int((trip["status_group"] == "Completed").sum())
cancelled = int((trip["status_group"] == "Cancelled").sum())
inprogress = total_booking - completed - cancelled
no_driver_found = len(notfound)
total_demand = total_booking + no_driver_found

completion_rate = completed / total_demand * 100
cancellation_rate = cancelled / total_booking * 100
no_driver_found_rate = no_driver_found / total_demand * 100
discount_usage_rate = trip["has_discount"].mean() * 100

net_revenue_vnd = int(trip.loc[trip["status_group"] == "Completed", "cost_net_vnd"].sum())
aov_vnd = net_revenue_vnd / completed

print(f"Total Booking: {total_booking:,} | Completed: {completed:,} | Cancelled: {cancelled:,} | "
      f"No-Driver-Found: {no_driver_found:,}")
print(f"Completion Rate: {completion_rate:.2f}% | Cancellation Rate: {cancellation_rate:.2f}% | "
      f"No-Driver-Found Rate: {no_driver_found_rate:.2f}%")
print(f"Discount Usage Rate: {discount_usage_rate:.2f}%")
print(f"Net Revenue (real, PRIVATE): {net_revenue_vnd:,} VND | AOV (real, PRIVATE): {aov_vnd:,.0f} VND")

# ---------- monthly trend ----------
trip["month"] = trip["month"].astype(int)
monthly = trip.groupby("month").agg(
    total_booking=("trip_id", "count"),
    completed=("status_group", lambda s: (s == "Completed").sum()),
    cancelled=("status_group", lambda s: (s == "Cancelled").sum()),
    net_revenue_vnd=("cost_net_vnd", lambda s: s[trip.loc[s.index, "status_group"] == "Completed"].sum()),
).reset_index()
nf_monthly = notfound.groupby("month").size().reindex(range(1, 13), fill_value=0)
monthly["no_driver_found"] = monthly["month"].map(nf_monthly).fillna(0).astype(int)
monthly["total_demand"] = monthly["total_booking"] + monthly["no_driver_found"]
monthly["completion_rate"] = (monthly["completed"] / monthly["total_demand"] * 100).round(2)
monthly["cancellation_rate"] = (monthly["cancelled"] / monthly["total_booking"] * 100).round(2)

# ---------- city failure rate (Case 2) ----------
demand_trip = trip.groupby("city_raw").size().rename("trip_rows")
demand_nf = notfound.groupby("city_raw").size().rename("nf_rows")
fail_trip = trip[trip["status_group"] == "Cancelled"].groupby("city_raw").size().rename("cancelled_rows")
city = pd.concat([demand_trip, demand_nf, fail_trip], axis=1).fillna(0)
city["total_demand"] = city["trip_rows"] + city["nf_rows"]
city["failure_rate"] = (city["cancelled_rows"] + city["nf_rows"]) / city["total_demand"] * 100
city_top = city.sort_values("total_demand", ascending=False).head(15).reset_index()

# ---------- hour x day-of-week failure rate heatmap (Case 2) ----------
DOW_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
trip["hour"] = trip["hour"].astype(int)
demand_hd = trip.groupby(["day_of_week", "hour"]).size().rename("trip_rows")
fail_hd = trip[trip["status_group"] == "Cancelled"].groupby(["day_of_week", "hour"]).size().rename("cancelled_rows")
nf_hd = notfound.groupby(["day_of_week", "hour"]).size().rename("nf_rows")
hd = pd.concat([demand_hd, fail_hd, nf_hd], axis=1).fillna(0)
hd["total"] = hd["trip_rows"] + hd["nf_rows"]
hd["failure_rate"] = (hd["cancelled_rows"] + hd["nf_rows"]) / hd["total"] * 100
heatmap_values = []
for d in DOW_ORDER:
    row = [round(hd.loc[(d, h), "failure_rate"], 2) if (d, h) in hd.index else 0.0 for h in range(24)]
    heatmap_values.append(row)

# ---------- discount by service (contains VND -> will be anonymized) ----------
disc_by_service = (
    trip[trip["has_discount"]].groupby("service_name")["discount_vnd"].mean().sort_values(ascending=False)
)

# ================= PRIVATE (real VND) =================
private_out = {
    "period": "2025 (01/01 - 31/12)",
    "kpi": {
        "total_booking": total_booking, "completed": completed, "cancelled": cancelled,
        "inprogress": inprogress, "no_driver_found": no_driver_found, "total_demand": total_demand,
        "completion_rate_pct": round(completion_rate, 2), "cancellation_rate_pct": round(cancellation_rate, 2),
        "no_driver_found_rate_pct": round(no_driver_found_rate, 2), "discount_usage_rate_pct": round(discount_usage_rate, 2),
        "net_revenue_vnd": net_revenue_vnd, "aov_vnd": round(aov_vnd, 0), "new_users_2025": len(user),
    },
    "monthly_trend": monthly.to_dict(orient="records"),
    "city_failure": city_top.to_dict(orient="records"),
    "discount_by_service_vnd": disc_by_service.round(0).to_dict(),
}
with open(f"{OUT}/kpi_summary_private.json", "w", encoding="utf-8") as f:
    json.dump(private_out, f, ensure_ascii=False, indent=2, default=str)

# ================= PUBLIC (anonymized) =================
avg_monthly_revenue = monthly["net_revenue_vnd"].mean()
monthly_pub = monthly.copy()
monthly_pub["revenue_share_pct"] = (monthly_pub["net_revenue_vnd"] / monthly_pub["net_revenue_vnd"].sum() * 100).round(2)
monthly_pub["revenue_index"] = (monthly_pub["net_revenue_vnd"] / avg_monthly_revenue * 100).round(1)  # avg month = 100
monthly_pub = monthly_pub.drop(columns=["net_revenue_vnd"])

disc_by_service_pub = (disc_by_service / disc_by_service.mean() * 100).round(1)  # overall avg = 100

public_out = {
    "period": "2025 (01/01 - 31/12)",
    "note": "Dữ liệu THẬT vận hành BUTL 2025 (490.928 trip, 68.964 no-driver-found, 455.937 user). "
            "Số lượng chuyến & tỷ lệ (%) là số thật vì không lộ quy mô tài chính. Net Revenue & AOV & "
            "Discount theo dịch vụ đã ẨN DANH HÓA thành % thị phần / index (trung bình = 100) để bảo mật "
            "doanh thu thật của doanh nghiệp.",
    "kpi": {
        "total_booking": total_booking, "completed": completed, "cancelled": cancelled,
        "inprogress": inprogress, "no_driver_found": no_driver_found, "total_demand": total_demand,
        "completion_rate_pct": round(completion_rate, 2), "cancellation_rate_pct": round(cancellation_rate, 2),
        "no_driver_found_rate_pct": round(no_driver_found_rate, 2), "discount_usage_rate_pct": round(discount_usage_rate, 2),
        "new_users_2025": len(user),
        "aov_index_avg_100": 100.0,
    },
    "monthly_trend": monthly_pub.to_dict(orient="records"),
    "city_failure_top15": city_top[["city_raw", "total_demand", "failure_rate"]].round(2).to_dict(orient="records"),
    "heatmap_failure_rate": {"days": DOW_ORDER, "hours": list(range(24)), "values": heatmap_values},
    "discount_by_service_index_avg_100": disc_by_service_pub.to_dict(),
}
with open(f"{OUT}/kpi_summary_public.json", "w", encoding="utf-8") as f:
    json.dump(public_out, f, ensure_ascii=False, indent=2, default=str)

print("\nSaved output/kpi_summary_private.json (real VND, keep private)")
print("Saved output/kpi_summary_public.json (anonymized, safe for GitHub/dashboard)")
