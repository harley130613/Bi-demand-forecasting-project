# PHẦN E — TABLEAU CALCULATED FIELDS · PHẦN F — DASHBOARD SPECIFICATION
## BUTL 2025 — phạm vi đã xác nhận (4 dashboard khả thi, xem Phần A–D)

> **Lưu ý:** đây là dữ liệu vận hành THẬT của BUTL (2025). Mọi số liệu tài chính tuyệt đối (VNĐ) trong tài liệu này đã được ẩn danh hóa hoặc chuyển thành số tương đối trước khi công khai — xem README.md mục "Bảo mật dữ liệu".


Toàn bộ field dưới đây dùng cú pháp Tableau (không DAX). Áp dụng LOD Expression, Table Calculation, Parameter, Set, Filter, Dashboard Action theo đúng yêu cầu.

---

# PHẦN E — CALCULATED FIELDS

## E.0 Chuẩn bị dữ liệu trước khi vào Tableau (bắt buộc, làm trước)

`raw_trip` và `raw_notfound` **không có khóa chung đáng tin cậy** (xem Phần A/D) → không JOIN 2 bảng này. Cách xử lý đúng trong Tableau:

1. Import riêng 3 file: `datauser2025.xlsx`, `datatrip2025.xlsx`, `datanotfound2025.xlsx` làm 3 Data Source độc lập.
2. Trong `datatrip2025`, **xoá/ẩn cột `user_id`** khỏi mọi worksheet (đã xác nhận là bản sao lỗi của `id` — xem A.9) để tránh nhầm lẫn khi kéo thả field.
3. Muốn tính **Total Demand** (= Total Booking + No Driver Found) theo ngày/city/service: tạo **Union** (không phải Join) giữa `datatrip2025` và `datanotfound2025` trong Tableau (Data pane → kéo `datanotfound2025` thả chồng lên `datatrip2025` → chọn Union), Tableau sẽ tự thêm cột `Table Name` phân biệt nguồn. Đổi tên `Table Name` thành `Source Table`.
   - Sau Union, field `id` của 2 bảng gộp vào 1 cột (`id (datatrip2025.xlsx)` sẽ auto-merge nếu cùng tên) — **kiểm tra kỹ tên cột trùng** trước khi rely vào Union, vì `raw_trip.id` và `raw_notfound.id` không cùng ý nghĩa (xem A.2) — chỉ dùng Union để COUNT dòng theo ngày/city/service, không dùng để so sánh giá trị `id` giữa 2 nguồn.
4. Với `raw_notfound.user_id` muốn join sang `raw_user`: dùng **Relationship** (không phải Join vật lý) giữa `datanotfound2025.user_id` và `datauser2025.user_id`, kiểu Left — vì chỉ khớp ~54% (xem A.2), Relationship trong Tableau xử lý non-matching an toàn hơn Inner Join (không làm mất dòng).

## E.1 Date & Time Calculated Fields

Áp dụng cho cả `[trip_datetime]` (raw_trip) và `[request_datetime]` (raw_notfound) — thay tên field tương ứng.

| Field | Công thức | Loại |
|---|---|---|
| `Trip Year` | `DATEPART('year', [trip_datetime])` | Dimension |
| `Trip Month` | `DATE(DATETRUNC('month', [trip_datetime]))` | Dimension (dùng làm trục X trend) |
| `Trip Week` | `DATEPART('week', [trip_datetime])` | Dimension |
| `Trip Hour` | `DATEPART('hour', [trip_datetime])` | Dimension |
| `Trip Day of Week` | `DATENAME('weekday', [trip_datetime])` | Dimension |
| `Is Weekend` | `IF DATEPART('weekday', [trip_datetime]) IN (1,7) THEN 'Weekend' ELSE 'Weekday' END` | Dimension — Tableau: Chủ Nhật=1, Thứ Bảy=7 |
| `Time Slot` | `CASE [Trip Hour]`<br>`WHEN 0 THEN '00-05h Đêm khuya'` … nhóm theo IF/ELSEIF: `IF [Trip Hour]>=6 AND [Trip Hour]<12 THEN 'Sáng (6-12h)' ELSEIF [Trip Hour]>=12 AND [Trip Hour]<18 THEN 'Chiều (12-18h)' ELSEIF [Trip Hour]>=18 AND [Trip Hour]<24 THEN 'Tối (18-24h)' ELSE 'Đêm khuya (0-6h)' END` | Dimension |

**Cách validate:** kéo `Trip Month` lên Rows, `[Trip Datetime]` (MIN/MAX) lên Text — số tháng phải đúng 12, min/max phải nằm trong 2025.

## E.2 Status & Demand Calculated Fields (áp dụng cho `raw_trip`)

| Field | Công thức | Loại | Mục đích |
|---|---|---|---|
| `Status Group` | `CASE [status]`<br>`WHEN 'Chuyến đi hoàn tất' THEN 'Completed'`<br>`WHEN 'Đã huỷ' THEN 'Cancelled'`<br>`ELSE 'In-progress' END` | Dimension | Chuẩn hoá 5 giá trị status gốc → 3 nhóm |
| `Is Completed` | `IIF([Status Group]='Completed',1,0)` | Measure | Dùng SUM để đếm |
| `Is Cancelled` | `IIF([Status Group]='Cancelled',1,0)` | Measure | — |
| `Total Booking` | `COUNTD([id])` | Measure (Agg) | Grain = 1 dòng/trip nên COUNTD([id]) = COUNT(*) |
| `Completion Rate` | (Sau khi Union với notfound) `SUM([Is Completed]) / (SUM([Is Trip Row]) + SUM([Is NoDriverFound Row]))` | Table Calc / Agg trên bảng Union | Cần field `Is Trip Row`, `Is NoDriverFound Row` từ `[Source Table]` sau Union (xem E.0 bước 3) |
| `Is Trip Row` | `IIF([Source Table]='datatrip2025.xlsx',1,0)` | Measure | Chỉ có sau khi Union |
| `Is NoDriverFound Row` | `IIF([Source Table]='datanotfound2025.xlsx',1,0)` | Measure | Chỉ có sau khi Union |
| `Cancellation Rate` | `SUM([Is Cancelled]) / SUM([Is Trip Row])` | Agg | Trên bảng gốc `raw_trip` (không cần Union) |
| `No Driver Found Rate` | `SUM([Is NoDriverFound Row]) / (SUM([Is Trip Row]) + SUM([Is NoDriverFound Row]))` | Agg trên bảng Union | — |
| `Net Revenue` | `IIF([Status Group]='Completed', [cost_net_vnd], 0)` → dùng SUM | Measure | `cost` đã xác nhận là net (A.9 #3) |
| `AOV` | `SUM([Net Revenue]) / SUM([Is Completed])` | Agg | — |

**Lỗi thường gặp:** quên lọc `Status Group = Completed` khi tính AOV/Net Revenue sẽ làm lẫn cả trip cancelled (cost vẫn có giá trị dù huỷ — xem A.2 cột cost).
**Cách validate:** `SUM([Is Completed]) + SUM([Is Cancelled]) + (đếm riêng 3 status in-progress)` phải bằng `Total Booking`.

## E.3 Operations / Failure Calculated Fields (Case 2 — LOD Expression)

| Field | Công thức | Loại |
|---|---|---|
| `City Failure Rate` | `{FIXED [city_raw] : SUM([Is Cancelled]) + SUM([Is NoDriverFound Row])} / {FIXED [city_raw] : SUM([Is Trip Row]) + SUM([Is NoDriverFound Row])}` | LOD FIXED — tính trên bảng Union |
| `City Total Demand` | `{FIXED [city_raw] : SUM([Is Trip Row]) + SUM([Is NoDriverFound Row])}` | LOD FIXED — dùng để sort/Top N |
| `Hour-DOW Failure Rate` | `{FIXED [Trip Hour], [Trip Day of Week] : SUM([Is Cancelled]) + SUM([Is NoDriverFound Row])} / {FIXED [Trip Hour],[Trip Day of Week] : SUM([Is Trip Row])+SUM([Is NoDriverFound Row])}` | LOD FIXED — dùng cho heatmap |
| `Risk Level` | `IF [City Failure Rate] >= [p_Threshold Critical] THEN 'Critical' ELSEIF [City Failure Rate] >= [p_Threshold Serious] THEN 'Serious' ELSEIF [City Failure Rate] >= [p_Threshold Warning] THEN 'Warning' ELSE 'Good' END` | Dimension — dùng Parameter (xem E.6) để điều chỉnh ngưỡng |

**Compute Using / Partitioning:** với `Hour-DOW Failure Rate`, nếu dùng Table Calculation thay vì LOD, đặt **Compute Using = Trip Hour, Trip Day of Week**, Addressing theo 2 field này, Partitioning theo phần còn lại (City nếu có trên view) — khuyến nghị dùng LOD FIXED ở trên để tránh sai Compute Using khi thêm filter.

**Lỗi thường gặp:** LOD FIXED không tự động bị ảnh hưởng bởi filter thường (trừ Context Filter) — nếu muốn Failure Rate đổi theo filter ngày, phải đưa `Trip Month`/date filter vào **Context Filter** trước, hoặc thêm `[Trip Month]` vào FIXED LOD.
**Cách validate:** so tổng `SUM([Is Cancelled])` toàn bộ dashboard với con số đã audit ở Phần A (127.298).

## E.4 Discount Calculated Fields (Case 1 — phạm vi giới hạn, xem B)

| Field | Công thức | Loại |
|---|---|---|
| `Has Discount` | `IIF([discount_vnd] > 0, 1, 0)` | Measure |
| `Discount Usage Rate` | `SUM([Has Discount]) / SUM([Is Trip Row])` | Agg (trên `raw_trip`, không cần Union) |
| `Avg Discount (khi có discount)` | `SUM([discount_vnd]) / SUM([Has Discount])` — **lưu ý phải lọc `[discount_vnd] > 0`** ở cấp Filter, không lọc trong công thức (tránh chia cho 0 sai) | Agg |
| `Gross Value` | `[cost_net_vnd] + [discount_vnd]` | Measure |
| `Discount-to-Gross Ratio` | `SUM([discount_vnd]) / SUM([Gross Value])` | Agg |

## E.5 User / Growth Calculated Fields (Case 3 — phạm vi rất giới hạn, xem B)

| Field | Công thức | Loại |
|---|---|---|
| `Register Month` | `DATE(DATETRUNC('month',[register_datetime]))` | Dimension |
| `New Registered User` | `COUNTD([user_id])` trên `raw_user` | Measure |
| `NotFound Repeat Count` | `{FIXED [user_id] : COUNTD([request_id])}` trên `raw_notfound` | LOD FIXED |
| `Is Repeat NotFound User` | `IIF([NotFound Repeat Count] > 1, 1, 0)` | Measure |
| `NotFound Repeat Rate` | `COUNTD(IIF([Is Repeat NotFound User]=1,[user_id],NULL)) / COUNTD([user_id])` | Agg |

⚠️ **Không tạo** các field Retention/Cohort/RFM/Repeat Rate/One-and-done cho `raw_trip` — đã xác nhận không khả thi (A.9, B).

## E.6 Parameters

| Parameter | Kiểu | Giá trị mặc định | Mục đích |
|---|---|---|---|
| `p_Threshold Warning` | Float | 30 | Ngưỡng % Failure Rate mức Warning (điều chỉnh được) |
| `p_Threshold Serious` | Float | 50 | Ngưỡng Serious |
| `p_Threshold Critical` | Float | 70 | Ngưỡng Critical |
| `p_Top N Cities` | Integer | 15 | Số tỉnh/thành hiển thị trên bar chart, dùng trong Set (E.7) |

## E.7 Sets

| Set | Định nghĩa | Dùng ở |
|---|---|---|
| `Top N Cities by Demand` | Top `[p_Top N Cities]` theo `SUM([City Total Demand])`, field `city_raw` | Filter cho bar chart Failure Rate theo city |
| `High Risk Cities` | Cities có `[City Failure Rate] >= [p_Threshold Serious]` (dùng Set condition theo field tính toán) | Highlight trên map/bar, Dashboard Action |

## E.8 Chuẩn hoá City (khung sườn — cần bạn tự xác nhận mapping)

Không tự suy đoán mapping tỉnh/thành (theo yêu cầu ban đầu — xem A.4, A.9). Cách làm trong Tableau:

1. Tạo 1 sheet Excel phụ `city_mapping.xlsx` gồm 2 cột: `city_raw` (giá trị gốc, đã liệt kê đủ 59 giá trị ở Phần A) và `city_standard` (bạn tự điền, đặc biệt 5 giá trị thiếu tiền tố: Bến Tre, Hà Tĩnh, Long Xuyên, Sơn La, Vũng Tàu).
2. Join `city_mapping.xlsx` vào `raw_trip`/`raw_notfound` bằng Relationship trên `city_raw`.
3. Field `City Standard`: dùng thẳng `city_standard` từ bảng mapping thay vì `city_raw` trong mọi biểu đồ.

---

# PHẦN F — DASHBOARD SPECIFICATION (4 dashboard khả thi)

## Dashboard 1 — Executive Overview
- **Mục tiêu:** sức khoẻ vận hành tổng thể theo tháng.
- **Người dùng:** Ban Giám đốc, Marketing/Growth lead.
- **Quyết định hỗ trợ:** phát hiện tháng/giai đoạn có vấn đề bất thường cần điều tra sâu hơn ở Dashboard 2.
- **KPI Cards (hàng trên cùng):** Total Booking, Completion Rate, Cancellation Rate, No-Driver-Found Rate, Net Revenue, AOV (6 card, dùng field ở E.2).
- **Biểu đồ:** (1) Line chart 3 series — Completion/Cancellation/No-Driver-Found Rate theo `Trip Month`, 1 trục Y duy nhất (không dual-axis). (2) Bar chart Net Revenue theo `Trip Month`.
- **Filter:** `Trip Year` (2025 mặc định, dự phòng nếu sau này có nhiều năm).
- **Dashboard Action:** không cần — đây là landing dashboard, có nút "Xem chi tiết vận hành →" điều hướng sang Dashboard 2 (Navigate Action).
- **Tooltip:** hiện đủ 3 rate + số tuyệt đối (Completed/Cancelled/NoDriverFound count) khi hover từng điểm trên line chart.
- **Kích thước:** 1280×720 (Desktop).
- **Wireframe (text):**
  ```
  [ KPI 1 ][ KPI 2 ][ KPI 3 ][ KPI 4 ][ KPI 5 ][ KPI 6 ]
  [ Line chart 3-rate trend (60%) ][ Bar Net Revenue (40%) ]
  ```

## Dashboard 2 — Trip Failure & Regional Coverage (Case 2)
- **Mục tiêu:** xác định khu vực & khung giờ ưu tiên bổ sung tài xế.
- **Người dùng:** Operations.
- **Quyết định hỗ trợ:** phân bổ tài xế theo tỉnh/thành và khung giờ.
- **KPI Cards:** Total Booking, Cancelled Trip, No Driver Found Trip, No Driver Found Rate.
- **Biểu đồ:** (1) Horizontal bar `City Failure Rate` theo `city_raw`/`City Standard`, sort desc, filter theo Set `Top N Cities by Demand`, màu theo `Risk Level` (E.3). (2) Heatmap `Hour-DOW Failure Rate` (Trip Hour × Trip Day of Week).
- **Dimension:** city_raw, Trip Hour, Trip Day of Week, service_name.
- **Filter:** Set `Top N Cities by Demand`, Parameter `p_Top N Cities`.
- **Parameter:** `p_Threshold Warning/Serious/Critical` — cho phép Operations tự điều chỉnh ngưỡng cảnh báo theo mùa vụ.
- **Dashboard Action:** Filter Action — click vào 1 city trên bar chart → lọc heatmap chỉ hiện city đó (yêu cầu thêm field `city_raw` vào FIXED LOD của heatmap nếu muốn drill theo city, hiện tại heatmap đang ở mức toàn hệ thống — xem lưu ý dưới).
- **Cảnh báo:** Muốn heatmap lọc theo city cần đổi `Hour-DOW Failure Rate` LOD thêm `[city_raw]` vào FIXED — sẽ làm ô heatmap có ít dữ liệu hơn ở city nhỏ, dễ nhiễu (n nhỏ) — nên hiện cả `City Total Demand` trong tooltip để người xem tự đánh giá độ tin cậy.
- **Kích thước:** 1280×720.

## Dashboard 3 — Discount Usage Overview (Case 1, giới hạn)
- **Mục tiêu:** mô tả mức độ và xu hướng sử dụng discount — **không phải** voucher funnel đầy đủ.
- **Người dùng:** Marketing/Growth (tham khảo, không dùng để quyết định phân bổ ngân sách voucher chi tiết vì thiếu dữ liệu).
- **KPI Cards:** Discount Usage Rate, Avg Discount, Discount-to-Gross Ratio.
- **Biểu đồ:** (1) Area/line chart `Discount Usage Rate` theo `Trip Month`. (2) Bar chart `Avg Discount` theo `service_name`.
- **Filter:** `Trip Month` range.
- **Cảnh báo hiển thị ngay trên dashboard:** text box cố định "Chỉ 1,32% trip có discount — không đủ cơ sở phân tích theo từng chương trình khuyến mãi."
- **Kích thước:** 1280×500 (thấp hơn — ít nội dung).

## Dashboard 4 — User Growth (Case 3, giới hạn)
- **Mục tiêu:** theo dõi xu hướng đăng ký mới song song xu hướng booking — **không** phải retention thật.
- **Người dùng:** Marketing/Growth.
- **Biểu đồ:** (1) Bar `New Registered User` theo `Register Month`. (2) Bar `Total Booking` theo `Trip Month` (đặt cạnh nhau, KHÔNG dual-axis — 2 chart riêng biệt). (3) Horizontal bar Top 10 `registered_province`.
- **Cảnh báo hiển thị ngay trên dashboard:** text box "2 biểu đồ độc lập — không thể tách trip theo khách mới/cũ do thiếu user_id hợp lệ trên raw_trip." + "Phân bố tỉnh/thành chỉ trên 21% user có dữ liệu (79% null)."
- **Kích thước:** 1280×760.

## Dashboard Action tổng thể (áp dụng toàn workbook)
- Navigate Action: nút trên Dashboard 1 → Dashboard 2/3/4.
- Filter Action: click city trên Dashboard 2 → áp dụng cho toàn bộ sheet trong dashboard đó (không áp dụng sang Dashboard khác để tránh gây nhầm lẫn ngữ cảnh, vì Dashboard 3/4 không có dimension city đầy đủ).
