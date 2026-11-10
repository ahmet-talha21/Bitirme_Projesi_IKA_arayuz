"""Windows uyumlu PySide6 masaüstü arayüzü. python -m ika.app"""
import json
import math
import sys
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QPointF, QRectF, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QPolygonF, QRadialGradient
from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
    QSlider, QScrollArea, QTextEdit, QVBoxLayout, QWidget)
from PySide6.QtWebSockets import QWebSocket

from .model import Simulator, DEFAULT_ROUTE, OBSTACLES, WIDTH, HEIGHT, encode_route, decode_route, validate_route

STYLE = '''
QMainWindow, QWidget { background: #0b1020; color: #e6edff; font-family: 'Segoe UI', 'DejaVu Sans'; font-size: 12px; }
QFrame#header { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1f2e61, stop:0.5 #202649, stop:1 #34225b); border: 1px solid #45548a; border-radius: 14px; }
QFrame#header QLabel { background: transparent; }
QFrame#panel { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #17233c, stop:1 #111b30); border: 1px solid #2d3d60; border-radius: 12px; }
QFrame#panel QLabel { background: transparent; }
QSlider { background: transparent; }
QLabel#muted { color: #a0b2d2; font-size: 11px; }
QLabel#title { font-size: 25px; font-weight: 700; color: #f4f7ff; }
QLabel#section { font-size: 13px; font-weight: 700; color: #b9caff; }
QLabel#metric { font-size: 25px; font-weight: 700; color: #50e1cb; }
QPushButton { background: #223456; border: 1px solid #435d8a; border-radius: 7px; padding: 9px 11px; font-weight: 600; }
QPushButton:hover { background: #304a77; border-color: #8bafff; color: #ffffff; }
QPushButton:pressed { background: #3b58a0; border-color: #b9ccff; }
QPushButton:disabled { color: #8090ad; border-color: #30415f; background: #1a263e; }
QPushButton#primary { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #20cdb4,stop:1 #4c9bff); color: #061d32; border: 1px solid #67dfed; }
QPushButton#primary:hover { background: #77e9df; }
QPushButton#primary:disabled { background: #24465a; color: #99b3c6; border-color: #36556a; }
QPushButton#stop { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #922f50,stop:1 #612443); color: #fff0f4; border: 1px solid #f57293; font-size: 14px; padding: 14px; }
QPushButton#stop:hover { background: #b43659; border-color: #ffb0c6; }
QPushButton#draw { background: #3b326a; border-color: #9078dc; color: #e4d9ff; }
QPushButton#draw:hover { background: #59448d; }
QPushButton#draw:disabled { background: #262b49; color: #9394b0; border-color: #424765; }
QPushButton#drive { background: #1e3554; color: #85d9ff; font-size: 20px; border-color: #3e638b; }
QPushButton#drive:pressed { background: #267b92; color: #ffffff; }
QPushButton#drive:disabled { background: #1b273d; color: #778ba7; border-color: #33445f; }
QComboBox, QLineEdit { background: #0d192e; border: 1px solid #41577e; border-radius: 6px; padding: 8px; selection-background-color: #3e63ab; }
QComboBox:hover, QLineEdit:focus { border-color: #8caeff; }
QComboBox QAbstractItemView { background: #192844; color: #eef3ff; selection-background-color: #3e5390; }
QTextEdit { background: #0e182b; border: 1px solid #263858; border-radius: 6px; color: #b3c5e7; font-family: Consolas, monospace; font-size: 11px; }
QSlider::groove:horizontal { height: 6px; background: #30425f; border-radius: 3px; }
QSlider::sub-page:horizontal { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #7b83ff,stop:1 #46d9d0); border-radius: 3px; }
QSlider::handle:horizontal { background: #b1fcf1; border: 2px solid #39cdbd; width: 14px; margin: -5px 0; border-radius: 8px; }
'''


def label(text, name=None):
    obj = QLabel(text)
    if name:
        obj.setObjectName(name)
    obj.setWordWrap(True)
    return obj


def button(text, callback=None, name=None):
    obj = QPushButton(text)
    if callback:
        obj.clicked.connect(callback)
    if name:
        obj.setObjectName(name)
    obj.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    return obj


def panel(title):
    box = QFrame()
    box.setObjectName('panel')
    layout = QVBoxLayout(box)
    layout.setContentsMargins(16,16,16,16)
    layout.setSpacing(12)
    layout.addWidget(label(title, 'section'))
    return box, layout


class MapCanvas(QWidget):
    changed = Signal()

    def __init__(self, simulator):
        super().__init__()
        self.sim = simulator
        self.route = list(DEFAULT_ROUTE)
        self.editing = False
        self.simulation = True
        self.trace = []
        self.setMinimumSize(510, 390)
        self.setMouseTracking(True)

    def area(self):
        scale = min((self.width()-70)/WIDTH, (self.height()-70)/HEIGHT)
        return scale, (self.width()-WIDTH*scale)/2, (self.height()-HEIGHT*scale)/2

    def screen(self, x, y):
        s,ox,oy = self.area()
        return QPointF(ox+x*s, oy+(HEIGHT-y)*s)

    def mousePressEvent(self, event):
        if not self.editing:
            return
        if event.button() == Qt.MouseButton.RightButton:
            if self.route:
                self.route.pop()
        elif event.button() == Qt.MouseButton.LeftButton:
            s,ox,oy = self.area()
            x,y = (event.position().x()-ox)/s, HEIGHT-(event.position().y()-oy)/s
            if not (0 <= x <= WIDTH and 0 <= y <= HEIGHT) or len(self.route)>=200:
                return
            if not self.route or math.dist(self.route[-1],(x,y))>=.15:
                self.route.append((round(x,2),round(y,2)))
        self.changed.emit()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s,ox,oy = self.area()
        rect = QRectF(ox,oy,WIDTH*s,HEIGHT*s)
        field = QLinearGradient(rect.topLeft(), rect.bottomRight())
        field.setColorAt(0, QColor('#142b45'))
        field.setColorAt(1, QColor('#191b35'))
        p.fillRect(rect, field)
        p.setPen(QPen(QColor('#2a3d5b'),1))
        for x in range(21):
            p.drawLine(self.screen(x,0),self.screen(x,HEIGHT))
        for y in range(15):
            p.drawLine(self.screen(0,y),self.screen(WIDTH,y))
        p.setPen(QPen(QColor('#4c6895'), 1.3))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect, 5, 5)
        p.setPen(QColor('#96accf'))
        p.setFont(QFont('Segoe UI',9))
        for x in range(0,21,5):
            a = self.screen(x,0)
            p.drawText(QPointF(a.x()-8,a.y()+20),f'{x} m')
        for y in range(0,15,2):
            a = self.screen(0,y)
            p.drawText(QPointF(a.x()-35,a.y()+4),str(y))
        if self.simulation:
            for x,y,r in OBSTACLES:
                p.setPen(QPen(QColor('#edb76d'),1,Qt.PenStyle.DashLine))
                p.setBrush(QColor(255,177,76,24))
                p.drawEllipse(self.screen(x,y),(r+.4)*s,(r+.4)*s)
                p.setPen(QPen(QColor('#ffc077'),1.5))
                p.setBrush(QColor('#87562f'))
                p.drawEllipse(self.screen(x,y),r*s,r*s)
        if len(self.trace)>1:
            p.setPen(QPen(QColor('#63a9ff'),2.5))
            p.drawPolyline(QPolygonF([self.screen(*a) for a in self.trace]))
        if len(self.route)>1:
            route_shape = QPolygonF([self.screen(*a) for a in self.route])
            p.setPen(QPen(QColor(63, 231, 208, 25), 10))
            p.drawPolyline(route_shape)
            p.setPen(QPen(QColor('#48ead0'),2.5,Qt.PenStyle.DashLine))
            p.drawPolyline(route_shape)
        for i, point in enumerate(self.route):
            a = self.screen(*point)
            p.setBrush(QColor('#176862') if i else QColor('#6051ba'))
            p.setPen(QPen(QColor('#68e1c7'),2))
            p.drawEllipse(a,11,11)
            p.setPen(QColor('#e1fff9'))
            p.drawText(QRectF(a.x()-11,a.y()-11,22,22),Qt.AlignmentFlag.AlignCenter,str(i+1))
        if self.sim.detour and self.simulation:
            p.setPen(QPen(QColor('#f3b967'),2,Qt.PenStyle.DotLine))
            p.drawPolyline(QPolygonF([self.screen(self.sim.x,self.sim.y)]+[self.screen(*a) for a in self.sim.detour]))
        a = self.screen(self.sim.x,self.sim.y)
        p.save()
        p.translate(a)
        p.rotate(-math.degrees(self.sim.yaw))
        halo = QRadialGradient(QPointF(), 35)
        halo.setColorAt(0, QColor(64, 241, 208, 100))
        halo.setColorAt(1, QColor(64, 241, 208, 0))
        p.setBrush(halo)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(),35,35)
        # Simülasyonda ön sensörün ölçüm ışını.
        if self.simulation:
            p.setPen(QPen(QColor(113,219,255,150),1.5,Qt.PenStyle.DotLine))
            p.drawLine(QPointF(20,0),QPointF(max(20,self.sim.front*s),0))
        p.setBrush(QColor('#effffb'))
        p.setPen(QPen(QColor('#63d8c0'),2))
        p.drawPolygon(QPolygonF([QPointF(17,0),QPointF(-11,-10),QPointF(-6,0),QPointF(-11,10)]))
        p.restore()
        p.setPen(QColor('#7e98af'))
        p.drawText(QPointF(ox+12,oy+22),'Y ↑     YEREL KOORDİNAT     X →')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('İKA • Yer Kontrol İstasyonu')
        self.resize(1440, 900)
        self.setMinimumSize(1200,780)
        self.sim = Simulator()
        self.manual = [0.,0.]
        self.keys = set()
        self.last_data = None
        self.last_state = ''
        self.socket = QWebSocket()
        self.socket.connected.connect(self.on_connected)
        self.socket.disconnected.connect(self.on_disconnected)
        self.socket.textMessageReceived.connect(self.receive)
        self.socket.errorOccurred.connect(lambda _: self.log('Bağlantı hatası: '+self.socket.errorString()))
        self.build_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(50)
        self.last_tick = time.monotonic()
        self.log('İstasyon hazır. Simülasyon verileri kullanılıyor.')
        self.route_changed()
        self.update_ui()

    @property
    def is_sim(self):
        return self.source.currentIndex()==0

    def build_ui(self):
        root = QWidget()
        root.setMinimumSize(1200, 900)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(root)
        self.setCentralWidget(scroll)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(24,20,24,18)
        outer.setSpacing(16)
        header_box = QFrame()
        header_box.setObjectName('header')
        header = QHBoxLayout(header_box)
        header.setContentsMargins(20, 14, 20, 14)
        branding = QVBoxLayout()
        brand_title = label('İKA  /  YER KONTROL', 'title')
        brand_title.setMinimumWidth(560)
        branding.addWidget(brand_title)
        branding.addWidget(label('İnsansız kara aracı   •   Görev ve sürüş istasyonu', 'muted'))
        header.addLayout(branding)
        header.addStretch()
        self.badge = label('●  SİMÜLASYON', 'section')
        self.badge.setFixedHeight(44)
        self.badge.setStyleSheet('color: #ddceff; padding: 12px; background: #433269; border: 1px solid #9b7ad9; border-radius: 8px;')
        header.addWidget(self.badge)
        outer.addWidget(header_box)
        columns = QHBoxLayout()
        columns.setSpacing(16)
        left = QVBoxLayout()
        box, layout = panel('01  BAĞLANTI')
        box.setFixedWidth(245)
        self.source = QComboBox()
        self.source.addItems(['Simülasyon', 'ESP32 / Wi-Fi'])
        self.source.currentIndexChanged.connect(self.source_changed)
        layout.addWidget(self.source)
        self.endpoint = QLineEdit('ws://192.168.4.1:81')
        self.endpoint.setPlaceholderText('ws://ESP32-IP:port')
        self.endpoint.setEnabled(False)
        layout.addWidget(self.endpoint)
        self.connect_btn = button('Araca bağlan',self.connect_vehicle)
        self.connect_btn.setEnabled(False)
        layout.addWidget(self.connect_btn)
        self.connection_info = label('Yerel demo • donanım gerektirmez','muted')
        layout.addWidget(self.connection_info)
        left.addWidget(box)
        box, layout = panel('02  SÜRÜŞ KONTROLÜ')
        self.mode = QComboBox()
        self.mode.addItems(['Manuel', 'Otonom'])
        self.mode.currentIndexChanged.connect(self.mode_changed)
        layout.addWidget(self.mode)
        self.speed_label = label('Hız sınırı   0.8 m/s','section')
        layout.addWidget(self.speed_label)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(2,15)
        self.slider.setValue(8)
        self.slider.valueChanged.connect(lambda v:self.speed_label.setText(f'Hız sınırı   {v/10:.1f} m/s'))
        layout.addWidget(self.slider)
        pad = QGridLayout()
        self.drive_buttons = []
        for text,row,col,axis,value in [('↑',0,1,0,1.),('←',1,0,1,1.),('↓',1,1,0,-1.),('→',1,2,1,-1.)]:
            b = button(text, name='drive')
            b.setMinimumHeight(42)
            b.pressed.connect(lambda a=axis,v=value:self.set_manual(a,v))
            b.released.connect(lambda a=axis:self.set_manual(a,0.))
            pad.addWidget(b,row,col)
            self.drive_buttons.append(b)
        layout.addLayout(pad)
        layout.addWidget(label('Basılı tutarak sürün. W A S D / ok tuşları\nBoşluk: durdur', 'muted'))
        self.start_btn = button('▶  Rotayı başlat',self.start_route,'primary')
        layout.addWidget(self.start_btn)
        self.stop_btn = button('■  DURDUR', self.stop, 'stop')
        layout.addWidget(self.stop_btn)
        layout.addWidget(label('Yazılım durdurmasıdır; fiziksel acil durdurma yerine geçmez.','muted'))
        left.addWidget(box)
        left.addStretch()
        columns.addLayout(left)
        center = QVBoxLayout()
        box, layout = panel('ROTA PLANLAYICI')
        toolbar = QHBoxLayout()
        self.edit_btn = button('✎  Rota çiz',self.toggle_edit,'draw')
        self.undo_btn = button('Geri al',self.undo)
        self.clear_btn = button('Temizle',self.clear_route)
        self.demo_btn = button('Örnek',self.demo_route)
        for b in (self.edit_btn,self.undo_btn,self.clear_btn,self.demo_btn):
            toolbar.addWidget(b)
        toolbar.addStretch()
        toolbar.addWidget(button('Aç',self.load_route))
        toolbar.addWidget(button('Kaydet',self.save_route))
        layout.addLayout(toolbar)
        self.canvas = MapCanvas(self.sim)
        self.canvas.changed.connect(self.route_changed)
        layout.addWidget(self.canvas,1)
        self.route_info = label('', 'muted')
        layout.addWidget(self.route_info)
        layout.addWidget(label('Sol tık: nokta ekle   •   Sağ tık: son noktayı kaldır   •   Alan: 20 × 14 metre', 'muted'))
        center.addWidget(box,1)
        log_box, log_layout = panel('OLAY KAYDI')
        self.events = QTextEdit()
        self.events.setReadOnly(True)
        self.events.document().setMaximumBlockCount(300)
        self.events.setFixedHeight(90)
        log_layout.addWidget(self.events)
        center.addWidget(log_box)
        columns.addLayout(center,1)
        right = QVBoxLayout()
        box, layout = panel('ARAÇ DURUMU')
        box.setFixedWidth(240)
        self.state_label = label('Hazır','section')
        self.state_label.setStyleSheet('color: #79f1d4; background: #163d3e; border: 1px solid #2a7169; border-radius: 7px; padding: 10px;')
        layout.addWidget(self.state_label)
        self.mode_label = label('MANUEL','muted')
        layout.addWidget(self.mode_label)
        self.metrics = {}
        metric_colors = {'speed': '#55e8ce', 'front': '#ffc578', 'position': '#8dc5ff', 'heading': '#c4a5ff', 'progress': '#71e4f0'}
        for key,title in [('speed','ANLIK HIZ'),('front','ÖN MESAFE SENSÖRÜ'),('position','KONUM · ENKODER + IMU'),('heading','YÖNELİM'),('progress','ROTA İLERLEMESİ')]:
            card = QFrame()
            color = metric_colors[key]
            card.setStyleSheet(f'QFrame {{ background: #162840; border: none; border-left: 3px solid {color}; border-radius: 5px; }} QLabel {{ border: none; background: transparent; }}')
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(11, 7, 8, 7)
            card_layout.setSpacing(3)
            card_layout.addWidget(label(title,'muted'))
            self.metrics[key] = label('—','metric')
            size = 19 if key=='position' else 24
            self.metrics[key].setStyleSheet(f'font-size: {size}px; color: {color}; font-weight: 700;')
            card_layout.addWidget(self.metrics[key])
            layout.addWidget(card)
        self.age_label = label('Veri kaynağı: simülasyon','muted')
        layout.addWidget(self.age_label)
        right.addWidget(box)
        box, layout = panel('GÖREV NOTLARI')
        layout.addWidget(label('• Turkuaz: planlanan rota\n• Mavi: aracın geçtiği iz\n• Sarı: kaçınma yolu\n• Turuncu: demo engeller','muted'))
        layout.addWidget(label('Başlangıç: (0, 0) yerel referans. Gerçek araçta enkoder + IMU konumu aynı referansa göre üretilmeli.','muted'))
        self.reset_btn = button('Simülasyonu sıfırla',self.reset)
        layout.addWidget(self.reset_btn)
        right.addWidget(box)
        right.addStretch()
        columns.addLayout(right)
        outer.addLayout(columns,1)
        self.footer = label('SİMÜLASYON  /  Engel kaçınması demo modelidir. Gerçek ESP32 algoritması ayrıca geliştirilecektir.','muted')
        outer.addWidget(self.footer)

    def log(self, message):
        self.events.append(f'{datetime.now():%H:%M:%S}   {message}')

    def set_manual(self, axis, value):
        if self.is_sim and self.mode.currentIndex()==0:
            self.manual[axis] = value

    def mode_changed(self):
        self.stop()
        self.log('Mod: '+self.mode.currentText())
        self.update_ui()

    def source_changed(self):
        self.stop()
        self.socket.abort()
        self.last_data = None
        self.sim.reset()
        self.canvas.trace.clear()
        self.canvas.simulation = self.is_sim
        self.canvas.editing = False
        self.edit_btn.setText('✎  Rota çiz')
        self.endpoint.setEnabled(not self.is_sim)
        self.connect_btn.setEnabled(not self.is_sim)
        self.badge.setText('●  SİMÜLASYON' if self.is_sim else '○  ESP32 / BAĞLANTI YOK')
        self.footer.setText('SİMÜLASYON  /  Engel kaçınması demo modelidir.' if self.is_sim else 'ESP32 / İlk sürüm: telemetri izleme + durdurma isteği. Gerçek hareket kontrolü henüz etkin değil.')
        self.log('Kaynak: '+self.source.currentText())
        self.update_ui()

    def connect_vehicle(self):
        if self.socket.isValid():
            self.socket.close()
            return
        url = QUrl(self.endpoint.text().strip())
        if url.scheme() not in ('ws','wss') or not url.host() or url.userInfo():
            self.error('Geçerli bir ws:// veya wss:// adresi girin; kimlik bilgisi eklemeyin.')
            return
        self.socket.abort()
        self.connection_info.setText('Bağlanılıyor…')
        self.socket.open(url)

    def on_connected(self):
        self.badge.setText('●  ESP32 / VERİ BEKLENİYOR')
        self.connect_btn.setText('Bağlantıyı kes')
        self.log('WebSocket açıldı. Geçerli telemetri bekleniyor.')

    def on_disconnected(self):
        self.manual = [0.,0.]
        self.last_data = None
        self.connect_btn.setText('Araca bağlan')
        if not self.is_sim:
            self.badge.setText('○  ESP32 / BAĞLANTI YOK')
            self.connection_info.setText('Bağlantı kapalı')
            self.log('Araç bağlantısı kapandı. Son konum güncel değildir.')

    def receive(self, raw):
        if self.is_sim:
            return
        try:
            if len(raw)>16384:
                raise ValueError('Mesaj çok büyük')
            d = json.loads(raw)
            if not isinstance(d,dict):
                raise ValueError('Nesne bekleniyor')
            if d.get('type')=='ack':
                self.log('Araç yanıtı: '+str(d.get('command','?'))+' / '+str(d.get('status','?')))
                return
            if d.get('type')!='telemetry':
                raise ValueError('Telemetri mesajı bekleniyor')
            for key in ('x_m','y_m','yaw_rad','speed_mps','front_m'):
                v = d[key]
                if isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v):
                    raise ValueError('Geçersiz ölçüm: '+key)
            if not (0<=d['x_m']<=WIDTH and 0<=d['y_m']<=HEIGHT and 0<=d['front_m']<=100 and abs(d['speed_mps'])<=20):
                raise ValueError('Ölçüm izin verilen aralığın dışında')
            if d.get('mode') not in ('manual','autonomous') or not isinstance(d.get('state'),str):
                raise ValueError('Mod veya durum eksik')
            self.last_data = d
            self.last_rx = time.monotonic()
        except (ValueError,KeyError,TypeError) as exc:
            self.log('Telemetri reddedildi: '+str(exc))

    def stop(self):
        self.manual = [0.,0.]
        self.keys.clear()
        self.sim.stop()
        if not self.is_sim and self.socket.isValid():
            self.socket.sendTextMessage(json.dumps({'type':'command','command':'stop'}))
            self.log('Durdurma isteği gönderildi; aracın durduğu henüz doğrulanmadı.')
        elif self.is_sim:
            self.log('Simülasyon durduruldu.')
        self.update_ui()

    def start_route(self):
        if not self.is_sim or self.mode.currentIndex()!=1:
            return
        try:
            self.sim.begin(self.canvas.route)
        except ValueError as exc:
            self.error(str(exc))
            return
        self.manual = [0.,0.]
        self.canvas.editing = False
        self.edit_btn.setText('✎  Rota çiz')
        self.log('Otonom simülasyon başladı.')
        self.update_ui()

    def route_changed(self):
        route = self.canvas.route
        length = sum(math.dist(a,b) for a,b in zip(route,route[1:]))
        self.route_info.setText(f'{len(route):02d} YOL NOKTASI     /     {length:.1f} m PLANLANAN UZUNLUK     /     '+('ÇİZİM AÇIK' if self.canvas.editing else 'GÖRÜNTÜLEME'))
        self.canvas.update()
        self.update_ui()

    def toggle_edit(self):
        if self.sim.running:
            return
        self.manual = [0.,0.]
        self.canvas.editing = not self.canvas.editing
        self.edit_btn.setText('✓  Çizimi bitir' if self.canvas.editing else '✎  Rota çiz')
        self.route_changed()

    def undo(self):
        if not self.sim.running and self.canvas.route:
            self.canvas.route.pop()
            self.route_changed()

    def clear_route(self):
        if not self.sim.running:
            self.canvas.route.clear()
            self.route_changed()

    def demo_route(self):
        if not self.sim.running:
            self.canvas.route = list(DEFAULT_ROUTE)
            self.route_changed()

    def save_route(self):
        self.manual = [0.,0.]
        self.keys.clear()
        try:
            text = encode_route(self.canvas.route)
            filename,_ = QFileDialog.getSaveFileName(self,'Rotayı kaydet','rota.json','JSON (*.json)')
            if filename:
                Path(filename).write_text(text,encoding='utf-8')
                self.log('Rota dosyaya kaydedildi.')
        except (ValueError,OSError) as exc:
            self.error(str(exc))

    def load_route(self):
        self.manual = [0.,0.]
        self.keys.clear()
        if self.sim.running:
            self.error('Rota yüklemeden önce görevi durdurun.')
            return
        filename,_ = QFileDialog.getOpenFileName(self,'Rota aç','','JSON (*.json)')
        if filename:
            try:
                if Path(filename).stat().st_size>65536:
                    raise ValueError('Rota dosyası çok büyük.')
                self.canvas.route = decode_route(Path(filename).read_text(encoding='utf-8'))
                self.route_changed()
                self.log('Rota yüklendi.')
            except (ValueError,OSError) as exc:
                self.error(str(exc))

    def reset(self):
        if self.is_sim:
            self.stop()
            self.sim.reset()
            self.canvas.trace.clear()
            self.log('Simülasyon başlangıç konumuna alındı.')

    def error(self, message):
        self.log(message)
        QMessageBox.warning(self,'İKA',message)

    def tick(self):
        now = time.monotonic()
        dt = min(now-self.last_tick,.1)
        self.last_tick = now
        if self.is_sim:
            self.sim.tick(dt,self.slider.value()/10,self.manual if not self.canvas.editing else (0.,0.))
            state = self.sim.state
            self.metrics['speed'].setText(f'{abs(self.sim.speed):.2f} m/s')
            self.metrics['front'].setText(f'{self.sim.front:.2f} m')
            self.metrics['position'].setText(f'{self.sim.x:.2f}, {self.sim.y:.2f} m')
            self.metrics['heading'].setText(f'{math.degrees(self.sim.yaw)%360:.0f}°')
            self.metrics['progress'].setText(f'{min(self.sim.index,len(self.sim.route))} / {len(self.sim.route)}' if self.mode.currentIndex()==1 else '—')
            self.mode_label.setText(self.mode.currentText().upper()+' · SİMÜLASYON')
            self.age_label.setText('Canlı demo · 20 Hz\nÖn sensör menzili: 4 m (demo)')
        else:
            fresh = self.last_data is not None and now-self.last_rx<1.
            state = 'Veri bekleniyor / güncel değil'
            if fresh:
                d = self.last_data
                self.sim.x,self.sim.y,self.sim.yaw = d['x_m'],d['y_m'],d['yaw_rad']
                for k,text in [('speed',f"{d['speed_mps']:.2f} m/s"),('front',f"{d['front_m']:.2f} m"),('position',f"{d['x_m']:.2f}, {d['y_m']:.2f} m"),('heading',f"{math.degrees(d['yaw_rad'])%360:.0f}°"),('progress','—')]:
                    self.metrics[k].setText(text)
                self.mode_label.setText('ARAÇ MODU: '+('MANUEL' if d['mode']=='manual' else 'OTONOM'))
                state = self.last_data['state'][:100]
                self.badge.setText('●  ESP32 / TELEMETRİ AKTİF')
            else:
                for value in self.metrics.values():
                    value.setText('—')
                self.mode_label.setText('ARAÇ MODU: BİLİNMİYOR')
                if self.socket.isValid():
                    self.badge.setText('○  ESP32 / VERİ GÜNCEL DEĞİL')
            self.age_label.setText(f'Son veri: {now-self.last_rx:.1f} sn önce' if self.last_data else 'Henüz geçerli telemetri yok')
            self.connection_info.setText('WebSocket açık' if self.socket.isValid() else 'Bağlantı kapalı')
        self.state_label.setText(state)
        if self.is_sim:
            badge_colors = ('#ddceff', '#433269', '#9b7ad9')
        elif self.last_data is not None and now-self.last_rx<1.:
            badge_colors = ('#83f5dd', '#153d3e', '#328878')
        else:
            badge_colors = ('#ffd6a0', '#4b3431', '#ae7949')
        fg, bg, border = badge_colors
        self.badge.setStyleSheet(f'color: {fg}; background: {bg}; border: 1px solid {border}; border-radius: 8px; padding: 12px;')
        if 'kaçıl' in state or 'güncel değil' in state or 'Güvenli geçiş yok' in state:
            self.state_label.setStyleSheet('color: #ffda9d; background: #453528; border: 1px solid #a67c40; border-radius: 7px; padding: 10px;')
        else:
            self.state_label.setStyleSheet('color: #79f1d4; background: #163d3e; border: 1px solid #2a7169; border-radius: 7px; padding: 10px;')
        if state!=self.last_state:
            self.log(state)
            self.last_state = state
        if self.is_sim or (self.last_data is not None and now-self.last_rx<1.):
            point = self.sim.x,self.sim.y
            if not self.canvas.trace or math.dist(self.canvas.trace[-1],point)>.04:
                self.canvas.trace.append(point)
                self.canvas.trace = self.canvas.trace[-4000:]
        self.canvas.update()
        self.update_ui()

    def update_ui(self):
        if not hasattr(self,'start_btn'):
            return
        editable = not self.sim.running
        for b in (self.edit_btn,self.undo_btn,self.clear_btn,self.demo_btn):
            b.setEnabled(editable)
        self.start_btn.setEnabled(self.is_sim and self.mode.currentIndex()==1 and editable and len(self.canvas.route)>=2)
        for b in self.drive_buttons:
            b.setEnabled(self.is_sim and self.mode.currentIndex()==0 and not self.canvas.editing)
        self.mode.setEnabled(self.is_sim)
        self.reset_btn.setEnabled(self.is_sim)
        self.slider.setEnabled(self.is_sim)

    def keyPressEvent(self, event):
        if event.key()==Qt.Key.Key_Space and not isinstance(QApplication.focusWidget(),QLineEdit):
            self.stop()
            return
        if not event.isAutoRepeat() and self.is_sim and self.mode.currentIndex()==0 and not self.canvas.editing and not isinstance(QApplication.focusWidget(),QLineEdit):
            self.keys.add(event.key())
            self.key_motion()
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if not event.isAutoRepeat():
            self.keys.discard(event.key())
            self.key_motion()
        super().keyReleaseEvent(event)

    def key_motion(self):
        if not self.is_sim or self.mode.currentIndex()!=0:
            return
        k = self.keys
        self.manual = [float(bool(k & {Qt.Key.Key_W,Qt.Key.Key_Up}))-float(bool(k & {Qt.Key.Key_S,Qt.Key.Key_Down})),float(bool(k & {Qt.Key.Key_A,Qt.Key.Key_Left}))-float(bool(k & {Qt.Key.Key_D,Qt.Key.Key_Right}))]

    def changeEvent(self,event):
        from PySide6.QtCore import QEvent
        if event.type()==QEvent.Type.ActivationChange and not self.isActiveWindow():
            self.manual = [0.,0.]
            self.keys.clear()
        super().changeEvent(event)

    def closeEvent(self,event):
        self.stop()
        self.socket.close()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__=='__main__':
    main()
