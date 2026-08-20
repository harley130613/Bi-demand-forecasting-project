# BUTL 2025 - BI Dashboard & Demand Forecasting

Dự án thực hiện **Data Audit, xây dựng hệ thống KPI, thiết kế BI Dashboard và phát triển mô hình dự báo nhu cầu** từ dữ liệu vận hành thực tế của BUTL năm 2025.

### Quy mô dữ liệu

| Nguồn dữ liệu | Số lượng |
| --- | ---: |
| Chuyến đặt trên hệ thống | 490.928 |
| Lượt không tìm được tài xế | 68.964 |
| Người dùng | 455.937 |

> **Điểm khác biệt của dự án**
>
> Thay vì trực tiếp xây dựng Dashboard hoặc mô hình theo yêu cầu ban đầu, dự án bắt đầu bằng việc Audit ba bảng dữ liệu thô. Quá trình này phát hiện dữ liệu chưa đủ điều kiện để phân tích Voucher Funnel, Customer Retention và Churn Prediction do thiếu khóa liên kết hợp lệ và dữ liệu Campaign.
>
> Vì vậy, phạm vi dự án được thiết kế lại dựa trên những gì dữ liệu thực tế có thể hỗ trợ. Đây cũng là phần quan trọng nhất của dự án: đánh giá tính khả thi trước khi phân tích, thay vì giả định dữ liệu đã đầy đủ và chính xác.

## Mục lục

- [Bảo mật dữ liệu](#bảo-mật-dữ-liệu)
- [Bài toán ban đầu](#bài-toán-ban-đầu)
- [Phần A - Data Audit](#phần-a---data-audit)
- [Phần B/C/D - Business Questions, KPI Dictionary và Semantic Model](#phần-bcd---business-questions-kpi-dictionary-và-semantic-model)
- [Phần E/F - Tableau Calculated Fields và Dashboard Specification](#phần-ef---tableau-calculated-fields-và-dashboard-specification)
- [Machine Learning - Demand Forecasting](#machine-learning---demand-forecasting)
- [BI Dashboard](#bi-dashboard)
- [Công nghệ sử dụng](#công-nghệ-sử-dụng)
- [Cấu trúc thư mục](#cấu-trúc-thư-mục)
- [Cách chạy dự án](#cách-chạy-dự-án)

---

## Bảo mật dữ liệu

Dự án sử dụng dữ liệu kinh doanh thực tế của doanh nghiệp nơi tác giả đang làm việc.

Các tệp dữ liệu gốc định dạng `.pkl`, tương ứng với ba bảng đã chuẩn hóa gồm `datauser2025`, `datatrip2025` và `datanotfound2025`, chỉ được lưu trong môi trường làm việc cục bộ và không được đưa vào Repository công khai.

Trước khi công khai dữ liệu, các chỉ số được xử lý theo nguyên tắc sau:

| Nhóm dữ liệu | Phương pháp xử lý |
| --- | --- |
| Net Revenue, AOV và Discount trung bình theo dịch vụ | Chuyển từ giá trị VNĐ tuyệt đối thành tỷ trọng hoặc chỉ số Index, với mức trung bình bằng 100 |
| Số chuyến, số người dùng và các tỷ lệ vận hành | Giữ nguyên do không trực tiếp làm lộ quy mô tài chính |
| Completion Rate, Cancellation Rate, No-Driver-Found Rate và Discount Usage Rate | Giữ nguyên dưới dạng tỷ lệ phần trăm |
| MAE, RMSE và MAPE của mô hình | Giữ nguyên để phục vụ đánh giá hiệu quả dự báo |
| Các giá trị Cost bất thường trong tài liệu Audit | Chuyển thành số lần so với Median thay vì công khai giá trị VNĐ |

Các tệp có thể công khai:

```text
output/kpi_summary_public.json
output/dashboard_public.html
```

Tệp chứa số liệu tài chính tuyệt đối không được đưa vào Repository:

```text
output/kpi_summary_private.json
```

---

## Bài toán ban đầu

Dựa trên ba nguồn dữ liệu xuất từ hệ thống vận hành, dự án ban đầu được xây dựng để giải quyết ba bài toán:

1. **Case 1 - Voucher Funnel:** Voucher được phân phối nhiều nhưng tỷ lệ chuyển đổi thấp, cần phân tích hành trình từ phát hành đến sử dụng.

2. **Case 2 - Trip Failure and Regional Coverage:** Tỷ lệ hủy chuyến và không tìm được tài xế cao, cần xác định khu vực và khung giờ ưu tiên bổ sung nguồn cung.

3. **Case 3 - Customer Retention and Churn:** Khách hàng cũ đóng góp phần lớn số chuyến nhưng tỷ lệ quay lại thấp, cần phân tích Retention và dự đoán Churn.

---

## Phần A - Data Audit

### Mục tiêu

Audit toàn bộ ba bảng dữ liệu thô dựa trên:

- Cấu trúc bảng và kiểu dữ liệu
- Tỷ lệ Null
- Tính duy nhất của khóa
- Khả năng liên kết giữa các bảng
- Độ phủ thời gian
- Giá trị bất thường
- Mức độ phù hợp với từng câu hỏi nghiệp vụ

Quá trình Audit phát hiện hai vấn đề nghiêm trọng làm thay đổi phạm vi dự án.

### 1. Không có khóa khách hàng hợp lệ trong bảng chuyến đi

Kết quả kiểm tra cho thấy:

```text
raw_trip.user_id = raw_trip.id
```

Hai trường này trùng nhau trên 100% bản ghi. Điều này cho thấy `raw_trip.user_id` không phải khóa khách hàng thực tế và nhiều khả năng phát sinh từ lỗi Export dữ liệu.

#### Ảnh hưởng

Không thể liên kết chính xác bảng chuyến đi với bảng khách hàng ở cấp độ từng người dùng. Vì vậy, dữ liệu hiện tại không đủ điều kiện để thực hiện:

- Customer Retention
- Repeat Rate
- Cohort Analysis
- RFM Segmentation
- Customer Lifetime Value
- Churn Prediction

Do đó, **Case 3 không thể triển khai ở cấp độ khách hàng**.

### 2. Không có dữ liệu Voucher và Campaign đầy đủ

Dữ liệu chỉ có trường:

```text
discount_from_code
```

Trong đó, khoảng **1,32% số chuyến** có giá trị lớn hơn 0.

Tuy nhiên, dữ liệu không có:

- Mã định danh Voucher
- Ngày phát hành
- Ngày nhận Voucher
- Ngày Claim
- Ngày hết hạn
- Campaign ID
- Nhóm khách hàng nhận Voucher

#### Ảnh hưởng

Không thể xây dựng đầy đủ Voucher Funnel:

```text
Issued -> Claimed -> Redeemed
```

Vì vậy, **Case 1 chỉ có thể thực hiện ở mức Discount Usage Overview**, không thể đánh giá toàn bộ hiệu quả phát hành và chuyển đổi Voucher.

### Các phát hiện khác

- Trường `raw_user.name` thực chất chứa tỉnh hoặc thành phố đăng ký, không phải tên khách hàng.
- `raw_notfound` và `raw_trip` sử dụng hai hệ thống ID độc lập.
- Hai bảng chỉ có thể liên kết qua `user_id`, với tỷ lệ khớp khoảng 47% đến 54%.
- Khi kết hợp dữ liệu cần sử dụng `LEFT JOIN` để tránh làm mất các bản ghi gốc.
- Một số người dùng có hơn 100 lượt không tìm được tài xế trong năm, có khả năng là tài khoản Test hoặc Bot.
- Các trường bị đặt sai tên được đổi tên trước khi sử dụng trong mô hình dữ liệu.
- Các cột không đủ độ tin cậy được loại khỏi phạm vi phân tích.

Toàn bộ quyết định xử lý dữ liệu và điều chỉnh phạm vi dự án đã được xác nhận với Stakeholder trước khi tiếp tục.

Chi tiết Data Audit:

```text
docs/01_data_audit.md
```

### Quyết định điều chỉnh phạm vi

Do không có khóa khách hàng hợp lệ, bài toán Customer Churn không thể triển khai một cách đáng tin cậy.

Dự án được chuyển hướng sang:

> **Dự báo nhu cầu đặt chuyến theo ngày và khu vực để hỗ trợ phân bổ tài xế.**

Bài toán mới vẫn phục vụ mục tiêu vận hành, đồng thời phù hợp với phạm vi dữ liệu thực tế.

---

## Phần B/C/D - Business Questions, KPI Dictionary và Semantic Model

### Feasibility Assessment

Ba mươi câu hỏi nghiệp vụ thuộc ba Case được đánh giá theo ba mức:

| Ký hiệu | Mức độ khả thi |
| :---: | --- |
| ✅ | Có thể triển khai đầy đủ |
| ⚠️ | Chỉ khả thi một phần hoặc cần sử dụng Proxy |
| ❌ | Không thể triển khai với dữ liệu hiện tại |

### Kết quả đánh giá

| Case | Mức độ khả thi | Phạm vi sau điều chỉnh |
| --- | :---: | --- |
| Case 1 - Voucher Funnel | ❌ Phần lớn không khả thi | Chuyển thành Discount Usage Overview |
| Case 2 - Trip Failure and Regional Coverage | ✅ Khả thi nhất | Giữ lại gần như toàn bộ mục tiêu |
| Case 3 - Retention and Cohort | ❌ Không khả thi | Chuyển thành Demand Forecasting |

Việc đánh giá này giúp thể hiện rõ câu hỏi nào có thể trả lời, câu hỏi nào chỉ có thể sử dụng chỉ số đại diện và câu hỏi nào không nên tiếp tục phân tích.

### KPI Dictionary

KPI Dictionary định nghĩa rõ cho từng chỉ số:

- Business Definition
- Numerator
- Denominator
- Data Grain
- Data Source
- Filter Condition
- Limitation
- Interpretation Warning

Ví dụ, `Completion Rate` được tính trên tổng nhu cầu:

```text
Completion Rate =
Completed Trips / (Total Bookings + No-Driver-Found)
```

Nếu chỉ sử dụng `Total Bookings` làm mẫu số, chỉ số sẽ bỏ qua nhóm khách hàng có nhu cầu nhưng hệ thống không tìm được tài xế.

### Semantic Model

Semantic Model được thiết kế lại dựa trên giới hạn thực tế của dữ liệu.

#### Nguyên tắc chính

- Không tạo quan hệ `FACT_TRIP -> DIM_USER` do không có khóa khách hàng hợp lệ.
- `FACT_TRIP` và `FACT_NODRIVERFOUND` không được Join trực tiếp để tính tổng nhu cầu.
- Hai bảng Fact cần được chuẩn hóa cùng Grain và `UNION` khi phân tích Demand.
- `DIM_DATE`, `DIM_CITY` và các bảng Dimension dùng chung được xây dựng riêng để hỗ trợ phân tích.

Chi tiết Business Questions, KPI Dictionary và Semantic Model:

```text
docs/02_business_questions_kpi_semantic_model.md
```

---

## Phần E/F - Tableau Calculated Fields và Dashboard Specification

Dự án xây dựng bộ Calculated Fields theo cú pháp Tableau, bao gồm:

### Date and Time

- Year
- Month
- Week
- Day of Week
- Hour
- Time Slot
- Weekend Flag

### Status and Demand

- Completed Trips
- Cancelled Trips
- No-Driver-Found
- Total Demand
- Completion Rate
- Cancellation Rate
- No-Driver-Found Rate
- Failure Rate

### Tableau nâng cao

- LOD Expression cho Failure Rate theo tỉnh/thành
- LOD Expression theo giờ và ngày trong tuần
- Parameter thiết lập ngưỡng cảnh báo
- Set xác định Top N Cities
- Dashboard Action
- Dynamic Filter
- Highlight Action

### Dashboard Specification

Bốn Dashboard được thiết kế:

1. **Executive Overview**
2. **Trip Failure and Regional Coverage**
3. **Discount Usage Overview**
4. **User Growth Overview**

Mỗi Dashboard được mô tả theo:

- Business Objective
- Target User
- KPI Cards
- Biểu đồ
- Bộ lọc
- Dashboard Action
- Wireframe
- Insight cần rút ra
- Quyết định kinh doanh được hỗ trợ

Chi tiết Tableau Calculated Fields và Dashboard Specification:

```text
docs/03_tableau_calculated_fields_dashboard_spec.md
```

---

## Machine Learning - Demand Forecasting

### Bài toán

Dự báo số Booking theo **ngày và tỉnh/thành** cho sáu khu vực có sản lượng lớn nhất:

- TP.HCM
- Hà Nội
- Bình Dương
- Đồng Nai
- Đà Nẵng
- Vũng Tàu

Mục tiêu là hỗ trợ đội ngũ vận hành dự báo nhu cầu và phân bổ tài xế trước một tuần.

### Feature Engineering

Các Feature được xây dựng hoàn toàn từ dữ liệu quá khứ để tránh Data Leakage:

| Feature | Ý nghĩa |
| --- | --- |
| `lag_1` | Số Booking của ngày liền trước |
| `lag_7` | Số Booking của cùng thứ trong tuần trước |
| `roll_mean_7` | Trung bình trượt trong 7 ngày |
| `roll_mean_14` | Trung bình trượt trong 14 ngày |
| `dow` | Thứ trong tuần |
| `month` | Tháng |
| `is_weekend` | Biến xác định cuối tuần |
| `day_of_year` | Thứ tự ngày trong năm |

### Train/Test Split

Dữ liệu được chia theo thời gian, không sử dụng Random Split:

| Tập dữ liệu | Thời gian |
| --- | --- |
| Train | 01/01 - 31/10/2025 |
| Test | 01/11 - 31/12/2025 |

Tập Test được giữ nguyên trạng và không được sử dụng trong quá trình huấn luyện.

### Kết quả mô hình

Mô hình được so sánh với Naive Baseline, trong đó dự báo của ngày hiện tại bằng số Booking của cùng thứ trong tuần trước.

| Model | MAE | RMSE | MAPE |
| --- | ---: | ---: | ---: |
| Naive Baseline (`lag_7`) | 28,00 | 64,07 | 32,10% |
| Linear Regression | 35,84 | 69,28 | 65,53% |
| Random Forest | 30,58 | 66,63 | 28,65% |
| **Gradient Boosting** | **29,91** | **65,90** | **26,75%** |

### Mô hình được lựa chọn

**Gradient Boosting** được lựa chọn với MAPE đạt **26,75%**, thấp hơn mức **32,10%** của Naive Baseline.

Mức cải thiện tương đối:

```text
(32,10% - 26,75%) / 32,10% = 16,7%
```

### Đánh giá kết quả

- MAPE giảm khoảng **16,7%** so với Naive Baseline.
- MAE của Gradient Boosting vẫn gần với Baseline.
- Nhu cầu đặt chuyến có tính lặp lại mạnh theo tuần, vì vậy Baseline đơn giản đã đạt hiệu quả tương đối tốt.
- Lợi thế chính của Gradient Boosting nằm ở khả năng dự báo ổn định hơn trong những ngày có sản lượng thấp.
- `lag_1` là Feature quan trọng nhất, chiếm khoảng **94% Feature Importance**.

### Hạn chế của mô hình

Mô hình có xu hướng dự báo thấp hơn thực tế trong các giai đoạn nhu cầu tăng đột biến, đặc biệt vào cuối tháng 11 và cuối tháng 12.

Đây là hạn chế phổ biến của các mô hình phụ thuộc nhiều vào Lag Feature. Mô hình chưa được bổ sung các biến ngoại sinh như:

- Ngày lễ
- Thời tiết
- Sự kiện lớn
- Campaign
- Giá dịch vụ
- Nguồn cung tài xế
- Hoạt động Promotion

Chi tiết báo cáo Demand Forecasting:

```text
docs/04_ml_demand_forecasting_report.md
```

---

## BI Dashboard

Dashboard tương tác được lưu tại:

```text
output/dashboard_public.html
```

Dashboard được xây dựng bằng **HTML, CSS, SVG và JavaScript thuần**, không phụ thuộc thư viện biểu đồ bên ngoài và có thể mở trực tiếp trên trình duyệt.

### Nội dung Dashboard

- KPI tổng quan
- Booking Trend theo tháng
- Completion Rate
- Cancellation Rate
- No-Driver-Found Rate
- Failure Rate theo tỉnh/thành
- Heatmap Failure Rate theo khung giờ và ngày trong tuần
- So sánh hiệu quả các mô hình dự báo
- Feature Importance
- Bảng KPI chi tiết theo tỉnh/thành

Booking và ba chỉ số Rate được trình bày trên cùng một hệ trục phù hợp, không sử dụng Dual Axis gây sai lệch khi đọc biểu đồ.

Toàn bộ dữ liệu tài chính trong Dashboard đã được ẩn danh theo nguyên tắc tại phần [Bảo mật dữ liệu](#bảo-mật-dữ-liệu).

---

## Công nghệ sử dụng

| Nhóm | Công nghệ và phương pháp |
| --- | --- |
| Data Processing | Python, Pandas, NumPy |
| Machine Learning | scikit-learn |
| BI Dashboard | HTML, CSS, SVG, JavaScript |
| Tableau | Calculated Fields, LOD Expression, Parameter, Set, Dashboard Action |
| Data Modeling | KPI Dictionary, Semantic Model, ERD |
| Phương pháp phân tích | Data Audit, Feasibility Assessment, Time-series Feature Engineering |
| Bảo mật | Data Anonymization |

### Quy trình dự án

```text
Raw Data
    -> Data Audit
    -> Feasibility Assessment
    -> Data Cleaning
    -> KPI Dictionary
    -> Semantic Model
    -> Dashboard Specification
    -> Demand Forecasting
    -> BI Dashboard
```

---

## Cấu trúc thư mục

```text
bi_demand_forecasting_project/
├── docs/
│   ├── 01_data_audit.md
│   ├── 02_business_questions_kpi_semantic_model.md
│   ├── 03_tableau_calculated_fields_dashboard_spec.md
│   └── 04_ml_demand_forecasting_report.md
├── scripts/
│   ├── 01_data_audit.py
│   ├── 02_kpi_engineering.py
│   ├── 03_ml_demand_forecasting.py
│   └── 04_build_dashboard.py
├── output/
│   ├── kpi_summary_public.json
│   ├── ml_model_comparison.json
│   └── dashboard_public.html
└── README.md
```

### Mô tả các tệp chính

| Tệp | Nội dung |
| --- | --- |
| `docs/01_data_audit.md` | Schema, tỷ lệ Null, Anomaly và các quyết định xử lý dữ liệu |
| `docs/02_business_questions_kpi_semantic_model.md` | Feasibility Matrix, KPI Dictionary và ERD |
| `docs/03_tableau_calculated_fields_dashboard_spec.md` | Calculated Fields và Specification cho bốn Dashboard |
| `docs/04_ml_demand_forecasting_report.md` | Báo cáo đầy đủ về Demand Forecasting |
| `scripts/01_data_audit.py` | Audit Schema, Null và tính hợp lệ của khóa |
| `scripts/02_kpi_engineering.py` | Tính KPI và ẩn danh hóa dữ liệu tài chính |
| `scripts/03_ml_demand_forecasting.py` | Feature Engineering, huấn luyện và so sánh mô hình |
| `scripts/04_build_dashboard.py` | Xây dựng BI Dashboard |
| `output/kpi_summary_public.json` | KPI đã ẩn danh và an toàn để công khai |
| `output/ml_model_comparison.json` | Kết quả so sánh các mô hình |
| `output/dashboard_public.html` | BI Dashboard đã ẩn danh |

> Thư mục `data_private/` gồm năm bảng dữ liệu đã chuẩn hóa là `fact_trip`, `fact_notfound`, `dim_user`, `dim_city` và `daily_city`. Thư mục này cùng với `output/kpi_summary_private.json` chỉ tồn tại trong môi trường làm việc cục bộ và không được đưa vào Repository công khai.

---

## Cách chạy dự án

### 1. Cài đặt thư viện

```bash
pip install pandas numpy scikit-learn
```

### 2. Chuẩn bị dữ liệu

Đặt năm tệp `.pkl` đã chuẩn hóa vào thư mục:

```text
data_private/
```

Danh sách tệp cần thiết:

```text
fact_trip.pkl
fact_notfound.pkl
dim_user.pkl
dim_city.pkl
daily_city.pkl
```

### 3. Chạy Data Audit

```bash
python scripts/01_data_audit.py
```

### 4. Tính KPI và ẩn danh hóa dữ liệu

```bash
python scripts/02_kpi_engineering.py
```

Kết quả:

```text
output/kpi_summary_private.json
output/kpi_summary_public.json
```

### 5. Huấn luyện và so sánh mô hình

```bash
python scripts/03_ml_demand_forecasting.py
```

Kết quả:

```text
output/ml_model_comparison.json
```

### 6. Xây dựng BI Dashboard

```bash
python scripts/04_build_dashboard.py
```

Kết quả:

```text
output/dashboard_public.html
```

---
