import json
import os
import time
import unittest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtCore import Qt, QPoint, QUrl
from PySide6.QtNetwork import QHostAddress
from PySide6.QtTest import QTest
from PySide6.QtWebSockets import QWebSocketServer
from PySide6.QtWidgets import QApplication
from ika.app import MainWindow,STYLE

app=QApplication.instance() or QApplication([])
app.setStyleSheet(STYLE)


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.window=MainWindow(); self.window.show(); QTest.qWait(70)

    def tearDown(self):
        self.window.close(); self.window.deleteLater(); app.processEvents()

    def test_draw_route_and_start_stop(self):
        w=self.window
        w.clear_route(); w.toggle_edit()
        for p in [(2,2),(6,2),(7,6)]:
            screen=w.canvas.screen(*p)
            QTest.mouseClick(w.canvas,Qt.MouseButton.LeftButton,pos=QPoint(round(screen.x()),round(screen.y())))
        self.assertEqual(len(w.canvas.route),3)
        w.toggle_edit(); w.mode.setCurrentIndex(1)
        QTest.mouseClick(w.start_btn,Qt.MouseButton.LeftButton)
        self.assertTrue(w.sim.running)
        self.assertFalse(w.edit_btn.isEnabled())
        QTest.mouseClick(w.stop_btn,Qt.MouseButton.LeftButton)
        self.assertFalse(w.sim.running)
        self.assertEqual(w.sim.speed,0)
        self.assertTrue(w.edit_btn.isEnabled())

    def test_manual_key_release(self):
        w=self.window; w.setFocus()
        QTest.keyPress(w,Qt.Key.Key_W); self.assertEqual(w.manual[0],1.)
        QTest.qWait(100)
        QTest.keyRelease(w,Qt.Key.Key_W); self.assertEqual(w.manual,[0.,0.])

    def test_websocket_telemetry_stop_and_staleness(self):
        server=QWebSocketServer('test',QWebSocketServer.SslMode.NonSecureMode)
        self.assertTrue(server.listen(QHostAddress.SpecialAddress.LocalHost,0))
        w=self.window
        w.source.setCurrentIndex(1)
        self.assertFalse(w.start_btn.isEnabled())
        w.endpoint.setText(f'ws://127.0.0.1:{server.serverPort()}'); w.connect_vehicle()
        for _ in range(30):
            QTest.qWait(10)
            if server.hasPendingConnections(): break
        peer=server.nextPendingConnection(); self.assertIsNotNone(peer)
        payload={'type':'telemetry','x_m':3.,'y_m':4.,'yaw_rad':.5,'speed_mps':.4,'front_m':1.3,'mode':'autonomous','state':'Rota takibi'}
        peer.sendTextMessage(json.dumps(payload)); QTest.qWait(100)
        self.assertEqual(w.metrics['front'].text(),'1.30 m')
        self.assertIn('OTONOM',w.mode_label.text())
        commands=[]; peer.textMessageReceived.connect(commands.append)
        w.stop(); QTest.qWait(50)
        self.assertEqual(json.loads(commands[-1]),{'type':'command','command':'stop'})
        w.last_rx=time.monotonic()-2; w.tick()
        self.assertEqual(w.metrics['speed'].text(),'—')
        self.assertIn('BİLİNMİYOR',w.mode_label.text())
        previous=w.last_data
        payload['x_m']=float('nan'); w.receive(json.dumps(payload))
        self.assertIs(w.last_data,previous)
        peer.close(); server.close(); QTest.qWait(30)
        self.assertIsNone(w.last_data)
