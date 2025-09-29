CREATE TABLE raise_ticket (
  raise_ticket_id SERIAL PRIMARY KEY,       -- ID ticket gọi ủng hộ, hệ thống tự đặt
  patient_id SERIAL NOT NULL       -- ID người bệnh
  fundraiser_id SERIAL NOT NULL,       -- cá nhân gọi huy động
  hospital_id SERIAL NOT NULL,       -- ID bệnh viện
  hospital_region SERIAL NOT NULL,       -- tỉnh thành của bệnh viện
  patient_hospitalid SERIAL NOT NULL  -- ID của bệnh nhân trên hệ thống của bệnh viện
  patient_bed_no
  main_type VARCHAR(100) NOT NULL,     -- loại chính (chữa bệnh)
  sub_type VARCHAR(100),               -- loại phụ (vd: …
  unit_price NUMERIC(15,2),                 -- giá (đơn vị chi phí mà mạnh thường quân hỗ trợ, ví dụ 1 unit = 100.000đ)
  total_price_need NUMERIC(15,2),    -- tổng chi phí bệnh nhân cần điều trị
  total_unit_need NUMERIC(15,2),                 -- tổng unit cần (được quy đổi tự động)
  finish_unit NUMERIC(15,2),                 -- tổng unit đã được cộng đồng đóng góp
  start_date DATE,               -- ngày đăng tin
  description TEXT,                    -- mô tả chi tiết về người bệnh
  update_at TIMESTAMP NOT NULL DEFAULT NOW(),
  created_by_id VARCHAR(100)              -- email người tạo tin
  patient_bill_id SERIAL    -- id của hóa đơn chi tiết
  document_bill_id SERIAL    -- id của folder hình ảnh document liên quan
  video_url SERIAL    -- url video tưởng trình
  video_thanks_url SERIAL    -- url video cảm ơn, update sau khi đã kêu gọi hoàn thành
);
CREATE TABLE donate_ticket ( 
  donate_ticket_id SERIAL PRIMARY KEY, 
  donor_id INTEGER NOT NULL REFERENCES bookings(booking_id) ON DELETE CASCADE, 
  raise_ticket_id
  patient_id
  amount NUMERIC(12,2) NOT NULL, 
  currency VARCHAR(3) DEFAULT 'VND', 
  paid_at TIMESTAMP,
  raw_response JSONB,
  created_at TIMESTAMP NOT NULL DEFAULT NOW() 
)
;

CREATE TABLE patients (
    patient_id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW()
    phone VARCHAR(50) UNIQUE

);

CREATE TABLE donors (
    donor_id SERIAL PRIMARY KEY,
    email VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
   phone VARCHAR(50) UNIQUE

);
CREATE TABLE fundraisers (
    donor_id SERIAL PRIMARY KEY,
    email VARCHAR(50) UNIQUE NOT NULL, -- email của bệnh viện
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
 role
   phone VARCHAR(50) UNIQUE

);
