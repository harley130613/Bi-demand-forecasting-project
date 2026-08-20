# PHẦN A — DATA AUDIT
## BUTL 2025 · datauser2025 / datatrip2025 / datanotfound2025

> **Lưu ý:** đây là dữ liệu vận hành THẬT của BUTL (2025). Mọi số liệu tài chính tuyệt đối (VNĐ) trong tài liệu này đã được ẩn danh hóa hoặc chuyển thành số tương đối trước khi công khai — xem README.md mục "Bảo mật dữ liệu".


---

## A.1 Danh sách file/bảng

| # | Tên file | Bảng | Số dòng | Số cột | Vai trò dự kiến |
|---|----------|------|--------:|-------:|------------------|
| 1 | datauser2025.xlsx | `raw_user` | 455.937 | 3 | Danh sách user tạo/đăng ký trong 2025 |
| 2 | datatrip2025.xlsx | `raw_trip` | 490.928 | 9 | Danh sách chuyến đi (booking) phát sinh trong 2025 |
| 3 | datanotfound2025.xlsx | `raw_notfound` | 68.964 | 5 | Danh sách lượt đặt xe không tìm được tài xế (no-driver-found) trong 2025 |

Cả 3 file chỉ có **1 sheet** (`Sheet1`), không có sheet phụ (không có bảng voucher, driver, campaign, location riêng).

---

## A.2 Chi tiết từng cột

### Bảng `raw_user` (datauser2025.xlsx)

| Cột | Kiểu dữ liệu hiện tại | Kiểu đề xuất | % Null | Số giá trị duy nhất | Ghi chú |
|---|---|---|---:|---:|---|
| `user_id` | int64 | Integer (PK) | 0% | 455.937 (100%) | Duy nhất tuyệt đối → có thể dùng làm khóa chính |
| `name` | text | ⚠️ chưa xác định | 78,98% | 61 | **Không chứa tên người** — toàn bộ giá trị là tên tỉnh/thành (vd "Thành phố Hồ Chí Minh", "Tỉnh Đồng Nai"). Nhiều khả năng đây là **tỉnh/thành đăng ký của user**, bị đặt sai tên cột. Cần xác nhận. |
| `create_time` | datetime | Datetime | 0% | 386.447 | Thời điểm tạo tài khoản — phủ đủ 01/01/2025 → 31/12/2025 |

**Grain:** 1 dòng = 1 user được tạo trong 2025.
**Primary key khả dụng:** `user_id`.

---

### Bảng `raw_trip` (datatrip2025.xlsx)

| Cột | Kiểu dữ liệu hiện tại | Kiểu đề xuất | % Null | Số giá trị duy nhất | Ghi chú |
|---|---|---|---:|---:|---|
| `id` | int64 | Integer (PK) | 0% | 490.928 (100%) | ID chuyến đi, gần như liên tục (397.263 → 888.192, span = 490.929 ≈ số dòng) → khả năng là auto-increment toàn hệ thống |
| `user_id` | int64 | ⚠️ **KHÔNG DÙNG ĐƯỢC** | 0% | 490.928 (100%) | 🚩 **`user_id` == `id` ở 100% số dòng (490.928/490.928).** Đây không phải ID khách hàng thật — trông giống lỗi export (cột bị nhân đôi từ `id`). Xem câu hỏi bắt buộc xác nhận ở mục B. |
| `create_date` | datetime | Datetime | 0% | 477.013 | Phủ đủ 01/01 → 31/12/2025 |
| `status` | text | Category | 0% | 5 | `Chuyến đi hoàn tất` (363.611, 74,1%), `Đã huỷ` (127.298, 25,9%), 3 trạng thái đang chạy dở (`Tài xế đang đến đón bạn`, `Tài xế đã bắt đầu chuyến`, `Tài xế đã đến điểm đón` — cộng 19 dòng, đều rơi vào cuối tháng 12 → khả năng là chuyến đang mở tại thời điểm xuất dữ liệu) |
| `city` | text | Category | 32,41% | 38 | Tên tỉnh/thành, không chuẩn hoá 100% (vd "Vũng Tàu", "Bến Tre", "Long Xuyên" thiếu tiền tố "Tỉnh/Thành phố") |
| `service_name` | text | Category | 0% | 6 | Tx Ô tô (65,3%), Tx Xe máy (34,1%), Tx Đi Tỉnh, Bship Bike, Đăng kiểm hộ, Liên kết bãi giữ xe |
| `cost` | int64 | Currency (VND) | 0% | 3.912 | Median ở mức phổ biến của giá cước trong app (đã ẩn danh hóa, không nêu số VNĐ tuyệt đối); có 3 dòng = 0; có 10 dòng bất thường lớn (~47–110 lần median) — toàn bộ đều ở status `Đã huỷ` |
| `discount_from_code` | int64 | Currency (VND) | 0% | 797 | Chỉ 6.460/490.928 dòng (1,3%) có giá trị > 0. Không rõ đây là số tiền giảm từ 1 "code" cụ thể nào, không có cột định danh code/voucher/campaign đi kèm |
| `point` | int64 | Integer | 0% | 89 | 161.100/490.928 dòng (32,8%) > 0, range 0–292. Không rõ là điểm tích lũy được cộng hay điểm được dùng để trừ |

**Grain:** 1 dòng = 1 chuyến đi (booking) được tạo trong 2025 (không phân biệt rõ "booking" và "trip" — mọi trạng thái kể cả `Đã huỷ` đều nằm chung 1 bảng).
**Primary key khả dụng:** `id`.
**Foreign key khả dụng:** ❌ Hiện chưa có — `user_id` không đáng tin cậy (xem mục B).

---

### Bảng `raw_notfound` (datanotfound2025.xlsx)

| Cột | Kiểu dữ liệu hiện tại | Kiểu đề xuất | % Null | Số giá trị duy nhất | Ghi chú |
|---|---|---|---:|---:|---|
| `id` | int64 | Integer (PK?) | 0% | 68.964 (100%) | Range 45.428 → 1.288.169 — **vượt xa** range của `raw_trip.id` (397.263–888.192) và có phần **thấp hơn** cả điểm bắt đầu của `raw_trip.id` → khả năng đây là ID thuộc hệ thống/sequence khác (booking-request ID), không cùng không gian ID với `raw_trip.id`. Chỉ 36.543/68.964 dòng (53%) trùng giá trị với `raw_trip.id` — có thể là trùng ngẫu nhiên do cùng dải số |
| `user_id` | int64 | Integer (FK, có vẻ hợp lệ) | 0% | 31.372 | ✅ Khác với `raw_trip`, cột này **có lặp lại thật** (14.575/31.372 user có >1 lần không tìm được tài xế) → nhiều khả năng đây là user_id thật. Trùng với `raw_user.user_id`: 17.027/31.372 (54%) |
| `create_date` | datetime | Datetime | 0% | 68.717 | Phủ đủ 01/01 → 31/12/2025 |
| `city` | text | Category | 35,99% | 59 | Cùng vấn đề chuẩn hoá tên tỉnh/thành như `raw_trip.city` |
| `service_name` | text | Category | 0% | 6 | Có thêm giá trị `Tra cứu phạt nguội` không xuất hiện trong `raw_trip` |

**Grain:** 1 dòng = 1 lượt tìm tài xế thất bại (không tìm được tài xế) trong 2025.
**Primary key khả dụng:** `id` (trong phạm vi bảng này).
**Foreign key khả dụng:** `user_id` — có vẻ hợp lệ nhưng cần xác nhận vì chỉ khớp 54% với `raw_user`.

⚠️ Điểm bất thường: 1 user_id (214.988) có **141 lần** không tìm được tài xế trong năm, 1 user khác (568.163) có **111 lần** — cao bất thường so với trung vị, nên xem xét loại trừ hoặc gắn cờ khi phân tích (khả năng test account/bot/tài xế tự thử hệ thống).

---

## A.3 Độ đầy đủ dữ liệu theo thời gian

Cả 3 bảng đều phủ đủ 12 tháng (01/01/2025 – 31/12/2025), không phát hiện tháng nào bị thiếu dữ liệu hoàn toàn.

| Tháng | raw_user (đăng ký) | raw_trip (booking) | raw_notfound |
|---|---:|---:|---:|
| 01 | 23.000 | 35.699 | 8.564 |
| 02 | 45.016 | 30.546 | 5.192 |
| 03 | 50.223 | 35.519 | 3.966 |
| 04 | 39.118 | 34.831 | 3.787 |
| 05 | 45.612 | 34.327 | 5.269 |
| 06 | 34.222 | 35.820 | 6.151 |
| 07 | 35.304 | 41.830 | 6.530 |
| 08 | 47.664 | 42.256 | 7.166 |
| 09 | 40.882 | 39.832 | 4.562 |
| 10 | 39.735 | 48.650 | 6.195 |
| 11 | 29.147 | 52.823 | 5.932 |
| 12 | 26.014 | 58.795 | 5.650 |

Nhận xét: booking tăng rõ rệt nửa cuối năm (Q4 ~52k–59k/tháng so với Q1 ~30k–35k/tháng) — khớp với insight "tăng trưởng nửa cuối 2025" đã có trong các slide port hiện tại.

---

## A.4 Các trường cần chuẩn hoá

1. **`raw_user.name`** — đổi tên/định nghĩa lại (không phải tên người).
2. **`city`** (cả `raw_trip` và `raw_notfound`) — chuẩn hoá tiền tố "Tỉnh"/"Thành phố" (vd "Vũng Tàu" → "Tỉnh Bà Rịa – Vũng Tàu"?, "Long Xuyên" → thuộc "Tỉnh An Giang"?) — cần xác nhận cách map.
3. **`raw_trip.user_id`** — không dùng được ở dạng hiện tại, cần nguồn thay thế hoặc xác nhận đây là lỗi export.
4. **`raw_trip.status`** — 3 trạng thái "đang chạy" (19 dòng) cần quyết định xử lý (loại khỏi phân tích do chưa kết thúc, hay gộp vào 1 nhóm "in-progress").

---

## A.5 KPI có thể tính ngay (với dữ liệu hiện có)

- Total Booking, Completed Trip, Cancelled Trip theo ngày/tuần/tháng (từ `raw_trip.status`)
- Completion Rate, Cancellation Rate (ở mức toàn hệ thống — **chưa** phân theo user)
- Gross Revenue/GMV theo `cost` (cần xác nhận `cost` là giá trị đã tính discount hay trước discount)
- Average Order Value, phân bố theo `service_name`, `city` (với 32–36% dòng thiếu city)
- No Driver Found volume & xu hướng theo thời gian, theo `service_name`, theo `city` (từ `raw_notfound`, ở mức toàn hệ thống)
- New Registered User theo tháng (từ `raw_user.create_time`)
- Discount usage rate ở mức **tổng thể** (6.460/490.928 chuyến có discount > 0) — nhưng **không** phân tích được theo từng mã/chương trình khuyến mãi vì không có cột định danh voucher/campaign

## A.6 KPI CHƯA thể tính do thiếu dữ liệu

Toàn bộ các KPI sau trong 3 case đều **chưa làm được** với dữ liệu hiện tại:

- **Mọi KPI theo user thật** trong `raw_trip`: Repeat Rate, Retention D7/D14/D30/D60/D90, First-to-Second Trip Conversion, One-and-done, Cohort retention, RFM, Customer Lifetime Trips, Trip Concentration — vì không có cột user_id hợp lệ trong `raw_trip` (case 3 gần như không triển khai được nếu không xử lý được vấn đề này).
- **Toàn bộ Voucher/Campaign funnel** (Case 1): Voucher Issued, Voucher Claimed, Voucher Redeemed, Redemption Rate theo từng voucher, Time to Redeem, Voucher Expired Unused, Promotion Cost theo campaign — vì không có bảng voucher/campaign, không có mã định danh voucher, không có ngày phát hành/hạn dùng.
- **Cancellation Reason & Cancellation theo actor** (Case 2): không có cột lý do huỷ, không có cờ phân biệt khách/tài xế/hệ thống huỷ.
- **Driver Matching Time, Driver Supply/Active Driver** (Case 2): không có bảng tài xế, không có thời điểm bắt đầu tìm tài xế và thời điểm ghép thành công để tính matching time.
- **Net Revenue** (nếu khác Gross): không có cột chi phí vận hành/chiết khấu tài xế.
- **Segment/Campaign nguồn khách** (UTM, kênh acquisition): không có trong 3 file.

---

## A.7 Giá trị bất thường phát hiện

| Vị trí | Bất thường | Ghi chú |
|---|---|---|
| `raw_trip.cost` | 10 chuyến `Đã huỷ` có cost cao bất thường (~47–110 lần median, số VNĐ tuyệt đối đã ẩn danh hóa) | Bất thường vì trạng thái huỷ hiếm khi có giá trị cao bất thường như vậy — cần xác nhận `cost` là giá ước tính hay giá thực thu |
| `raw_trip.cost` | 3 chuyến cost = 0 | Cả 3 đều ngày 20/10/2025, cùng batch — nghi lỗi ghi nhận |
| `raw_notfound.user_id` | user 214.988: 141 lần; user 568.163: 111 lần không tìm được tài xế trong năm | Bất thường cao so với trung vị — nghi test account/bot |
| `raw_trip.status` | 19 dòng trạng thái "đang chạy" (chưa kết thúc), đều thuộc nửa cuối 12/2025 | Nhiều khả năng là snapshot tại thời điểm export, không phải lỗi |

---

## A.8 Tóm tắt Primary/Foreign Key

| Bảng | Primary Key | Foreign Key khả dụng | Foreign Key KHÔNG khả dụng |
|---|---|---|---|
| `raw_user` | `user_id` | — | — |
| `raw_trip` | `id` | — | `user_id` (= `id`, không phải khóa ngoại thật) |
| `raw_notfound` | `id` | `user_id` → `raw_user.user_id` (khớp 54%, cần xác nhận) | `id` → không khớp rõ ràng với `raw_trip.id` (chỉ trùng 53%, nhiều khả năng ngẫu nhiên) |

**Hệ quả quan trọng nhất:** hiện tại **không có cách nào join `raw_trip` với `raw_user` theo đúng khách hàng thật**, vì cột duy nhất có thể dùng để join (`raw_trip.user_id`) thực chất là bản sao của `raw_trip.id`. Đây là vấn đề chặn (blocking issue) cho toàn bộ Case 3 và một phần Case 1, Case 2 — cần xác nhận trước khi đi tiếp.

---

## A.9 Quyết định đã xác nhận với stakeholder (17/08/2026)

| # | Câu hỏi | Trả lời | Tác động |
|---|---|---|---|
| 1 | `raw_trip.user_id` = `raw_trip.id` 100% — có xuất lại được file đúng không? | **Không, dữ liệu gốc chỉ có vậy** | ❌ Loại bỏ hoàn toàn khỏi phạm vi: Retention D7–D90, Repeat Rate, One-and-done, First-to-Second Trip Conversion, Cohort Retention, RFM, Customer Lifetime Trips, Trip Concentration, và mọi phân tích "theo từng khách hàng" dựa trên bảng trip. Case 3 chỉ còn thực hiện được ở mức **tổng thể theo thời gian** (vd: % trip từ user mới trong tháng dựa vào so sánh số lượng, không phải join trực tiếp từng dòng). |
| 2 | `raw_user.name` = tỉnh/thành đăng ký | Xác nhận đúng | Đổi tên field chuẩn: `registered_province` |
| 3 | `cost` đã trừ discount hay chưa | **Đã trừ discount (net)** | GMV/Revenue tính trên `cost` là **Net Revenue thực thu**, không phải giá gốc trước khuyến mãi. Muốn có Gross phải cộng lại: `gross = cost + discount_from_code` |
| 4 | Có bảng voucher/campaign riêng không | **Không, `discount_from_code` là toàn bộ dữ liệu khuyến mãi có** | Case 1 (voucher funnel Issued→Claimed→Redeemed, redemption rate theo từng voucher, expired unused, time-to-redeem) **không triển khai được** — chỉ còn phân tích được "chuyến có/không có discount" và số tiền discount ở mức tổng thể |
| 5 | `raw_notfound.id` khác không gian với `raw_trip.id` | Xác nhận đúng — user đặt lại (retry) đến khi có trip | `raw_notfound` và `raw_trip` là 2 sự kiện độc lập theo thời gian, join qua `user_id` (không qua `id`) khi có thể |
| 6 | Có file driver/cancellation reason/campaign/location khác không | **Không có** | Ghi nhận Data Limitation chính thức — không có Driver Matching Time, Cancellation Reason, Cancellation Actor (khách/tài xế/hệ thống), Driver Supply |
| 7 | Ý nghĩa `point` | Điểm thưởng trong app, được claim theo scheme từng chương trình, quy đổi theo tỷ lệ cố định do doanh nghiệp quy định (số VNĐ/điểm đã ẩn danh hóa) | `point` là cơ chế khuyến mãi **thứ 2**, độc lập phần lớn với `discount_from_code` (chỉ 3.153/490.928 dòng có cả 2, còn lại tách biệt) |

### Hệ quả cho phạm vi ML đã chọn trước đó (dự đoán khách hàng rời bỏ/ngủ đông)

Do không có user_id hợp lệ trong `raw_trip`, bài toán **customer churn prediction dựa trên lịch sử nhiều chuyến của cùng 1 khách** (recency/frequency theo từng user) **không thể thực hiện được** với dữ liệu hiện tại — cần pivot sang bài toán khác phù hợp với dữ liệu thật.
