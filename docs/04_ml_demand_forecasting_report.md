# ML Project — Demand Forecasting theo Ngày/Khu Vực (BUTL 2025)

## 1. Bài toán

Dự báo **số lượng booking theo ngày, theo tỉnh/thành** cho 6 khu vực có khối lượng lớn nhất (TP.HCM, Hà Nội, Bình Dương, Đồng Nai, Đà Nẵng, Vũng Tàu) — phục vụ phân bổ tài xế và hoạch định vận hành. Đây là bài toán **regression theo chuỗi thời gian**, được pivot từ đề xuất ban đầu ("dự đoán khách hàng rời bỏ") vì `raw_trip` không có user_id hợp lệ để làm bài toán churn ở cấp độ khách hàng (xem Phần A.9 Data Audit).

## 2. Dữ liệu & Feature Engineering

- Nguồn: `fact_trip` (490.928 trip, đã audit ở Phần A), tổng hợp theo (ngày × tỉnh/thành) cho 6 khu vực lớn nhất → 2.190 dòng (365 ngày × 6 khu vực), điền 0 cho ngày không phát sinh booking để có lưới thời gian đầy đủ.
- Feature: `city_code` (mã hoá tỉnh/thành), `dow` (thứ trong tuần), `month`, `is_weekend`, `day_of_year` (xu hướng), `lag_1` (booking hôm qua), `lag_7` (booking cùng thứ tuần trước), `roll_mean_7`, `roll_mean_14` (trung bình trượt 7/14 ngày trước đó — chỉ dùng dữ liệu quá khứ, không rò rỉ thông tin tương lai).
- **Phát hiện dữ liệu đáng chú ý:** Hà Nội có booking = 0 liên tục từ 01/01 đến 18/05/2025, bắt đầu phát sinh từ 19/05/2025 — nhiều khả năng thị trường Hà Nội mới mở giữa năm. Model xử lý đúng giai đoạn này nhờ lag/rolling feature tự nhiên phản ánh baseline thấp trước ngày mở.
- **Train/test split theo thời gian** (không random-split, tránh rò rỉ dữ liệu tương lai vào train): Train = 01/01 – 31/10/2025 (1.740 dòng), Test = 01/11 – 31/12/2025 (366 dòng, 2 tháng cuối năm — giữ nguyên trạng, không nhìn thấy trong lúc train).

## 3. Model & Kết quả

So sánh 3 mô hình trên tập test, cùng 1 baseline naive để đối chứng:

| Model | MAE | RMSE | MAPE |
|---|---:|---:|---:|
| Naive baseline (booking cùng thứ tuần trước — lag_7) | 28,00 | 64,07 | 32,10% |
| Linear Regression | 35,35 | 69,20 | 56,96% |
| Random Forest (300 trees, depth 8) | 31,24 | 69,08 | 28,68% |
| **Gradient Boosting (300 trees, depth 3, lr 0.05)** | **29,91** | **65,90** | **26,75%** |

**Model được chọn: Gradient Boosting Regressor.**

**Đánh giá trung thực:** MAE của Gradient Boosting (29,91) **gần bằng, thậm chí nhỉnh hơn một chút** so với naive baseline (28,00) — nghĩa là chỉ dùng "booking cùng thứ tuần trước" cũng đã là một baseline khá mạnh, vì nhu cầu đi lại có tính lặp lại theo tuần rất rõ. Điểm cải thiện thật sự của model nằm ở **MAPE giảm từ 32,1% xuống 26,75%** (cải thiện tương đối ~17%) — model ổn định hơn baseline ở những ngày có volume thấp (ít bị lệch phần trăm lớn). Feature quan trọng nhất là `lag_1` (94%) — mô hình dựa chủ yếu vào giá trị hôm qua, kết hợp điều chỉnh nhẹ theo `lag_7`, `roll_mean_7/14`.

**Hạn chế cần nêu rõ:** Ở các đợt tăng đột biến (vd cuối tháng 11, cuối tháng 12), model có xu hướng **dự báo thấp hơn thực tế** (xem chart Actual vs Predicted) — đặc điểm điển hình của model dựa nhiều vào lag feature, phản ứng trễ với thay đổi xu hướng đột ngột. Muốn cải thiện thêm cần thêm biến số ngoài dữ liệu hiện có: lịch nghỉ lễ, thời tiết, hoặc cờ đánh dấu campaign đang chạy (dữ liệu hiện tại không có).

## 4. Ứng dụng nghiệp vụ

- Dự báo nhu cầu theo ngày/khu vực giúp Operations chủ động phân bổ tài xế trước 1 tuần, đặc biệt tại các khu vực có Failure Rate cao đã phát hiện ở Dashboard (Tây Ninh, Bắc Ninh, Khánh Hòa — xem Dashboard section 2).
- Vì model học được pattern theo thứ trong tuần rõ rệt, có thể dùng để lên lịch ca trực tài xế theo tuần thay vì phản ứng bị động theo ngày.

## 5. Công cụ thực hiện

- Python (pandas) — tổng hợp dữ liệu theo ngày × tỉnh/thành, feature engineering (lag, rolling mean)
- Python (scikit-learn) — huấn luyện & so sánh Linear Regression / Random Forest / Gradient Boosting
- Python (matplotlib) — trực quan hoá actual vs predicted, feature importance
