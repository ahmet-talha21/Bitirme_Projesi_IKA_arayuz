import math
import unittest
from ika.model import Simulator, DEFAULT_ROUTE, OBSTACLES, validate_route, encode_route, decode_route


class RouteTests(unittest.TestCase):
    def test_route_round_trip(self):
        self.assertEqual(decode_route(encode_route(DEFAULT_ROUTE)), DEFAULT_ROUTE)

    def test_invalid_routes(self):
        for route in [[], [[1,1]], [[0,0],[float('nan'),2]], [[0,0],[21,1]], [[0,0],[True,1]], [[0,0],[0,0]]]:
            with self.subTest(route=route), self.assertRaises(ValueError):
                validate_route(route)

    def test_avoidance_and_rejoin_complete_without_collision(self):
        sim=Simulator(); sim.begin(DEFAULT_ROUTE); states=set()
        for _ in range(3000):
            sim.tick(.05,.8); states.add(sim.state)
            self.assertTrue(all(math.hypot(sim.x-x,sim.y-y)>=r+.3 for x,y,r in OBSTACLES))
            if not sim.running: break
        self.assertEqual(sim.state,'Rota tamamlandı')
        self.assertIn('Engelden kaçılıyor',states)
        self.assertIn('Rotaya dönülüyor',states)
        self.assertLess(math.dist((sim.x,sim.y),DEFAULT_ROUTE[-1]),.12)

    def test_stop_prevents_resume(self):
        sim=Simulator(); sim.begin(DEFAULT_ROUTE); sim.tick(.05,.8); sim.stop()
        point=sim.x,sim.y
        for _ in range(20): sim.tick(.05,.8)
        self.assertEqual(point,(sim.x,sim.y))
        self.assertEqual(sim.speed,0)

    def test_manual_collision_stops(self):
        sim=Simulator(); sim.x,sim.y,sim.yaw=7.,4.5,0.
        for _ in range(100): sim.tick(.05,1.,(1.,0.))
        self.assertLess(sim.x,9-.85-.3)
        self.assertEqual(sim.speed,0)
