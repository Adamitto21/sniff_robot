/* ============================================================
   sniff_robot dashboard
   Łączy się z rosbridge (WebSocket, port 9090) i web_video_server
   (MJPEG, port 8080). Zero zależności — własny mini-klient
   protokołu rosbridge, działa offline w sieci robota.
   ============================================================ */

'use strict';

const APP_VERSION = 'js v3';   // musi zgadzać się z 'html v3' w stopce

/* ======================= KONFIGURACJA ======================= */

const DEFAULT_CFG = {
  host: '',                       // puste = host, z którego serwowana jest strona
  wsPort: 9090,
  videoPort: 8080,
  cmdVelTopic: '/cmd_vel',
  cameraTopic: '/oak/rgb/image_raw',
  mapTopic: '/map',
  poseTopic: '/pose',             // slam_toolbox publikuje PoseWithCovarianceStamped
  scanTopic: '/scan',
  maxLinear: 0.4,                 // m/s
  maxAngular: 1.2,                // rad/s
  sensors: [
    // Przykład — odkomentuj / dodaj przez UI (+ dodaj), gdy czujnik zacznie publikować:
    // { topic: '/sniff/air_quality', type: 'std_msgs/msg/Float32', label: 'Jakość powietrza', unit: 'ppm', field: 'data' },
  ],
};

const CFG_KEY = 'sniff_dashboard_cfg_v1';

function loadCfg() {
  try {
    const raw = localStorage.getItem(CFG_KEY);
    if (raw) return Object.assign({}, DEFAULT_CFG, JSON.parse(raw));
  } catch (e) { /* localStorage niedostępny — jedziemy na domyślnych */ }
  return Object.assign({}, DEFAULT_CFG);
}
function saveCfg() {
  try { localStorage.setItem(CFG_KEY, JSON.stringify(cfg)); } catch (e) {}
}

const cfg = loadCfg();
const HOST = cfg.host || location.hostname || 'localhost';
const WS_URL = `ws://${HOST}:${cfg.wsPort}`;
const VIDEO_BASE = `http://${HOST}:${cfg.videoPort}`;

/* Pola wiadomości dla popularnych typów czujników (ścieżka kropkowa) */
const FIELD_GUESS = {
  'std_msgs/msg/Float32': 'data',
  'std_msgs/msg/Float64': 'data',
  'std_msgs/msg/Int32': 'data',
  'std_msgs/msg/Int16': 'data',
  'std_msgs/msg/UInt16': 'data',
  'std_msgs/msg/Bool': 'data',
  'sensor_msgs/msg/Temperature': 'temperature',
  'sensor_msgs/msg/RelativeHumidity': 'relative_humidity',
  'sensor_msgs/msg/FluidPressure': 'fluid_pressure',
  'sensor_msgs/msg/Range': 'range',
  'sensor_msgs/msg/BatteryState': 'voltage',
  'sensor_msgs/msg/Illuminance': 'illuminance',
};

/* ======================= MINI-KLIENT ROSBRIDGE ======================= */

class RosBridge {
  constructor() {
    this.ws = null;
    this.url = '';
    this.connected = false;
    this.subs = new Map();      // topic -> {type, cbs:Set, throttle}
    this.adv = new Map();       // topic -> type
    this.svcCbs = new Map();    // id -> cb
    this.svcId = 0;
    this.onStatus = () => {};
    this._retryTimer = null;
  }

  connect(url) {
    this.url = url;
    this._open();
  }

  _open() {
    clearTimeout(this._retryTimer);
    try { this.ws = new WebSocket(this.url); }
    catch (e) { this._scheduleRetry(); return; }

    this.ws.onopen = () => {
      this.connected = true;
      this.onStatus(true);
      // odtwórz stan po (re)połączeniu
      for (const [topic, type] of this.adv) {
        this._send({ op: 'advertise', topic, type });
      }
      for (const [topic, s] of this.subs) {
        this._send({ op: 'subscribe', topic, type: s.type, throttle_rate: s.throttle, queue_length: 1 });
      }
    };

    this.ws.onmessage = (ev) => {
      let d;
      try { d = JSON.parse(ev.data); } catch (e) { return; }
      if (d.op === 'publish') {
        const s = this.subs.get(d.topic);
        if (s) for (const cb of [...s.cbs]) {
          try { cb(d.msg); } catch (err) { console.error('handler', d.topic, err); }
        }
      } else if (d.op === 'service_response') {
        const cb = this.svcCbs.get(d.id);
        if (cb) { this.svcCbs.delete(d.id); cb(d.values, d.result); }
      }
    };

    this.ws.onclose = () => {
      if (this.connected) { this.connected = false; this.onStatus(false); }
      this._scheduleRetry();
    };
    this.ws.onerror = () => { try { this.ws.close(); } catch (e) {} };
  }

  _scheduleRetry() {
    clearTimeout(this._retryTimer);
    this._retryTimer = setTimeout(() => this._open(), 2000);
  }

  _send(obj) {
    if (this.ws && this.ws.readyState === 1) this.ws.send(JSON.stringify(obj));
  }

  /* Wielu odbiorców na jeden topic: karta czujnika, podgląd i panel wartości
     mogą słuchać tego samego topicu naraz. unsubscribe(topic, cb) zdejmuje
     tylko jednego z nich; subskrypcja znika, gdy nie zostanie żaden. */
  subscribe(topic, type, cb, throttle = 0) {
    let s = this.subs.get(topic);
    if (!s) {
      s = { type, cbs: new Set([cb]), throttle };
      this.subs.set(topic, s);
      const m = { op: 'subscribe', topic, throttle_rate: throttle, queue_length: 1 };
      if (type) m.type = type;          // bez typu rosbridge odczyta go sam
      this._send(m);
    } else {
      s.cbs.add(cb);
      if (throttle && throttle < s.throttle) {
        s.throttle = throttle;
        this._send({ op: 'subscribe', topic, type: s.type, throttle_rate: throttle, queue_length: 1 });
      }
    }
    return cb;
  }
  unsubscribe(topic, cb) {
    const s = this.subs.get(topic);
    if (!s) return;
    if (cb) s.cbs.delete(cb); else s.cbs.clear();
    if (s.cbs.size === 0) {
      this.subs.delete(topic);
      this._send({ op: 'unsubscribe', topic });
    }
  }
  advertise(topic, type) {
    this.adv.set(topic, type);
    this._send({ op: 'advertise', topic, type });
  }
  publish(topic, msg) {
    this._send({ op: 'publish', topic, msg });
  }
  callService(service, args, cb) {
    const id = 'svc' + (++this.svcId);
    if (cb) this.svcCbs.set(id, cb);
    const m = { op: 'call_service', service, id };
    if (args) m.args = args;
    this._send(m);
  }
}

const ros = new RosBridge();

/* ======================= POMOCNICZE ======================= */

const $ = (id) => document.getElementById(id);

function toast(txt) {
  const t = $('toast');
  t.textContent = txt;
  t.classList.remove('hidden');
  clearTimeout(t._tm);
  t._tm = setTimeout(() => t.classList.add('hidden'), 2200);
}

/* Ścieżka do pola: 'a.b.c' oraz indeksy tablic: 'data[3]', 'pose.position.x' */
function getPath(obj, path) {
  if (!path) return undefined;
  return String(path).replace(/\[(\d+)\]/g, '.$1').split('.').filter(Boolean)
    .reduce((o, k) => (o == null ? undefined : o[k]), obj);
}

/* Agregat długiej tablicy — np. min z /scan ranges = najbliższa przeszkoda.
   Pętla zamiast Math.min(...arr): tablice skanu mają setki elementów.
   null/inf (brak echa lidara) są pomijane. */
function aggregate(arr, agg) {
  if (!Array.isArray(arr)) return undefined;
  if (agg === 'len') return arr.length;
  let n = 0, sum = 0, mn = Infinity, mx = -Infinity;
  for (const v of arr) {
    if (typeof v !== 'number' || !isFinite(v)) continue;
    n++; sum += v;
    if (v < mn) mn = v;
    if (v > mx) mx = v;
  }
  if (!n) return undefined;
  if (agg === 'min') return mn;
  if (agg === 'max') return mx;
  if (agg === 'avg') return sum / n;
  return undefined;
}

/* Wartość karty czujnika z wiadomości */
function resolveValue(msg, s) {
  const raw = getPath(msg, s.field);
  return s.agg ? aggregate(raw, s.agg) : raw;
}

/* Rozkłada wiadomość na listę pól nadających się na kartę.
   Zagnieżdżenia schodzą po kropkach, krótkie tablice liczb dostają indeksy,
   długie (np. ranges ze skanu) — agregat do wyboru. */
function flattenMsg(obj, prefix, out, depth) {
  out = out || []; depth = depth || 0; prefix = prefix || '';
  if (depth > 5 || out.length > 150) return out;
  for (const k in obj) {
    if (!Object.prototype.hasOwnProperty.call(obj, k)) continue;
    const v = obj[k];
    if (v === null || v === undefined) continue;
    const path = prefix ? prefix + '.' + k : k;
    const t = typeof v;
    if (t === 'number' || t === 'boolean' || t === 'string') {
      out.push({ path, kind: t });
    } else if (Array.isArray(v)) {
      // typ oceniamy po pierwszym NIE-null elemencie: w LaserScan brak echa
      // to null i często trafia akurat na ranges[0]
      let probe;
      for (const el of v) { if (el !== null && el !== undefined) { probe = el; break; } }
      if (typeof probe !== 'number') continue;    // pusta lub tablica obiektów
      if (v.length <= 8) {
        for (let i = 0; i < v.length; i++) out.push({ path: path + '[' + i + ']', kind: 'number' });
      } else {
        out.push({ path, kind: 'array', len: v.length });
      }
    } else if (t === 'object') {
      flattenMsg(v, path, out, depth + 1);
    }
  }
  return out;
}

/* Jednostka zgadywana z nazwy pola — działa też dla własnych wiadomości */
const UNIT_BY_NAME = [
  [/(^|_)e?co2($|_)/i, 'ppm'], [/tvoc|voc/i, 'ppb'], [/pm_?(1|2_?5|10)/i, 'µg/m³'],
  [/temp/i, '°C'], [/humid/i, '%'], [/pressure/i, 'Pa'], [/volt/i, 'V'],
  [/current/i, 'A'], [/percent/i, '%'], [/range|distance/i, 'm'], [/illum|lux/i, 'lx'],
];
function guessUnit(path) {
  const leaf = path.split('.').pop();
  for (const [re, u] of UNIT_BY_NAME) if (re.test(leaf)) return u;
  return '';
}
function defaultLabel(path) {
  return path.split('.').pop().replace(/\[(\d+)\]/, ' $1').replace(/_/g, ' ');
}

function fmtVal(v) {
  if (typeof v === 'number') {
    const a = Math.abs(v);
    if (a >= 100) return v.toFixed(0);
    if (a >= 1) return v.toFixed(2);
    return v.toFixed(3);
  }
  if (typeof v === 'boolean') return v ? 'TAK' : 'NIE';
  if (v === undefined || v === null) return '—';
  return String(v);
}

function quatYaw(q) {
  return Math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z));
}

/* ======================= STATUS POŁĄCZENIA ======================= */

ros.onStatus = (ok) => {
  $('statusDot').className = 'dot ' + (ok ? 'ok' : 'err');
  $('statusTxt').textContent = ok ? 'połączono' : 'brak połączenia';
  if (!ok) {
    $('latTxt').textContent = '';
    stopAll(false); // rozłączenie → lokalnie zerujemy komendę
  }
};

setInterval(() => {
  if (!ros.connected) return;
  const t0 = performance.now();
  ros.callService('/rosapi/get_time', {}, () => {
    $('latTxt').textContent = Math.round(performance.now() - t0) + ' ms';
  });
}, 4000);

/* ======================= STEROWANIE (cmd_vel) ======================= */

const drive = { nx: 0, ny: 0, engaged: false, zeroBurst: 0 };

function pubTwist(lin, ang) {
  ros.publish(cfg.cmdVelTopic, {
    linear: { x: lin, y: 0, z: 0 },
    angular: { x: 0, y: 0, z: ang },
  });
}

function currentCmd() {
  return { lin: drive.ny * cfg.maxLinear, ang: -drive.nx * cfg.maxAngular };
}

function updateSpeedUI(lin, ang) {
  $('speedRead').textContent =
    'v ' + lin.toFixed(2) + ' m/s\u00a0\u00a0\u03c9 ' + ang.toFixed(2) + ' rad/s';
}

/* pętla 10 Hz — publikuje tylko gdy sterujemy (+ krótka seria zer po puszczeniu) */
setInterval(() => {
  if (!ros.connected) return;
  if (drive.engaged) {
    const c = currentCmd();
    pubTwist(c.lin, c.ang);
    updateSpeedUI(c.lin, c.ang);
  } else if (drive.zeroBurst > 0) {
    drive.zeroBurst--;
    pubTwist(0, 0);
    updateSpeedUI(0, 0);
  }
}, 100);

function setDrive(nx, ny) {
  drive.nx = Math.max(-1, Math.min(1, nx));
  drive.ny = Math.max(-1, Math.min(1, ny));
  drive.engaged = true;
}

function releaseDrive() {
  if (!drive.engaged) return;
  drive.engaged = false;
  drive.nx = 0; drive.ny = 0;
  drive.zeroBurst = 4;
}

function stopAll(flash = true) {
  keysDown.clear();
  drive.engaged = false;
  drive.nx = 0; drive.ny = 0;
  drive.zeroBurst = 6;
  joyReset();
  if (flash) {
    $('btnStop').classList.add('flash');
    setTimeout(() => $('btnStop').classList.remove('flash'), 250);
    toast('STOP — wysłano zatrzymanie');
  }
}

/* ---------- wirtualny joystick (mysz + dotyk, pointer events) ---------- */

const joyEl = $('joy'), knob = $('knob');
let joyPointer = null;

function joyReset() {
  knob.style.transform = 'translate(0px, 0px)';
}

function joyMove(e) {
  const r = joyEl.getBoundingClientRect();
  const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
  let dx = e.clientX - cx, dy = e.clientY - cy;
  const R = r.width / 2 - 40;
  const d = Math.hypot(dx, dy);
  if (d > R) { dx *= R / d; dy *= R / d; }
  knob.style.transform = `translate(${dx}px, ${dy}px)`;
  setDrive(dx / R, -dy / R); // do góry = jazda do przodu
}

joyEl.addEventListener('pointerdown', (e) => {
  e.preventDefault();
  joyPointer = e.pointerId;
  joyEl.setPointerCapture(e.pointerId);
  joyMove(e);
});
joyEl.addEventListener('pointermove', (e) => {
  if (e.pointerId === joyPointer) joyMove(e);
});
function joyEnd(e) {
  if (e.pointerId !== joyPointer) return;
  joyPointer = null;
  joyReset();
  releaseDrive();
}
joyEl.addEventListener('pointerup', joyEnd);
joyEl.addEventListener('pointercancel', joyEnd);

/* ---------- klawiatura: WASD / strzałki / spacja ---------- */

const keysDown = new Set();
const KEYMAP = {
  KeyW: 'up', ArrowUp: 'up',
  KeyS: 'down', ArrowDown: 'down',
  KeyA: 'left', ArrowLeft: 'left',
  KeyD: 'right', ArrowRight: 'right',
};

function keysApply() {
  const ny = (keysDown.has('up') ? 1 : 0) - (keysDown.has('down') ? 1 : 0);
  const nx = (keysDown.has('right') ? 1 : 0) - (keysDown.has('left') ? 1 : 0);
  if (nx === 0 && ny === 0) releaseDrive();
  else setDrive(nx, ny);
}

window.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
  if (e.code === 'Space') { e.preventDefault(); stopAll(); return; }
  const dir = KEYMAP[e.code];
  if (dir) { e.preventDefault(); keysDown.add(dir); keysApply(); }
});
window.addEventListener('keyup', (e) => {
  const dir = KEYMAP[e.code];
  if (dir) { keysDown.delete(dir); keysApply(); }
});

/* bezpieczeństwo: schowana karta / utrata fokusu → stop */
document.addEventListener('visibilitychange', () => { if (document.hidden) stopAll(false); });
window.addEventListener('blur', () => stopAll(false));

$('btnStop').addEventListener('click', () => stopAll());
$('stopFab').addEventListener('click', () => stopAll());

/* ---------- suwaki prędkości ---------- */

function bindSlider(id, valId, key, unit) {
  const s = $(id), v = $(valId);
  s.value = cfg[key];
  v.textContent = Number(cfg[key]).toFixed(2) + ' ' + unit;
  s.addEventListener('input', () => {
    cfg[key] = parseFloat(s.value);
    v.textContent = cfg[key].toFixed(2) + ' ' + unit;
    saveCfg();
  });
}
bindSlider('sliderLin', 'valLin', 'maxLinear', 'm/s');
bindSlider('sliderAng', 'valAng', 'maxAngular', 'rad/s');

/* ======================= KAMERA (MJPEG) ======================= */

const camImg = $('camImg');

function camConnect() {
  $('camOverlay').classList.add('hidden');
  const url = `${VIDEO_BASE}/stream?topic=${cfg.cameraTopic}&type=mjpeg&quality=70&t=${Date.now()}`;
  camImg.src = url;
}
camImg.addEventListener('error', () => {
  $('camOverlay').classList.remove('hidden');
});
$('camRetry').addEventListener('click', camConnect);

/* ======================= MAPA (OccupancyGrid) ======================= */

const mapCanvas = $('mapCanvas');
const mapCtx = mapCanvas.getContext('2d');
const mapWrap = $('mapWrap');
const mapOff = document.createElement('canvas'); // bitmapa mapy w rozdzielczości gridu
let mapInfo = null;
let robot = null;          // {x, y, yaw} w układzie mapy [m]
let scanPts = null;        // Float32Array [px0,py0,px1,py1,...] w pikselach mapy
let showScan = true;
const view = { scale: 1, x: 0, y: 0, fitted: false };
let renderPending = false;

function sizeMapCanvas() {
  const dpr = window.devicePixelRatio || 1;
  mapCanvas.width = Math.max(1, Math.round(mapWrap.clientWidth * dpr));
  mapCanvas.height = Math.max(1, Math.round(mapWrap.clientHeight * dpr));
  if (view.fitted) fitMap();
  requestRender();
}
new ResizeObserver(sizeMapCanvas).observe(mapWrap);

function onMapMsg(m) {
  const w = m.info.width, h = m.info.height;
  mapOff.width = w; mapOff.height = h;
  const ctx = mapOff.getContext('2d');
  const img = ctx.createImageData(w, h);
  const D = m.data, px = img.data;
  for (let row = 0; row < h; row++) {
    const src = row * w;
    let di = (h - 1 - row) * w * 4; // odbicie w pionie: oś Y mapy do góry
    for (let col = 0; col < w; col++, di += 4) {
      const v = D[src + col];
      let r, g, b;
      if (v === -1 || v == null) { r = 44; g = 51; b = 60; }       // nieznane
      else if (v < 50)           { r = 223; g = 227; b = 231; }    // wolne
      else                       { r = 9;  g = 12;  b = 16;  }     // zajęte
      px[di] = r; px[di + 1] = g; px[di + 2] = b; px[di + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
  mapInfo = m.info;
  $('mapOverlay').classList.add('hidden');
  $('mapMeta').textContent = `${w}×${h} @ ${m.info.resolution.toFixed(3)} m/px`;
  if (!view.fitted) fitMap();
  requestRender();
}

function worldToPix(wx, wy) {
  const o = mapInfo.origin.position;
  return [
    (wx - o.x) / mapInfo.resolution,
    mapInfo.height - (wy - o.y) / mapInfo.resolution,
  ];
}

function fitMap() {
  if (!mapInfo) return;
  const cw = mapWrap.clientWidth, ch = mapWrap.clientHeight;
  const s = Math.min(cw / mapOff.width, ch / mapOff.height) * 0.94;
  view.scale = s;
  view.x = (cw - mapOff.width * s) / 2;
  view.y = (ch - mapOff.height * s) / 2;
  view.fitted = true;
}

function requestRender() {
  if (renderPending) return;
  renderPending = true;
  requestAnimationFrame(() => { renderPending = false; renderMap(); });
}

function renderMap() {
  const dpr = window.devicePixelRatio || 1;
  mapCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
  mapCtx.clearRect(0, 0, mapCanvas.width, mapCanvas.height);
  if (!mapInfo) return;

  mapCtx.translate(view.x, view.y);
  mapCtx.scale(view.scale, view.scale);
  mapCtx.imageSmoothingEnabled = false;
  mapCtx.drawImage(mapOff, 0, 0);

  // punkty skanu lidara
  if (showScan && scanPts) {
    mapCtx.fillStyle = 'rgba(55,194,166,0.85)';
    const s = Math.max(0.6, 1.6 / view.scale);
    for (let i = 0; i < scanPts.length; i += 2) {
      mapCtx.fillRect(scanPts[i] - s / 2, scanPts[i + 1] - s / 2, s, s);
    }
  }

  // pozycja robota
  if (robot) {
    const [px, py] = worldToPix(robot.x, robot.y);
    const size = 13 / view.scale;
    mapCtx.save();
    mapCtx.translate(px, py);
    mapCtx.rotate(-robot.yaw); // canvas Y w dół, mapa Y w górę
    mapCtx.beginPath();
    mapCtx.moveTo(size, 0);
    mapCtx.lineTo(-size * 0.62, size * 0.55);
    mapCtx.lineTo(-size * 0.62, -size * 0.55);
    mapCtx.closePath();
    mapCtx.fillStyle = '#37c2a6';
    mapCtx.fill();
    mapCtx.lineWidth = Math.max(0.4, 1.4 / view.scale);
    mapCtx.strokeStyle = '#0c1013';
    mapCtx.stroke();
    mapCtx.restore();
  }
}

function onPoseMsg(m) {
  const p = m.pose && m.pose.pose ? m.pose.pose : m.pose; // PoseWithCovarianceStamped lub PoseStamped
  if (!p || !p.position) return;
  robot = { x: p.position.x, y: p.position.y, yaw: quatYaw(p.orientation) };
  requestRender();
}

function onScanMsg(m) {
  if (!robot || !mapInfo) { scanPts = null; return; }
  const n = m.ranges.length;
  const out = new Float32Array(2 * Math.ceil(n / 2));
  let k = 0;
  for (let i = 0; i < n; i += 2) { // co drugi promień wystarczy do podglądu
    const r = m.ranges[i];
    if (!(r >= m.range_min && r <= m.range_max)) continue;
    const a = robot.yaw + m.angle_min + i * m.angle_increment;
    const [px, py] = worldToPix(robot.x + r * Math.cos(a), robot.y + r * Math.sin(a));
    out[k++] = px; out[k++] = py;
  }
  scanPts = out.subarray(0, k);
  requestRender();
}

/* ---------- pan / zoom mapy (kółko, przeciąganie, pinch) ---------- */

function zoomAt(mx, my, f) {
  const ns = Math.min(80, Math.max(0.15, view.scale * f));
  f = ns / view.scale;
  view.x = mx - (mx - view.x) * f;
  view.y = my - (my - view.y) * f;
  view.scale = ns;
  view.fitted = false;
  requestRender();
}

mapCanvas.addEventListener('wheel', (e) => {
  e.preventDefault();
  const r = mapCanvas.getBoundingClientRect();
  zoomAt(e.clientX - r.left, e.clientY - r.top, e.deltaY < 0 ? 1.15 : 1 / 1.15);
}, { passive: false });

const mapPtrs = new Map();
let pinchDist = 0;

mapCanvas.addEventListener('pointerdown', (e) => {
  mapCanvas.setPointerCapture(e.pointerId);
  mapPtrs.set(e.pointerId, { x: e.clientX, y: e.clientY });
  if (mapPtrs.size === 2) {
    const [a, b] = [...mapPtrs.values()];
    pinchDist = Math.hypot(a.x - b.x, a.y - b.y);
  }
});
mapCanvas.addEventListener('pointermove', (e) => {
  const p = mapPtrs.get(e.pointerId);
  if (!p) return;
  if (mapPtrs.size === 1) {
    view.x += e.clientX - p.x;
    view.y += e.clientY - p.y;
    view.fitted = false;
    requestRender();
  }
  p.x = e.clientX; p.y = e.clientY;
  if (mapPtrs.size === 2) {
    const [a, b] = [...mapPtrs.values()];
    const d = Math.hypot(a.x - b.x, a.y - b.y);
    const r = mapCanvas.getBoundingClientRect();
    const mx = (a.x + b.x) / 2 - r.left, my = (a.y + b.y) / 2 - r.top;
    if (pinchDist > 0 && d > 0) zoomAt(mx, my, d / pinchDist);
    pinchDist = d;
  }
});
function mapPtrEnd(e) {
  mapPtrs.delete(e.pointerId);
  pinchDist = 0;
}
mapCanvas.addEventListener('pointerup', mapPtrEnd);
mapCanvas.addEventListener('pointercancel', mapPtrEnd);

$('btnFit').addEventListener('click', () => { fitMap(); requestRender(); });
$('btnScan').addEventListener('click', () => {
  showScan = !showScan;
  $('btnScan').classList.toggle('on', showScan);
  syncScanSub();
  requestRender();
});

function syncScanSub() {
  if (showScan) {
    ros.subscribe(cfg.scanTopic, 'sensor_msgs/msg/LaserScan', onScanMsg, 400);
  } else {
    ros.unsubscribe(cfg.scanTopic, onScanMsg);   // tylko nakładka, nie karty czujników
    scanPts = null;
  }
}

/* ======================= CZUJNIKI ======================= */

const sensorHandlers = new Map(); // topic -> Set(fn)

function sensorSubDispatch(topic) {
  return (msg) => {
    const set = sensorHandlers.get(topic);
    if (set) for (const fn of set) fn(msg);
  };
}

function buildSensors() {
  const grid = $('sensorGrid');
  grid.innerHTML = '';
  sensorHandlers.clear();
  $('sensorsEmpty').classList.toggle('hidden', cfg.sensors.length > 0);

  cfg.sensors.forEach((s, idx) => {
    const card = document.createElement('div');
    card.className = 'sensor-card stale';
    card.innerHTML =
      `<button class="s-del" title="Usuń kartę">✕</button>` +
      `<div class="s-label"></div>` +
      `<div class="s-val">—<span class="s-unit"></span></div>` +
      `<canvas width="140" height="30"></canvas>` +
      `<div class="s-topic mono"></div>`;
    card.querySelector('.s-label').textContent = s.label || s.field || s.topic;
    card.querySelector('.s-unit').textContent = s.unit ? ' ' + s.unit : '';
    card.querySelector('.s-topic').textContent =
      s.topic + (s.field ? ' · ' + (s.agg ? s.agg + '(' + s.field + ')' : s.field) : '');
    card.querySelector('.s-del').addEventListener('click', () => {
      cfg.sensors.splice(idx, 1);
      saveCfg();
      rebuildSensorSubs();
    });
    grid.appendChild(card);

    const valEl = card.querySelector('.s-val');
    const unitTxt = s.unit ? ' ' + s.unit : '';
    const spark = card.querySelector('canvas');
    const sctx = spark.getContext('2d');
    const hist = [];
    let lastMsg = 0;

    const update = (msg) => {
      const v = resolveValue(msg, s);
      valEl.innerHTML = '';
      valEl.appendChild(document.createTextNode(fmtVal(v)));
      const u = document.createElement('span');
      u.className = 's-unit';
      u.textContent = unitTxt;
      valEl.appendChild(u);
      lastMsg = Date.now();
      card.classList.remove('stale');
      if (typeof v === 'number' && isFinite(v)) {
        hist.push(v);
        if (hist.length > 120) hist.shift();
        drawSpark(sctx, spark, hist);
      }
    };
    card._staleCheck = () => {
      if (lastMsg && Date.now() - lastMsg > 6000) card.classList.add('stale');
    };

    if (!sensorHandlers.has(s.topic)) sensorHandlers.set(s.topic, new Set());
    sensorHandlers.get(s.topic).add(update);
  });

}

/* Jedna subskrypcja na topic, trzymana między przebudowami kart.
   Dispatcher czyta sensorHandlers dopiero przy wiadomości, więc przeżywa rebuild. */
const sensorDispatch = new Map();   // topic -> fn

function syncSensorSubs() {
  for (const [topic, fn] of [...sensorDispatch]) {
    if (!sensorHandlers.has(topic)) {          // ostatnia karta z topicu zniknęła
      ros.unsubscribe(topic, fn);
      sensorDispatch.delete(topic);
    }
  }
  for (const topic of sensorHandlers.keys()) {
    if (sensorDispatch.has(topic)) continue;
    const s = cfg.sensors.find((x) => x.topic === topic);
    const fn = sensorSubDispatch(topic);
    sensorDispatch.set(topic, fn);
    ros.subscribe(topic, s.type, fn, 250);
  }
}

function rebuildSensorSubs() {
  buildSensors();
  syncSensorSubs();
}

function drawSpark(ctx, cv, hist) {
  const w = cv.width, h = cv.height;
  ctx.clearRect(0, 0, w, h);
  if (hist.length < 2) return;
  let mn = Infinity, mx = -Infinity;
  for (const v of hist) { if (v < mn) mn = v; if (v > mx) mx = v; }
  const span = mx - mn || 1;
  ctx.beginPath();
  for (let i = 0; i < hist.length; i++) {
    const x = (i / (hist.length - 1)) * (w - 2) + 1;
    const y = h - 3 - ((hist[i] - mn) / span) * (h - 6);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }
  ctx.strokeStyle = '#e8b34b';
  ctx.lineWidth = 1.4;
  ctx.stroke();
}

setInterval(() => {
  document.querySelectorAll('.sensor-card').forEach((c) => c._staleCheck && c._staleCheck());
}, 2000);

/* ======================= PRZEGLĄDARKA TOPIKÓW ======================= */

let previewTopic = null, previewCb = null;

function openTopics() {
  $('modalTopics').classList.remove('hidden');
  refreshTopics();
}

function refreshTopics() {
  const list = $('topicList');
  list.innerHTML = '<div class="small" style="padding:8px">ładowanie…</div>';
  if (!ros.connected) {
    list.innerHTML = '<div class="small" style="padding:8px">Brak połączenia z rosbridge.</div>';
    return;
  }
  ros.callService('/rosapi/topics', {}, (vals) => {
    list.innerHTML = '';
    if (!vals || !vals.topics) {
      list.innerHTML = '<div class="small" style="padding:8px">Nie udało się pobrać listy topików.</div>';
      return;
    }
    const rows = vals.topics
      .map((t, i) => ({ topic: t, type: vals.types[i] || '' }))
      .sort((a, b) => a.topic.localeCompare(b.topic));

    for (const r of rows) {
      const row = document.createElement('div');
      row.className = 'topic-row';
      const isTwist = r.type.indexOf('Twist') !== -1;
      const isImage = r.type.indexOf('/Image') !== -1 || r.type.indexOf('CompressedImage') !== -1;
      if (isTwist || isImage) row.classList.add('hl');

      const name = document.createElement('span');
      name.className = 't-name';
      name.textContent = r.topic;
      const type = document.createElement('span');
      type.className = 't-type';
      type.textContent = r.type;
      row.appendChild(name);
      row.appendChild(type);

      const mkBtn = (txt, fn) => {
        const b = document.createElement('button');
        b.className = 'btn btn-sm';
        b.textContent = txt;
        b.addEventListener('click', fn);
        row.appendChild(b);
      };
      mkBtn('podgląd', () => previewStart(r.topic, r.type));
      mkBtn('+ czujnik', () => fieldsStart(r.topic, r.type));
      if (isTwist) mkBtn('→ sterowanie', () => {
        cfg.cmdVelTopic = r.topic; saveCfg();
        toast('Sterowanie → ' + r.topic);
        applyCmdVel();
      });
      if (isImage) mkBtn('→ kamera', () => {
        cfg.cameraTopic = r.topic.replace(/\/compressed$/, ''); saveCfg();
        toast('Kamera → ' + cfg.cameraTopic);
        applyCamera();
      });
      list.appendChild(row);
    }
  });
}

function previewStart(topic, type) {
  previewStop();
  previewTopic = topic;
  $('topicPreviewWrap').classList.remove('hidden');
  $('topicPreviewTitle').textContent = topic + (type ? '  [' + type + ']' : '');
  $('topicPreview').textContent = 'oczekiwanie na wiadomość…';
  previewCb = ros.subscribe(topic, type, (msg) => {
    let txt;
    try { txt = JSON.stringify(msg, null, 1); } catch (e) { txt = String(msg); }
    if (txt.length > 6000) txt = txt.slice(0, 6000) + '\n…';
    $('topicPreview').textContent = txt;
  }, 300);
  $('topicPreviewWrap').scrollIntoView({ block: 'nearest' });
}

function previewStop() {
  if (previewTopic) ros.unsubscribe(previewTopic, previewCb);
  previewTopic = null;
  previewCb = null;
  $('topicPreviewWrap').classList.add('hidden');
}

/* ---------- panel: wartości wszystkich zmiennych topicu ---------- */

let fieldsTopic = null, fieldsCb = null, fieldsRows = new Map(), fieldsGot = false;
let fieldsTypeCache = '';   // typ z listy topików — do podpowiedzi domyślnego pola

function fieldsStart(topic, type) {
  fieldsStop();
  previewStop();
  const mt = $('modalTopics');
  if (mt) mt.classList.add('hidden');   // panel jest na stronie głównej — okno zbędne
  fieldsTopic = topic;
  fieldsTypeCache = type || '';
  fieldsGot = false;
  fieldsRows.clear();
  $('fieldsWrap').classList.remove('hidden');
  $('sensorsEmpty').classList.add('hidden');
  $('fieldsTitle').textContent = topic + (type ? '  [' + type + ']' : '');
  $('fieldsList').innerHTML =
    '<div class="small" style="padding:10px">oczekiwanie na wiadomość z tego topicu…</div>';
  $('btnFieldsAdd').disabled = true;
  fieldsCb = ros.subscribe(topic, type, onFieldsMsg, 300);
  $('fieldsWrap').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function onFieldsMsg(msg) {
  if (!fieldsTopic) return;
  if (!fieldsGot) {
    fieldsGot = true;
    buildFieldRows(msg);
    $('btnFieldsAdd').disabled = false;
  }
  // wartości na żywo — widać, które pole reaguje na czujnik
  for (const [path, row] of fieldsRows) {
    const v = row.agg ? aggregate(getPath(msg, path), row.agg.value) : getPath(msg, path);
    row.val.textContent = fmtVal(v);
  }
}

function buildFieldRows(msg) {
  const list = $('fieldsList');
  list.innerHTML = '';
  fieldsRows.clear();

  const fields = flattenMsg(msg);
  if (!fields.length) {
    list.innerHTML = '<div class="small" style="padding:10px">' +
      'W tej wiadomości nie ma pól, które da się pokazać na karcie.</div>';
    return;
  }

  const guess = FIELD_GUESS[fieldsTypeCache] || null;

  for (const f of fields) {
    const row = document.createElement('div');
    row.className = 'field-row';

    const cb = document.createElement('input');
    cb.type = 'checkbox';
    if (guess && f.path === guess) cb.checked = true;

    const name = document.createElement('span');
    name.className = 'f-name mono';
    name.textContent = f.path + (f.kind === 'array' ? ' [' + f.len + ']' : '');

    const val = document.createElement('span');
    val.className = 'f-val mono';
    val.textContent = '…';

    const opts = document.createElement('div');
    opts.className = 'f-opts';

    let agg = null;
    if (f.kind === 'array') {
      agg = document.createElement('select');
      for (const [v, t] of [['min', 'min'], ['max', 'max'], ['avg', 'średnia'], ['len', 'ilość']]) {
        const o = document.createElement('option');
        o.value = v; o.textContent = t;
        agg.appendChild(o);
      }
      opts.appendChild(agg);
    }
    const lab = document.createElement('input');
    lab.className = 'f-lab';
    lab.placeholder = 'etykieta';
    lab.value = defaultLabel(f.path);
    const unit = document.createElement('input');
    unit.className = 'f-unit';
    unit.placeholder = 'jedn.';
    unit.value = guessUnit(f.path);
    opts.appendChild(lab);
    opts.appendChild(unit);

    row.appendChild(cb);
    row.appendChild(name);
    row.appendChild(val);
    row.appendChild(opts);

    // klik w wiersz przełącza zaznaczenie (wygodniej na telefonie)
    row.addEventListener('click', (e) => {
      const t = e.target.tagName;
      if (t === 'INPUT' || t === 'SELECT' || t === 'OPTION') return;
      cb.checked = !cb.checked;
    });

    fieldsRows.set(f.path, { cb, val, lab, unit, agg });
    list.appendChild(row);
  }
}

function fieldsAdd() {
  if (!fieldsTopic) return;
  const picked = [];
  for (const [path, row] of fieldsRows) {
    if (!row.cb.checked) continue;
    picked.push({
      topic: fieldsTopic,
      type: fieldsTypeCache || undefined,
      field: path,
      label: row.lab.value.trim() || defaultLabel(path),
      unit: row.unit.value.trim(),
      agg: row.agg ? row.agg.value : null,
    });
  }
  if (!picked.length) { toast('Zaznacz przynajmniej jedno pole'); return; }
  for (const p of picked) {
    const dup = cfg.sensors.some((s) => s.topic === p.topic && s.field === p.field && s.agg === p.agg);
    if (!dup) cfg.sensors.push(p);
  }
  saveCfg();
  fieldsStop();
  rebuildSensorSubs();
  toast(picked.length === 1 ? 'Dodano: ' + picked[0].label : 'Dodano kart: ' + picked.length);
}

function fieldsStop() {
  if (fieldsTopic) ros.unsubscribe(fieldsTopic, fieldsCb);
  fieldsTopic = null;
  fieldsCb = null;
  fieldsRows.clear();
  fieldsGot = false;
  $('fieldsWrap').classList.add('hidden');
  $('sensorsEmpty').classList.toggle('hidden', cfg.sensors.length > 0);
}

$('btnTopics').addEventListener('click', openTopics);
$('btnAddSensor').addEventListener('click', openTopics);
$('btnTopicsRefresh').addEventListener('click', refreshTopics);
$('btnPreviewClose').addEventListener('click', previewStop);
$('btnFieldsClose').addEventListener('click', fieldsStop);
$('btnFieldsAdd').addEventListener('click', fieldsAdd);

/* Dodawanie wprost z panelu Czujniki — bez okna i bez rosapi */
function addFromPanel() {
  let t = $('addTopic').value.trim();
  if (!t) { toast('Wpisz nazwę topicu'); return; }
  if (t[0] !== '/') t = '/' + t;        // ROS2 wymaga wiodącego ukośnika
  fieldsStart(t, null);                 // typ wykryje rosbridge
}
$('addGo').addEventListener('click', addFromPanel);
$('addTopic').addEventListener('keydown', (e) => { if (e.key === 'Enter') addFromPanel(); });

/* ======================= USTAWIENIA ======================= */

function openSettings() {
  $('f_host').value = cfg.host;
  $('f_wsPort').value = cfg.wsPort;
  $('f_videoPort').value = cfg.videoPort;
  $('f_cmdVelTopic').value = cfg.cmdVelTopic;
  $('f_cameraTopic').value = cfg.cameraTopic;
  $('f_mapTopic').value = cfg.mapTopic;
  $('f_poseTopic').value = cfg.poseTopic;
  $('f_scanTopic').value = cfg.scanTopic;
  $('modalSettings').classList.remove('hidden');
}

$('btnSettings').addEventListener('click', openSettings);

$('btnCfgSave').addEventListener('click', () => {
  cfg.host = $('f_host').value.trim();
  cfg.wsPort = parseInt($('f_wsPort').value, 10) || 9090;
  cfg.videoPort = parseInt($('f_videoPort').value, 10) || 8080;
  cfg.cmdVelTopic = $('f_cmdVelTopic').value.trim() || '/cmd_vel';
  cfg.cameraTopic = $('f_cameraTopic').value.trim() || DEFAULT_CFG.cameraTopic;
  cfg.mapTopic = $('f_mapTopic').value.trim() || '/map';
  cfg.poseTopic = $('f_poseTopic').value.trim() || '/pose';
  cfg.scanTopic = $('f_scanTopic').value.trim() || '/scan';
  saveCfg();
  location.reload();
});

$('btnCfgReset').addEventListener('click', () => {
  try { localStorage.removeItem(CFG_KEY); } catch (e) {}
  location.reload();
});

/* zamykanie modali */
function closeModal(id) {
  if (id === 'modalTopics') { previewStop(); fieldsStop(); }
  $(id).classList.add('hidden');
}
document.querySelectorAll('[data-close]').forEach((b) => {
  b.addEventListener('click', () => closeModal(b.dataset.close));
});
document.querySelectorAll('.modal').forEach((m) => {
  m.addEventListener('pointerdown', (e) => { if (e.target === m) closeModal(m.id); });
});

/* ======================= START ======================= */

function applyCmdVel() {
  ros.advertise(cfg.cmdVelTopic, 'geometry_msgs/msg/Twist');
  $('cmdVelBadge').textContent = cfg.cmdVelTopic;
}
function applyCamera() {
  $('camTopicBadge').textContent = cfg.cameraTopic;
  camConnect();
}

function init() {
  $('footUrl').textContent = WS_URL;
  const av = $('appVer');
  if (av) av.textContent = APP_VERSION;
  $('mapTopicHint').textContent = cfg.mapTopic;
  const link = $('camServerLink');
  link.href = VIDEO_BASE;
  link.textContent = VIDEO_BASE;

  applyCmdVel();
  applyCamera();

  ros.subscribe(cfg.mapTopic, 'nav_msgs/msg/OccupancyGrid', onMapMsg, 2000);
  ros.subscribe(cfg.poseTopic, 'geometry_msgs/msg/PoseWithCovarianceStamped', onPoseMsg, 200);
  syncScanSub();
  rebuildSensorSubs();
  sizeMapCanvas();

  ros.connect(WS_URL);
}

init();