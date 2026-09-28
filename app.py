import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date

# ---------------------------------------------------------
# CẤU HÌNH TRANG STREAMLIT
# ---------------------------------------------------------
st.set_page_config(
    page_title="Hệ Thống Quản Lý Khách Sạn",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# CẤU HÌNH LOGO KHÁCH SẠN
# ---------------------------------------------------------
# Phương án 1: Sử dụng URL ảnh từ Internet (Dùng sẵn để chạy ngay)
LOGO_URL = "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=400&q=80"

# Phương án 2: Sử dụng file ảnh trong máy (Ví dụ file 'logo.png' cùng thư mục)
# Hãy bỏ dấu comment (#) dòng dưới nếu bạn có sẵn file ảnh local:
# LOGO_URL = "logo.png"

# ---------------------------------------------------------
# KẾT NỐI VÀ KHỞI TẠO CƠ SỞ DỮ LIỆU SQLITE
# ---------------------------------------------------------
DB_NAME = "hotel_management.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Bảng Quản lý Phòng
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            room_number TEXT PRIMARY KEY,
            room_type TEXT NOT NULL,
            price_per_night REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Trống'
        )
    ''')
    
    # Bảng Quản lý Đặt phòng / Thuê phòng
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            room_number TEXT NOT NULL,
            check_in_date DATE NOT NULL,
            check_out_date DATE NOT NULL,
            total_price REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Đã đặt',
            FOREIGN KEY (room_number) REFERENCES rooms (room_number)
        )
    ''')
    
    # Thêm dữ liệu mẫu nếu bảng phòng trống
    cursor.execute("SELECT COUNT(*) FROM rooms")
    if cursor.fetchone()[0] == 0:
        sample_rooms = [
            ("101", "Đơn Standard", 300000, "Trống"),
            ("102", "Đơn Standard", 300000, "Trống"),
            ("201", "Đôi Deluxe", 500000, "Trống"),
            ("202", "Đôi Deluxe", 500000, "Trống"),
            ("301", "VIP Suite", 900000, "Trống"),
        ]
        cursor.executemany("INSERT INTO rooms VALUES (?, ?, ?, ?)", sample_rooms)
    
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# CÁC HÀM XỬ LÝ DỮ LIỆU (HELPER FUNCTIONS)
# ---------------------------------------------------------
def fetch_rooms():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM rooms ORDER BY room_number", conn)
    conn.close()
    return df

def fetch_bookings():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM bookings ORDER BY id DESC", conn)
    conn.close()
    return df

def add_room(room_number, room_type, price):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO rooms VALUES (?, ?, ?, 'Trống')", (room_number, room_type, price))
        conn.commit()
        return True, "Thêm phòng thành công!"
    except sqlite3.IntegrityError:
        return False, f"Mã phòng {room_number} đã tồn tại!"
    finally:
        conn.close()

def update_room_status(room_number, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE rooms SET status = ? WHERE room_number = ?", (status, room_number))
    conn.commit()
    conn.close()

def create_booking(guest_name, phone, room_number, check_in, check_out, total_price):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO bookings (guest_name, phone, room_number, check_in_date, check_out_date, total_price, status)
        VALUES (?, ?, ?, ?, ?, ?, 'Đã check-in')
    ''', (guest_name, phone, room_number, check_in, check_out, total_price))
    cursor.execute("UPDATE rooms SET status = 'Đang có khách' WHERE room_number = ?", (room_number,))
    conn.commit()
    conn.close()

def checkout_booking(booking_id, room_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET status = 'Đã check-out' WHERE id = ?", (booking_id,))
    cursor.execute("UPDATE rooms SET status = 'Trống' WHERE room_number = ?", (room_number,))
    conn.commit()
    conn.close()

# ---------------------------------------------------------
# GIAO DIỆN CHÍNH (SIDEBAR MENU)
# ---------------------------------------------------------
# Hiển thị Logo ở Thanh Sidebar
with st.sidebar:
    st.image(LOGO_URL, use_container_width=True)
    st.title("🏨 GRAND HOTEL")
    st.caption("Hệ thống quản lý phòng thông minh")
    st.divider()

menu = st.sidebar.radio(
    "Danh mục quản lý:",
    ["📊 Sơ Đồ Phòng & Tổng Quan", "📝 Đặt Phòng / Check-in", "💳 Check-out & Thanh Toán", "⚙️ Quản Lý Phòng", "📈 Báo Cáo Doanh Thu"]
)

# Hiển thị Logo + Tiêu đề thương hiệu ở đầu trang chính
header_col1, header_col2 = st.columns([1, 6])
with header_col1:
    st.image(LOGO_URL, width=90)
with header_col2:
    st.markdown("<h1 style='margin-bottom:0;'>GRAND HOTEL MANAGEMENT</h1>", unsafe_allow_html=True)
    st.caption("Phần mềm quản lý khách sạn và doanh thu trực quan")

st.divider()

# ---------------------------------------------------------
# 1. SƠ ĐỒ PHÒNG & TỔNG QUAN
# ---------------------------------------------------------
if menu == "📊 Sơ Đồ Phòng & Tổng Quan":
    st.subheader("📊 Sơ Đồ Trạng Thái Phòng Thực Tế")
    
    rooms_df = fetch_rooms()
    bookings_df = fetch_bookings()
    
    # Chỉ số nhanh (KPIs)
    total_rooms = len(rooms_df)
    empty_rooms = len(rooms_df[rooms_df['status'] == 'Trống'])
    occupied_rooms = len(rooms_df[rooms_df['status'] == 'Đang có khách'])
    maintenance_rooms = len(rooms_df[rooms_df['status'] == 'Bảo trì'])
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tổng số phòng", total_rooms)
    col2.metric("Phòng trống", empty_rooms)
    col3.metric("Đang có khách", occupied_rooms)
    col4.metric("Bảo trì", maintenance_rooms)
    
    st.write("---")
    
    # Hiển thị dạng lưới (Grid View)
    grid_cols = st.columns(4)
    for idx, row in rooms_df.iterrows():
        col = grid_cols[idx % 4]
        status_color = "#28a745" if row['status'] == "Trống" else ("#dc3545" if row['status'] == "Đang có khách" else "#ffc107")
        
        with col:
            st.markdown(
                f"""
                <div style="
                    border: 2px solid {status_color};
                    border-radius: 10px;
                    padding: 15px;
                    margin-bottom: 15px;
                    background-color: rgba(255, 255, 255, 0.05);
                    text-align: center;">
                    <h3 style="margin:0; color:{status_color};">Phòng {row['room_number']}</h3>
                    <p style="margin:5px 0;"><b>Loại:</b> {row['room_type']}</p>
                    <p style="margin:5px 0;"><b>Giá:</b> {row['price_per_night']:,} VNĐ/đêm</p>
                    <span style="
                        background-color:{status_color}; 
                        color:white; 
                        padding:3px 10px; 
                        border-radius:12px; 
                        font-size: 12px;">{row['status']}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

# ---------------------------------------------------------
# 2. ĐẶT PHÒNG / CHECK-IN
# ---------------------------------------------------------
elif menu == "📝 Đặt Phòng / Check-in":
    st.subheader("📝 Nhận Phòng (Check-in)")
    
    rooms_df = fetch_rooms()
    available_rooms = rooms_df[rooms_df['status'] == 'Trống']
    
    if available_rooms.empty:
        st.warning("Hiện tại không có phòng nào trống!")
    else:
        with st.form("checkin_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                guest_name = st.text_input("Tên khách hàng *")
                phone = st.text_input("Số điện thoại *")
                selected_room = st.selectbox(
                    "Chọn phòng trống *",
                    available_rooms['room_number'].tolist(),
                    format_func=lambda x: f"Phòng {x} - {rooms_df[rooms_df['room_number']==x]['room_type'].values[0]} ({rooms_df[rooms_df['room_number']==x]['price_per_night'].values[0]:,} VNĐ)"
                )
            
            with col2:
                check_in = st.date_input("Ngày Check-in", value=date.today())
                check_out = st.date_input("Ngày Check-out dự kiến", value=date.today())
                
                # Tính số đêm
                num_nights = (check_out - check_in).days
                if num_nights <= 0:
                    num_nights = 1
                
                price_per_night = rooms_df[rooms_df['room_number'] == selected_room]['price_per_night'].values[0]
                total_price = num_nights * price_per_night
                
                st.info(f"Số đêm: **{num_nights} đêm** | Tổng tiền dự kiến: **{total_price:,} VNĐ**")
            
            submitted = st.form_submit_button("Xác Nhận Check-in 🚀")
            
            if submitted:
                if not guest_name or not phone:
                    st.error("Vui lòng điền đầy đủ thông tin khách hàng!")
                else:
                    create_booking(guest_name, phone, selected_room, check_in, check_out, total_price)
                    st.success(f"Check-in thành công phòng {selected_room} cho khách {guest_name}!")
                    st.rerun()

# ---------------------------------------------------------
# 3. CHECK-OUT & THANH TOÁN
# ---------------------------------------------------------
elif menu == "💳 Check-out & Thanh Toán":
    st.subheader("💳 Trả Phòng & Thanh Toán")
    
    bookings_df = fetch_bookings()
    active_bookings = bookings_df[bookings_df['status'] == 'Đã check-in']
    
    if active_bookings.empty:
        st.info("Hiện không có phòng nào đang sử dụng.")
    else:
        st.dataframe(
            active_bookings[['id', 'room_number', 'guest_name', 'phone', 'check_in_date', 'check_out_date', 'total_price']],
            use_container_width=True
        )
        
        st.divider()
        col1, col2 = st.columns([2, 1])
        
        with col1:
            booking_to_checkout = st.selectbox(
                "Chọn thông tin trả phòng:",
                active_bookings['id'].tolist(),
                format_func=lambda x: f"Mã Đặt: {x} | Phòng {active_bookings[active_bookings['id']==x]['room_number'].values[0]} | Khách: {active_bookings[active_bookings['id']==x]['guest_name'].values[0]}"
            )
        
        selected_info = active_bookings[active_bookings['id'] == booking_to_checkout].iloc[0]
        
        with col2:
            st.write("**Thông tin hóa đơn:**")
            st.write(f"- Khách: **{selected_info['guest_name']}**")
            st.write(f"- Số tiền cần thu: **{selected_info['total_price']:,} VNĐ**")
            
            if st.button("Xác Nhận Thanh Toán & Trả Phòng 🛑"):
                checkout_booking(booking_to_checkout, selected_info['room_number'])
                st.success(f"Đã thanh toán & hoàn tất trả phòng {selected_info['room_number']}!")
                st.rerun()

# ---------------------------------------------------------
# 4. QUẢN LÝ PHÒNG
# ---------------------------------------------------------
elif menu == "⚙️ Quản Lý Phòng":
    st.subheader("⚙️ Cấu Hình Danh Sách Phòng")
    
    tab1, tab2 = st.tabs(["Thêm Phòng Mới", "Trạng Thái & Sửa Phòng"])
    
    with tab1:
        with st.form("add_room_form"):
            room_num = st.text_input("Số phòng (VD: 103, 204)")
            room_type = st.selectbox("Loại phòng", ["Đơn Standard", "Đôi Deluxe", "VIP Suite", "Gia Đình"])
            price = st.number_input("Giá phòng theo đêm (VNĐ)", min_value=100000, step=50000, value=400000)
            
            if st.form_submit_button("Lưu Phòng Mới"):
                if room_num:
                    success, msg = add_room(room_num, room_type, price)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Vui lòng nhập số phòng!")
                    
    with tab2:
        rooms_df = fetch_rooms()
        st.dataframe(rooms_df, use_container_width=True)
        
        st.write("---")
        st.subheader("Cập nhật trạng thái bảo trì phòng")
        c1, c2, c3 = st.columns(3)
        with c1:
            r_num = st.selectbox("Chọn phòng", rooms_df['room_number'].tolist())
        with c2:
            new_status = st.selectbox("Trạng thái mới", ["Trống", "Bảo trì"])
        with c3:
            st.write("")
            st.write("")
            if st.button("Cập nhật"):
                update_room_status(r_num, new_status)
                st.success("Đã cập nhật trạng thái!")
                st.rerun()

# ---------------------------------------------------------
# 5. BÁO CÁO DOANH THU
# ---------------------------------------------------------
elif menu == "📈 Báo Cáo Doanh Thu":
    st.subheader("📈 Báo Cáo Doanh Thu Khách Sạn")
    
    bookings_df = fetch_bookings()
    completed_bookings = bookings_df[bookings_df['status'] == 'Đã check-out']
    
    if completed_bookings.empty:
        st.warning("Chưa có dữ liệu thanh toán hoàn tất.")
    else:
        total_revenue = completed_bookings['total_price'].sum()
        total_orders = len(completed_bookings)
        
        c1, c2 = st.columns(2)
        c1.metric("Tổng doanh thu", f"{total_revenue:,} VNĐ")
        c2.metric("Lượt phòng đã hoàn tất", f"{total_orders} lượt")
        
        st.divider()
        
        # Biểu đồ doanh thu theo phòng bằng Plotly
        rev_by_room = completed_bookings.groupby('room_number')['total_price'].sum().reset_index()
        fig = px.bar(
            rev_by_room,
            x='room_number',
            y='total_price',
            labels={'room_number': 'Số Phòng', 'total_price': 'Doanh Thu (VNĐ)'},
            title="Tổng Doanh Thu Theo Từng Phòng",
            color='total_price',
            color_continuous_scale='Greens'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Lịch sử giao dịch")
        st.dataframe(completed_bookings, use_container_width=True)
