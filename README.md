# BUTL 2025 — BI Dashboard & Demand Forecasting

Data audit, KPI framework, BI dashboard và mô hình dự báo nhu cầu — xây dựng từ **dữ liệu vận hành
thật** của BUTL năm 2025 (490.928 chuyến, 68.964 lượt không tìm được tài xế, 455.937 user).

> **Điểm khác biệt của project này:** thay vì đi thẳng vào build dashboard/model theo đúng đề bài gốc
> (voucher funnel, customer retention, churn prediction...), bước đầu tiên là **audit nghiêm ngặt 3
> bảng dữ liệu thô** — và phát hiện ra dữ liệu **không đủ điều kiện** để trả lời phần lớn câu hỏi ban
> đầu (không có khóa nối hợp lệ giữa chuyến đi và khách hàng, không có bảng voucher/campaign...).
> Toàn bộ phạm vi phân tích bên dưới được **thiết kế lại** dựa trên giới hạn thật của dữ liệu, thay vì
> giả định dữ liệu "đẹp" như đề bài ban đầu — đây là phần việc mình cho là quan trọng nhất của project.

## Bảo mật dữ liệu

Đây là số liệu kinh doanh thật của doanh nghiệp nơi tác giả đang làm việc. File dữ liệu gốc (`.pkl`,
tương đương 3 bảng `datauser2025` / `datatrip2025` / `datanotfound2025` đã chuẩn hoá) **chỉ lưu cục
bộ, không đưa vào repo công khai** — xem mục "Cấu trúc thư mục". Trước khi công khai:

- **Net Revenue, AOV, giá trị discount trung bình theo dịch vụ** — chuyển từ VNĐ tuyệt đối thành
  **% thị phần / chỉ số (index, trung bình = 100)**.
- **Số lượng chuyến, user, tỷ lệ % (Completion/Cancellation/No-Driver-Found/Discount Usage Rate),
  MAPE mô hình** — giữ nguyên số thật vì không làm lộ quy mô tài chính của doanh nghiệp.
- 2 ví dụ VNĐ bất thường trong `docs/01_data_audit.md` (giá trị `cost` cao bất thường ở 10 chuyến đã
  huỷ) được đổi thành **số lần so với median** thay vì số VNĐ tuyệt đối.

`output/kpi_summary_public.json` và `output/dashboard_public.html` là bản **đã ẩn danh hóa**, an toàn
để công khai; `output/kpi_summary_private.json` (số VNĐ thật) không nằm trong bản public.

## Bài toán

BUTL đề xuất 3 bài toán ban đầu dựa trên 3 nguồn dữ liệu xuất từ hệ thống vận hành:

1. **Case 1** — Voucher push nhiều nhưng chuyển đổi thấp — cần phân tích voucher funnel.
2. **Case 2** — Tỷ lệ huỷ chuyến & không tìm được tài xế cao — cần xác định khu vực/khung giờ ưu tiên.
3. **Case 3** — Khách hàng cũ chiếm phần lớn chuyến nhưng retention thấp — cần dự đoán churn.

## Phần A — Data Audit (điểm mấu chốt của project)

Audit chi tiết 3 bảng thô — schema, % null, tính duy nhất của khóa, độ phủ thời gian — phát hiện
**2 vấn đề chặn phân tích nghiêm trọng**:

- **`raw_trip.user_id` trùng 100% với `raw_trip.id`** — không phải khóa khách hàng thật (nhiều khả
  năng là lỗi export) → **không thể nối bảng chuyến đi với bảng khách hàng theo từng người**, chặn
  toàn bộ Retention/Repeat Rate/Cohort/RFM ở cấp khách hàng (Case 3).
- **Không có bảng voucher/campaign riêng** — chỉ có 1 cột `discount_from_code` (1,32% chuyến có giá
  trị > 0), không có mã định danh voucher, không có ngày phát hành/hạn dùng → **không dựng được
  voucher funnel** (Issued → Claimed → Redeemed) như đề bài gốc yêu cầu (Case 1).

Các phát hiện khác: `raw_user.name` thực chất là tỉnh/thành đăng ký (không phải tên người, bị đặt sai
tên cột); `raw_notfound` và `raw_trip` dùng 2 hệ ID độc lập, chỉ nối được qua `user_id` (khớp ~47–54%,
dùng LEFT JOIN); phát hiện vài user có đến 100+ lần không tìm được tài xế trong năm (nghi test/bot
account). Toàn bộ quyết định xử lý (đổi tên field, loại bỏ cột không dùng được, phạm vi Case nào còn
khả thi) đã được **xác nhận với stakeholder** trước khi đi tiếp — xem `docs/01_data_audit.md`.

**Hệ quả:** Case 3 (customer churn) không triển khai được ở cấp khách hàng → **pivot sang bài toán
dự báo nhu cầu (demand forecasting) theo ngày/khu vực**, vẫn phục vụ đúng mục tiêu nghiệp vụ (phân
bổ tài xế) nhưng phù hợp với dữ liệu thật đang có.

## Phần B/C/D — Business Questions, KPI Dictionary & Semantic Model

Từng câu hỏi nghiệp vụ gốc (30 câu, 3 case) được đánh giá lại theo 3 mức: ✅ khả thi đầy đủ · ⚠️ khả
thi một phần/cần proxy · ❌ không khả thi — thay vì âm thầm bỏ qua phần không làm được. Kết quả:

| Case | Khả thi | Ghi chú |
|---|---|---|
| Case 1 — Voucher funnel | ❌ phần lớn | Chỉ còn "Discount Usage Overview" mô tả tổng thể |
| Case 2 — Trip Failure & Regional Coverage | ✅ khả thi nhất | Giữ được gần hết mục tiêu gốc |
| Case 3 — Retention/Cohort | ❌ | Pivot sang Demand Forecasting (ML) |

KPI Dictionary định nghĩa rõ numerator/denominator/grain/cảnh báo cho từng KPI khả thi (vd:
`Completion Rate` phải chia cho **Total Booking + No-Driver-Found** chứ không chỉ Total Booking, để
phản ánh đúng "tổng nhu cầu"). Semantic Model (ERD) được thiết kế lại — **không** có quan hệ
`FACT_TRIP → DIM_USER` vì lý do đã nêu ở Phần A, `FACT_TRIP` và `FACT_NODRIVERFOUND` phải **UNION**
(không JOIN) khi tính tổng nhu cầu. Chi tiết đầy đủ: `docs/02_business_questions_kpi_semantic_model.md`.

## Phần E/F — Tableau Calculated Fields & Dashboard Spec

Bộ Calculated Fields đầy đủ theo cú pháp Tableau (Date/Time, Status & Demand, LOD Expression cho
Failure Rate theo city và theo giờ×ngày, Parameter cho ngưỡng cảnh báo, Set cho Top N Cities) và
specification cho 4 dashboard khả thi (Executive Overview, Trip Failure & Regional Coverage, Discount
Usage Overview, User Growth) — mục tiêu, KPI card, biểu đồ, filter, dashboard action, wireframe cho
từng dashboard. Chi tiết: `docs/03_tableau_calculated_fields_dashboard_spec.md`.

## ML — Demand Forecasting

**Bài toán:** dự báo số booking theo ngày × tỉnh/thành cho 6 khu vực lớn nhất (TP.HCM, Hà Nội, Bình
Dương, Đồng Nai, Đà Nẵng, Vũng Tàu) — phục vụ phân bổ tài xế trước 1 tuần.

**Feature engineering:** `lag_1` (booking hôm qua), `lag_7` (cùng thứ tuần trước), `roll_mean_7/14`
(trung bình trượt), đặc trưng thời vụ (`dow`, `month`, `is_weekend`, `day_of_year`) — chỉ dùng dữ liệu
quá khứ, không rò rỉ thông tin tương lai. **Train/test split theo thời gian** (không random-split):
Train = 01/01–31/10/2025, Test = 01/11–31/12/2025 (giữ nguyên trạng, không nhìn thấy lúc train).

**Kết quả (so với baseline naive = booking cùng thứ tuần trước):**

| Model | MAE | RMSE | MAPE |
|---|---:|---:|---:|
| Naive baseline (lag_7) | 28,00 | 64,07 | 32,10% |
| Linear Regression | 35,84 | 69,28 | 65,53% |
| Random Forest | 30,58 | 66,63 | 28,65% |
| **Gradient Boosting** | **29,91** | **65,90** | **26,75%** |

Model được chọn: **Gradient Boosting** — MAPE giảm từ 32,10% xuống 26,75% (cải thiện tương đối
~16,7%). **Đánh giá trung thực:** MAE gần bằng baseline naive — nhu cầu đi lại có tính lặp lại rất
mạnh theo tuần nên baseline đơn giản đã khá tốt; cải thiện thật sự nằm ở việc model ổn định hơn ở
những ngày volume thấp. Feature quan trọng nhất là `lag_1` (~94% importance). **Hạn chế:** ở các đợt
tăng đột biến (cuối tháng 11, cuối tháng 12), model có xu hướng dự báo thấp hơn thực tế — đặc điểm
điển hình của model dựa nhiều vào lag feature. Chi tiết: `docs/04_ml_demand_forecasting_report.md`.

## BI Dashboard

`output/dashboard_public.html` — dashboard tương tác dựng bằng **HTML + SVG thuần** (không phụ thuộc
thư viện biểu đồ ngoài, mở trực tiếp bằng trình duyệt): KPI tổng quan, Booking & 3-rate trend theo
tháng (1 trục Y, không dual-axis), Failure Rate theo tỉnh/thành & theo khung giờ×ngày (heatmap), so
sánh model dự báo, feature importance, và bảng chi tiết theo tỉnh/thành. Toàn bộ số liệu tài chính
trong dashboard đã ẩn danh hóa theo đúng nguyên tắc ở mục "Bảo mật dữ liệu".

## Công nghệ sử dụng

Python (Pandas, NumPy, scikit-learn) cho data audit, KPI engineering & ML · HTML/CSS/SVG/JavaScript
thuần cho BI Dashboard · Tableau (Calculated Fields, LOD Expression, Parameter, Set, Dashboard Action)
cho spec thiết kế dashboard · Phương pháp: data audit & feasibility assessment, KPI dictionary,
semantic modeling (ERD), time-series feature engineering, model comparison có baseline đối chứng, data
anonymization cho số liệu kinh doanh nhạy cảm.

## Cấu trúc thư mục

```
bi_demand_forecasting_project/
├── docs/
│   ├── 01_data_audit.md                              # Phần A — schema, % null, anomaly, quyết định đã xác nhận
│   ├── 02_business_questions_kpi_semantic_model.md   # Phần B/C/D — feasibility matrix, KPI dictionary, ERD
│   ├── 03_tableau_calculated_fields_dashboard_spec.md # Phần E/F — Calculated Fields, 4 dashboard spec
│   └── 04_ml_demand_forecasting_report.md            # Báo cáo đầy đủ ML demand forecasting
├── scripts/
│   ├── 01_data_audit.py            # audit schema/null/key-validity trên dữ liệu thật
│   ├── 02_kpi_engineering.py       # tính KPI Case 1/2 + ẩn danh hóa số liệu tài chính
│   ├── 03_ml_demand_forecasting.py # feature engineering + so sánh 3 model + baseline
│   └── 04_build_dashboard.py       # dựng output/dashboard_public.html
├── output/
│   ├── kpi_summary_public.json     # KPI đã ẩn danh hóa — an toàn để public
│   ├── ml_model_comparison.json    # so sánh model (không chứa số tiền)
│   └── dashboard_public.html       # BI Dashboard (đã ẩn danh hóa)
└── README.md
```

> `data_private/` (5 bảng dữ liệu thật đã chuẩn hoá: `fact_trip`, `fact_notfound`, `dim_user`,
> `dim_city`, `daily_city`) và `output/kpi_summary_private.json` (số VNĐ thật) chỉ tồn tại ở bản làm
> việc cục bộ, **không** có trong repo public.

## Cách chạy lại

```bash
pip install pandas numpy scikit-learn

# cần đặt 5 file .pkl (fact_trip, fact_notfound, dim_user, dim_city, daily_city) vào data_private/
python scripts/01_data_audit.py            # in kết quả audit
python scripts/02_kpi_engineering.py       # tính KPI + ghi output/kpi_summary_{private,public}.json
python scripts/03_ml_demand_forecasting.py # train & so sánh model, ghi output/ml_model_comparison.json
python scripts/04_build_dashboard.py       # dựng output/dashboard_public.html
```

---
*Trần Thị Cẩm Loan — Marketing Data Analyst*
