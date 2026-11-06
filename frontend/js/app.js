

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

let discoveredDevicesCache = [];

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

    let response;

    try {

        response = await fetch(`${API}${path}`, options);

    } catch (error) {

        throw new Error(

            "Não foi possível conectar à API. Verifique se o backend está ativo."

        );

    }

    if (!response.ok) {

        let message = `Erro HTTP ${response.status}`;

        try {

            const body = await response.json();

            if (Array.isArray(body.detail)) {

                message = body.detail.map(item => {

                    const field = Array.isArray(item.loc)

                        ? item.loc.filter(part => part !== "body").join(".")

                        : "campo";

                    return `${field}: ${item.msg || "Valor inválido"}`;

                }).join(" | ");

            } else if (typeof body.detail === "string") {

                message = body.detail;

            } else if (body.detail && typeof body.detail === "object") {

                message = JSON.stringify(body.detail);

            } else if (body.error) {

                message = String(body.error);

            }

        } catch {

            message = `Erro HTTP ${response.status}: ${response.statusText}`;

        }

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
        button.classList.toggle("active", button.dataset.page === page);
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

    const heading = $("#page-heading");
    if (heading) heading.textContent = titles[page] || "G10 SENTINELHOME";

    if (page === "universe") {
        setTimeout(() => {
            ensureDiscoveryUI();
            if (universeScene) universeScene.resize();
            else createUniverse();
        }, 100);
    }
}

/* =====================================================

   DESCOBERTA DE DISPOSITIVOS — ARP

===================================================== */

function ensureDiscoveryUI() {

    const universe = $("#universe-container");

    if (!universe || !universe.parentNode || $("#discovery-panel")) return;

    const panel = document.createElement("section");

    panel.id = "discovery-panel";

    panel.style.cssText = `

        background: rgba(8, 20, 42, 0.95);

        border: 1px solid rgba(0, 240, 255, 0.25);

        border-radius: 12px;

        padding: 20px;

        margin-bottom: 20px;

        color: #dceaff;

    `;

    panel.innerHTML = `

        <div style="display:flex; justify-content:space-between;

                    align-items:center; flex-wrap:wrap; gap:15px;">

            <div>

                <h3 style="margin:0 0 6px;">DESCOBERTA DE REDE</h3>

                <p style="margin:0; color:#829bb5; font-size:12px;">

                    Identificação de dispositivos por requisições ARP.

                </p>

            </div>

            <div style="display:flex; gap:10px; flex-wrap:wrap;">

                <input

                    id="discovery-network"

                    type="text"

                    value="192.168.0.0/24"

                    aria-label="Faixa de rede"

                    placeholder="192.168.0.0/24"

                    style="padding:10px; border-radius:6px;

                           background:#101f38; color:#fff;

                           border:1px solid #31506e; min-width:170px;"

                >

                <button

                    id="discover-network-button"

                    type="button"

                    class="neon-button">

                    DESCOBRIR DISPOSITIVOS

                </button>

            </div>

        </div>

        <div id="discovery-status"

             style="margin-top:18px; color:#829bb5; font-size:13px;">

            Aguardando início da descoberta.

        </div>

        <div id="discovery-results" style="margin-top:15px;"></div>

    `;

    universe.parentNode.insertBefore(panel, universe);

    $("#discover-network-button").addEventListener(

        "click",

        discoverNetwork

    );

}

/* =====================================================

   EXECUTAR DESCOBERTA PELA API

===================================================== */

async function discoverNetwork() {

    const networkInput = $("#discovery-network");
    const button = $("#discover-network-button");
    const status = $("#discovery-status");
    const results = $("#discovery-results");

    if (!networkInput || !button || !status || !results) {
        console.error("Elementos da interface de descoberta não encontrados.");
        toast("A interface de descoberta não foi carregada corretamente.", true);
        return;
    }

    const network = networkInput.value.trim();

    if (!network) {

        toast("Informe a faixa de rede.", true);

        return;

    }

    button.disabled = true;

    button.textContent = "PESQUISANDO...";

    status.textContent =

        "Consultando dispositivos na rede. Aguarde...";

    results.innerHTML = "";

    try {

        const query = new URLSearchParams({

            network: network,

            timeout: "2"

        });

        const response = await api(

            `/api/network/discover?${query.toString()}`,

            { method: "POST" }

        );

        if (!response.discovery) {

            throw new Error("Resposta inválida do servidor.");

        }

        discoveredDevicesCache =

            response.discovery.devices || [];

        renderDiscoveredDevices();

        status.textContent =

            `${response.discovery.total_found} dispositivos encontrados ` +

            `em ${response.discovery.scan_duration_seconds} segundos.`;

        toast("Descoberta de rede concluída.");

        if (universeScene) {

            createUniverse();

        }

    } catch (error) {

        console.error("Erro na descoberta:", error);

        status.textContent =

            "Não foi possível concluir a descoberta.";

        toast(error.message, true);

    } finally {

        button.disabled = false;

        button.textContent = "DESCOBRIR DISPOSITIVOS";

    }

}

/* =====================================================

   COMPARAÇÃO COM O INVENTÁRIO

===================================================== */

function renderDiscoveredDevices() {

    const container = $("#discovery-results");

    if (!container) return;

    if (!discoveredDevicesCache.length) {

        container.innerHTML = `

            <div style="padding:15px; color:#829bb5;">

                Nenhum dispositivo respondeu às requisições ARP.

            </div>

        `;

        return;

    }

    const devices = discoveredDevicesCache.map(device => {

        const registered = devicesCache.some(item => {

            const sameIP =

                item.ip_address &&

                item.ip_address === device.ip_address;

            const sameMAC =

                item.mac_address &&

                device.mac_address &&

                item.mac_address.toLowerCase() ===

                device.mac_address.toLowerCase();

            return sameIP || sameMAC;

        });

        return {

            ...device,

            registered

        };

    });

    const newDevices = devices.filter(

        device => !device.registered

    );

    container.innerHTML = `

        <div style="

            display:flex;

            justify-content:space-between;

            align-items:center;

            flex-wrap:wrap;

            gap:15px;

            margin-bottom:18px;

        ">

            <div style="display:flex;gap:20px;flex-wrap:wrap;">

                <span>

                    Encontrados:

                    <strong>${devices.length}</strong>

                </span>

                <span>

                    Cadastrados:

                    <strong>${devices.length - newDevices.length}</strong>

                </span>

                <span style="color:#ffc857;">

                    Novos:

                    <strong>${newDevices.length}</strong>

                </span>

            </div>

            <button

                type="button"

                id="register-selected-devices"

                class="neon-button"

                ${newDevices.length === 0 ? "disabled" : ""}

            >

                CADASTRAR SELECIONADOS

            </button>

        </div>

        <div style="overflow-x:auto;">

            <table style="

                width:100%;

                border-collapse:collapse;

                font-size:13px;

            ">

                <thead>

                    <tr style="text-align:left;color:#829bb5;">

                        <th style="padding:12px;">

                            <input

                                type="checkbox"

                                id="select-all-discovered"

                                aria-label="Selecionar todos os novos"

                                ${newDevices.length === 0 ? "disabled" : ""}

                            >

                        </th>

                        <th style="padding:12px;">ENDEREÇO IP</th>

                        <th style="padding:12px;">ENDEREÇO MAC</th>

                        <th style="padding:12px;">STATUS</th>

                        <th style="padding:12px;">INVENTÁRIO</th>

                    </tr>

                </thead>

                <tbody>

                    ${devices.map((device, index) => `

                        <tr style="border-top:1px solid #243b59;">

                            <td style="padding:12px;">

                                ${

                                    device.registered

                                    ? '<span style="color:#00ffb3;">✓</span>'

                                    : `

                                        <input

                                            type="checkbox"

                                            class="discovered-device-checkbox"

                                            data-discovery-index="${index}"

                                            checked

                                            aria-label="Selecionar ${escapeHTML(device.ip_address)}"

                                        >

                                    `

                                }

                            </td>

                            <td style="padding:12px;">

                                ${escapeHTML(device.ip_address)}

                            </td>

                            <td style="padding:12px;">

                                ${escapeHTML(device.mac_address)}

                            </td>

                            <td style="padding:12px;color:#00ffb3;">

                                ONLINE (ARP)

                            </td>

                            <td style="

                                padding:12px;

                                color:${device.registered ? "#00ffb3" : "#ffc857"};

                            ">

                                ${device.registered ? "CADASTRADO" : "NOVO"}

                            </td>

                        </tr>

                    `).join("")}

                </tbody>

            </table>

        </div>

        <p style="color:#829bb5;font-size:11px;margin-top:12px;">

            Os dispositivos já cadastrados não podem ser selecionados novamente.

        </p>

    `;

    $("#select-all-discovered")?.addEventListener(

        "change",

        event => {

            container

                .querySelectorAll(".discovered-device-checkbox")

                .forEach(checkbox => {

                    checkbox.checked = event.target.checked;

                });

            updateRegisterButton();

        }

    );

    container

        .querySelectorAll(".discovered-device-checkbox")

        .forEach(checkbox => {

            checkbox.addEventListener(

                "change",

                updateRegisterButton

            );

        });

    $("#register-selected-devices")?.addEventListener(

        "click",

        registerSelectedDevices

    );

}

/* =====================================================

   ATUALIZAR BOTAO DE CADASTRO

===================================================== */

function updateRegisterButton() {

    const selected = document.querySelectorAll(

        ".discovered-device-checkbox:checked"

    );

    const button = $("#register-selected-devices");

    if (button) {

        button.disabled = selected.length === 0;

    }

}

/* =====================================================

   CADASTRAR DISPOSITIVOS SELECIONADOS

===================================================== */

async function registerSelectedDevices() {

    const selectedIndexes = Array.from(

        document.querySelectorAll(

            ".discovered-device-checkbox:checked"

        )

    ).map(checkbox =>

        Number(checkbox.dataset.discoveryIndex)

    );

    const selectedDevices = selectedIndexes

        .map(index => discoveredDevicesCache[index])

        .filter(Boolean);

    if (!selectedDevices.length) {

        toast("Selecione pelo menos um dispositivo.", true);

        return;

    }

    const button = $("#register-selected-devices");

    if (button) {

        button.disabled = true;

        button.textContent = "CADASTRANDO...";

    }

    const payload = selectedDevices.map(device => ({

        ip_address: device.ip_address,

        mac_address: device.mac_address,

        device_type: "Desconhecido"

    }));

    try {

        const result = await api(

            "/api/devices/register-discovered",

            {

                method: "POST",

                headers: {

                    "Content-Type": "application/json"

                },

                body: JSON.stringify(payload)

            }

        );

        toast(

            `${result.total_created} dispositivo(s) cadastrado(s).`

        );

        if (result.total_skipped > 0) {

            toast(

                `${result.total_skipped} dispositivo(s) ignorado(s) por duplicidade.`

            );

        }

        await refreshDashboard();

        renderDiscoveredDevices();

        if (universeScene) {

            createUniverse();

        }

    } catch (error) {

        console.error("Erro ao cadastrar dispositivos:", error);

        toast(error.message, true);

        if (button) {

            button.disabled = false;

            button.textContent = "CADASTRAR SELECIONADOS";

        }

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

   NETWORK UNIVERSE — G10 SENTINELHOME

   Inventário visual baseado nos dispositivos da API.

   As linhas são ligações ilustrativas, não tráfego observado.

===================================================== */

let selectedUniverseDevice = null;

function getUniverseRisk(device) {

    const raw = device?.risk_score;

    if (raw === null || raw === undefined || raw === "" || !Number.isFinite(Number(raw))) {

        return { level: "SEM DADOS", color: 0x8492a6, css: "unknown" };

    }

    const score = Number(raw);

    if (score >= 70) return { level: "CRÍTICO", color: 0xff416c, css: "critical" };

    if (score >= 40) return { level: "MODERADO", color: 0xffc857, css: "moderate" };

    return { level: "BAIXO", color: 0x00ffb3, css: "low" };

}

function getUniverseStatus(device) {

    const status = String(device?.status || "").trim().toLowerCase();

    if (["online", "ativo", "active", "connected"].includes(status)) return "ATIVO";

    if (["offline", "inativo", "inactive", "disconnected"].includes(status)) return "OFFLINE";

    return status ? status.toUpperCase() : "DESCONHECIDO";

}

function updateUniverseStats() {

    const total = devicesCache.length;

    const active = devicesCache.filter(d => getUniverseStatus(d) === "ATIVO").length;

    const warning = devicesCache.filter(d => getUniverseRisk(d).css === "moderate").length;

    const critical = devicesCache.filter(d => getUniverseRisk(d).css === "critical").length;

    if ($("#universe-total")) $("#universe-total").textContent = total;

    if ($("#universe-active")) $("#universe-active").textContent = active;

    if ($("#universe-warning")) $("#universe-warning").textContent = warning;

    if ($("#universe-critical")) $("#universe-critical").textContent = critical;

}

function selectUniverseDevice(deviceId) {

    const device = devicesCache.find(item => String(item.id) === String(deviceId));

    if (!device) return;

    selectedUniverseDevice = device.id;

    const risk = getUniverseRisk(device);

    const status = getUniverseStatus(device);

    const container = $("#universe-detail-content");

    if (container) {

        const score = device.risk_score === null || device.risk_score === undefined || device.risk_score === ""

            ? "Não calculado"

            : `${Number(device.risk_score).toFixed(1)}%`;

        container.innerHTML = `

            <div class="universe-selected-device">

                <div class="universe-device-icon ${risk.css}"><i class="fa-solid fa-computer"></i></div>

                <h4>${escapeHTML(device.name || "Dispositivo sem nome")}</h4>

                <span class="universe-device-type">${escapeHTML(device.device_type || "Tipo não informado")}</span>

                <div class="universe-detail-divider"></div>

                <div class="universe-detail-row"><span>ENDEREÇO IP</span><strong>${escapeHTML(device.ip_address || "Não informado")}</strong></div>

                <div class="universe-detail-row"><span>ENDEREÇO MAC</span><strong>${escapeHTML(device.mac_address || "Não informado")}</strong></div>

                <div class="universe-detail-row"><span>STATUS CADASTRADO</span><strong>${escapeHTML(status)}</strong></div>

                <div class="universe-detail-row"><span>RISCO</span><strong class="risk-text ${risk.css}">${escapeHTML(score)}</strong></div>

                <div class="universe-detail-row"><span>CLASSIFICAÇÃO</span><strong class="risk-text ${risk.css}">${risk.level}</strong></div>

                <div class="universe-detail-divider"></div>

                <p class="universe-detail-note">Dados provenientes do inventário da API. O status é o valor armazenado e não representa uma sondagem de conectividade em tempo real.</p>

            </div>`;

    }

    document.querySelectorAll("[data-universe-device]").forEach(card => {

        card.classList.toggle("selected", String(card.dataset.universeDevice) === String(deviceId));

    });

    if (universeScene) universeScene.select(deviceId);

}

   function createUniverse() {

    const container = $("#universe-container");

    if (

        !container ||

        !container.clientWidth ||

        !container.clientHeight ||

        typeof THREE === "undefined"

    ) {

        return;

    }

    if (universeScene) {

        universeScene.destroy();

        universeScene = null;

    }

    container.innerHTML = "";

    const scene = new THREE.Scene();

    const camera = new THREE.PerspectiveCamera(55, container.clientWidth / container.clientHeight, 0.1, 100);

    camera.position.set(0, 0, 9);

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });

    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

    renderer.setSize(container.clientWidth, container.clientHeight);

    container.appendChild(renderer.domElement);

    const group = new THREE.Group();

    scene.add(group);

    const core = new THREE.Mesh(

        new THREE.IcosahedronGeometry(0.55, 2),

        new THREE.MeshBasicMaterial({ color: COLORS.cyan, wireframe: true })

    );

    group.add(core);

    const coreRing = new THREE.Mesh(

        new THREE.TorusGeometry(0.85, 0.008, 8, 100),

        new THREE.MeshBasicMaterial({ color: COLORS.purple, transparent: true, opacity: 0.65 })

    );

    coreRing.rotation.x = Math.PI / 2.5;

    group.add(coreRing);

    const innerCore = new THREE.Mesh(

        new THREE.SphereGeometry(0.13, 24, 24),

        new THREE.MeshBasicMaterial({ color: COLORS.cyan })

    );

    group.add(innerCore);

    const nodes = [];

    const total = devicesCache.length;

    devicesCache.forEach((device, index) => {

        const angle = (index / Math.max(total, 1)) * Math.PI * 2;

        const radius = 2.1 + (index % 3) * 0.35;

        const risk = getUniverseRisk(device);

        const position = new THREE.Vector3(

            Math.cos(angle) * radius,

            Math.sin(angle) * radius,

            (index % 3 - 1) * 0.35

        );

        const mesh = new THREE.Mesh(

            new THREE.SphereGeometry(0.13, 24, 24),

            new THREE.MeshBasicMaterial({ color: risk.color })

        );

        mesh.position.copy(position);

        mesh.userData.deviceId = device.id;

        group.add(mesh);

        const ring = new THREE.Mesh(

            new THREE.TorusGeometry(0.21, 0.008, 8, 48),

            new THREE.MeshBasicMaterial({ color: risk.color, transparent: true, opacity: 0.65 })

        );

        ring.position.copy(position);

        group.add(ring);

        const line = new THREE.Line(

            new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), position]),

            new THREE.LineBasicMaterial({ color: risk.color, transparent: true, opacity: 0.45 })

        );

        group.add(line);

        nodes.push({ mesh, ring, line, device });

    });

    const starPositions = [];

    for (let i = 0; i < 350; i++) {

        starPositions.push((Math.random() - 0.5) * 10, (Math.random() - 0.5) * 7, (Math.random() - 0.5) * 5);

    }

    const starGeometry = new THREE.BufferGeometry();

    starGeometry.setAttribute("position", new THREE.Float32BufferAttribute(starPositions, 3));

    const stars = new THREE.Points(starGeometry, new THREE.PointsMaterial({ color: 0x8aaeff, size: 0.018, transparent: true, opacity: 0.7 }));

    scene.add(stars);

    const raycaster = new THREE.Raycaster();

    const pointer = new THREE.Vector2();

    let pointerStart = null;

    let dragging = false;

    let previousX = 0;

    let previousY = 0;

    let animationId = null;

    renderer.domElement.addEventListener("pointerdown", event => {

        pointerStart = { x: event.clientX, y: event.clientY };

        dragging = true;

        previousX = event.clientX;

        previousY = event.clientY;

        renderer.domElement.setPointerCapture(event.pointerId);

    });

    renderer.domElement.addEventListener("pointermove", event => {

        if (!dragging) return;

        const dx = event.clientX - previousX;

        const dy = event.clientY - previousY;

        group.rotation.y += dx * 0.004;

        group.rotation.x += dy * 0.004;

        previousX = event.clientX;

        previousY = event.clientY;

    });

    const finishPointer = event => {

        dragging = false;

        if (!pointerStart) return;

        const moved = Math.hypot(event.clientX - pointerStart.x, event.clientY - pointerStart.y);

        pointerStart = null;

        if (moved > 6 || !nodes.length) return;

        const rect = renderer.domElement.getBoundingClientRect();

        pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;

        pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        raycaster.setFromCamera(pointer, camera);

        const hits = raycaster.intersectObjects(nodes.map(node => node.mesh));

        if (hits.length) selectUniverseDevice(hits[0].object.userData.deviceId);

    };

    renderer.domElement.addEventListener("pointerup", finishPointer);

    renderer.domElement.addEventListener("pointercancel", () => { dragging = false; pointerStart = null; });

    function animate() {

        animationId = requestAnimationFrame(animate);

        if (!dragging) group.rotation.y += 0.001;

        core.rotation.x += 0.002;

        core.rotation.z += 0.0015;

        coreRing.rotation.z += 0.002;

        innerCore.scale.setScalar(1 + Math.sin(Date.now() * 0.002) * 0.08);

        stars.rotation.y -= 0.0001;

        nodes.forEach((node, index) => node.ring.scale.setScalar(1 + Math.sin(Date.now() * 0.002 + index) * 0.08));

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

    const resizeObserver = new ResizeObserver(resize);

    resizeObserver.observe(container);

    universeScene = {

        resize,

        select(deviceId) {

            nodes.forEach(node => {

                const selected = String(node.device.id) === String(deviceId);

                node.mesh.scale.setScalar(selected ? 1.65 : 1);

                node.ring.material.opacity = selected ? 1 : 0.65;

                node.ring.scale.setScalar(selected ? 1.3 : 1);

            });

        },

        destroy() {

            cancelAnimationFrame(animationId);

            resizeObserver.disconnect();

            scene.traverse(object => {

                if (object.geometry) object.geometry.dispose();

                if (object.material) {

                    if (Array.isArray(object.material)) object.material.forEach(material => material.dispose());

                    else object.material.dispose();

                }

            });

            renderer.dispose();

            if (renderer.domElement.parentNode === container) container.removeChild(renderer.domElement);

        }

    };

    if (selectedUniverseDevice !== null) universeScene.select(selectedUniverseDevice);

    if (!total) {

        const message = document.createElement("div");

        message.className = "universe-overlay-message";

        message.textContent = "Nenhum dispositivo cadastrado no inventário.";

        container.appendChild(message);

    }

    renderUniverseDevices();

}

function renderUniverseDevices() {

    const container = $("#universe-devices");

    updateUniverseStats();

    if (!container) return;

    if (!devicesCache.length) {

        container.innerHTML = `<div class="empty-state">Nenhum dispositivo cadastrado na topologia.</div>`;

        return;

    }

    container.innerHTML = devicesCache.map(device => {

        const risk = getUniverseRisk(device);

        const status = getUniverseStatus(device);

        const score = device.risk_score === null || device.risk_score === undefined || device.risk_score === ""

            ? "Não calculado"

            : `${Number(device.risk_score).toFixed(1)}%`;

        const selected = String(selectedUniverseDevice) === String(device.id);

        return `

            <button type="button" class="device-card universe-device-card ${risk.css} ${selected ? "selected" : ""}"

                data-universe-device="${escapeHTML(device.id)}">

                <div class="universe-card-heading">

                    <i class="fa-solid fa-computer"></i>

                    <span class="universe-risk-badge ${risk.css}">${risk.level}</span>

                </div>

                <strong>${escapeHTML(device.name || "Dispositivo sem nome")}</strong>

                <span>IP: ${escapeHTML(device.ip_address || "Não informado")}</span>

                <span>Tipo: ${escapeHTML(device.device_type || "Não informado")}</span>

                <span>Status: ${escapeHTML(status)}</span>

                <span>Risco: ${escapeHTML(score)}</span>

            </button>`;

    }).join("");

    container.querySelectorAll("[data-universe-device]").forEach(card => {

        card.addEventListener("click", () => selectUniverseDevice(card.dataset.universeDevice));

    });

}

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

function renderFuzzyDevices() {

    const select = $("#fuzzy-device");

    if (!select) return;

    const selectedValue = select.value;

    select.innerHTML = "";

    if (!devicesCache.length) {

        select.innerHTML = `

            <option value="">Nenhum dispositivo cadastrado</option>

        `;

        return;

    }

    select.innerHTML = `

        <option value="">Selecione um dispositivo</option>

    `;

    devicesCache.forEach(device => {

        const option = document.createElement("option");

        option.value = device.id;

        option.textContent = `${device.name} — ${device.ip_address}`;

        select.appendChild(option);

    });

    if (

        selectedValue &&

        devicesCache.some(device => String(device.id) === selectedValue)

    ) {

        select.value = selectedValue;

    }

}

async function loadDevices() {

    const data = await api("/api/devices/");

    devicesCache = Array.isArray(data) ? data : [];

renderFuzzyDevices();

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

    const deviceId = $("#fuzzy-device")?.value;

    const packets = Number($("#fuzzy-packets").value);

    const ports = Number($("#fuzzy-ports").value);

    const traffic = Number($("#fuzzy-traffic").value);

    if (!deviceId) {

        toast("Selecione um dispositivo para analisar.", true);

        return;

    }

    const values = [packets, ports, traffic];

    if (values.some(value =>

        !Number.isFinite(value) || value < 0 || value > 100

    )) {

        toast("Os valores devem estar entre 0 e 100.", true);

        return;

    }

    const button = $("#fuzzy-form button[type='submit']");

    if (button) {

        button.disabled = true;

        button.textContent = "CALCULANDO...";

    }

    try {

        const result = await api(

            `/api/devices/${encodeURIComponent(deviceId)}/calculate-risk`,

            {

                method: "POST",

                headers: {

                    "Content-Type": "application/json"

                },

                body: JSON.stringify({

                    packet_score: packets,

                    port_score: ports,

                    traffic_score: traffic

                })

            }

        );

        const score = Number(result.risk_score);

        $("#fuzzy-result").textContent =

            `${score.toFixed(1)}%`;

        $("#fuzzy-level").textContent =

            String(result.classification || "NÃO CLASSIFICADO").toUpperCase();

        $("#fuzzy-explanation").textContent =

            `Análise persistida para o dispositivo ${

                result.device?.name || ""

            }. Evento registrado: ${result.event_id ?? "não informado"}. ` +

            "O índice é uma avaliação heurística, não uma probabilidade de ataque.";

        toast("Risco calculado e registrado no banco de dados.");

        await refreshDashboard();

    } catch (error) {

        console.error("Erro na análise Fuzzy:", error);

        toast(error.message, true);

    } finally {

        if (button) {

            button.disabled = false;

            button.textContent = "EXECUTAR INFERÊNCIA";

        }

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
