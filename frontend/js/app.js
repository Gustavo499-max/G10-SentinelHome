
import * as THREE from "three";

/* =====================================================
   G10 SENTINELHOME — CYBER INTELLIGENCE PLATFORM
   Frontend 3D + FastAPI + Chart.js
===================================================== */

const API = "http://127.0.0.1:8000";

let severityChart = null;
let trafficChart = null;
let globeScene = null;
let universeScene = null;
let animationFrame = null;

let devicesCache = [];
let alertsCache = [];

const $ = selector => document.querySelector(selector);

const COLORS = {
    cyan: 0x00f0ff,
    blue: 0x1677ff,
    purple: 0x9b5cff,
    pink: 0xff3cac,
    green: 0x00ffb3,
    red: 0xff416c,
    background: 0x030712
};

/* =====================================================
   UTILITÁRIOS
===================================================== */

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}

function toast(message, error = false) {
    const container = $("#toast-container");
    if (!container) return;

    const element = document.createElement("div");
    element.className = `toast ${error ? "error" : ""}`;
    element.textContent = message;

    container.appendChild(element);

    setTimeout(() => element.remove(), 4000);
}

async function api(path, options = {}) {
    const response = await fetch(`${API}${path}`, options);

    if (!response.ok) {
        let message = `Erro HTTP ${response.status}`;

        try {
            const body = await response.json();
            message = body.detail || body.error || message;
        } catch {}

        throw new Error(message);
    }

    if (response.status === 204) return null;

    const contentType = response.headers.get("content-type") || "";

    if (contentType.includes("application/json")) {
        return response.json();
    }

    return null;
}

function riskClass(level) {
    const normalized = String(level || "").toLowerCase();

    if (normalized.includes("critico") || normalized.includes("alto")) {
        return "critico";
    }

    if (normalized.includes("moderado") || normalized.includes("medio")) {
        return "moderado";
    }

    return "low";
}

function formatNumber(value) {
    return Number(value || 0).toLocaleString("pt-BR", {
        maximumFractionDigits: 1
    });
}

/* =====================================================
   RELÓGIO
===================================================== */

function updateClock() {
    const now = new Date();

    if ($("#clock")) {
        $("#clock").textContent = now.toLocaleTimeString("pt-BR");
    }

    if ($("#current-date")) {
        $("#current-date").textContent =
            now.toLocaleDateString("pt-BR");
    }
}

updateClock();
setInterval(updateClock, 1000);

/* =====================================================
   NAVEGAÇÃO
===================================================== */

function navigate(page) {
    document.querySelectorAll(".page").forEach(section => {
        section.classList.remove("active");
    });

    document.querySelectorAll(".nav-link").forEach(button => {
        button.classList.toggle(
            "active",
            button.dataset.page === page
        );
    });

    const selected = $(`#page-${page}`);

    if (!selected) return;

    selected.classList.add("active");

    const titles = {
        overview: "VISÃO GERAL",
        universe: "NETWORK UNIVERSE",
        devices: "DISPOSITIVOS",
        alerts: "CENTRAL DE ALERTAS",
        analysis: "FUZZY RISK ENGINE",
        reports: "RELATÓRIOS"
    };

    $("#page-heading").textContent = titles[page] || "G10 SENTINELHOME";

    if (page === "universe") {
        setTimeout(() => {
            if (universeScene) {
                universeScene.resize();
            } else {
                createUniverse();
            }
        }, 100);
    }
}

/* =====================================================
   THREE.JS — GLOBO HOLOGRÁFICO
===================================================== */

function createGlobe() {
    const container = $("#globe-container");

    if (!container || typeof THREE === "undefined") {
        return;
    }

    const width = container.clientWidth;
    const height = container.clientHeight;

    if (width <= 0 || height <= 0) return;

    const scene = new THREE.Scene();

    const camera = new THREE.PerspectiveCamera(
        45,
        width / height,
        0.1,
        100
    );

    camera.position.z = 4.5;

    const renderer = new THREE.WebGLRenderer({
        alpha: true,
        antialias: true
    });

    renderer.setPixelRatio(
        Math.min(window.devicePixelRatio || 1, 2)
    );

    renderer.setSize(width, height);

    container.appendChild(renderer.domElement);

    const group = new THREE.Group();
    scene.add(group);

    /* ESFERA PRINCIPAL */

    const sphereGeometry = new THREE.SphereGeometry(1.25, 64, 64);

    const sphereMaterial = new THREE.MeshBasicMaterial({
        color: COLORS.blue,
        wireframe: true,
        transparent: true,
        opacity: 0.27
    });

    const sphere = new THREE.Mesh(
        sphereGeometry,
        sphereMaterial
    );

    group.add(sphere);

    /* CAMADA EXTERNA */

    const outerGeometry = new THREE.SphereGeometry(1.31, 48, 48);

    const outerMaterial = new THREE.MeshBasicMaterial({
        color: COLORS.cyan,
        wireframe: true,
        transparent: true,
        opacity: 0.08
    });

    const outerSphere = new THREE.Mesh(
        outerGeometry,
        outerMaterial
    );

    group.add(outerSphere);

    /* PONTOS DO GLOBO */

    const pointPositions = [];

    for (let i = 0; i < 1800; i++) {
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);

        const radius = 1.27;

        const x = radius * Math.sin(phi) * Math.cos(theta);
        const y = radius * Math.cos(phi);
        const z = radius * Math.sin(phi) * Math.sin(theta);

        pointPositions.push(x, y, z);
    }

    const pointsGeometry = new THREE.BufferGeometry();

    pointsGeometry.setAttribute(
        "position",
        new THREE.Float32BufferAttribute(pointPositions, 3)
    );

    const pointsMaterial = new THREE.PointsMaterial({
        color: COLORS.cyan,
        size: 0.018,
        transparent: true,
        opacity: 0.9,
        sizeAttenuation: true
    });

    const points = new THREE.Points(
        pointsGeometry,
        pointsMaterial
    );

    group.add(points);

    /* NÚCLEO CENTRAL */

    const coreGeometry = new THREE.SphereGeometry(0.12, 32, 32);

    const coreMaterial = new THREE.MeshBasicMaterial({
        color: COLORS.cyan
    });

    const core = new THREE.Mesh(
        coreGeometry,
        coreMaterial
    );

    group.add(core);

    /* NÓS DE REDE */

    const nodes = [];

    for (let i = 0; i < 18; i++) {
        const phi = Math.acos(
            2 * Math.random() - 1
        );

        const theta = Math.random() * Math.PI * 2;

        const position = new THREE.Vector3(
            1.29 * Math.sin(phi) * Math.cos(theta),
            1.29 * Math.cos(phi),
            1.29 * Math.sin(phi) * Math.sin(theta)
        );

        const node = new THREE.Mesh(
            new THREE.SphereGeometry(0.035, 16, 16),
            new THREE.MeshBasicMaterial({
                color: i % 4 === 0 ? COLORS.pink : COLORS.cyan
            })
        );

        node.position.copy(position);
        group.add(node);
        nodes.push(node);
    }

    /* CONEXÕES ENTRE NÓS */

    const connectionMaterial = new THREE.LineBasicMaterial({
        color: COLORS.cyan,
        transparent: true,
        opacity: 0.28
    });

    for (let i = 0; i < nodes.length; i++) {
        const next = (i + 1) % nodes.length;

        const geometry = new THREE.BufferGeometry().setFromPoints([
            nodes[i].position,
            nodes[next].position
        ]);

        const line = new THREE.Line(
            geometry,
            connectionMaterial
        );

        group.add(line);
    }

    /* ÓRBITAS */

    const orbitMaterial = new THREE.MeshBasicMaterial({
        color: COLORS.purple,
        wireframe: true,
        transparent: true,
        opacity: 0.16
    });

    const orbit = new THREE.Mesh(
        new THREE.TorusGeometry(1.65, 0.006, 8, 120),
        orbitMaterial
    );

    orbit.rotation.x = Math.PI / 2.5;
    group.add(orbit);

    /* ESTRELAS */

    const starPositions = [];

    for (let i = 0; i < 450; i++) {
        starPositions.push(
            (Math.random() - 0.5) * 8,
            (Math.random() - 0.5) * 8,
            (Math.random() - 0.5) * 8
        );
    }

    const starGeometry = new THREE.BufferGeometry();

    starGeometry.setAttribute(
        "position",
        new THREE.Float32BufferAttribute(starPositions, 3)
    );

    const starMaterial = new THREE.PointsMaterial({
        color: 0x8aaeff,
        size: 0.012,
        transparent: true,
        opacity: 0.7
    });

    const stars = new THREE.Points(
        starGeometry,
        starMaterial
    );

    scene.add(stars);

    /* INTERAÇÃO */

    let dragging = false;
    let previousX = 0;
    let previousY = 0;

    renderer.domElement.addEventListener("pointerdown", event => {
        dragging = true;
        previousX = event.clientX;
        previousY = event.clientY;
        renderer.domElement.setPointerCapture(event.pointerId);
    });

    renderer.domElement.addEventListener("pointermove", event => {
        if (!dragging) return;

        const deltaX = event.clientX - previousX;
        const deltaY = event.clientY - previousY;

        group.rotation.y += deltaX * 0.005;
        group.rotation.x += deltaY * 0.005;

        previousX = event.clientX;
        previousY = event.clientY;
    });

    renderer.domElement.addEventListener("pointerup", () => {
        dragging = false;
    });

    renderer.domElement.addEventListener("pointercancel", () => {
        dragging = false;
    });

    /* ANIMAÇÃO */

    let animationId;

    function animate() {
        animationId = requestAnimationFrame(animate);

        if (!dragging) {
            group.rotation.y += 0.0018;
        }

        orbit.rotation.z += 0.0015;
        stars.rotation.y -= 0.00015;

        const pulse = 1 + Math.sin(Date.now() * 0.002) * 0.05;
        core.scale.setScalar(pulse);

        renderer.render(scene, camera);
    }

    animate();

    const resize = () => {
        const newWidth = container.clientWidth;
        const newHeight = container.clientHeight;

        if (!newWidth || !newHeight) return;

        camera.aspect = newWidth / newHeight;
        camera.updateProjectionMatrix();

        renderer.setSize(newWidth, newHeight);
    };

    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(container);

    const loading = $("#globe-loading");

    if (loading) {
        loading.style.opacity = "0";

        setTimeout(() => {
            loading.style.display = "none";
        }, 500);
    }

    globeScene = {
        resize,
        destroy() {
            cancelAnimationFrame(animationId);
            resizeObserver.disconnect();
            renderer.dispose();
            container.removeChild(renderer.domElement);
        }
    };
}

/* =====================================================
   NETWORK UNIVERSE — TOPOLOGIA
===================================================== */

function createUniverse() {
    const container = $("#universe-container");

    if (!container || !container.clientWidth) return;

    if (universeScene) {
        universeScene.destroy();
        universeScene = null;
    }

    const scene = new THREE.Scene();

    const camera = new THREE.PerspectiveCamera(
        55,
        container.clientWidth / container.clientHeight,
        0.1,
        100
    );

    camera.position.set(0, 0, 9);

    const renderer = new THREE.WebGLRenderer({
        alpha: true,
        antialias: true
    });

    renderer.setPixelRatio(
        Math.min(window.devicePixelRatio || 1, 2)
    );

    renderer.setSize(
        container.clientWidth,
        container.clientHeight
    );

    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    const group = new THREE.Group();
    scene.add(group);

    /* NÓ CENTRAL */

    const center = new THREE.Mesh(
        new THREE.IcosahedronGeometry(0.55, 2),
        new THREE.MeshBasicMaterial({
            color: COLORS.cyan,
            wireframe: true
        })
    );

    group.add(center);

    /* DISPOSITIVOS REAIS */

    const nodes = [];

    const total = devicesCache.length;

    devicesCache.forEach((device, index) => {
        const angle = (index / Math.max(total, 1)) * Math.PI * 2;
        const radius = 2.2 + (index % 3) * 0.35;

        const node = new THREE.Mesh(
            new THREE.SphereGeometry(0.11, 16, 16),
            new THREE.MeshBasicMaterial({
                color: COLORS.green
            })
        );

        node.position.set(
            Math.cos(angle) * radius,
            Math.sin(angle) * radius,
            (index % 2) * 0.25
        );

        group.add(node);

        const lineGeometry = new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(0, 0, 0),
            node.position
        ]);

        const line = new THREE.Line(
            lineGeometry,
            new THREE.LineBasicMaterial({
                color: COLORS.cyan,
                transparent: true,
                opacity: 0.45
            })
        );

        group.add(line);

        nodes.push({
            mesh: node,
            device
        });
    });

    function animate() {
        animationFrame = requestAnimationFrame(animate);

        group.rotation.y += 0.0012;
        center.rotation.x += 0.003;
        center.rotation.y += 0.004;

        renderer.render(scene, camera);
    }

    animate();

    const resize = () => {
        const width = container.clientWidth;
        const height = container.clientHeight;

        if (!width || !height) return;

        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.setSize(width, height);
    };

    universeScene = {
        resize,
        destroy() {
            cancelAnimationFrame(animationFrame);
            renderer.dispose();
            container.innerHTML = "";
        }
    };

    renderUniverseDevices();
}

function renderUniverseDevices() {
    const container = $("#universe-devices");

    if (!container) return;

    if (!devicesCache.length) {
        container.innerHTML = `
            <div class="empty-state">
                Nenhum dispositivo cadastrado na topologia.
            </div>
        `;
        return;
    }

    container.innerHTML = devicesCache.map(device => `
        <article class="device-card">
            <strong>
                <i class="fa-solid fa-computer"></i>
                ${escapeHTML(device.name)}
            </strong>
            <span>${escapeHTML(device.ip_address)}</span>
            <br>
            <span>${escapeHTML(device.device_type)}</span>
        </article>
    `).join("");
}

/* =====================================================
   CHARTS
===================================================== */

function renderSeverityChart(data) {
    const canvas = $("#traffic-chart");

    if (!canvas || typeof Chart === "undefined") return;

    const labels = ["Baixo", "Moderado", "Alto", "Crítico"];

    const keys = [
        "baixo",
        "moderado",
        "alto",
        "critico"
    ];

    const values = keys.map(key => Number(data[key] || 0));

    if (severityChart) severityChart.destroy();

    severityChart = new Chart(canvas, {
        type: "doughnut",
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: [
                    "#00ffb3",
                    "#ffc857",
                    "#ff8a65",
                    "#ff416c"
                ],
                borderColor: "#081326",
                borderWidth: 4,
                hoverOffset: 9
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "72%",
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        color: "#829bb5",
                        padding: 16,
                        usePointStyle: true,
                        font: { size: 9 }
                    }
                }
            }
        }
    });
}

/* Gráfico de telemetria demonstrativo.
   Não representa tráfego real capturado. */

function renderTrafficChart() {
    const canvas = $("#flow-canvas");

    if (!canvas || typeof Chart === "undefined") return;

    const labels = Array.from(
        { length: 20 },
        (_, index) => `${index + 1}`
    );

    const values = labels.map(() => Math.random() * 70 + 15);

    if (trafficChart) trafficChart.destroy();

    trafficChart = new Chart(canvas, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "Simulação de atividade",
                data: values,
                borderColor: "#00f0ff",
                backgroundColor: "#00f0ff18",
                borderWidth: 2,
                fill: true,
                tension: 0.45,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 1000
            },
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    display: false,
                    min: 0,
                    max: 100
                }
            }
        }
    });
}

/* =====================================================
   RISCO MÉDIO
===================================================== */

function updateRisk(value) {
    const score = Math.max(0, Math.min(100, Number(value) || 0));

    const gauge = $("#risk-gauge");

    if (!gauge) return;

    let color = "#00ffb3";
    let level = "BAIXO";

    if (score >= 70) {
        color = "#ff416c";
        level = "CRÍTICO";
    } else if (score >= 40) {
        color = "#ffc857";
        level = "MODERADO";
    }

    gauge.style.background = `
        conic-gradient(
            ${color} ${score * 3.6}deg,
            #162b49 ${score * 3.6}deg
        )
    `;

    $("#risk-value").textContent = `${score.toFixed(1)}%`;
    $("#risk-level").textContent = level;
    $("#average-risk").textContent = `${score.toFixed(1)}%`;
    $("#average-risk-label").textContent = `RISCO ${level}`;
}

/* =====================================================
   CARREGAMENTO DOS DADOS
===================================================== */

async function loadSummary() {
    const data = await api("/api/analytics/summary");

    $("#stat-devices").textContent = data.devices.total;
    $("#stat-alerts").textContent = data.alerts.open;
    $("#stat-critical").textContent = data.alerts.critical;
    $("#nav-alert-count").textContent = data.alerts.open;

    updateRisk(data.average_device_risk);
}

async function loadDevices() {
    const data = await api("/api/devices/");

    devicesCache = Array.isArray(data) ? data : [];

    const tbody = $("#devices-table");

    if (!devicesCache.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="empty-state">
                    Nenhum dispositivo cadastrado.
                </td>
            </tr>
        `;
    } else {
        tbody.innerHTML = devicesCache.map(device => `
            <tr>
                <td>${escapeHTML(device.name)}</td>
                <td>${escapeHTML(device.ip_address)}</td>
                <td>${escapeHTML(device.device_type)}</td>
                <td>
                    <span class="status-label">
                        ${escapeHTML(device.status)}
                    </span>
                </td>
                <td>${formatNumber(device.risk_score)}%</td>
                <td>
                    <button class="action-button"
                        data-delete-device="${device.id}"
                        title="Excluir dispositivo">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join("");
    }

    renderUniverseDevices();

    if (universeScene) {
        const container = $("#universe-container");

        if (container && container.clientWidth) {
            createUniverse();
        }
    }
}

async function loadAlerts() {
    const data = await api("/api/alerts/");

    alertsCache = Array.isArray(data) ? data : [];

    const tbody = $("#alerts-table");

    if (!alertsCache.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="empty-state">
                    Nenhum alerta registrado.
                </td>
            </tr>
        `;

        $("#recent-alerts").innerHTML = `
            <div class="empty-state">
                Nenhum alerta registrado.
            </div>
        `;

        return;
    }

    tbody.innerHTML = alertsCache.map(alert => `
        <tr>
            <td>${escapeHTML(alert.title)}</td>
            <td>${escapeHTML(alert.event_type)}</td>
            <td>${escapeHTML(alert.source_ip || "Não informado")}</td>
            <td>
                <span class="severity ${riskClass(alert.severity)}">
                    ${escapeHTML(alert.severity)}
                </span>
            </td>
            <td>${formatNumber(alert.risk_score)}%</td>
            <td>${escapeHTML(alert.status)}</td>
            <td>
                ${alert.status !== "resolvido" ? `
                    <button class="action-button"
                        data-resolve-alert="${alert.id}"
                        title="Resolver alerta">
                        <i class="fa-solid fa-check"></i>
                    </button>
                ` : ""}

                <button class="action-button"
                    data-delete-alert="${alert.id}"
                    title="Excluir alerta">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join("");

    $("#recent-alerts").innerHTML = alertsCache
        .slice(0, 5)
        .map(alert => `
            <div class="alert-item">
                <div class="alert-item-icon">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                </div>

                <div class="alert-item-info">
                    <strong>${escapeHTML(alert.title)}</strong>
                    <small>${escapeHTML(alert.source_ip || "Origem não informada")}</small>
                </div>

                <span class="alert-level">
                    ${escapeHTML(alert.severity)}
                </span>
            </div>
        `).join("");
}

async function loadAnalytics() {
    const severity = await api("/api/analytics/severity");

    renderSeverityChart(severity);
}

async function refreshDashboard() {
    try {
        await api("/api/health");

        $("#connection-dot").className = "status-dot online";
        $("#connection-text").textContent = "API CONECTADA";
        $("#system-state").textContent = "SISTEMA ONLINE";

        const results = await Promise.allSettled([
            loadSummary(),
            loadDevices(),
            loadAlerts(),
            loadAnalytics()
        ]);

        const failed = results.filter(result => result.status === "rejected");

        if (failed.length) {
            console.error("Falhas ao carregar módulos:", failed);
            toast("Alguns módulos não puderam carregar.", true);
        }

    } catch (error) {
        $("#connection-dot").className = "status-dot offline";
        $("#connection-text").textContent = "API DESCONECTADA";
        $("#system-state").textContent = "SEM CONEXÃO";

        console.error(error);

        toast(
            "Não foi possível conectar ao backend. Inicie a API.",
            true
        );
    }
}

/* =====================================================
   CADASTRO DE DISPOSITIVOS
===================================================== */

async function createDevice(event) {
    event.preventDefault();

    const form = event.currentTarget;

    const data = Object.fromEntries(
        new FormData(form)
    );

    try {
        await api("/api/devices/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });

        $("#device-dialog").close();
        form.reset();

        toast("Dispositivo cadastrado.");

        await refreshDashboard();

    } catch (error) {
        toast(error.message, true);
    }
}

/* =====================================================
   ALERTAS
===================================================== */

async function createAlert(event) {
    event.preventDefault();

    const form = event.currentTarget;

    const data = Object.fromEntries(
        new FormData(form)
    );

    data.risk_score = Number(data.risk_score);

    if (!data.description) data.description = null;
    if (!data.source_ip) data.source_ip = null;

    try {
        await api("/api/alerts/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });

        $("#alert-dialog").close();
        form.reset();

        toast("Alerta registrado.");

        await refreshDashboard();

    } catch (error) {
        toast(error.message, true);
    }
}

/* =====================================================
   MOTOR FUZZY
===================================================== */

async function calculateFuzzy(event) {
    event.preventDefault();

    const packets = Number($("#fuzzy-packets").value);
    const ports = Number($("#fuzzy-ports").value);
    const traffic = Number($("#fuzzy-traffic").value);

    const values = [packets, ports, traffic];

    if (values.some(value =>
        !Number.isFinite(value) || value < 0 || value > 100
    )) {
        toast("Os valores devem estar entre 0 e 100.", true);
        return;
    }

    try {
        const result = await api(
            `/api/risk?packets=${packets}&ports=${ports}&traffic=${traffic}`
        );

        $("#fuzzy-result").textContent =
            `${Number(result.risk_score).toFixed(1)}%`;

        $("#fuzzy-level").textContent =
            String(result.risk_level).toUpperCase();

        $("#fuzzy-explanation").textContent =
            "Resultado calculado pelo motor de inferência Fuzzy.";

        toast("Análise concluída.");

    } catch (error) {
        toast(error.message, true);
    }
}

/* =====================================================
   ANÁLISE PCAP
===================================================== */

async function analyzeCapture(event) {
    event.preventDefault();

    const file = $("#pcap-file").files[0];

    if (!file) {
        toast("Selecione um arquivo PCAP.", true);
        return;
    }

    const formData = new FormData();

    formData.append("file", file);

    $("#pcap-result").textContent = "ANALISANDO CAPTURA...";

    try {
        const result = await api("/api/network/analyze", {
            method: "POST",
            body: formData
        });

        $("#pcap-result").textContent =
            JSON.stringify(result, null, 2);

        toast("Captura analisada com sucesso.");

    } catch (error) {
        $("#pcap-result").textContent = error.message;
        toast(error.message, true);
    }
}

/* =====================================================
   AÇÕES DA INTERFACE
===================================================== */

document.addEventListener("click", async event => {
    const pageButton = event.target.closest("[data-page]");

    if (pageButton) {
        navigate(pageButton.dataset.page);
    }

    const closeButton = event.target.closest("[data-close]");

    if (closeButton) {
        $(`#${closeButton.dataset.close}`).close();
    }

    const deleteDevice = event.target.closest("[data-delete-device]");

    if (deleteDevice && confirm("Excluir este dispositivo?")) {
        try {
            await api(
                `/api/devices/${deleteDevice.dataset.deleteDevice}`,
                { method: "DELETE" }
            );

            toast("Dispositivo excluído.");
            await refreshDashboard();

        } catch (error) {
            toast(error.message, true);
        }
    }

    const resolveAlert = event.target.closest("[data-resolve-alert]");

    if (resolveAlert) {
        try {
            await api(
                `/api/alerts/${resolveAlert.dataset.resolveAlert}`,
                {
                    method: "PATCH",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        status: "resolvido"
                    })
                }
            );

            toast("Alerta resolvido.");
            await refreshDashboard();

        } catch (error) {
            toast(error.message, true);
        }
    }

    const deleteAlert = event.target.closest("[data-delete-alert]");

    if (deleteAlert && confirm("Excluir este alerta?")) {
        try {
            await api(
                `/api/alerts/${deleteAlert.dataset.deleteAlert}`,
                { method: "DELETE" }
            );

            toast("Alerta excluído.");
            await refreshDashboard();

        } catch (error) {
            toast(error.message, true);
        }
    }
});

/* =====================================================
   FORMULÁRIOS E BOTÕES
===================================================== */

$("#add-device-button")?.addEventListener("click", () => {
    $("#device-dialog").showModal();
});

$("#add-alert-button")?.addEventListener("click", () => {
    $("#alert-dialog").showModal();
});

$("#device-form")?.addEventListener("submit", createDevice);
$("#alert-form")?.addEventListener("submit", createAlert);
$("#fuzzy-form")?.addEventListener("submit", calculateFuzzy);
$("#pcap-form")?.addEventListener("submit", analyzeCapture);

$("#refresh-button")?.addEventListener("click", () => {
    refreshDashboard();
});

/* =====================================================
   INICIALIZAÇÃO
===================================================== */

async function initialize() {
    console.log(
        "%c G10 SENTINELHOME ",
        "background:#00eaff;color:#02040c;font-weight:bold;padding:8px"
    );

    console.log("Inicializando ambiente 3D...");

    try {
        createGlobe();
        renderTrafficChart();
    } catch (error) {
        console.error("Erro na inicialização 3D:", error);
    }

    await refreshDashboard();

    console.log("G10 SentinelHome inicializado.");
}

initialize();

setInterval(refreshDashboard, 30000);
