# project/gui/gui_utils.py

def center_window(window):
    """
    จัดตำแหน่งหน้าต่างให้อยู่กึ่งกลางของหน้าจอ
    """
    frameGm = window.frameGeometry()
    screen_center = window.screen().availableGeometry().center()
    frameGm.moveCenter(screen_center)
    window.move(frameGm.topLeft())
