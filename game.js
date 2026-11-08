// main_src.js
import * as j from "three";
import { EffectComposer as Ds } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass as Os } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass as Ws } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass as Vs } from "three/addons/postprocessing/OutputPass.js";

// world.js
import * as s from "three";
function Zt(e, t) {
  let n = { pink: 16722902, blue: 2742783, green: 5111674, violet: 10503935, red: 16722490 }, c = [n.pink, n.blue, n.green, n.violet], d = (o) => "#" + o.toString(16).padStart(6, "0"), p = [[-40, -36], [0, -38], [38, -36], [58, -26], [63, -8], [54, 8], [36, 12], [22, 4], [6, 8], [0, 24], [12, 38], [-6, 46], [-36, 44], [-58, 34], [-64, 12], [-52, -2], [-34, 4], [-24, -10], [-40, -20], [-60, -24], [-62, -34]], m = 10, E = m / 2;
  function y(o, f) {
    let i = [], r = o.length;
    for (let a = 0; a < r; a++) {
      let l = o[(a - 1 + r) % r], h = o[a], M = o[(a + 1) % r], H = o[(a + 2) % r];
      for (let C = 0; C < f; C++) {
        let P = C / f, A = P * P, X = A * P;
        i.push([0, 1].map((_) => 0.5 * (2 * h[_] + (-l[_] + M[_]) * P + (2 * l[_] - 5 * h[_] + 4 * M[_] - H[_]) * A + (-l[_] + 3 * h[_] - 3 * M[_] + H[_]) * X)));
      }
    }
    return i;
  }
  let w = y(p, 60), g = 0.5, u = { x: [], z: [], tx: [], tz: [], nx: [], nz: [], curv: [] };
  {
    let o = [0];
    for (let a = 1; a <= w.length; a++) {
      let l = w[a - 1], h = w[a % w.length];
      o.push(o[a - 1] + Math.hypot(h[0] - l[0], h[1] - l[1]));
    }
    let f = o[o.length - 1], i = Math.floor(f / g), r = 0;
    for (let a = 0; a < i; a++) {
      let l = a * f / i;
      for (; o[r + 1] < l; ) r++;
      let h = w[r], M = w[(r + 1) % w.length], H = (l - o[r]) / (o[r + 1] - o[r]);
      u.x.push(h[0] + (M[0] - h[0]) * H), u.z.push(h[1] + (M[1] - h[1]) * H);
    }
  }
  let x = u.x.length, R = x * g;
  for (let o = 0; o < x; o++) {
    let f = (o - 1 + x) % x, i = (o + 1) % x, r = u.x[i] - u.x[f], a = u.z[i] - u.z[f], l = Math.hypot(r, a);
    r /= l, a /= l, u.tx.push(r), u.tz.push(a), u.nx.push(a), u.nz.push(-r);
  }
  for (let o = 0; o < x; o++) {
    let f = (o - 6 + x) % x, i = (o + 6) % x, r = u.tx[i] - u.tx[f], a = u.tz[i] - u.tz[f];
    u.curv.push((r * u.nx[o] + a * u.nz[o]) / (12 * g));
  }
  let U = (o) => (o % R + R) % R;
  function O(o, f = 0) {
    let i = U(o) / g, r = Math.floor(i) % x, a = (r + 1) % x, l = i - Math.floor(i), h = u.x[r] + (u.x[a] - u.x[r]) * l, M = u.z[r] + (u.z[a] - u.z[r]) * l;
    return { x: h + u.nx[r] * f, z: M + u.nz[r] * f, tx: u.tx[r], tz: u.tz[r], nx: u.nx[r], nz: u.nz[r], i: r };
  }
  function lt(o, f, i) {
    let r = i, a = 1e9, l = i < 0 ? x : 40;
    for (let h = -l; h <= l; h++) {
      let M = i < 0 ? (h + x) % x : (i + h + x) % x, H = (u.x[M] - o) ** 2 + (u.z[M] - f) ** 2;
      H < a && (a = H, r = M);
    }
    return r;
  }
  let k = { x0: -82, x1: 82, z0: -56, z1: 66 };
  function ne(o, f, i, r = {}) {
    let a = document.createElement("canvas");
    a.width = o, a.height = f;
    let l = a.getContext("2d");
    i(l, o, f);
    let h = new s.CanvasTexture(a);
    return h.colorSpace = s.SRGBColorSpace, h.anisotropy = e.capabilities.getMaxAnisotropy(), r.repeat && (h.wrapS = h.wrapT = s.RepeatWrapping), h;
  }
  function Ct(o, f, i, r, a = 9e3, l = "255,255,255") {
    for (let h = 0; h < a; h++)
      o.fillStyle = `rgba(${l},${Math.random() * r})`, o.fillRect(Math.random() * f, Math.random() * i, 1 + Math.random() * 2, 1 + Math.random() * 2);
  }
  let Xe = [];
  {
    let o = 0;
    for (; o < x; ) {
      let f = u.curv[o];
      if (Math.abs(f) > 0.05) {
        let i = o, r = o, a = Math.abs(f);
        for (; i < x && Math.abs(u.curv[i]) > 0.035; )
          Math.abs(u.curv[i]) > a && (a = Math.abs(u.curv[i]), r = i), i++;
        let l = Math.sign(u.curv[r]);
        for (let h of [10, -4]) {
          let M = (r - Math.round(h / g) + x) % x;
          Xe.push({ idx: M, inner: l, color: c[Xe.length % 4] });
        }
        o = i + 20;
      } else o++;
    }
  }
  let W = 12.5, Lt = ne(Math.round((k.x1 - k.x0) * W), Math.round((k.z1 - k.z0) * W), (o, f, i) => {
    let r = (h) => (h - k.x0) * W, a = (h) => (h - k.z0) * W;
    o.fillStyle = "#16151c", o.fillRect(0, 0, f, i), Ct(o, f, i, 0.05, 3e4);
    let l = () => {
      o.beginPath();
      for (let h = 0; h <= x; h++) {
        let M = h % x;
        h ? o.lineTo(r(u.x[M]), a(u.z[M])) : o.moveTo(r(u.x[M]), a(u.z[M]));
      }
    };
    o.lineJoin = "round", o.lineCap = "round", l(), o.strokeStyle = "#2b2a33", o.lineWidth = (m + 3.2) * W, o.stroke(), l(), o.strokeStyle = "#5d5e66", o.lineWidth = m * W, o.stroke(), o.save(), l(), o.lineWidth = m * W, o.strokeStyle = "rgba(0,0,0,0)", o.stroke();
    for (let h = 0; h < 6; h++) {
      o.beginPath();
      let M = (Math.random() - 0.5) * 6;
      for (let H = 0; H <= x; H += 2) {
        let C = H % x, P = r(u.x[C] + u.nx[C] * (M + Math.sin(H * 0.02 + h) * 1.2)), A = a(u.z[C] + u.nz[C] * (M + Math.sin(H * 0.02 + h) * 1.2));
        H ? o.lineTo(P, A) : o.moveTo(P, A);
      }
      o.strokeStyle = `rgba(20,20,24,${0.12 + Math.random() * 0.12})`, o.lineWidth = 3 + Math.random() * 4, o.stroke();
    }
    o.restore();
    {
      let h = O(0), M = 10, H = m / M;
      for (let C = 0; C < 2; C++) for (let P = 0; P < M; P++) {
        o.fillStyle = (C + P) % 2 ? "#111" : "#f4f4f4";
        let A = -E + P * H, X = C * H, _ = h.x + h.nx * A + h.tx * X, Z = h.z + h.nz * A + h.tz * X;
        o.save(), o.translate(r(_), a(Z)), o.rotate(Math.atan2(h.nz, h.nx)), o.fillRect(0, 0, H * W + 1, H * W + 1), o.restore();
      }
    }
    o.strokeStyle = "rgba(255,255,255,.55)", o.lineWidth = 3;
    for (let h = 0; h < 6; h++) {
      let M = O(-6.2 - h * 6 + 1.2, h % 2 ? 2.3 : -2.3);
      o.save(), o.translate(r(M.x), a(M.z)), o.rotate(Math.atan2(M.nz, M.nx)), o.beginPath(), o.moveTo(-1.2 * W, 0), o.lineTo(1.2 * W, 0), o.stroke(), o.restore();
    }
    {
      o.save(), o.beginPath(), o.rect(r(-8), a(-46), 52 * W, 26 * W), o.clip(), o.fillStyle = "#a99f97", o.fillRect(r(-8), a(-46), 52 * W, 26 * W);
      let P = 3.4 * W, A = 0.32 * W, X = 0;
      for (let _ = a(-46); _ < a(-20); _ += P, X++) {
        let Z = 0;
        for (let L = r(-8); L < r(44); L += P, Z++) {
          o.fillStyle = (X + Z) % 2 ? "#8b5a54" : "#77747a", o.fillRect(L + A, _ + A, P - A, P - A), o.strokeStyle = "rgba(0,0,0,.12)", o.lineWidth = 1;
          for (let F = 1; F < 4; F++)
            o.beginPath(), o.moveTo(L + A, _ + A + F * P / 4), o.lineTo(L + P, _ + A + F * P / 4), o.stroke();
        }
      }
      Ct(o, f, i, 0.05, 6e3, "0,0,0"), o.restore();
    }
    o.globalCompositeOperation = "lighter";
    for (let h of Xe) {
      let M = O(h.idx * g, -h.inner * (E + 1.6)), H = o.createRadialGradient(r(M.x), a(M.z), 0, r(M.x), a(M.z), 9 * W), C = new s.Color(h.color);
      H.addColorStop(0, `rgba(${C.r * 255 | 0},${C.g * 255 | 0},${C.b * 255 | 0},0.42)`), H.addColorStop(1, "rgba(0,0,0,0)"), o.fillStyle = H, o.fillRect(r(M.x) - 9 * W, a(M.z) - 9 * W, 18 * W, 18 * W);
    }
    for (let [h, M, H, C] of [[-60, -45, n.green, 30], [70, -40, n.blue, 30], [70, 50, n.pink, 34], [-65, 50, n.violet, 34], [18, -30, n.red, 18]]) {
      let P = o.createRadialGradient(r(h), a(M), 0, r(h), a(M), C * W), A = new s.Color(H);
      P.addColorStop(0, `rgba(${A.r * 255 | 0},${A.g * 255 | 0},${A.b * 255 | 0},0.22)`), P.addColorStop(1, "rgba(0,0,0,0)"), o.fillStyle = P, o.fillRect(0, 0, f, i);
    }
    o.globalCompositeOperation = "source-over";
  }), B = new s.Group();
  t.add(B), t.add(new s.HemisphereLight(9075967, 1708064, 0.7));
  let It = new s.DirectionalLight(16777215, 0.7);
  It.position.set(10, 40, -20), t.add(It);
  for (let [o, f, i] of [[-50, -30, n.green], [55, -30, n.blue], [50, 40, n.pink], [-50, 40, n.violet]]) {
    let r = new s.PointLight(i, i === n.green ? 40 : 70, 60, 1.3);
    r.position.set(o, 9, f), t.add(r);
  }
  {
    let o = new s.PlaneGeometry(k.x1 - k.x0, k.z1 - k.z0);
    o.rotateX(-Math.PI / 2);
    let f = new s.MeshStandardMaterial({ map: Lt, roughness: 0.42, metalness: 0.15, emissive: 16777215, emissiveMap: Lt, emissiveIntensity: 0.12 }), i = new s.Mesh(o, f);
    i.position.set((k.x0 + k.x1) / 2, 0, (k.z0 + k.z1) / 2), B.add(i);
  }
  let At = ne(512, 256, (o, f, i) => {
    let r = o.createLinearGradient(0, 0, 0, i);
    r.addColorStop(0, "#2a2d3a"), r.addColorStop(1, "#4b5160"), o.fillStyle = r, o.fillRect(0, 0, f, i);
    for (let a = 0; a < f; a += 16)
      o.fillStyle = "rgba(0,0,0,.25)", o.fillRect(a, 0, 3, i), o.fillStyle = "rgba(255,255,255,.06)", o.fillRect(a + 4, 0, 2, i);
  }, { repeat: !0 });
  At.repeat.set(8, 1);
  {
    let f = new s.MeshStandardMaterial({ map: At, roughness: 0.8, metalness: 0.2 }), i = k.x1 - k.x0, r = k.z1 - k.z0, a = (k.x0 + k.x1) / 2, l = (k.z0 + k.z1) / 2, h = (z, I, $, Y) => {
      let te = new s.Mesh(new s.PlaneGeometry(z, 14), f);
      te.position.set(I, 14 / 2, $), te.rotation.y = Y, B.add(te);
    };
    h(i, a, k.z0, 0), h(i, a, k.z1, Math.PI), h(r, k.x0, l, Math.PI / 2), h(r, k.x1, l, -Math.PI / 2);
    let M = new s.Mesh(new s.PlaneGeometry(i, r), new s.MeshStandardMaterial({ color: 723986, roughness: 1 }));
    M.rotation.x = Math.PI / 2, M.position.set(a, 14, l), B.add(M);
    let H = new s.MeshStandardMaterial({ color: 3108682, emissive: 866848, roughness: 0.5, metalness: 0.6 }), C = new s.InstancedMesh(new s.BoxGeometry(1, 1, 1), H, 600), P = 0, A = new s.Matrix4(), X = new s.Quaternion(), _ = new s.Vector3(), Z = new s.Vector3(), L = (z, I, $, Y, te, re, pe = 0) => {
      X.setFromEuler(new s.Euler(0, 0, pe)), A.compose(Z.set(z, I, $), X, _.set(Y, te, re)), C.setMatrixAt(P++, A);
    };
    for (let z = k.x0 + 8; z < k.x1; z += 14) {
      L(z, 14 - 0.4, l, 0.5, 0.5, r), L(z, 14 - 2.6, l, 0.35, 0.35, r);
      for (let I = k.z0; I < k.z1; I += 4)
        L(z, 14 - 1.5, I, 0.18, 2.4, 0.18);
    }
    for (let z = k.z0 + 6; z < k.z1; z += 12) L(a, 14 - 2.6, z, i, 0.25, 0.25);
    C.count = P, B.add(C);
    let F = (z, I, $, Y, te, re) => {
      let pe = new s.Mesh(new s.BoxGeometry(z, 0.18, 0.18), new s.MeshStandardMaterial({ color: re, emissive: re, emissiveIntensity: 3.2 }));
      pe.position.set(I, $, Y), pe.rotation.y = te, B.add(pe);
    };
    F(i - 4, a, 3.2, k.z0 + 0.3, 0, n.green), F(i - 4, a, 3.2, k.z1 - 0.3, 0, n.pink), F(r - 4, k.x0 + 0.3, 3.2, l, Math.PI / 2, n.violet), F(r - 4, k.x1 - 0.3, 3.2, l, Math.PI / 2, n.blue), F(i - 4, a, 10.5, k.z0 + 0.3, 0, n.blue), F(i - 4, a, 10.5, k.z1 - 0.3, 0, n.violet);
    let S = new s.MeshStandardMaterial({ color: 1778752, roughness: 0.6, metalness: 0.4 });
    for (let [z, I] of [[-20, -22], [46, -14], [30, 26], [-12, 10]]) {
      let $ = new s.Mesh(new s.BoxGeometry(1.1, 14, 1.1), S);
      $.position.set(z, 14 / 2, I), B.add($);
      let Y = new s.Mesh(new s.BoxGeometry(1.25, 0.15, 1.25), new s.MeshStandardMaterial({ color: n.violet, emissive: n.violet, emissiveIntensity: 3 }));
      Y.position.set(z, 2.4, I), B.add(Y);
    }
  }
  {
    let o = new s.CylinderGeometry(0.42, 0.42, 0.34, 14), f = new s.MeshStandardMaterial({ color: 1118484, roughness: 0.85 }), i = new s.InstancedMesh(o, f, 2400), r = 0, a = new s.Matrix4();
    for (let Z of [-1, 1])
      for (let L = 0; L < x; L += 2) {
        let F = Z * (E + 0.9), S = u.x[L] + u.nx[L] * F, z = u.z[L] + u.nz[L] * F, I = lt(S, z, -1);
        if (!(Math.hypot(u.x[I] - S, u.z[I] - z) < E + 0.5))
          for (let $ = 0; $ < 2; $++)
            a.makeTranslation(S, 0.17 + $ * 0.34, z), r < 2400 && i.setMatrixAt(r++, a);
      }
    i.count = r, B.add(i);
    let l = new s.BoxGeometry(1.02, 0.36, 0.5), h = new s.InstancedMesh(l, new s.MeshStandardMaterial({ color: 16762910, roughness: 0.45, emissive: 3811840 }), 1200), M = new s.InstancedMesh(l, new s.MeshStandardMaterial({ color: 1381658, roughness: 0.5 }), 1200), H = 0, C = 0, P = new s.Quaternion(), A = new s.Vector3(0, 1, 0), X = new s.Vector3(), _ = new s.Vector3(1, 1, 1);
    for (let Z of [-1, 1])
      for (let L = 0; L < x; L += 2) {
        let F = Z * (E + 0.85), S = u.x[L] + u.nx[L] * F, z = u.z[L] + u.nz[L] * F, I = lt(S, z, -1);
        Math.hypot(u.x[I] - S, u.z[I] - z) < E + 0.5 || (P.setFromAxisAngle(A, Math.atan2(u.tx[L], u.tz[L]) + Math.PI / 2), a.compose(X.set(S, 0.86, z), P, _), Math.floor(L / 4) % 2 ? H < 1200 && h.setMatrixAt(H++, a) : C < 1200 && M.setMatrixAt(C++, a));
      }
    h.count = H, M.count = C, B.add(h, M);
  }
  function Rs(o, f) {
    return ne(512, 200, (i, r, a) => {
      i.fillStyle = "#0a0a12", i.fillRect(0, 0, r, a), i.strokeStyle = d(o), i.lineWidth = 16, i.lineCap = "round", i.lineJoin = "round", i.shadowColor = d(o), i.shadowBlur = 24;
      for (let l = 0; l < 4; l++) {
        let h = 70 + l * 110;
        i.beginPath(), f ? (i.moveTo(h, 34), i.lineTo(h + 50, a / 2), i.lineTo(h, a - 34)) : (i.moveTo(h + 50, 34), i.lineTo(h, a / 2), i.lineTo(h + 50, a - 34)), i.stroke();
      }
      i.shadowBlur = 0, i.strokeStyle = d(o), i.lineWidth = 6, i.strokeRect(6, 6, r - 12, a - 12);
    });
  }
  let ft = {};
  for (let o of Xe) {
    let f = O(o.idx * g, -o.inner * (E + 2.2)), i = f.nx * o.inner, r = f.nz * o.inner, a = -f.tx + i * 0.9, l = -f.tz + r * 0.9, h = Math.hypot(a, l);
    a /= h, l /= h;
    let M = Math.atan2(a, l), H = Math.cos(M), C = -Math.sin(M), P = H * i + C * r > 0, A = o.color + "_" + P;
    ft[A] || (ft[A] = Rs(o.color, P));
    let X = ft[A], _ = new s.Mesh(new s.PlaneGeometry(4.2, 1.65), new s.MeshStandardMaterial({ map: X, emissive: 16777215, emissiveMap: X, emissiveIntensity: 2.4, roughness: 0.6 }));
    _.position.set(f.x, 1.75, f.z), _.rotation.y = M, B.add(_);
    let Z = new s.Mesh(new s.BoxGeometry(4.4, 1.85, 0.12), new s.MeshStandardMaterial({ color: 789524, roughness: 0.7 }));
    Z.position.set(f.x - a * 0.08, 1.75, f.z - l * 0.08), Z.rotation.y = M, B.add(Z);
    for (let L of [-1.9, 1.9]) {
      let F = new s.Mesh(new s.BoxGeometry(0.12, 1, 0.12), new s.MeshStandardMaterial({ color: 3355456 }));
      F.position.set(f.x + H * L - a * 0.15, 0.5, f.z + C * L - l * 0.15), B.add(F);
    }
  }
  let Re = new s.TextureLoader().load("assets/logo.png");
  Re.colorSpace = s.SRGBColorSpace, Re.anisotropy = 8;
  function Qe(o, f, i, r, a) {
    let l = a * 667 / 1024, h = new s.Mesh(new s.PlaneGeometry(a * 1.08, l * 1.08), new s.MeshBasicMaterial({ color: 722710 }));
    h.position.set(o, f, i), h.rotation.y = r, B.add(h);
    let M = new s.Mesh(new s.PlaneGeometry(a, l), new s.MeshStandardMaterial({ map: Re, transparent: !0, emissive: 16777215, emissiveMap: Re, emissiveIntensity: 0.6, roughness: 1 }));
    M.position.set(o, f, i), M.rotation.y = r, M.translateZ(0.02), B.add(M);
    let H = new s.Mesh(new s.TorusGeometry(1, 0.03, 4, 4), new s.MeshBasicMaterial({ color: n.violet }));
    return M;
  }
  Qe(0, 8, k.z0 + 0.2, 0, 22), Qe(k.x0 + 0.2, 8, 10, Math.PI / 2, 20), Qe(-10, 8, k.z1 - 0.2, Math.PI, 22);
  {
    Qe(k.x1 - 0.25, 7.5, -30, -Math.PI / 2, 24);
    let o = ne(1024, 128, (i, r, a) => {
      i.clearRect(0, 0, r, a), i.font = "italic 900 88px system-ui, Arial", i.textAlign = "center", i.textBaseline = "middle", i.fillStyle = "#29d9ff", i.shadowColor = "#29d9ff", i.shadowBlur = 22, i.fillText("НЕОНОВАЯ ГОНКА", r / 2, a / 2);
    }), f = new s.Mesh(new s.PlaneGeometry(20, 2.5), new s.MeshStandardMaterial({ map: o, transparent: !0, emissive: 16777215, emissiveMap: o, emissiveIntensity: 1.8 }));
    f.position.set(k.x1 - 0.3, 1.9, -30), f.rotation.y = -Math.PI / 2, B.add(f);
  }
  function bs(o, f, i = 1024, r = 160, a = "900 110px system-ui, Arial") {
    return ne(i, r, (l, h, M) => {
      l.clearRect(0, 0, h, M), l.font = a, l.textAlign = "center", l.textBaseline = "middle", l.shadowColor = f, l.shadowBlur = 18, l.fillStyle = f, l.fillText(o, h / 2, M / 2 + 6);
    });
  }
  Hs();
  function gs(o, f, i, r) {
    return ne(256, 320, (a, l, h) => {
      let M = a.createLinearGradient(0, 0, l, h);
      M.addColorStop(0, i), M.addColorStop(1, r), a.fillStyle = M, a.fillRect(0, 0, l, h), a.fillStyle = "rgba(255,255,255,.18)", a.beginPath(), a.arc(l * 0.7, h * 0.35, 70, 0, 7), a.fill(), a.fillStyle = "#fff", a.font = "900 44px system-ui, Arial", a.textAlign = "center", a.fillText(o, l / 2, h - 90), a.font = "600 22px system-ui, Arial", a.fillText(f, l / 2, h - 52);
    });
  }
  function Hs() {
    let o = new s.Group();
    o.position.set(17, 0, -24), B.add(o);
    let f = new s.MeshStandardMaterial({ color: 1746326, roughness: 0.5, metalness: 0.15 }), i = new s.MeshStandardMaterial({ color: 1276528, roughness: 0.6 }), r = new s.MeshStandardMaterial({ color: 15659765, roughness: 0.35, metalness: 0.1 }), a = new s.MeshStandardMaterial({ color: 795187, roughness: 0.3, metalness: 0.7, emissive: 666180, emissiveIntensity: 0.6 }), l = (S, z, I, $, Y, te = 0) => {
      let re = new s.Mesh(S, z);
      return re.position.set(I, $, Y), re.rotation.y = te, o.add(re), re;
    }, h = [["ЛЕТО", "в Сибае", "#ff7a2a", "#ff2bd6"], ["КИНО", "премьеры", "#2a6bff", "#29d9ff"], ["КАРТИНГ", "клуб", "#a046ff", "#ff2bd6"], ["КОНЦЕРТ", "суббота", "#16b38a", "#4dff7a"]], M = 0;
    for (let [S, z] of [[-11.5, 13], [11.5, 13]]) {
      l(new s.BoxGeometry(z, 6, 7), f, S, 3, 0), l(new s.BoxGeometry(z + 0.4, 0.7, 7.4), r, S, 6.35, 0), l(new s.BoxGeometry(z + 0.1, 0.6, 7.1), i, S, 0.3, 0), l(new s.BoxGeometry(z - 1.2, 1.3, 0.12), a, S, 4.7, -3.55);
      for (let I of [-3.2, 3.2]) {
        let $ = h[M++ % 4], Y = gs($[0], $[1], $[2], $[3]), te = l(new s.PlaneGeometry(2.8, 3.4), new s.MeshStandardMaterial({ map: Y, emissive: 16777215, emissiveMap: Y, emissiveIntensity: 0.55, roughness: 0.6 }), S + I, 2.2, -3.57, Math.PI);
        l(new s.BoxGeometry(3, 3.6, 0.08), r, S + I, 2.2, -3.52);
      }
    }
    l(new s.BoxGeometry(5, 7.6, 6.5), new s.MeshStandardMaterial({ color: 14278371, roughness: 0.5 }), 20.5, 3.8, 0.4), l(new s.BoxGeometry(3.2, 5.4, 0.12), a, 20.5, 4.2, -2.9), l(new s.BoxGeometry(10, 6.8, 6), a, 0, 3.4, 0.6);
    {
      let S = new s.CylinderGeometry(5, 5, 6.5, 40, 1, !0, -Math.PI / 2, Math.PI);
      S.rotateX(-Math.PI / 2);
      let z = new s.Mesh(S, new s.MeshStandardMaterial({ color: 15922679, roughness: 0.3, metalness: 0.2, side: s.DoubleSide }));
      z.position.set(0, 6.4, -0.6), z.scale.set(1, 0.62, 1), o.add(z);
    }
    let H = new s.Group();
    H.position.set(0, 6.4, -3.9), H.scale.set(1, 0.62, 1), o.add(H);
    let C = new s.TorusGeometry(5, 0.2, 8, 48, Math.PI);
    H.add(new s.Mesh(C, r)), H.add(new s.Mesh(new s.CircleGeometry(1, 24, 0, Math.PI), r));
    for (let S = 0; S <= 10; S++) {
      let z = S / 10 * Math.PI, I = new s.Mesh(new s.BoxGeometry(4, 0.16, 0.16), r);
      I.position.set(Math.cos(z) * 3, Math.sin(z) * 3, 0), I.rotation.z = z, H.add(I);
    }
    let P = new s.Mesh(new s.CircleGeometry(4.9, 40, 0, Math.PI), new s.MeshStandardMaterial({ color: 727592, roughness: 0.35, metalness: 0.7, emissive: 1450042 }));
    P.position.z = 0.05, H.add(P);
    let A = new s.Mesh(new s.TorusGeometry(5.25, 0.07, 6, 48, Math.PI), new s.MeshStandardMaterial({ color: n.pink, emissive: n.pink, emissiveIntensity: 2.6 }));
    H.add(A);
    for (let S of [-4.4, -1.5, 1.5, 4.4]) l(new s.CylinderGeometry(0.24, 0.24, 6.4, 14), r, S, 3.2, -3.9);
    for (let S = 0; S < 3; S++) l(new s.BoxGeometry(11 - S * 0.8, 0.22, 1), new s.MeshStandardMaterial({ color: 10658472, roughness: 0.9 }), 0, 0.11 + S * 0.22, -4.6 + S * 0.45);
    let X = (S, z, I) => {
      let $ = bs(S, "#ff2a3a", 1024, 160, "900 112px system-ui, Arial");
      l(new s.PlaneGeometry(I, I * 160 / 1024), new s.MeshStandardMaterial({ map: $, transparent: !0, emissive: 16777215, emissiveMap: $, emissiveIntensity: 2, side: s.DoubleSide }), z, 7.6, -3, Math.PI), l(new s.BoxGeometry(I * 0.9, 0.08, 0.08), new s.MeshStandardMaterial({ color: 1365 }), z, 6.9, -3);
    };
    X("УРАЛ АРЬЯҒЫ", -11.5, 10.5), X("★ ЗАУРАЛЬЕ", 11.5, 10.5);
    let _ = new s.MeshStandardMaterial({ color: 2829619, metalness: 0.7, roughness: 0.4 }), Z = new s.MeshStandardMaterial({ color: 16774102, emissive: 16769704, emissiveIntensity: 2.2 }), L = new s.MeshStandardMaterial({ color: 3112248, roughness: 0.9 }), F = new s.MeshStandardMaterial({ color: 4862754 });
    for (let S of [-22, -14, -6, 6, 14, 22])
      l(new s.CylinderGeometry(0.07, 0.1, 3.6, 8), _, S, 1.8, -5.8), l(new s.SphereGeometry(0.28, 14, 10), Z, S, 3.75, -5.8);
    for (let S of [-25.5, 26.5])
      l(new s.SphereGeometry(2, 14, 12), L, S, 3.2, -2.5), l(new s.CylinderGeometry(0.18, 0.25, 2.2), F, S, 1.1, -2.5);
    for (let S of [-18, -10, 10, 18])
      l(new s.BoxGeometry(2.4, 0.5, 1), new s.MeshStandardMaterial({ color: 6179386, roughness: 0.8 }), S, 0.25, -5), l(new s.SphereGeometry(0.55, 10, 8), new s.MeshStandardMaterial({ color: [16732043, 16762938, 10503935, 2742783][(S + 18) / 8 | 0], roughness: 0.8 }), S, 0.7, -5);
  }
  {
    let o = new s.MeshStandardMaterial({ color: 2829619, metalness: 0.7, roughness: 0.4 }), f = new s.MeshStandardMaterial({ color: 16774102, emissive: 16769704, emissiveIntensity: 2.2 });
    for (let r = -4; r <= 40; r += 8) {
      let a = new s.Mesh(new s.CylinderGeometry(0.07, 0.1, 3.6, 8), o);
      a.position.set(r, 1.8, -45), B.add(a);
      let l = new s.Mesh(new s.SphereGeometry(0.28, 14, 10), f);
      l.position.set(r, 3.75, -45), B.add(l);
    }
    let i = new s.MeshStandardMaterial({ color: 3112248, roughness: 0.9 });
    for (let r of [0, 16, 32]) {
      let a = new s.Mesh(new s.SphereGeometry(1.8, 14, 12), i);
      a.position.set(r + 4, 2.9, -48), B.add(a);
      let l = new s.Mesh(new s.CylinderGeometry(0.16, 0.22, 2), new s.MeshStandardMaterial({ color: 4862754 }));
      l.position.set(r + 4, 1, -48), B.add(l);
    }
  }
  let me = { x: -30, z: 26 };
  {
    let o = new s.Mesh(new s.CylinderGeometry(3.2, 3.4, 0.35, 48), new s.MeshStandardMaterial({ color: 1315356, roughness: 0.32, metalness: 0.7 }));
    o.position.set(me.x, 0.17, me.z), B.add(o);
    let f = new s.Mesh(new s.TorusGeometry(3.3, 0.04, 8, 64), new s.MeshStandardMaterial({ color: n.violet, emissive: n.violet, emissiveIntensity: 1.4 }));
    f.rotation.x = Math.PI / 2, f.position.set(me.x, 0.36, me.z), B.add(f);
    let i = new s.SpotLight(16777215, 260, 30, 0.45, 0.5, 1.2);
    i.position.set(me.x + 2, 9, me.z - 3), i.target.position.set(me.x, 0, me.z), B.add(i, i.target);
  }
  let _t = [];
  {
    let o = O(0), f = Math.atan2(o.tx, o.tz), i = new s.Group();
    i.position.set(o.x, 0, o.z), i.rotation.y = f, B.add(i);
    let r = new s.MeshStandardMaterial({ color: 1315868, metalness: 0.6, roughness: 0.4 });
    for (let h of [-E - 1.6, E + 1.6]) {
      let M = new s.Mesh(new s.BoxGeometry(0.5, 6.2, 0.5), r);
      M.position.set(h, 3.1, 0), i.add(M);
      let H = new s.Mesh(new s.BoxGeometry(0.12, 6, 0.12), new s.MeshStandardMaterial({ color: n.violet, emissive: n.violet, emissiveIntensity: 3 }));
      H.position.set(h + (h < 0 ? 0.3 : -0.3), 3, -0.28), i.add(H);
    }
    let a = new s.Mesh(new s.BoxGeometry(m + 4, 1.8, 0.5), r);
    a.position.set(0, 6.4, 0), i.add(a);
    let l = new s.Mesh(new s.PlaneGeometry(4.4, 4.4 * 667 / 1024), new s.MeshStandardMaterial({ map: Re, transparent: !0, emissive: 16777215, emissiveMap: Re, emissiveIntensity: 1.6 }));
    l.position.set(-3.6, 6.4, -0.27), l.rotation.y = Math.PI, i.add(l);
    for (let h = 0; h < 5; h++) {
      let M = new s.Mesh(new s.CircleGeometry(0.34, 18), new s.MeshStandardMaterial({ color: 2228224, emissive: 0, emissiveIntensity: 4 }));
      M.position.set(1 + h * 0.9, 6.4, -0.27), M.rotation.y = Math.PI, i.add(M), _t.push(M);
    }
  }
  function Ss(o) {
    return ne(128, 96, (f, i, r) => {
      f.fillStyle = "#f2f2f2", f.fillRect(0, 0, i, r), f.fillStyle = "#111", f.font = "900 78px Arial", f.textAlign = "center", f.textBaseline = "middle", f.fillText(String(o), i / 2, r / 2 + 4);
    });
  }
  function Bt(o, f, i) {
    let r = new s.Shape(), a = -o / 2, l = -f / 2;
    return r.moveTo(a + i, l), r.lineTo(a + o - i, l), r.quadraticCurveTo(a + o, l, a + o, l + i), r.lineTo(a + o, l + f - i), r.quadraticCurveTo(a + o, l + f, a + o - i, l + f), r.lineTo(a + i, l + f), r.quadraticCurveTo(a, l + f, a, l + f - i), r.lineTo(a, l + i), r.quadraticCurveTo(a, l, a + i, l), r;
  }
  let zs = (() => {
    let o = Bt(1.75, 2.75, 0.55), f = new s.Path(), i = Bt(1.45, 2.45, 0.42);
    f.setFromPoints(i.getPoints(24).reverse()), o.holes.push(f);
    let r = new s.ExtrudeGeometry(o, { depth: 0.26, bevelEnabled: !0, bevelThickness: 0.03, bevelSize: 0.03, bevelSegments: 2, curveSegments: 16 });
    return r.rotateX(-Math.PI / 2), r;
  })(), qt = new s.CylinderGeometry(0.27, 0.27, 0.26, 18);
  qt.rotateZ(Math.PI / 2);
  let $t = new s.CylinderGeometry(0.15, 0.15, 0.27, 12);
  $t.rotateZ(Math.PI / 2);
  let Gs = ne(64, 64, (o) => {
    let f = o.createRadialGradient(32, 32, 0, 32, 32, 32);
    f.addColorStop(0, "rgba(0,0,0,.75)"), f.addColorStop(1, "rgba(0,0,0,0)"), o.fillStyle = f, o.fillRect(0, 0, 64, 64);
  }), ks = ne(64, 64, (o) => {
    let f = o.createRadialGradient(32, 32, 0, 32, 32, 32);
    f.addColorStop(0, "rgba(255,255,255,1)"), f.addColorStop(0.3, "rgba(255,255,255,.6)"), f.addColorStop(1, "rgba(255,255,255,0)"), o.fillStyle = f, o.fillRect(0, 0, 64, 64);
  });
  function Ps(o, f, i, r = 3124821) {
    let a = new s.Group(), l = new s.Group();
    a.add(l);
    let h = new s.MeshStandardMaterial({ color: 1447451, roughness: 0.55, metalness: 0.1 }), M = new s.MeshStandardMaterial({ color: 2763569, roughness: 0.5, metalness: 0.5 }), H = new s.MeshStandardMaterial({ color: i, roughness: 0.35, metalness: 0.2, emissive: i, emissiveIntensity: 0.25 }), C = new s.Mesh(zs, h);
    C.position.y = 0.16, l.add(C);
    let P = new s.Mesh(new s.BoxGeometry(1.78, 0.05, 2.5), new s.MeshStandardMaterial({ color: i, emissive: i, emissiveIntensity: 2.2 }));
    P.position.y = 0.2, P.scale.set(1, 1, 1), l.add(P);
    let A = new s.Mesh(new s.BoxGeometry(1.1, 0.1, 2.2), M);
    A.position.y = 0.26, l.add(A);
    let X = new s.Mesh(new s.BoxGeometry(0.9, 0.22, 0.6), h);
    X.position.set(0, 0.42, 0.9), X.rotation.x = -0.25, l.add(X);
    let _ = new s.Mesh(new s.PlaneGeometry(0.46, 0.34), new s.MeshStandardMaterial({ map: Ss(o), roughness: 0.6 }));
    _.position.set(0, 0.62, 0.78), _.rotation.x = -0.75, l.add(_);
    for (let Me of [-0.62, 0.62]) {
      let oe = new s.Mesh(new s.BoxGeometry(0.22, 0.2, 1), H);
      oe.position.set(Me, 0.4, -0.05), l.add(oe);
    }
    let Z = new s.Mesh(new s.BoxGeometry(0.6, 0.18, 0.55), h);
    Z.position.set(0, 0.42, -0.35), l.add(Z);
    let L = new s.Mesh(new s.BoxGeometry(0.6, 0.65, 0.12), h);
    L.position.set(0, 0.72, -0.62), L.rotation.x = -0.2, l.add(L);
    let F = new s.MeshStandardMaterial({ color: r, roughness: 0.3, metalness: 0.6 }), S = new s.CatmullRomCurve3([new s.Vector3(-0.32, 0.4, -0.7), new s.Vector3(-0.3, 1.05, -0.78), new s.Vector3(0.3, 1.05, -0.78), new s.Vector3(0.32, 0.4, -0.7)]);
    l.add(new s.Mesh(new s.TubeGeometry(S, 16, 0.035, 6), F));
    let z = new s.Mesh(new s.BoxGeometry(0.34, 0.34, 0.42), M);
    z.position.set(0.48, 0.5, -0.8), l.add(z);
    let I = new s.Mesh(new s.CylinderGeometry(0.025, 0.025, 0.7), M);
    I.position.set(0, 0.62, 0.32), I.rotation.x = 1, l.add(I);
    let $ = new s.Mesh(new s.TorusGeometry(0.17, 0.03, 6, 20), h);
    $.position.set(0, 0.82, 0.12), $.rotation.x = -0.9, l.add($);
    let Y = new s.MeshStandardMaterial({ color: f, roughness: 0.6 }), te = new s.Mesh(new s.CapsuleGeometry(0.22, 0.32, 4, 10), Y);
    te.position.set(0, 0.86, -0.42), te.rotation.x = -0.25, l.add(te);
    let re = new s.Mesh(new s.BoxGeometry(0.36, 0.18, 0.75), Y);
    re.position.set(0, 0.5, 0.1), l.add(re);
    let pe = new s.Mesh(new s.SphereGeometry(0.24, 18, 14), new s.MeshStandardMaterial({ color: i, roughness: 0.28, metalness: 0.4 }));
    pe.position.set(0, 1.32, -0.36), l.add(pe);
    let Nt = new s.Mesh(new s.SphereGeometry(0.245, 16, 10, -0.9, 1.8, 1.1, 0.7), new s.MeshStandardMaterial({ color: 328970, roughness: 0.22, metalness: 0.8 }));
    Nt.position.copy(pe.position), l.add(Nt);
    for (let Me of [-1, 1]) {
      let oe = new s.Mesh(new s.CapsuleGeometry(0.06, 0.38, 3, 6), Y);
      oe.position.set(Me * 0.2, 0.95, -0.08), oe.rotation.set(1.15, 0, -Me * 0.35), l.add(oe);
    }
    let $s = new s.MeshStandardMaterial({ color: 789518, roughness: 0.8 }), Fs = new s.MeshStandardMaterial({ color: 12106948, roughness: 0.3, metalness: 0.9 }), Kt = [];
    for (let [Me, oe, Qt] of [[-0.66, 0.78, 1], [0.66, 0.78, 1], [-0.7, -0.78, 1.25], [0.7, -0.78, 1.25]]) {
      let _e = new s.Group();
      _e.position.set(Me, 0.27, oe);
      let jt = new s.Mesh(qt, $s);
      jt.scale.x = Qt, _e.add(jt);
      let Ut = new s.Mesh($t, Fs);
      Ut.scale.x = Qt * 1.02, _e.add(Ut), a.add(_e), Kt.push(_e);
    }
    let ht = new s.Mesh(new s.PlaneGeometry(2.4, 3.2), new s.MeshBasicMaterial({ map: Gs, transparent: !0, depthWrite: !1 }));
    ht.rotation.x = -Math.PI / 2, ht.position.y = 0.02, a.add(ht);
    let Xt = [];
    for (let Me of [-0.7, 0.7]) {
      let oe = new s.Sprite(new s.SpriteMaterial({ map: ks, color: 6737151, blending: s.AdditiveBlending, depthWrite: !1, transparent: !0 }));
      oe.position.set(Me, 0.2, -1.15), oe.scale.setScalar(0.01), a.add(oe), Xt.push(oe);
    }
    let Ae = new s.Mesh(new s.ConeGeometry(0.16, 0.9, 10), new s.MeshBasicMaterial({ color: 6742271, transparent: !0, opacity: 0.85, blending: s.AdditiveBlending, depthWrite: !1 }));
    return Ae.rotation.x = -Math.PI / 2, Ae.position.set(0.48, 0.5, -1.3), Ae.visible = !1, a.add(Ae), a.userData = { body: l, wheels: Kt, sparks: Xt, flame: Ae }, a;
  }
  let dt = [], Ft = ne(128, 128, (o, f, i) => {
    o.fillStyle = "rgba(20,10,40,.6)", o.fillRect(0, 0, f, i), o.strokeStyle = "#fff", o.lineWidth = 8, o.strokeRect(6, 6, f - 12, i - 12), o.fillStyle = "#fff", o.font = "900 86px Arial", o.textAlign = "center", o.textBaseline = "middle", o.fillText("?", f / 2, i / 2 + 4);
  }), Cs = new s.BoxGeometry(1.1, 1.1, 1.1);
  for (let o of [0.1, 0.4, 0.66, 0.88])
    for (let f of [-3.3, -1.1, 1.1, 3.3]) {
      let i = O(o * R, f), r = new s.MeshStandardMaterial({ map: Ft, color: 16777215, emissive: 16777215, emissiveMap: Ft, emissiveIntensity: 1.6, transparent: !0, opacity: 0.92 }), a = new s.Mesh(Cs, r);
      a.position.set(i.x, 1, i.z), B.add(a), dt.push({ type: "box", mesh: a, s: o * R, off: f, x: i.x, z: i.z, respawn: 0 });
    }
  let Dt = new s.CylinderGeometry(0.42, 0.42, 0.08, 20);
  Dt.rotateX(Math.PI / 2);
  let Ls = new s.MeshStandardMaterial({ color: 16762938, emissive: 16752640, emissiveIntensity: 0.45, metalness: 0.9, roughness: 0.25 });
  for (let [o, f] of [[0.03, "line"], [0.2, "wave"], [0.32, "line"], [0.5, "wave"], [0.6, "line"], [0.76, "wave"], [0.95, "line"]])
    for (let i = 0; i < 6; i++) {
      let r = o * R + i * 2.6, a = f === "line" ? o * 100 % 2 > 1 ? 2.5 : -2.5 : Math.sin(i * 0.9) * 3, l = O(r, a), h = new s.Mesh(Dt, Ls);
      h.position.set(l.x, 0.75, l.z), B.add(h), dt.push({ type: "coin", mesh: h, s: r, off: a, x: l.x, z: l.z, respawn: 0 });
    }
  let Is = ne(128, 256, (o, f, i) => {
    o.fillStyle = "rgba(0,0,0,0)", o.clearRect(0, 0, f, i), o.strokeStyle = "#fff", o.lineWidth = 14, o.lineCap = "round";
    for (let r = 0; r < 3; r++) {
      let a = 200 - r * 70;
      o.beginPath(), o.moveTo(18, a), o.lineTo(64, a - 46), o.lineTo(110, a), o.stroke();
    }
  }), Ot = [];
  for (let [o, f] of [[0.27, 2.2], [0.55, -2.2], [0.82, 2.2], [0.985, -2.4]]) {
    let i = O(o * R, f), r = new s.Mesh(new s.PlaneGeometry(2.6, 4.2), new s.MeshBasicMaterial({ map: Is, color: n.violet, transparent: !0, blending: s.AdditiveBlending, depthWrite: !1 }));
    r.rotation.x = -Math.PI / 2, r.rotation.z = Math.atan2(i.tx, i.tz) + Math.PI, r.position.set(i.x, 0.03, i.z), B.add(r);
    let a = new s.Mesh(new s.PlaneGeometry(2.8, 4.4), new s.MeshBasicMaterial({ color: 2755157, transparent: !0, opacity: 0.8 }));
    a.rotation.copy(r.rotation), a.position.set(i.x, 0.025, i.z), B.add(a), Ot.push({ s: o * R, off: f, x: i.x, z: i.z, mesh: r });
  }
  let Wt = [], Vt = [], As = ne(128, 128, (o) => {
    let f = o.createRadialGradient(64, 64, 4, 64, 64, 60);
    f.addColorStop(0, "rgba(10,0,30,.95)"), f.addColorStop(0.7, "rgba(60,20,120,.85)"), f.addColorStop(1, "rgba(160,70,255,0)"), o.fillStyle = f, o.beginPath();
    for (let i = 0; i < 6.3; i += 0.4) {
      let r = 46 + Math.random() * 14;
      o.lineTo(64 + Math.cos(i) * r, 64 + Math.sin(i) * r);
    }
    o.fill();
  });
  function _s(o, f, i) {
    let r = new s.Mesh(new s.PlaneGeometry(2.4, 2.4), new s.MeshBasicMaterial({ map: As, transparent: !0, depthWrite: !1 }));
    r.rotation.x = -Math.PI / 2, r.position.set(o, 0.04, f), B.add(r), Wt.push({ x: o, z: f, owner: i, mesh: r, life: 25, safe: 0.6 });
  }
  let Bs = new s.TorusGeometry(0.32, 0.16, 10, 18);
  function qs(o, f) {
    let i = new s.Mesh(Bs, new s.MeshStandardMaterial({ color: 1118481, emissive: n.green, emissiveIntensity: 0.6, roughness: 0.6 }));
    B.add(i), Vt.push({ owner: o, target: f, d: o.d + 2, off: o.off ?? 0, mesh: i, life: 6 });
  }
  return { COLORS: n, NEON: c, hex: d, T: u, M: x, L: R, DS: g, TRACK_W: m, HALF_W: E, HALL: k, trackAt: O, nearestIdx: lt, wrapS: U, world: B, startLights: _t, makeKart: Ps, pickups: dt, pads: Ot, hazards: Wt, projectiles: Vt, dropOil: _s, throwTire: qs, canvasTex: ne, SHOW: me, logoTex: Re };
}

// audio.js
var J = (e) => 440 * Math.pow(2, (e - 69) / 12), je = class {
  constructor() {
    this.ctx = null, this.musicOn = !0, this.sfxOn = !0, this.musicMode = "off";
  }
  init() {
    if (this.ctx) {
      this.ctx.state === "suspended" && this.ctx.resume();
      return;
    }
    let t;
    try {
      t = new (window.AudioContext || window.webkitAudioContext)();
    } catch {
      return;
    }
    this.ctx = t;
    let n = t.createDynamicsCompressor();
    n.threshold.value = -14, n.knee.value = 10, n.ratio.value = 4, n.attack.value = 4e-3, n.release.value = 0.18, this.master = t.createGain(), this.master.gain.value = 0.9, this.master.connect(n), n.connect(t.destination), this.sfx = t.createGain(), this.sfx.gain.value = this.sfxOn ? 1 : 0, this.sfx.connect(this.master), this.music = t.createGain(), this.music.gain.value = this.musicOn ? 0.34 : 0, this.music.connect(this.master), this.reverb = t.createConvolver(), this.reverb.buffer = this._impulse(1.8, 2.6), this.revSend = t.createGain(), this.revSend.gain.value = 0.32, this.revSend.connect(this.reverb), this.reverb.connect(this.master);
    let c = t.createBuffer(1, t.sampleRate * 2, t.sampleRate), d = c.getChannelData(0);
    for (let p = 0; p < d.length; p++) d[p] = Math.random() * 2 - 1;
    this.noiseBuf = c, this._buildEngine(), this._buildMusicBus();
  }
  _impulse(t, n) {
    let c = this.ctx, d = c.sampleRate * t, p = c.createBuffer(2, d, c.sampleRate);
    for (let m = 0; m < 2; m++) {
      let E = p.getChannelData(m);
      for (let y = 0; y < d; y++) E[y] = (Math.random() * 2 - 1) * Math.pow(1 - y / d, n);
    }
    return p;
  }
  _noise(t = !0) {
    let n = this.ctx.createBufferSource();
    return n.buffer = this.noiseBuf, n.loop = t, n;
  }
  setMusic(t) {
    this.musicOn = t, this.ctx && this.music.gain.setTargetAtTime(t ? 0.34 : 0, this.ctx.currentTime, 0.2);
  }
  setSfx(t) {
    this.sfxOn = t, this.ctx && this.sfx.gain.setTargetAtTime(t ? 1 : 0, this.ctx.currentTime, 0.05);
  }
  // ------------------------------------------------------------ engine / skid / wind
  _buildEngine() {
    let t = this.ctx, n = t.createWaveShaper(), c = new Float32Array(1024);
    for (let E = 0; E < 1024; E++) {
      let y = E / 512 - 1;
      c[E] = Math.tanh(y * 2.6);
    }
    n.curve = c, this.engFilter = t.createBiquadFilter(), this.engFilter.type = "lowpass", this.engFilter.frequency.value = 600, this.engFilter.Q.value = 3.5, this.engGain = t.createGain(), this.engGain.gain.value = 0, this.eo1 = t.createOscillator(), this.eo1.type = "sawtooth", this.eo2 = t.createOscillator(), this.eo2.type = "sawtooth", this.eo2.detune.value = 14, this.eo3 = t.createOscillator(), this.eo3.type = "square";
    let d = t.createGain();
    d.gain.value = 0.45, this.am = t.createGain(), this.am.gain.value = 0.7, this.lfo = t.createOscillator(), this.lfo.type = "square";
    let p = t.createGain();
    p.gain.value = 0.3, this.lfo.connect(p), p.connect(this.am.gain), this.eo1.connect(this.am), this.eo2.connect(this.am), this.eo3.connect(d), d.connect(this.am), this.am.connect(n), n.connect(this.engFilter), this.engFilter.connect(this.engGain), this.engGain.connect(this.sfx);
    let m = t.createGain();
    m.gain.value = 0.12, this.engGain.connect(m), m.connect(this.revSend), [this.eo1, this.eo2, this.eo3, this.lfo].forEach((E) => E.start()), this.skid = this._noise(), this.skidF = t.createBiquadFilter(), this.skidF.type = "bandpass", this.skidF.frequency.value = 1500, this.skidF.Q.value = 2.2, this.skidG = t.createGain(), this.skidG.gain.value = 0, this.skid.connect(this.skidF), this.skidF.connect(this.skidG), this.skidG.connect(this.sfx), this.skid.start(), this.wind = this._noise(), this.windF = t.createBiquadFilter(), this.windF.type = "lowpass", this.windF.frequency.value = 400, this.windG = t.createGain(), this.windG.gain.value = 0, this.wind.connect(this.windF), this.windF.connect(this.windG), this.windG.connect(this.sfx), this.wind.start(), this.rpm = 0, this.gear = 0, this.shiftDip = 0;
  }
  // speed01: 0..1 of top speed, throttle 0..1, drift level -1(off)/0..3, boost bool
  updateEngine(t, n, c, d, p, m) {
    if (!this.ctx) return;
    let E = this.ctx.currentTime;
    if (!p) {
      this.engGain.gain.setTargetAtTime(0, E, 0.08), this.skidG.gain.setTargetAtTime(0, E, 0.05), this.windG.gain.setTargetAtTime(0, E, 0.1);
      return;
    }
    let y = [0, 0.2, 0.42, 0.66, 0.9, 1.3], w = 0;
    for (; w < y.length - 2 && t > y[w + 1]; ) w++;
    w > this.gear && n > 0.5 && (this.shiftDip = 0.12), this.gear = w;
    let u = 0.28 + 0.72 * Math.min(1, Math.max(0, (t - y[w]) / (y[w + 1] - y[w])));
    n < 0.2 && (u *= 0.85), this.shiftDip > 0 && (this.shiftDip -= m, u *= 0.72), this.rpm += (u - this.rpm) * Math.min(1, m * 9);
    let x = 48 + this.rpm * 120 + w * 9 + (d ? 18 : 0);
    this.eo1.frequency.setTargetAtTime(x, E, 0.03), this.eo2.frequency.setTargetAtTime(x, E, 0.03), this.eo3.frequency.setTargetAtTime(x / 2, E, 0.03), this.lfo.frequency.setTargetAtTime(x / 4, E, 0.03), this.engFilter.frequency.setTargetAtTime(380 + this.rpm * 1700 + n * 600 + (d ? 900 : 0), E, 0.05), this.engGain.gain.setTargetAtTime(0.05 + 0.07 * n + 0.05 * this.rpm, E, 0.06);
    let R = c >= 0 ? 0.11 + c * 0.02 : 0;
    this.skidG.gain.setTargetAtTime(R, E, 0.04), this.skidF.frequency.setTargetAtTime(1300 + Math.max(0, c) * 350, E, 0.05), this.windG.gain.setTargetAtTime(Math.min(1.2, t) * 0.08 + (d ? 0.07 : 0), E, 0.1), this.windF.frequency.setTargetAtTime(300 + t * 900 + (d ? 1200 : 0), E, 0.1);
  }
  // ------------------------------------------------------------ helpers
  _tone({ type: t = "sine", f: n = 440, f2: c = null, t0: d = 0, dur: p = 0.2, vol: m = 0.2, attack: E = 5e-3, rev: y = 0.25, filter: w = null }) {
    if (!this.ctx) return;
    let g = this.ctx, u = g.currentTime + d, x = g.createOscillator();
    x.type = t, x.frequency.setValueAtTime(n, u), c && x.frequency.exponentialRampToValueAtTime(Math.max(20, c), u + p);
    let R = g.createGain();
    R.gain.setValueAtTime(1e-4, u), R.gain.exponentialRampToValueAtTime(m, u + E), R.gain.exponentialRampToValueAtTime(1e-4, u + p);
    let U = x;
    if (w) {
      let O = g.createBiquadFilter();
      O.type = w.type || "lowpass", O.frequency.value = w.f, O.Q.value = w.q || 0.7, x.connect(O), U = O;
    }
    if (U.connect(R), R.connect(this.sfx), y) {
      let O = g.createGain();
      O.gain.value = y, R.connect(O), O.connect(this.revSend);
    }
    x.start(u), x.stop(u + p + 0.05);
  }
  _noiseHit({ t0: t = 0, dur: n = 0.2, vol: c = 0.3, type: d = "lowpass", f: p = 1e3, f2: m = null, q: E = 0.8, rev: y = 0.2 }) {
    if (!this.ctx) return;
    let w = this.ctx, g = w.currentTime + t, u = this._noise(!1), x = w.createBiquadFilter();
    x.type = d, x.frequency.setValueAtTime(p, g), x.Q.value = E, m && x.frequency.exponentialRampToValueAtTime(m, g + n);
    let R = w.createGain();
    if (R.gain.setValueAtTime(c, g), R.gain.exponentialRampToValueAtTime(1e-4, g + n), u.connect(x), x.connect(R), R.connect(this.sfx), y) {
      let U = w.createGain();
      U.gain.value = y, R.connect(U), U.connect(this.revSend);
    }
    u.start(g, Math.random() * 1.5), u.stop(g + n + 0.05);
  }
  // ------------------------------------------------------------ UI sounds (soft, Apple-like)
  tap() {
    this._tone({ type: "sine", f: 1900, f2: 1300, dur: 0.035, vol: 0.09, rev: 0.05 });
  }
  select() {
    this._tone({ type: "sine", f: 880, dur: 0.09, vol: 0.09, rev: 0.15 }), this._tone({ type: "sine", f: 1320, t0: 0.05, dur: 0.14, vol: 0.08, rev: 0.2 });
  }
  back() {
    this._tone({ type: "sine", f: 1100, f2: 700, dur: 0.08, vol: 0.08, rev: 0.1 });
  }
  buy() {
    [0, 4, 7, 12].forEach((t, n) => this._tone({ type: "triangle", f: J(76 + t), t0: n * 0.06, dur: 0.35, vol: 0.12, rev: 0.4 })), this.coin(0.28);
  }
  error() {
    this._tone({ type: "square", f: 220, dur: 0.12, vol: 0.06, filter: { f: 900 } }), this._tone({ type: "square", f: 185, t0: 0.1, dur: 0.16, vol: 0.06, filter: { f: 900 } });
  }
  // ------------------------------------------------------------ race sounds
  coin(t = 0) {
    this._tone({ type: "square", f: J(83), t0: t, dur: 0.07, vol: 0.06, filter: { f: 5e3 }, rev: 0.1 }), this._tone({ type: "square", f: J(88), t0: t + 0.065, dur: 0.38, vol: 0.06, filter: { f: 5e3 }, rev: 0.35 }), this._tone({ type: "sine", f: J(100), t0: t + 0.065, dur: 0.3, vol: 0.04, rev: 0.3 });
  }
  itemRoll(t = 1) {
    for (let c = 0; c < 14; c++) {
      let d = (c / 14) ** 1.4 * t;
      this._tone({ type: "triangle", f: 900 + c * 60, t0: d, dur: 0.04, vol: 0.07, rev: 0.05 });
    }
  }
  itemGet() {
    [0, 4, 7, 11, 14].forEach((t, n) => this._tone({ type: "triangle", f: J(79 + t), t0: n * 0.045, dur: 0.3, vol: 0.09, rev: 0.45 })), this._noiseHit({ dur: 0.4, vol: 0.05, type: "highpass", f: 6e3, rev: 0.4 });
  }
  boost(t = 1) {
    this._noiseHit({ dur: 0.7 * t, vol: 0.28, type: "bandpass", f: 400, f2: 3800, q: 1.2, rev: 0.25 }), this._tone({ type: "sawtooth", f: 90, f2: 260, dur: 0.6 * t, vol: 0.12, filter: { f: 1800 }, rev: 0.2 }), this._tone({ type: "sine", f: 220, f2: 880, dur: 0.35, vol: 0.08, rev: 0.3 });
  }
  miniTurbo(t) {
    let n = [0, 72, 76, 79][t] || 72;
    this._tone({ type: "triangle", f: J(n), dur: 0.12, vol: 0.1, rev: 0.3 }), this._tone({ type: "triangle", f: J(n + 12), t0: 0.06, dur: 0.25, vol: 0.09, rev: 0.4 }), this.boost(0.6 + t * 0.25);
  }
  driftStage(t) {
    this._tone({ type: "sine", f: J(76 + t * 4), dur: 0.12, vol: 0.07, rev: 0.25 });
  }
  hop() {
    this._tone({ type: "sine", f: 240, f2: 420, dur: 0.09, vol: 0.12, rev: 0.05 }), this._noiseHit({ dur: 0.06, vol: 0.08, type: "lowpass", f: 900 });
  }
  wall(t = 1) {
    this._tone({ type: "sine", f: 140, f2: 45, dur: 0.28, vol: 0.4 * t, rev: 0.15 }), this._noiseHit({ dur: 0.18, vol: 0.25 * t, type: "lowpass", f: 1200, f2: 300, rev: 0.25 });
  }
  bump() {
    this._tone({ type: "sine", f: 200, f2: 80, dur: 0.14, vol: 0.25, rev: 0.1 }), this._noiseHit({ dur: 0.08, vol: 0.12, type: "bandpass", f: 1800, q: 1.5 });
  }
  spin() {
    this._tone({ type: "triangle", f: 820, f2: 160, dur: 0.75, vol: 0.14, rev: 0.3 }), this._noiseHit({ dur: 0.6, vol: 0.12, type: "bandpass", f: 2200, f2: 700, q: 3 });
  }
  oil() {
    this._noiseHit({ dur: 0.25, vol: 0.2, type: "lowpass", f: 700, f2: 200, rev: 0.2 }), this._tone({ type: "sine", f: 300, f2: 90, dur: 0.2, vol: 0.12 });
  }
  throwIt() {
    this._noiseHit({ dur: 0.35, vol: 0.2, type: "bandpass", f: 600, f2: 2400, q: 2, rev: 0.25 });
  }
  countBeep(t) {
    t ? ([72, 76, 79, 84].forEach((n) => this._tone({ type: "square", f: J(n), dur: 0.7, vol: 0.05, filter: { f: 4e3 }, rev: 0.5 })), this._tone({ type: "sine", f: J(84), dur: 0.8, vol: 0.15, rev: 0.5 })) : (this._tone({ type: "square", f: J(69), dur: 0.22, vol: 0.06, filter: { f: 3e3 }, rev: 0.4 }), this._tone({ type: "sine", f: J(69), dur: 0.3, vol: 0.14, rev: 0.4 }));
  }
  finalLap() {
    [0, 4, 7, 12, 7, 12].forEach((t, n) => this._tone({ type: "square", f: J(72 + t), t0: n * 0.09, dur: 0.18, vol: 0.06, filter: { f: 3500 }, rev: 0.4 }));
  }
  finish(t) {
    let n = t ? [0, 4, 7, 12, 16, 19, 24] : [0, 3, 7, 12];
    n.forEach((d, p) => this._tone({ type: "square", f: J(67 + d), t0: p * 0.1, dur: 0.3, vol: 0.06, filter: { f: 4e3 }, rev: 0.5 }));
    let c = n.length * 0.1;
    [0, 4, 7, 12].forEach((d) => this._tone({ type: "sawtooth", f: J(55 + d + (t ? 0 : -1)), t0: c, dur: 1.6, vol: 0.05, attack: 0.05, filter: { f: 2200 }, rev: 0.6 }));
  }
  caseTick(t) {
    this._tone({ type: "triangle", f: 1200 + t % 2 * 200, dur: 0.035, vol: 0.08, rev: 0.05 });
  }
  caseReveal(t) {
    [[0, 4, 7], [0, 4, 7, 11], [0, 4, 7, 11, 14], [0, 4, 7, 11, 14, 19]][t].forEach((c, d) => this._tone({ type: "triangle", f: J(72 + c), t0: d * 0.07, dur: 1.2, vol: 0.09, rev: 0.6 })), this._noiseHit({ dur: 1.2, vol: 0.08 + t * 0.03, type: "highpass", f: 5e3, rev: 0.6 }), t >= 2 && this._tone({ type: "sine", f: J(48), dur: 1.4, vol: 0.25, rev: 0.4 });
  }
  reward(t) {
    this._tone({ type: "square", f: J(84 + t % 5), dur: 0.05, vol: 0.04, filter: { f: 5e3 }, rev: 0.15 });
  }
  // ------------------------------------------------------------ music (synthwave)
  _buildMusicBus() {
    let t = this.ctx;
    this.delay = t.createDelay(1), this.delayFb = t.createGain(), this.delayFb.gain.value = 0.32, this.delayF = t.createBiquadFilter(), this.delayF.type = "lowpass", this.delayF.frequency.value = 2600, this.delay.connect(this.delayF), this.delayF.connect(this.delayFb), this.delayFb.connect(this.delay);
    let n = t.createGain();
    n.gain.value = 0.35, this.delayF.connect(n), n.connect(this.music), this.musicRev = t.createGain(), this.musicRev.gain.value = 0.35, this.musicRev.connect(this.reverb), this.step = 0, this.nextT = 0, this.timer = null;
  }
  startMusic(t) {
    this.ctx && this.musicMode !== t && (this.musicMode = t, this.bpm = t === "race" ? 124 : 100, this.delay.delayTime.value = 60 / this.bpm * 0.75, this.timer || (this.step = 0, this.nextT = this.ctx.currentTime + 0.08, this.timer = setInterval(() => this._schedule(), 25)));
  }
  stopMusic() {
    this.musicMode = "off", this.timer && (clearInterval(this.timer), this.timer = null);
  }
  _schedule() {
    let t = this.ctx, n = 60 / this.bpm / 4;
    for (; this.nextT < t.currentTime + 0.12; )
      this._playStep(this.step, this.nextT, n), this.nextT += n, this.step++;
  }
  _mNote(t, n, c, d, p, m, E = {}) {
    let y = this.ctx, w = y.createOscillator();
    w.type = t, w.frequency.value = J(n), E.detune && (w.detune.value = E.detune);
    let g = y.createBiquadFilter();
    g.type = "lowpass", g.frequency.setValueAtTime(m, c), g.Q.value = E.q || 1, E.env && g.frequency.exponentialRampToValueAtTime(Math.max(200, m * 0.25), c + d);
    let u = y.createGain(), x = E.attack || 5e-3;
    if (u.gain.setValueAtTime(1e-4, c), u.gain.linearRampToValueAtTime(p, c + x), u.gain.setTargetAtTime(1e-4, c + Math.max(x, d - (E.release || 0.05)), (E.release || 0.05) / 3), w.connect(g), g.connect(u), u.connect(this.music), E.delay && u.connect(this.delay), E.rev) {
      let R = y.createGain();
      R.gain.value = E.rev, u.connect(R), R.connect(this.musicRev);
    }
    w.start(c), w.stop(c + d + (E.release || 0.05) * 3 + 0.05);
  }
  _drum(t, n, c = 1) {
    let d = this.ctx;
    if (t === "kick") {
      let p = d.createOscillator();
      p.type = "sine", p.frequency.setValueAtTime(140, n), p.frequency.exponentialRampToValueAtTime(42, n + 0.14);
      let m = d.createGain();
      m.gain.setValueAtTime(0.9 * c, n), m.gain.exponentialRampToValueAtTime(1e-4, n + 0.32), p.connect(m), m.connect(this.music), p.start(n), p.stop(n + 0.35);
    } else {
      let p = this._noise(!1), m = d.createBiquadFilter();
      m.type = t === "hat" ? "highpass" : "bandpass", m.frequency.value = t === "hat" ? 7500 : 1800, m.Q.value = t === "hat" ? 0.7 : 0.9;
      let E = d.createGain(), y = t === "hat" ? 0.05 : 0.2;
      if (E.gain.setValueAtTime((t === "hat" ? 0.16 : 0.42) * c, n), E.gain.exponentialRampToValueAtTime(1e-4, n + y), p.connect(m), m.connect(E), E.connect(this.music), t === "snare") {
        let w = d.createGain();
        w.gain.value = 0.5, E.connect(w), w.connect(this.musicRev), this._mNote("triangle", 55, n, 0.08, 0.18, 2e3);
      }
      p.start(n, Math.random()), p.stop(n + y + 0.02);
    }
  }
  _playStep(t, n, c) {
    let d = this.musicMode === "race", p = Math.floor(t / 16) % 4, m = t % 16, E = [45, 41, 48, 43], y = [[57, 60, 64, 69], [53, 57, 60, 65], [55, 60, 64, 67], [55, 59, 62, 67]], w = E[p], g = y[p];
    if (m === 0 && g.forEach((x, R) => this._mNote("sawtooth", x, n, c * 16, d ? 0.035 : 0.05, d ? 1400 : 1100, { detune: R % 2 ? 9 : -9, attack: 0.35, release: 0.4, rev: 0.5 })), (d ? [1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 1] : [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0])[m] && this._mNote("sawtooth", w + (m % 8 === 6 ? 12 : 0), n, c * 0.9, d ? 0.16 : 0.12, d ? 900 : 600, { env: !0, q: 4 }), d || m % 2 === 0) {
      let R = g[[0, 1, 2, 3, 2, 1, 0, 2][m % 8]] + 12;
      this._mNote("square", R, n, c * 0.8, d ? 0.035 : 0.03, d ? 2600 : 1800, { env: !0, delay: !0, rev: 0.2 });
    }
    if (d && (p === 2 || p === 3) && [0, 3, 6, 10, 12].includes(m)) {
      let x = p === 2 ? [76, 79, 81, 79, 76] : [74, 76, 79, 76, 71], R = [0, 3, 6, 10, 12].indexOf(m);
      this._mNote("sawtooth", x[R], n, c * (m === 12 ? 4 : 2.6), 0.045, 3200, { detune: 6, attack: 0.01, release: 0.15, delay: !0, rev: 0.4 });
    }
    d ? (m % 4 === 0 && this._drum("kick", n), (m === 4 || m === 12) && this._drum("snare", n), m % 2 === 1 && this._drum("hat", n, m % 4 === 3 ? 1 : 0.6)) : ((m === 0 || m === 10) && this._drum("kick", n, 0.5), m % 4 === 2 && this._drum("hat", n, 0.35));
  }
};

// main_src.js
var v = (e) => document.getElementById(e), K = (e, t = !0) => (typeof e == "string" ? v(e) : e).classList.toggle("hidden", !t), bt = matchMedia("(pointer: coarse)").matches || "ontouchstart" in window, Ns = v("gl"), ye = new j.WebGLRenderer({ canvas: Ns, antialias: !0, powerPreference: "high-performance" });
ye.toneMapping = j.ACESFilmicToneMapping;
ye.toneMappingExposure = 1.05;
ye.outputColorSpace = j.SRGBColorSpace;
var Ne = new j.Scene();
Ne.background = new j.Color(328460);
Ne.fog = new j.Fog(459791, 60, 170);
var ee = new j.PerspectiveCamera(66, 1, 0.1, 400), ke = new Ds(ye);
ke.addPass(new Os(Ne, ee));
var as = new Ws(new j.Vector2(256, 256), 0.8, 0.55, 0.82);
ke.addPass(as);
ke.addPass(new Vs());
var Ks = Zt(ye, Ne), { T: D, M: Mt, L: de, DS: Xs, HALF_W: Tt, HALL: Ue, trackAt: st, nearestIdx: Qs, world: xe, startLights: vt, makeKart: rs, pickups: gt, pads: cs, hazards: Ge, projectiles: $e, dropOil: Jt, throwTire: js, SHOW: Te, hex: yt } = Ks, b = new je(), ls = "ksib_neon_v2", et = () => ({ coins: 300, owned: ["club"], sel: "club", best: { lap: 0, gp: 0, wins: 0 }, set: { music: !0, sfx: !0, auto: !1, sens: 100, gfx: "auto" }, diff: 1 }), T = et();
try {
  let e = JSON.parse(localStorage.getItem(ls));
  e && e.owned && (T = Object.assign(et(), e, { set: Object.assign(et().set, e.set || {}), best: Object.assign(et().best, e.best || {}) }));
} catch {
}
var le = () => {
  try {
    localStorage.setItem(ls, JSON.stringify(T));
  } catch {
  }
}, ce = [{ n: "Обычный", c: "#c7c7cc", w: 50 }, { n: "Редкий", c: "#29d9ff", w: 30 }, { n: "Эпический", c: "#c46bff", w: 15 }, { n: "Легендарный", c: "#ffd24a", w: 5 }], Pe = [
  { id: "club", name: "Клубный №1", r: 0, price: 0, accent: 10503935, suit: 2759236, frame: 3124821, num: 1, s: [3, 3, 3] },
  { id: "pink", name: "Неон Пинк", r: 0, price: 400, accent: 16722902, suit: 2763320, frame: 16722902, num: 7, s: [3, 4, 3] },
  { id: "ice", name: "Ледяной", r: 1, price: 800, accent: 2742783, suit: 1714746, frame: 15267583, num: 9, s: [3, 3, 5] },
  { id: "lime", name: "Лайм", r: 1, price: 800, accent: 5111674, suit: 1845794, frame: 5111674, num: 5, s: [4, 4, 2] },
  { id: "zaur", name: "Зауралье", r: 2, price: 1500, accent: 1746326, suit: 14212578, frame: 16722490, num: 2, s: [4, 3, 4] },
  { id: "gold", name: "Золотой", r: 3, price: null, accent: 16762938, suit: 2761232, frame: 16762938, num: 1, s: [5, 4, 4] },
  { id: "night", name: "Ночной гонщик", r: 3, price: null, accent: 15921906, suit: 855312, frame: 16722490, num: 13, s: [5, 5, 3] }
], Ce = (e) => Pe.find((t) => t.id === e) || Pe[0], Us = (e) => ({ maxV: 23.6 + e.s[0] * 0.9, acc: 8 + e.s[1] * 1.7, hnd: 0.82 + e.s[2] * 0.07 }), se = (e) => {
  if (!e) return "—";
  let t = Math.floor(e / 60), n = e - t * 60;
  return t + ":" + (n < 10 ? "0" : "") + n.toFixed(2);
}, Ee = 1, Fe = !0, fs = !0;
function ds() {
  let e = T.set.gfx;
  fs = e === "auto", e === "eco" ? (Ee = 1, Fe = !1) : e === "high" ? (Ee = Math.min(devicePixelRatio || 1, 2), Fe = !0) : (Ee = Math.min(devicePixelRatio || 1, bt ? 1.5 : 2), Fe = !0), Ht();
}
function Ht() {
  let e = innerWidth, t = innerHeight;
  ye.setPixelRatio(Ee), ye.setSize(e, t, !1), ke.setPixelRatio(Ee), ke.setSize(e, t), as.setSize(Math.floor(e * Ee / 2), Math.floor(t * Ee / 2)), ee.aspect = e / t, ee.updateProjectionMatrix(), v("rotate").classList.toggle("need", t > e);
}
addEventListener("resize", Ht);
var ae = null, Zs = null;
function He(e) {
  ae && xe.remove(ae), Zs = e, ae = rs(e.num, e.suit, e.accent, e.frame), ae.position.set(Te.x, 0.35, Te.z), ae.scale.setScalar(1.15), xe.add(ae), mn(e);
}
var Js = ["Айдар", "Лиана", "Тимур", "Алина", "Руслан", "Динара", "Ильдар", "Зарина"], Le = 3, Q = [], G = null, fe = "gp";
function ut(e, t, n, c) {
  let d = e % 2 ? 2.3 : -2.3, p = -6.2 - e * 6, m = st(p, d), E = rs(t.num, t.suit, t.accent, t.frame);
  return xe.add(E), {
    isPlayer: n,
    name: c,
    def: t,
    st: Us(t),
    mesh: E,
    d: p,
    off: d,
    x: m.x,
    z: m.z,
    h: Math.atan2(m.tx, m.tz),
    idx: m.i,
    v: 0,
    item: null,
    itemCD: 0,
    coins: 0,
    spin: 0,
    boost: 0,
    finished: !1,
    finishTime: 0,
    skill: 1,
    laneT: d,
    laneTimer: 0,
    drift: 0,
    driftDir: 0,
    driftCharge: 0,
    driftLvl: 0,
    hop: 0,
    pendingDrift: !1,
    slip: 0,
    lean: 0,
    rolling: !1,
    lapStart: 0,
    lapNo: 0,
    bestLap: 0,
    wallT: 0
  };
}
var N = { L: !1, R: !1, gas: !1, brake: !1, drift: !1, itemPress: !1, driftEdge: !1 }, ie = {};
addEventListener("keydown", (e) => {
  e.repeat || (ie[e.code] = !0, (e.code === "KeyE" || e.code === "Enter") && (N.itemPress = !0), (e.code === "Space" || e.code.startsWith("Shift")) && (N.driftEdge = !0), (e.code === "Escape" || e.code === "KeyP") && (q === "race" || q === "countdown") && Pt(), ["Space", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.code) && e.preventDefault());
});
addEventListener("keyup", (e) => {
  ie[e.code] = !1;
});
var ge = { L: !1, R: !1, gas: !1, brake: !1, drift: !1 };
function Ie(e, t, n) {
  let c = (p) => {
    p.preventDefault(), e.classList.add("down");
    try {
      e.setPointerCapture(p.pointerId);
    } catch {
    }
    t && (ge[t] = !0), n && n(), navigator.vibrate && navigator.vibrate(8);
  }, d = () => {
    e.classList.remove("down"), t && (ge[t] = !1);
  };
  e.addEventListener("pointerdown", c), e.addEventListener("pointerup", d), e.addEventListener("pointercancel", d), e.addEventListener("lostpointercapture", d);
}
Ie(v("bL"), "L");
Ie(v("bR"), "R");
Ie(v("bGas"), "gas");
Ie(v("bBrake"), "brake");
Ie(v("bDrift"), "drift", () => {
  N.driftEdge = !0;
});
Ie(v("bItem"), null, () => {
  N.itemPress = !0;
});
function hs() {
  N.L = ge.L || !!ie.ArrowLeft || !!ie.KeyA, N.R = ge.R || !!ie.ArrowRight || !!ie.KeyD, N.gas = ge.gas || !!ie.ArrowUp || !!ie.KeyW, N.brake = ge.brake || !!ie.ArrowDown || !!ie.KeyS, N.drift = ge.drift || !!ie.Space || !!ie.ShiftLeft || !!ie.ShiftRight;
}
var wt = [{ id: "turbo", icon: "⚡", name: "Турбо" }, { id: "oil", icon: "🛢️", name: "Масло" }, { id: "tire", icon: "🛞", name: "Шина" }, { id: "turbo3", icon: "🚀", name: "Супер-турбо" }], q = "loading", we = 0, ze = 0, Rt = 0, us = null, qe = 0, ve = 0, he = 0;
function ue(e, t = "#fff") {
  let n = v("toast");
  n.textContent = e, n.style.color = t, n.classList.add("on"), clearTimeout(ue._t), ue._t = setTimeout(() => n.classList.remove("on"), 1200);
}
function De(e, t = "#fff") {
  let n = v("msg");
  n.textContent = e, n.style.color = t, n.style.transform = "translate(-50%,-50%) scale(1.15)", setTimeout(() => n.style.transform = "translate(-50%,-50%) scale(1)", 120);
}
function ms() {
  for (let e of Q) xe.remove(e.mesh);
  Q.length = 0;
  for (let e of Ge) xe.remove(e.mesh);
  Ge.length = 0;
  for (let e of $e) xe.remove(e.mesh);
  $e.length = 0;
  for (let e of gt)
    e.respawn = 0, e.mesh.visible = !0;
  G = null;
}
function St(e) {
  fe = e || fe, ms(), ae && (ae.visible = !1);
  let t = Ce(T.sel);
  if (fe === "gp") {
    let n = Pe.filter((m) => m.id !== t.id), c = [...Js].sort(() => Math.random() - 0.5), d = [[0.84, 0.9], [0.9, 0.97], [0.96, 1.02]][T.diff], p = 0;
    for (let m = 0; m < 6; m++) {
      if (m === 4) {
        G = ut(m, t, !0, "Ты"), Q.push(G);
        continue;
      }
      let E = ut(m, n[p % n.length], !1, c[p]);
      E.skill = d[0] + Math.random() * (d[1] - d[0]), Q.push(E), p++;
    }
  } else
    G = ut(0, t, !0, "Ты"), Q.push(G);
  we = 0, ze = 4.4, qe = 0, ve = 0, q = "countdown", K("menuLayer", !1), K("modesModal", !1), K("resultsModal", !1), K("pauseModal", !1), K("hud"), K("ctrl", bt), v("pos").style.display = fe === "gp" ? "" : "none", nt(), tt = !1, b.startMusic("race"), vt.forEach((n) => n.material.emissive.setHex(0));
}
function zt(e) {
  return [...Q].sort(ps).indexOf(e) + 1;
}
function ps(e, t) {
  return e.finished && t.finished ? e.finishTime - t.finishTime : e.finished ? -1 : t.finished ? 1 : t.d - e.d;
}
function Ys(e) {
  if (e.item || e.rolling) return;
  let t = fe === "gp" ? zt(e) : 3, n = fe === "tt" ? ["turbo", "turbo3"] : t <= 2 ? ["oil", "oil", "tire", "turbo"] : t <= 4 ? ["turbo", "tire", "oil", "turbo"] : ["turbo3", "turbo", "tire", "turbo3"], c = wt.find((d) => d.id === n[Math.floor(Math.random() * n.length)]);
  e.isPlayer ? (e.rolling = !0, Rt = 1, us = c, b.itemRoll(1)) : (e.item = c, e.itemCD = 1 + Math.random() * 4);
}
function Es(e) {
  if (!e.item) return;
  let t = e.item;
  if (e.item = null, t.id === "turbo" && (e.boost = Math.max(e.boost, 1.3), e.isPlayer && (b.boost(1), ue("⚡ Турбо", "#29d9ff"))), t.id === "turbo3" && (e.boost = Math.max(e.boost, 2.6), e.isPlayer && (b.boost(1.6), ue("🚀 Супер-турбо", "#4dff7a"))), t.id === "oil" && (Jt(e.x - Math.sin(e.h) * 2.4, e.z - Math.cos(e.h) * 2.4, e), e.isPlayer && (b.oil(), ue("🛢️ Масло сзади", "#c46bff"))), t.id === "tire") {
    let n = null, c = 1e9;
    for (let d of Q) {
      if (d === e || d.finished) continue;
      let p = d.d - e.d;
      p > 0 && p < c && (c = p, n = d);
    }
    n ? js(e, n) : Jt(e.x - Math.sin(e.h) * 2.4, e.z - Math.cos(e.h) * 2.4, e), e.isPlayer && (b.throwIt(), ue(n ? "🛞 Шина летит в " + n.name : "🛞 Ты первый — шина назад", "#4dff7a"));
  }
  e.isPlayer && nt();
}
function nt() {
  let e = v("itemSlot");
  G && G.rolling ? (e.classList.add("roll"), e.classList.remove("has"), e.textContent = wt[Math.floor(performance.now() / 80) % wt.length].icon) : (e.classList.remove("roll"), e.textContent = G && G.item ? G.item.icon : "", e.classList.toggle("has", !!(G && G.item)));
}
function Yt(e) {
  e.spin > 0 || e.boost > 2 || (e.spin = 1.1, e.v *= 0.35, e.driftCharge = 0, e.drift = 0, e.isPlayer && (b.spin(), ue("Занесло!", "#ff453a"), he = 0.5, navigator.vibrate && navigator.vibrate(60)));
}
function Oe(e) {
  return e > 2.2 ? 3 : e > 1.3 ? 2 : e > 0.6 ? 1 : 0;
}
function en(e, t) {
  hs();
  let n = q === "race" && !e.finished, c = e.st, d = T.set.sens / 100, p = n ? (N.R ? 1 : 0) - (N.L ? 1 : 0) : 0, m = p === 0 || Math.sign(p) !== Math.sign(ve) ? 9 : 4.5;
  ve += Math.max(-m * t, Math.min(m * t, p - ve));
  let E = n && (N.gas || T.set.auto && !N.brake), y = c.maxV + Math.min(e.coins, 10) * 0.2 + (e.boost > 0 ? 9 : 0);
  if (e.spin > 0 ? (e.spin -= t, e.v *= 1 - 1.6 * t) : n && N.brake ? e.v > 0.3 ? e.v -= 28 * t : e.v = Math.max(-6, e.v - 9 * t) : E ? e.v < 0 ? e.v += 30 * t : e.v < y ? e.v += (e.boost > 0 ? 34 : c.acc) * Math.max(0.05, 1 - (e.v / y) ** 2) * t : e.v -= 7 * t : e.finished ? e.v += (13 - e.v) * t : e.v -= Math.sign(e.v) * Math.min(Math.abs(e.v), 5 * t), N.driftEdge && (N.driftEdge = !1, n && e.v > 9 && !e.drift && e.hop <= 0 && e.spin <= 0 && (e.hop = 0.26, e.pendingDrift = !0, b.hop())), e.pendingDrift && !e.drift && (!N.drift || e.v < 8 ? e.pendingDrift = !1 : Math.abs(p) > 0 && (e.drift = 1, e.driftDir = Math.sign(p), e.driftCharge = 0, e.driftLvl = 0, e.pendingDrift = !1)), e.drift && (!N.drift || e.v < 7 || e.spin > 0 || !n)) {
    let R = Oe(e.driftCharge);
    R && e.spin <= 0 && n && (e.boost = Math.max(e.boost, [0, 0.7, 1.15, 1.7][R]), b.miniTurbo(R), ue(["", "Мини-турбо", "Супер-турбо", "Ультра-турбо"][R], ["", "#29d9ff", "#ff9f0a", "#ff2bd6"][R])), e.drift = 0, e.driftCharge = 0, e.driftLvl = 0;
  }
  let w = Math.abs(e.v), g = Math.min(1, w / 6), u = 1 - 0.38 * Math.min(1, w / 30), x;
  if (e.drift) {
    let R = ve * e.driftDir;
    x = e.driftDir * (0.95 + 0.55 * R) * 1.12 * c.hnd * d, e.driftCharge += t * (1 + 0.6 * Math.max(0, R));
    let U = Oe(e.driftCharge);
    U > e.driftLvl && (e.driftLvl = U, b.driftStage(U)), e.slip += (e.driftDir * 0.42 - e.slip) * Math.min(1, t * 6), e.v *= 1 - 0.03 * t;
  } else
    x = ve * 1.5 * c.hnd * g * u * d * (e.v < 0 ? -1 : 1), e.slip += (0 - e.slip) * Math.min(1, t * 6);
  e.spin > 0 && (x = 0), e.h -= x * t, e.lean += (ve * 0.07 + (e.drift ? e.driftDir * 0.05 : 0) - e.lean) * Math.min(1, t * 8), e.hop = Math.max(0, e.hop - t), e.x += Math.sin(e.h) * e.v * t, e.z += Math.cos(e.h) * e.v * t, tn(e, t);
}
function tn(e, t) {
  e.idx = Qs(e.x, e.z, e.idx);
  let n = e.idx, c = (e.x - D.x[n]) * D.nx[n] + (e.z - D.z[n]) * D.nz[n], d = Tt - 0.75;
  if (e.wallT = Math.max(0, e.wallT - t), Math.abs(c) > d) {
    let y = Math.sign(c), w = Math.abs(c) - d;
    e.x -= D.nx[n] * y * w, e.z -= D.nz[n] * y * w, c = y * d;
    let u = Math.atan2(D.tx[n], D.tz[n]) + (e.v < 0 ? Math.PI : 0) - e.h;
    for (; u > Math.PI; ) u -= 2 * Math.PI;
    for (; u < -Math.PI; ) u += 2 * Math.PI;
    Math.abs(u) < Math.PI / 2 && (e.h += u * Math.min(1, t * 5)), Math.abs(e.v) > 8 && w > 0.05 && (e.v *= 0.86, e.isPlayer && e.wallT <= 0 && (b.wall(Math.min(1, Math.abs(e.v) / 25)), he = Math.min(0.4, he + 0.22), e.wallT = 0.35, navigator.vibrate && navigator.vibrate(25)));
  }
  e.off = c;
  let p = n * Xs + ((e.x - D.x[n]) * D.tx[n] + (e.z - D.z[n]) * D.tz[n]), E = Math.floor(e.d / de) * de + p;
  E - e.d > de / 2 && (E -= de), e.d - E > de / 2 && (E += de), e.d = E;
}
function sn(e, t) {
  let n = q === "race" || q === "finished", c = e.d - G.d, d = [[0.88, 0.95, 1.06, 1.12], [0.9, 0.96, 1.04, 1.1], [0.95, 0.98, 1.03, 1.08]][T.diff], p = c > 25 ? d[0] : c > 8 ? d[1] : c < -25 ? d[3] : c < -8 ? d[2] : 1, m = st(e.d + 8), E = Math.abs(D.curv[m.i]), y = 26 * e.skill * p * (1 - Math.min(0.32, E * 1.4));
  e.boost > 0 && (y += 10), n || (y = 0), e.finished && (y = 13), e.spin > 0 && (e.spin -= t, y *= 0.2), e.v += (y - e.v) * Math.min(1, t * (e.v < y ? 0.9 : 2.5)), e.d += e.v * t, e.laneTimer -= t, e.laneTimer <= 0 && (e.laneTimer = 1.5 + Math.random() * 2.5, e.laneT = (Math.random() - 0.5) * 6);
  let w = e.laneT + Math.sign(D.curv[m.i]) * Math.min(2.5, E * 30);
  for (let R of Q) {
    if (R === e) continue;
    let U = R.d - e.d;
    U > 0 && U < 5 && Math.abs(R.off - e.off) < 1.8 && (w += e.off > R.off ? 2.5 : -2.5);
  }
  w = Math.max(-Tt + 1.2, Math.min(Tt - 1.2, w)), e.off += (w - e.off) * Math.min(1, t * 1.2);
  let g = st(e.d, e.off), u = g.x - e.x, x = g.z - e.z;
  if (u * u + x * x > 1e-6 && e.spin <= 0) {
    let R = Math.atan2(u, x) - e.h;
    for (; R > Math.PI; ) R -= 2 * Math.PI;
    for (; R < -Math.PI; ) R += 2 * Math.PI;
    e.h += R * Math.min(1, t * 10), e.lean += (-R * 2 - e.lean) * Math.min(1, t * 6);
  }
  e.x = g.x, e.z = g.z, e.idx = g.i, e.item && n && !e.finished && (e.itemCD -= t, e.itemCD <= 0 && Es(e));
}
function nn(e) {
  for (let t = 0; t < Q.length; t++) for (let n = t + 1; n < Q.length; n++) {
    let c = Q[t], d = Q[n], p = d.x - c.x, m = d.z - c.z, E = p * p + m * m;
    if (E < 2.1 * 2.1 && E > 1e-4) {
      let y = Math.sqrt(E), w = (2.1 - y) / 2, g = p / y, u = m / y;
      for (let [x, R] of [[c, -1], [d, 1]])
        x.isPlayer ? (x.x += g * w * R, x.z += u * w * R) : x.off += (g * D.nx[x.idx] + u * D.nz[x.idx]) * w * R;
      if (c.isPlayer || d.isPlayer) {
        let x = c.isPlayer ? c : d, R = c.isPlayer ? d : c;
        x.v = x.v * 0.85 + (x.v + R.v) / 2 * 0.15, (!x._bump || performance.now() - x._bump > 400) && (b.bump(), x._bump = performance.now(), he = Math.min(0.3, he + 0.12));
      }
    }
  }
  for (let t of gt) {
    if (t.respawn > 0) {
      t.respawn -= e, t.respawn <= 0 && (t.mesh.visible = !0);
      continue;
    }
    for (let n of Q)
      if ((n.x - t.x) ** 2 + (n.z - t.z) ** 2 < 1.6 * 1.6) {
        t.mesh.visible = !1, t.type === "box" ? (t.respawn = 4, Ys(n)) : (t.respawn = 8, n.coins = Math.min(10, n.coins + 1), n.isPlayer && (b.coin(), n.coinsTotal = (n.coinsTotal || 0) + 1));
        break;
      }
  }
  for (let t of cs) for (let n of Q) (n.x - t.x) ** 2 + (n.z - t.z) ** 2 < 2.2 * 2.2 && n.boost < 0.8 && (n.boost = 0.9, n.isPlayer && b.boost(0.8));
  for (let t = Ge.length - 1; t >= 0; t--) {
    let n = Ge[t];
    if (n.life -= e, n.safe -= e, n.life <= 0) {
      xe.remove(n.mesh), Ge.splice(t, 1);
      continue;
    }
    for (let c of Q)
      if (!(c === n.owner && n.safe > 0) && (c.x - n.x) ** 2 + (c.z - n.z) ** 2 < 1.3 * 1.3) {
        Yt(c), xe.remove(n.mesh), Ge.splice(t, 1);
        break;
      }
  }
  for (let t = $e.length - 1; t >= 0; t--) {
    let n = $e[t];
    n.life -= e, n.d += 45 * e, n.off += (n.target.off - n.off) * Math.min(1, e * 4);
    let c = st(n.d, n.off);
    n.mesh.position.set(c.x, 0.55, c.z), n.mesh.rotation.y = Math.atan2(c.tx, c.tz), n.mesh.rotation.x += e * 20, (Math.abs(n.d - n.target.d) < 1.4 || n.life <= 0) && (n.life > 0 && Yt(n.target), xe.remove(n.mesh), $e.splice(t, 1));
  }
}
function on(e, t, n) {
  let c = e.mesh, d = c.userData;
  c.position.set(e.x, 0, e.z), c.rotation.y = e.h + (e.spin > 0 ? (1.1 - e.spin) * Math.PI * 3.2 : 0), d.body.rotation.y = -e.slip * 0.9, d.body.rotation.z = e.lean * (e.isPlayer ? 1 : 0.6), d.body.position.y = Math.sin(n * 30 + e.d) * 0.012 * Math.min(1, Math.abs(e.v) / 10) + (e.hop > 0 ? Math.sin(e.hop / 0.26 * Math.PI) * 0.32 : 0);
  let p = e.v * t / 0.27;
  d.wheels.forEach((y, w) => {
    y.children.forEach((g) => g.rotation.x += p), w < 2 && (y.rotation.y = e.isPlayer ? -ve * 0.35 - e.slip * 0.6 : -e.lean * 0.5);
  });
  let m = e.drift ? Oe(e.driftCharge) : 0, E = [16777215, 2742783, 16752394, 16722902][m];
  d.sparks.forEach((y) => {
    y.material.color.setHex(E), y.scale.setScalar(e.drift ? (0.35 + m * 0.28) * (0.7 + Math.random() * 0.6) : 1e-3);
  }), d.flame.visible = e.boost > 0, e.boost > 0 && (d.flame.scale.set(1, 0.8 + Math.random() * 0.8, 1), d.flame.material.color.setHex(e.boost > 1.5 ? 16731104 : 6742271)), e.boost = Math.max(0, e.boost - t);
}
var mt = new j.Vector3(), es = new j.Vector3(), be = new j.Vector3(), tt = !1, Be = 0;
function an(e) {
  let t = G, n = t.h + t.slip * 0.35;
  tt || (Be = n);
  let c = n - Be;
  for (; c > Math.PI; ) c -= 2 * Math.PI;
  for (; c < -Math.PI; ) c += 2 * Math.PI;
  Be += c * Math.min(1, e * 5.5);
  let d = Math.abs(t.v), p = 3.7 + Math.min(d, 35) * 0.02;
  be.set(t.x - Math.sin(Be) * p, 1.6, t.z - Math.cos(Be) * p), be.x = Math.max(Ue.x0 + 1, Math.min(Ue.x1 - 1, be.x)), be.z = Math.max(Ue.z0 + 1, Math.min(Ue.z1 - 1, be.z)), tt || (mt.copy(be), tt = !0), mt.lerp(be, Math.min(1, e * 14)), es.set(t.x + Math.sin(t.h) * 3.4, 0.9, t.z + Math.cos(t.h) * 3.4), ee.position.copy(mt), he > 0 && (ee.position.x += (Math.random() - 0.5) * he * 0.5, ee.position.y += (Math.random() - 0.5) * he * 0.35, he = Math.max(0, he - e * 1.6)), ee.lookAt(es);
  let E = 64 + Math.min(1, d / 28) * 6 + (t.boost > 0 ? 8 : 0);
  ee.fov += (E - ee.fov) * Math.min(1, e * 4), ee.updateProjectionMatrix();
}
var pt = 0;
function rn(e) {
  pt += e, ae && (ae.rotation.y += e * 0.45, ae.position.y = 0.35 + Math.sin(pt * 1.5) * 0.02);
  let t = Te.x + Math.sin(pt * 0.12) * 1.5, n = Te.z - 7.4;
  ee.position.set(t, 2.4, n);
  let c = Te.x - t, d = Te.z - n, p = Math.hypot(c, d), m = -d / p, E = c / p, y = innerWidth > innerHeight ? 3 : 0;
  ee.lookAt(Te.x - m * y, 0.8, Te.z - E * y), Math.abs(ee.fov - 52) > 0.1 && (ee.fov = 52, ee.updateProjectionMatrix());
}
var Se = v("mini"), V = Se.getContext("2d"), We = 1 / 0, ot = -1 / 0, Ve = 1 / 0, it = -1 / 0;
for (let e = 0; e < Mt; e++)
  We = Math.min(We, D.x[e]), ot = Math.max(ot, D.x[e]), Ve = Math.min(Ve, D.z[e]), it = Math.max(it, D.z[e]);
var rt = Math.min((Se.width - 36) / (ot - We), (Se.height - 36) / (it - Ve)), cn = (Se.width - (ot - We) * rt) / 2, ln = (Se.height - (it - Ve) * rt) / 2, Ze = (e) => cn + (e - We) * rt, Je = (e) => ln + (e - Ve) * rt;
function fn() {
  V.clearRect(0, 0, Se.width, Se.height), V.lineJoin = "round", V.beginPath();
  for (let e = 0; e <= Mt; e += 4) {
    let t = e % Mt;
    e ? V.lineTo(Ze(D.x[t]), Je(D.z[t])) : V.moveTo(Ze(D.x[t]), Je(D.z[t]));
  }
  V.closePath(), V.strokeStyle = "rgba(255,255,255,.22)", V.lineWidth = 14, V.stroke(), V.strokeStyle = "rgba(255,255,255,.85)", V.lineWidth = 5, V.stroke();
  for (let e of Q)
    e.isPlayer || (V.fillStyle = yt(e.def.accent), V.beginPath(), V.arc(Ze(e.x), Je(e.z), 6, 0, 7), V.fill());
  G && (V.fillStyle = "#34c759", V.strokeStyle = "#fff", V.lineWidth = 3, V.beginPath(), V.arc(Ze(G.x), Je(G.z), 8, 0, 7), V.fill(), V.stroke());
}
var ts = 0;
function dn(e) {
  if (e - ts < 0.06) return;
  ts = e;
  let t = Math.max(1, Math.min(Le, Math.floor(G.d / de) + 1));
  if (v("hudLap").textContent = `Круг ${t}/${Le}`, v("hudTime").textContent = se(we) === "—" ? "0:00.00" : se(we), fe === "gp") {
    let c = zt(G);
    v("pos").innerHTML = `${c}<small>/${Q.length}</small>`, v("pos").style.color = c === 1 ? "#ffd24a" : c <= 3 ? "#34c759" : "#fff";
  }
  v("hudCoins").textContent = G.coins, v("spd").textContent = Math.round(Math.abs(G.v) * 3.2);
  let n = v("driftMeter");
  if (G.drift) {
    n.style.opacity = 1;
    let c = G.driftCharge;
    n.firstChild.style.width = Math.min(100, c / 2.2 * 100) + "%", n.firstChild.style.background = ["#fff", "#29d9ff", "#ff9f0a", "#ff2bd6"][Oe(c)];
  } else n.style.opacity = 0;
  fn();
}
function hn(e) {
  let t = Math.floor(e.d / de);
  if (t <= e.lapNo) return;
  let n = we - e.lapStart;
  e.lapStart = we, e.lapNo = t, (!e.bestLap || n < e.bestLap) && (e.bestLap = n);
  let c = !T.best.lap || n < T.best.lap;
  c && (T.best.lap = n, le()), t < Le && (ue(`Круг ${t}: ${se(n)}${c ? " · рекорд!" : ""}`, c ? "#ffd24a" : "#fff"), t === Le - 1 && setTimeout(() => {
    De("Финальный круг", "#ff2bd6"), b.finalLap(), setTimeout(() => De(""), 1400);
  }, 600));
}
function un() {
  q = "finished", b.finish(fe !== "gp" || zt(G) === 1), setTimeout(() => {
    for (let y of Q) y.finished || (y.finishTime = we + (Le * de - y.d) / (26 * 0.9));
    let e = [...Q].sort(ps), t = e.indexOf(G) + 1, n = 0, c = "", d = (G.coinsTotal || 0) * 5;
    if (fe === "gp") {
      let y = [200, 140, 100, 70, 50, 40][t - 1];
      n = y + d, c = `${y} за место + ${d} за монеты · лучший круг ${se(G.bestLap)}`, (!T.best.gp || G.finishTime < T.best.gp) && (T.best.gp = G.finishTime), t === 1 && (T.best.wins = (T.best.wins || 0) + 1), v("resPlace").textContent = t, v("resPlace").style.color = t === 1 ? "#ffd24a" : t <= 3 ? "#34c759" : "#fff", v("resTitle").textContent = t === 1 ? "Победа!" : t <= 3 ? "Подиум!" : "Финиш", v("resTable").innerHTML = e.map((w, g) => `<tr class="${w.isPlayer ? "me" : ""}"><td>${g + 1}</td><td>${w.name}</td><td>${w.def.name}</td><td>${se(w.finishTime)}</td></tr>`).join("");
    } else
      n = 60 + d, c = `Время ${se(G.finishTime)} · рекорд круга ${se(T.best.lap)}`, v("resPlace").textContent = "⏱", v("resPlace").style.color = "#29d9ff", v("resTitle").textContent = se(G.bestLap), v("resTable").innerHTML = `<tr><td>Лучший круг</td><td>${se(G.bestLap)}</td></tr><tr><td>Общее время</td><td>${se(G.finishTime)}</td></tr><tr class="me"><td>Рекорд</td><td>${se(T.best.lap)}</td></tr>`;
    v("resSub").textContent = c, T.coins += n, le(), K("resultsModal"), K("ctrl", !1);
    let p = 0, m = Math.max(1, Math.round(n / 30)), E = () => {
      p = Math.min(n, p + m), v("resCoins").textContent = p, b.reward(p), p < n && setTimeout(E, 35);
    };
    E();
  }, 1800);
}
var xs = "home";
function at() {
  v("coinsTop").textContent = T.coins.toLocaleString("ru-RU");
}
function Gt() {
  q = "menu", ms(), K("hud", !1), K("ctrl", !1), K("resultsModal", !1), K("pauseModal", !1), K("menuLayer"), ae && (ae.visible = !0), He(Ce(T.sel)), Ms(xs, !0), at(), b.startMusic("menu");
}
function Ms(e, t) {
  xs = e, document.querySelectorAll(".tab").forEach((n) => n.classList.toggle("on", n.dataset.tab === e)), document.querySelectorAll(".screenTab").forEach((n) => n.classList.toggle("hidden", n.id !== e)), e === "garage" && Ts(), e === "shop" && kt(), e === "tour" && (v("records").innerHTML = `Лучший круг: <b>${se(T.best.lap)}</b><br>Лучшая гонка (Гран-при): <b>${se(T.best.gp)}</b><br>Победы: <b>${T.best.wins || 0}</b>`), (e === "home" || e === "tour") && He(Ce(T.sel)), t || b.tap();
}
document.querySelectorAll(".tab").forEach((e) => e.addEventListener("click", () => Ms(e.dataset.tab)));
function ct(e) {
  return `background:linear-gradient(135deg, ${yt(e.accent)}, ${yt(e.suit)})`;
}
function mn(e) {
  let t = v("garageStats");
  if (!t) return;
  let n = ["Скорость", "Разгон", "Управление"];
  t.innerHTML = `<div class="row" style="background:none;padding:0"><div class="sw" style="${ct(e)}"></div><div><div class="nm">${e.name}</div><div class="rr" style="color:${ce[e.r].c}">${ce[e.r].n}</div></div></div>` + n.map((c, d) => `<div class="stat">${c}<div class="bar"><i style="width:${e.s[d] * 20}%"></i></div></div>`).join("");
}
function Ts() {
  let e = v("garageList");
  e.innerHTML = Pe.filter((t) => T.owned.includes(t.id)).map((t) => `<button class="row press ${t.id === T.sel ? "on" : ""}" data-id="${t.id}"><div class="sw" style="${ct(t)}"></div><div style="text-align:left"><div class="nm">${t.name}</div><div class="rr" style="color:${ce[t.r].c}">${ce[t.r].n}</div></div><div class="right">${t.id === T.sel ? "✓ Выбран" : "Выбрать"}</div></button>`).join("") + '<div class="note">Ещё карты — в Магазине и в Неоновом кейсе.</div>', e.querySelectorAll(".row").forEach((t) => t.addEventListener("click", () => {
    T.sel = t.dataset.id, le(), b.select(), He(Ce(T.sel)), Ts();
  })), He(Ce(T.sel));
}
function kt() {
  let e = v("shopList");
  e.innerHTML = Pe.filter((t) => t.id !== "club").map((t) => {
    let c = T.owned.includes(t.id) ? '<span style="color:#34c759">Есть</span>' : t.price ? `<span class="buyBtn ${T.coins < t.price ? "dim" : ""}" data-buy="${t.id}"><span class="coin-ic"></span>${t.price}</span>` : '<span class="note">Только в кейсе</span>';
    return `<div class="row press" data-id="${t.id}"><div class="sw" style="${ct(t)}"></div><div><div class="nm">${t.name}</div><div class="rr" style="color:${ce[t.r].c}">${ce[t.r].n}</div></div><div class="right">${c}</div></div>`;
  }).join(""), e.querySelectorAll(".row").forEach((t) => t.addEventListener("click", (n) => {
    let c = t.dataset.id, d = Ce(c);
    if (n.target.closest("[data-buy]")) {
      T.coins >= d.price ? (T.coins -= d.price, T.owned.push(c), T.sel = c, le(), b.buy(), at(), kt(), He(d)) : (b.error(), vs());
      return;
    }
    b.tap(), He(d);
  }));
}
function vs() {
  let e = v("coinsTop").parentElement;
  e.style.transition = "transform .1s", e.style.transform = "scale(1.12)", setTimeout(() => e.style.transform = "", 150);
}
var Et = 300;
function ss() {
  let e = ce.reduce((n, c) => n + c.w, 0), t = Math.random() * e;
  for (let n = 0; n < ce.length; n++)
    if (t -= ce[n].w, t <= 0) return n;
  return 0;
}
function ns(e) {
  let t = Pe.filter((n) => n.r === e);
  return t[Math.floor(Math.random() * t.length)];
}
v("btnCase").addEventListener("click", () => {
  if (T.coins < Et) {
    b.error(), vs();
    return;
  }
  T.coins -= Et, le(), at(), b.tap();
  let e = ns(ss()), t = [], n = 32;
  for (let x = 0; x < 40; x++) t.push(x === n ? e : ns(ss()));
  let c = v("reelStrip");
  c.innerHTML = t.map((x) => `<div class="rc" style="border-color:${ce[x.r].c}"><div class="sw" style="${ct(x)}"></div>${x.name}</div>`).join(""), c.style.transform = "translateX(0px)", v("caseResult").innerHTML = "", v("caseNote").textContent = "Крутим…", K("caseClose", !1), K("caseModal");
  let d = v("reel").clientWidth, p = 130, m = -(n * p + 60 - d / 2 + (Math.random() * 60 - 30)), E = 4.6, y = performance.now(), w = -1, g = () => {
    let x = Math.min(1, (performance.now() - y) / (E * 1e3)), R = 1 - Math.pow(1 - x, 4), U = m * R;
    c.style.transform = `translateX(${U}px)`;
    let O = Math.floor((-U + d / 2) / p);
    O !== w && (w = O, b.caseTick(O)), x < 1 ? requestAnimationFrame(g) : u();
  };
  requestAnimationFrame(g);
  function u() {
    let x = T.owned.includes(e.id);
    if (b.caseReveal(e.r), x) {
      let R = Math.round(Et * 0.5);
      T.coins += R, v("caseNote").textContent = `Уже есть — вернули ${R} монет`;
    } else
      T.owned.push(e.id), T.sel = e.id, v("caseNote").textContent = "Новый карт! Уже выбран в гараже";
    le(), at(), v("caseResult").innerHTML = `<div style="font-size:13px;font-weight:700;color:${ce[e.r].c};letter-spacing:.06em;text-transform:uppercase">${ce[e.r].n}</div><div style="font-size:26px;font-weight:800;margin-top:4px">${e.name}</div>`, K("caseClose"), He(e);
  }
});
v("caseClose").addEventListener("click", () => {
  K("caseModal", !1), b.tap(), kt();
});
var gn = T.diff;
v("btnPlay").addEventListener("click", () => {
  b.init(), b.tap(), v("ttDesc").textContent = T.best.lap ? `Твой рекорд круга: ${se(T.best.lap)}` : "Один на трассе. Поставь лучший круг.", K("modesModal");
});
v("modesClose").addEventListener("click", () => {
  b.back(), K("modesModal", !1);
});
document.querySelectorAll("#diffSeg button").forEach((e) => {
  e.classList.toggle("on", +e.dataset.d === T.diff), e.addEventListener("click", () => {
    T.diff = +e.dataset.d, le(), b.tap(), document.querySelectorAll("#diffSeg button").forEach((t) => t.classList.toggle("on", t === e));
  });
});
document.querySelectorAll(".mode").forEach((e) => e.addEventListener("click", () => {
  if (e.dataset.mode === "online") {
    b.error(), e.querySelector(".d").textContent = "В разработке — скоро в обновлении.";
    return;
  }
  b.select(), pn(), St(e.dataset.mode);
}));
function pn() {
  if (bt)
    try {
      let e = document.documentElement, t = (e.requestFullscreen || e.webkitRequestFullscreen)?.call(e);
      t && t.then && t.then(() => screen.orientation?.lock?.("landscape").catch(() => {
      })).catch(() => {
      });
    } catch {
    }
}
function Ke() {
  v("tgMusic").classList.toggle("on", T.set.music), v("tgSfx").classList.toggle("on", T.set.sfx), v("tgAuto").classList.toggle("on", T.set.auto), v("rgSens").value = T.set.sens, document.querySelectorAll("#gfxSeg button").forEach((e) => e.classList.toggle("on", e.dataset.q === T.set.gfx));
}
v("btnSettings").addEventListener("click", () => {
  b.init(), b.tap(), Ke(), K("settingsModal");
});
v("settingsClose").addEventListener("click", () => {
  b.tap(), K("settingsModal", !1);
});
v("tgMusic").addEventListener("click", () => {
  T.set.music = !T.set.music, b.setMusic(T.set.music), le(), Ke(), b.tap();
});
v("tgSfx").addEventListener("click", () => {
  T.set.sfx = !T.set.sfx, b.setSfx(T.set.sfx), le(), Ke(), b.tap();
});
v("tgAuto").addEventListener("click", () => {
  T.set.auto = !T.set.auto, le(), Ke(), b.tap();
});
v("rgSens").addEventListener("input", (e) => {
  T.set.sens = +e.target.value, le();
});
document.querySelectorAll("#gfxSeg button").forEach((e) => e.addEventListener("click", () => {
  T.set.gfx = e.dataset.q, le(), ds(), Ke(), b.tap();
}));
var ys = "race";
function Pt() {
  q !== "race" && q !== "countdown" || (ys = q, q = "paused", K("pauseModal"), b.tap());
}
v("pauseBtn").addEventListener("click", Pt);
v("btnResume").addEventListener("click", () => {
  q = ys, K("pauseModal", !1), b.tap();
});
v("btnRestart").addEventListener("click", () => {
  b.tap(), St(fe);
});
v("btnQuit").addEventListener("click", () => {
  b.back(), Gt();
});
v("btnAgain").addEventListener("click", () => {
  b.select(), St(fe);
});
v("btnMenu").addEventListener("click", () => {
  b.back(), Gt();
});
document.addEventListener("visibilitychange", () => {
  document.hidden ? (Pt(), b.ctx?.suspend()) : b.ctx?.resume();
});
addEventListener("pointerdown", () => {
  b.init(), b.setMusic(T.set.music), b.setSfx(T.set.sfx), q === "menu" && b.startMusic("menu");
}, { once: !0 });
var os = new j.Clock(), Ye = 0, xt = 0, is = 0;
function ws() {
  requestAnimationFrame(ws);
  let e = Math.min(0.05, os.getDelta()), t = os.elapsedTime;
  if (q === "menu" || q === "loading")
    rn(e), b.updateEngine(0, 0, -1, !1, !1, e);
  else if (q !== "paused") {
    if (q === "countdown") {
      ze -= e, hs(), N.gas || T.set.auto ? qe += e : qe = 0;
      let c = Math.min(5, Math.floor((4.4 - ze) / 0.72));
      vt.forEach((m, E) => m.material.emissive.setHex(E < c ? 16718362 : 0));
      let d = Math.ceil(ze - 0.8), p = ze > 3.6 ? "" : d >= 1 ? String(d) : "Старт!";
      v("msg").textContent !== p && (De(p, d >= 1 ? "#fff" : "#34c759"), p && b.countBeep(d < 1)), ze <= 0.8 && (q = "race", vt.forEach((m) => m.material.emissive.setHex(2293589)), setTimeout(() => De(""), 700), !T.set.auto && qe > 0.05 && qe < 0.9 && (G.boost = 1.1, G.v = 10, b.boost(1.2), ue("Ракетный старт!", "#34c759")), G.lapStart = 0);
    }
    q === "race" && (we += e), G.rolling && (Rt -= e, nt(), Rt <= 0 && (G.rolling = !1, G.item = us, b.itemGet(), nt())), N.itemPress && (N.itemPress = !1, q === "race" && G.item && Es(G)), en(G, e);
    for (let c of Q) c.isPlayer || sn(c, e);
    (q === "race" || q === "finished") && nn(e), q === "race" && hn(G);
    for (let c of Q) !c.finished && c.d >= Le * de && (c.finished = !0, c.finishTime = we, c.isPlayer && (De("Финиш!", "#34c759"), un()));
    for (let c of Q) on(c, e, t);
    an(e), dn(t);
    let n = (N.gas || T.set.auto && !N.brake) && q === "race" ? 1 : 0;
    b.updateEngine(Math.abs(G.v) / 27, n, G.drift ? Oe(G.driftCharge) : -1, G.boost > 0, !0, e);
  } else
    b.updateEngine(0, 0, -1, !1, !1, e);
  for (let n of gt)
    n.mesh.visible && (n.type === "box" ? (n.mesh.rotation.y = t * 1.4, n.mesh.rotation.x = t * 0.7, n.mesh.position.y = 1 + Math.sin(t * 2 + n.s) * 0.15, n.mesh.material.emissive.setHSL((t * 0.25 + n.s * 0.01) % 1, 1, 0.5)) : n.mesh.rotation.y = t * 3 + n.s);
  for (let n of cs) n.mesh.material.opacity = 0.55 + Math.sin(t * 8) * 0.35;
  if (Fe ? ke.render() : ye.render(Ne, ee), fs && (q === "race" || q === "countdown") && is < 2 && (Ye += e, xt++, Ye > 3)) {
    let n = Ye / xt;
    Ye = 0, xt = 0, is++, n > 1 / 40 && (Ee > 1 ? (Ee = 1, Ht()) : Fe = !1);
  }
}
ds();
b.musicOn = T.set.music;
b.sfxOn = T.set.sfx;
Gt();
v("loading").style.display = "none";
ws();
