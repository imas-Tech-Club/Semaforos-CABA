/* Semáforos CABA · reproduce la simulación grabada en trazas.js (ver scripts/exportar_traza.py). */
(function () {
  "use strict";
  var D = window.TRAZAS;
  var NOMBRE = { madrugada: "Madrugada (4 h)", pico: "Pico (12 h)", valle: "Valle de tarde (17 h)", noche: "Noche (20 h)" };
  // Medianas de results_ejemplo/resumen.csv (espera media, en segundos)
  var RES = {
    madrugada: { fijo: 3.213, ql: 0.057 }, pico: { fijo: 3.678, ql: 0.199 },
    valle: { fijo: 3.494, ql: 0.105 }, noche: { fijo: 3.510, ql: 0.152 }
  };
  var LEN = 6, WID = 2.6;        // autos dibujados un poco más grandes que reales (4,5 × 1,9 m) para que se vean
  var FRENTE = 2.25;             // x,y del simulador es el paragolpes delantero: el centro queda 2,25 m atrás
  var MEDIO = 120;               // metros desde el centro del cruce hasta el borde de la vista
  var PLANES = ["fijo", "ql"];

  function css(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }
  function $(id) { return document.getElementById(id); }
  function coma(x, d) { return x.toFixed(d).replace(".", ","); }

  var geo = D.geo, franja = null, t = 0, playing = true, last = 0, estadoSeg = {};
  var cv = { fijo: $("c-fijo"), ql: $("c-ql") };
  var cx = { fijo: cv.fijo.getContext("2d"), ql: cv.ql.getContext("2d") };
  var W = cv.fijo.width, H = cv.fijo.height, pad = 24;

  var cxm = 0, cym = 0;
  geo.lineas.forEach(function (l) { cxm += l.p[0] / geo.lineas.length; cym += l.p[1] / geo.lineas.length; });
  var esc = (W - 2 * pad) / (2 * MEDIO);
  function px(x) { return W / 2 + (x - cxm) * esc; }
  function py(y) { return H / 2 - (y - cym) * esc; }

  // ---------- filtros de franja
  var fr = $("franjas");
  Object.keys(D.franjas).forEach(function (f, i) {
    var inp = document.createElement("input");
    inp.type = "radio"; inp.name = "franja"; inp.id = "f-" + f; inp.value = f;
    var lab = document.createElement("label");
    lab.htmlFor = inp.id; lab.textContent = NOMBRE[f] || f;
    inp.addEventListener("change", function () { if (inp.checked) elegir(f); });
    fr.appendChild(inp); fr.appendChild(lab);
  });

  function prepararEstados(f, plan) {
    var d = D.franjas[f][plan], n = d.v.length, arr = new Array(n), cur = d.tls0, k = 0;
    for (var s = 0; s < n; s++) {
      while (k < d.tls.length && d.tls[k][0] <= s) { cur = d.tls[k][1]; k++; }
      arr[s] = cur;
    }
    return arr;
  }

  function cifra(titulo, valor, nota) {
    var div = document.createElement("div"), dt = document.createElement("dt"), dd = document.createElement("dd");
    dt.textContent = titulo; dd.textContent = valor;
    if (nota) { var s = document.createElement("small"); s.textContent = nota; dd.appendChild(s); }
    div.appendChild(dt); div.appendChild(dd); return div;
  }

  function elegir(f) {
    franja = f; t = 0;
    estadoSeg = { fijo: prepararEstados(f, "fijo"), ql: prepararEstados(f, "ql") };
    var d = D.franjas[f], n = d.fijo.v.length;
    $("t").max = n - 1; $("t").value = 0;
    $("f-" + f).checked = true;
    $("meta").textContent = (NOMBRE[f] || f) + ": índice horario " + coma(d.indice, 2) + " respecto del pico → unos " +
      d.veh_por_hora + " vehículos por hora (supuesto). Los dos planes ven exactamente la misma demanda.";
    $("vent").textContent = "Se muestran " + n + " s simulados, desde el segundo " + D.ventana.inicio_s +
      " de una hora simulada, cuando la red ya está cargada de autos.";
    var c = $("cifras"); c.textContent = "";
    c.appendChild(cifra("Espera media, plan fijo", coma(d.fijo.espera_media_s, 2) + " s", "promedio de la hora simulada"));
    c.appendChild(cifra("Espera media, Q-learning", coma(d.ql.espera_media_s, 2) + " s", "promedio de la hora simulada"));
    c.appendChild(cifra("Autos detenidos, plan fijo", coma(d.fijo.detenidos_medio, 1), "en promedio, a cada instante"));
    c.appendChild(cifra("Autos detenidos, Q-learning", coma(d.ql.detenidos_medio, 1), "en promedio, a cada instante"));
    dibujar();
  }

  // ---------- dibujo
  function colorLuz(c) { return c === "G" || c === "g" ? "#22c55e" : (c === "y" || c === "Y" ? "#facc15" : "#ef4444"); }
  function resumenSemaforo(st) {
    var g = 0, y = 0;
    for (var i = 0; i < st.length; i++) { if (st[i] === "G" || st[i] === "g") g++; else if (st[i] === "y" || st[i] === "Y") y++; }
    return y > 0 && g === 0 ? "amarillo" : (g > 0 ? "verde para un eje" : "todo rojo");
  }
  function base(ctx) {
    ctx.clearRect(0, 0, W, H);
    ctx.lineCap = "butt"; ctx.lineJoin = "round";
    ctx.strokeStyle = css("--calle"); ctx.fillStyle = css("--cruce");
    geo.carriles.forEach(function (c) {
      ctx.beginPath();
      c.s.forEach(function (p, i) { i ? ctx.lineTo(px(p[0]), py(p[1])) : ctx.moveTo(px(p[0]), py(p[1])); });
      ctx.lineWidth = Math.max(2, c.w * esc * 0.95); ctx.stroke();
    });
    geo.juncs.forEach(function (j) {
      ctx.beginPath();
      j.forEach(function (p, i) { i ? ctx.lineTo(px(p[0]), py(p[1])) : ctx.moveTo(px(p[0]), py(p[1])); });
      ctx.closePath(); ctx.fill();
    });
  }
  function luces(ctx, st) {
    geo.lineas.forEach(function (l) {
      var m = Math.hypot(l.d[0], l.d[1]) || 1, dx = l.d[0] / m, dy = l.d[1] / m, nx = -dy, ny = dx, hw = l.w / 2;
      ctx.strokeStyle = colorLuz(st[l.i] || "r"); ctx.lineWidth = Math.max(3, 0.9 * esc);
      ctx.beginPath();
      ctx.moveTo(px(l.p[0] - nx * hw), py(l.p[1] - ny * hw)); ctx.lineTo(px(l.p[0] + nx * hw), py(l.p[1] + ny * hw)); ctx.stroke();
    });
  }
  function autos(ctx, fila) {
    var movil = css("--auto"), quieto = css("--auto-detenido"), det = 0;
    for (var i = 0; i < fila.length; i += 4) {
      var x = fila[i] / 10, y = fila[i + 1] / 10, a = fila[i + 2] * Math.PI / 180, v = fila[i + 3] / 10, parado = v < 0.1;
      if (parado) det++;
      ctx.save(); ctx.translate(px(x - Math.sin(a) * FRENTE), py(y - Math.cos(a) * FRENTE)); ctx.rotate(a);
      ctx.fillStyle = parado ? quieto : movil;
      ctx.fillRect(-WID * esc / 2, -LEN * esc / 2, WID * esc, LEN * esc); ctx.restore();
    }
    return det;
  }
  function dibujar() {
    if (!franja) return;
    var d = D.franjas[franja], s = Math.min(Math.floor(t), d.fijo.v.length - 1);
    PLANES.forEach(function (p) {
      var ctx = cx[p], st = estadoSeg[p][s];
      base(ctx); var det = autos(ctx, d[p].v[s]); luces(ctx, st);
      $("d-" + p).textContent = det; $("s-" + p).textContent = resumenSemaforo(st);
    });
    $("tl").textContent = s + " s"; $("t").value = s;
  }
  function loop(ts) {
    if (playing && franja) {
      var dt = last ? Math.min((ts - last) / 1000, 0.25) : 0;
      t += dt * (+$("vel").value);
      if (t >= D.franjas[franja].fijo.v.length) t = 0;
      dibujar();
    }
    last = ts; requestAnimationFrame(loop);
  }

  $("play").onclick = function () { playing = !playing; this.textContent = playing ? "Pausa" : "Seguir"; };
  $("reset").onclick = function () { t = 0; dibujar(); };
  $("t").oninput = function () { t = +this.value; dibujar(); };
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", dibujar);

  // ---------- barras de espera media por franja
  var barras = $("barras"), mx = 0;
  Object.keys(D.franjas).forEach(function (f) { if (RES[f]) mx = Math.max(mx, RES[f].fijo, RES[f].ql); });
  Object.keys(D.franjas).forEach(function (f) {
    if (!RES[f]) return;
    var g = document.createElement("div"); g.className = "barras__grupo";
    var nombre = document.createElement("b"); nombre.textContent = (NOMBRE[f] || f).split(" (")[0]; g.appendChild(nombre);
    [["fijo", "Plan fijo", "--serie-fijo"], ["ql", "Q-learning", "--serie-ql"]].forEach(function (r) {
      var fila = document.createElement("div"); fila.className = "barra-fila";
      var w = RES[f][r[0]] / mx * 62;
      var b = document.createElement("div"); b.className = "barra"; b.style.width = w + "%"; b.style.background = "var(" + r[2] + ")";
      var v = document.createElement("span"); v.className = "barra-val"; v.style.left = "calc(" + w + "% + 8px)";
      v.textContent = coma(RES[f][r[0]], 2) + " s";
      fila.appendChild(b); fila.appendChild(v); g.appendChild(fila);
    });
    barras.appendChild(g);
  });

  elegir(Object.keys(D.franjas).indexOf("pico") >= 0 ? "pico" : Object.keys(D.franjas)[0]);
  requestAnimationFrame(loop);
})();
