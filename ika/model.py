"""Metre/radyan kullanan, donanımdan bağımsız simülasyon ve rota modeli."""
import json
import math

WIDTH, HEIGHT = 20.0, 14.0
DEFAULT_ROUTE = [(2., 3.), (7., 3.), (11., 6.), (16., 6.), (17., 11.)]
OBSTACLES = [(9., 4.5, .85), (14., 9., 1.1), (5., 10., .7)]


def validate_route(points):
    if not isinstance(points, list) or not 2 <= len(points) <= 200:
        raise ValueError('Rota 2 ile 200 arasında nokta içermeli.')
    result = []
    for p in points:
        if not isinstance(p, (list, tuple)) or len(p) != 2:
            raise ValueError('Her nokta bir x, y çifti olmalı.')
        if any(isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v) for v in p):
            raise ValueError('Koordinatlar sonlu sayılar olmalı.')
        x, y = map(float, p)
        if not (0 <= x <= WIDTH and 0 <= y <= HEIGHT):
            raise ValueError('Noktalar 20 × 14 m çalışma alanında olmalı.')
        if result and math.dist(result[-1], (x, y)) < .15:
            raise ValueError('Ardışık noktalar arasında en az 15 cm olmalı.')
        result.append((x, y))
    return result


def encode_route(points):
    return json.dumps({'version': 1, 'frame': 'local_m', 'points': validate_route(points)}, ensure_ascii=False, indent=2)


def decode_route(raw):
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get('version') != 1 or data.get('frame') != 'local_m':
        raise ValueError('Desteklenmeyen rota dosyası.')
    return validate_route(data.get('points'))


class Simulator:
    """Dairesel engelleri bilen DEMO modeli; gerçek mesafe sensörü algoritması değildir."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.x, self.y, self.yaw = 2., 3., 0.
        self.speed = 0.
        self.running = False
        self.route = list(DEFAULT_ROUTE)
        self.index = 0
        self.detour = []
        self.state = 'Hazır'
        self.distance = 0.

    @property
    def front(self):
        best = 4.
        for step in range(1, 81):
            d = step * .05
            x, y = self.x + d * math.cos(self.yaw), self.y + d * math.sin(self.yaw)
            if not (0 <= x <= WIDTH and 0 <= y <= HEIGHT) or any(math.hypot(x-a, y-b) <= r for a,b,r in OBSTACLES):
                best = d
                break
        return best

    def begin(self, route):
        self.route = validate_route(route)
        for x,y in self.route:
            if any(math.hypot(x-a,y-b) <= r+.4 for a,b,r in OBSTACLES):
                raise ValueError('Bir yol noktası simülasyon engeline çok yakın.')
        self.index = 0
        self.detour = []
        self.running = True
        self.state = 'Rota takip ediliyor'

    def stop(self):
        self.running = False
        self.speed = 0.
        self.state = 'Durduruldu'

    def _blocked(self, a, b, margin=.6):
        dx, dy = b[0]-a[0], b[1]-a[1]
        length = dx*dx+dy*dy
        for x,y,r in OBSTACLES:
            t = max(0., min(1., ((x-a[0])*dx+(y-a[1])*dy)/length)) if length else 0.
            if math.hypot(a[0]+t*dx-x,a[1]+t*dy-y) < r+margin:
                return x,y,r
        return None

    def tick(self, dt, limit, manual=(0.,0.)):
        old = self.x,self.y
        if self.running:
            if self.index >= len(self.route):
                self.stop()
                self.state = 'Rota tamamlandı'
                return
            target = self.detour[0] if self.detour else self.route[self.index]
            d = math.dist((self.x,self.y), target)
            if d < .12:
                if self.detour:
                    self.detour.pop(0)
                    if not self.detour:
                        self.state = 'Rotaya dönülüyor'
                else:
                    self.index += 1
                    self.state = 'Rota takip ediliyor'
                self.speed = 0.
                return
            obstacle = self._blocked((self.x,self.y), target)
            if obstacle and not self.detour:
                ox,oy,r = obstacle
                # Yerel demoda görünür engeller üzerinden iki yandan güvenli ara yol ara.
                heading = math.atan2(target[1]-self.y,target[0]-self.x)
                ux,uy = math.cos(heading),math.sin(heading)
                candidates = []
                for side in (1,-1):
                    clearance = r+1.1
                    nx,ny = -uy*side,ux*side
                    pts = [(ox-ux*clearance+nx*clearance,oy-uy*clearance+ny*clearance),
                           (ox+ux*clearance+nx*clearance,oy+uy*clearance+ny*clearance)]
                    chain = [(self.x,self.y)] + pts + [target]
                    if all(.3<x<WIDTH-.3 and .3<y<HEIGHT-.3 for x,y in pts) and all(not self._blocked(a,b,.4) for a,b in zip(chain,chain[1:])):
                        candidates.append(pts)
                if not candidates:
                    self.stop()
                    self.state = 'Güvenli geçiş yok • durduruldu'
                    return
                self.detour = min(candidates,key=lambda pts: math.dist((self.x,self.y),pts[0])+math.dist(pts[-1],target))
                self.state = 'Engelden kaçılıyor'
                return
            self.yaw = math.atan2(target[1]-self.y,target[0]-self.x)
            self.speed = min(limit, d/max(dt,.001))
            nx = self.x+math.cos(self.yaw)*self.speed*dt
            ny = self.y+math.sin(self.yaw)*self.speed*dt
        else:
            forward, turn = manual
            self.yaw = (self.yaw + turn*1.7*dt) % math.tau
            self.speed = forward*limit
            nx = self.x+math.cos(self.yaw)*self.speed*dt
            ny = self.y+math.sin(self.yaw)*self.speed*dt
        if not (.25 <= nx <= WIDTH-.25 and .25 <= ny <= HEIGHT-.25) or any(math.hypot(nx-a,ny-b)<r+.3 for a,b,r in OBSTACLES):
            self.stop()
            self.state = 'Engel / alan sınırı • durduruldu'
            return
        self.x,self.y = nx,ny
        self.distance += math.dist(old,(nx,ny))
