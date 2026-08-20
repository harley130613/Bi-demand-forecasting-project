"""
PHẦN A — Data Audit trên dữ liệu THẬT của BUTL (2025).

Nguồn: 3 bảng xuất thô từ hệ thống vận hành — datauser2025 / datatrip2025 /
datanotfound2025 — đã được chuẩn hoá tên cột và lưu lại dưới dạng
data_private/fact_trip.pkl, data_private/fact_notfound.pkl,
data_private/dim_user.pkl (private, KHÔNG nằm trong bản public trên GitHub).

Script này KHÔNG "làm sạch" âm thầm — mục tiêu là in ra đúng những gì audit
phát hiện được (kể cả các vấn đề chặn phân tích), để quyết định phạm vi khả
thi trước khi build KPI/dashboard/model. Xem docs/01_data_audit.md để đọc
đầy đủ audit gốc (schema, % null, anomaly, quyết định đã xác nhận với
stakeholder).
"""
import pandas as pd

DP = "/home/claude/bi_demand_forecasting_project/data_private"

trip = pd.read_pickle(f"{DP}/fact_trip.pkl")
notfound = pd.read_pickle(f"{DP}/fact_notfound.pkl")
user = pd.read_pickle(f"{DP}/dim_user.pkl")

print("=" * 70)
print("A.1 — SỐ DÒNG / SỐ CỘT")
print(f"fact_trip:      {trip.shape[0]:>10,} dòng x {trip.shape[1]} cột")
print(f"fact_notfound:  {notfound.shape[0]:>10,} dòng x {notfound.shape[1]} cột")
print(f"dim_user:       {user.shape[0]:>10,} dòng x {user.shape[1]} cột")

print("\nA.2 — VẤN ĐỀ CHẶN PHÂN TÍCH ĐÃ PHÁT HIỆN")
# trip.user_id (nếu còn tồn tại trong bản raw) trùng 100% với trip.id -> không
# dùng được làm khóa ngoại thật. Bản fact_trip đã loại cột này sau khi xác
# nhận với stakeholder (xem A.9) nên ở đây chỉ còn trip_id.
print(f"- fact_trip KHÔNG có user_id hợp lệ để nối với dim_user")
print(f"  => chặn toàn bộ Retention/Repeat Rate/Cohort/RFM ở cấp khách hàng (Case 3)")

match_rate = notfound["user_id_matched"].mean() * 100
print(f"- fact_notfound.user_id khớp với dim_user.user_id: {match_rate:.1f}% "
      f"({notfound['user_id_matched'].sum():,}/{len(notfound):,}) — dùng LEFT JOIN, không INNER JOIN")

print("\nA.3 — % NULL CÁC CỘT QUAN TRỌNG")
print(f"- fact_trip.city_raw thiếu: {trip['city_is_missing'].mean()*100:.2f}%")
print(f"- fact_notfound.city_raw thiếu: {notfound['city_is_missing'].mean()*100:.2f}%")
print(f"- dim_user.registered_province thiếu: {user['registered_province'].isna().mean()*100:.2f}%")

print("\nA.4 — DISCOUNT COVERAGE (Case 1 — voucher)")
disc_rate = (trip["has_discount"].mean()) * 100
print(f"- % trip có discount_from_code > 0: {disc_rate:.2f}%")
print("  => không có bảng voucher/campaign riêng, không có mã định danh voucher")
print("  => Case 1 (voucher funnel Issued->Claimed->Redeemed) KHÔNG khả thi, "
      "chỉ còn 'Discount Usage Overview' ở mức tổng thể")

print("\nA.5 — ANOMALY: user notfound lặp lại bất thường trong năm")
top_repeat = (
    notfound[notfound["user_id_matched"]]
    .groupby("user_id").size().sort_values(ascending=False).head(3)
)
for uid, cnt in top_repeat.items():
    print(f"  user_id={uid}: {cnt} lần không tìm được tài xế trong năm (nghi test/bot account)")

print("\nA.6 — KẾT LUẬN PHẠM VI KHẢ THI")
print("  Case 1 (Voucher funnel):      KHÔNG khả thi -> còn 'Discount Usage Overview'")
print("  Case 2 (Trip Failure/Ops):    KHẢ THI ĐẦY ĐỦ nhất")
print("  Case 3 (Retention/Cohort):    KHÔNG khả thi ở cấp khách hàng -> pivot sang ML demand forecasting")
print("\nChi tiết đầy đủ: xem docs/01_data_audit.md")
