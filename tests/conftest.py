import sys
import os

# เพิ่มโปรเจกต์ root (โฟลเดอร์ที่มี core อยู่) เข้าไปใน sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
