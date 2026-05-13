import * as THREE from "https://esm.sh/three@0.164.1";
import gsap from "https://esm.sh/gsap@3.12.5";
import { ScrollTrigger } from "https://esm.sh/gsap@3.12.5/ScrollTrigger";
import Lenis from "https://esm.sh/@studio-freight/lenis@1.0.42";

gsap.registerPlugin(ScrollTrigger);

const canvas = document.getElementById("ai-os-canvas");
const hudStage = document.getElementById("hudStage");
const cursorOrbit = document.querySelector(".cursor-orbit");
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: false,
    powerPreference: "high-performance"
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.8));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x02040a, 0.032);

const camera = new THREE.PerspectiveCamera(58, window.innerWidth / window.innerHeight, 0.1, 260);
camera.position.set(0, 4.2, 26);

const clock = new THREE.Clock();
const pointer = new THREE.Vector2(0, 0);
const targetPointer = new THREE.Vector2(0, 0);
const chapters = [
    { start: 0, end: 0.16, name: "Chaos Field" },
    { start: 0.16, end: 0.33, name: "AI Core Online" },
    { start: 0.33, end: 0.56, name: "Agent Civilization" },
    { start: 0.56, end: 0.73, name: "Global Execution" },
    { start: 0.73, end: 0.88, name: "Self Evolution" },
    { start: 0.88, end: 1, name: "Autonomous Work OS" }
];

let scrollProgress = 0;
let activeStage = "";

const cyan = new THREE.Color("#39f5ff");
const purple = new THREE.Color("#b25cff");
const blue = new THREE.Color("#2b7cff");
const red = new THREE.Color("#ff4164");

const ambient = new THREE.AmbientLight(0x4e6eff, 0.32);
scene.add(ambient);

const keyLight = new THREE.PointLight(0x39f5ff, 76, 120);
keyLight.position.set(-15, 16, 20);
scene.add(keyLight);

const bloomLight = new THREE.PointLight(0xb25cff, 58, 130);
bloomLight.position.set(20, -8, -22);
scene.add(bloomLight);

const root = new THREE.Group();
const chaosGroup = new THREE.Group();
const coreGroup = new THREE.Group();
const agentsGroup = new THREE.Group();
const worldGroup = new THREE.Group();
scene.add(root);
root.add(chaosGroup, coreGroup, agentsGroup, worldGroup);

function clamp(value, min = 0, max = 1) {
    return Math.min(max, Math.max(min, value));
}

function mapRange(value, inMin, inMax, outMin, outMax) {
    const t = clamp((value - inMin) / (inMax - inMin));
    return outMin + (outMax - outMin) * t;
}

function smoothstep(edge0, edge1, value) {
    const x = clamp((value - edge0) / (edge1 - edge0));
    return x * x * (3 - 2 * x);
}

function makeTextTexture(title, meta, accent = "#39f5ff") {
    const c = document.createElement("canvas");
    c.width = 640;
    c.height = 280;
    const ctx = c.getContext("2d");
    const gradient = ctx.createLinearGradient(0, 0, 640, 280);
    gradient.addColorStop(0, "rgba(8, 20, 38, 0.92)");
    gradient.addColorStop(1, "rgba(18, 9, 42, 0.78)");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, c.width, c.height);
    ctx.strokeStyle = "rgba(155, 232, 255, 0.42)";
    ctx.lineWidth = 3;
    ctx.strokeRect(12, 12, c.width - 24, c.height - 24);
    ctx.fillStyle = accent;
    ctx.shadowColor = accent;
    ctx.shadowBlur = 20;
    ctx.font = "700 42px Inter, sans-serif";
    ctx.fillText(title, 46, 86);
    ctx.shadowBlur = 0;
    ctx.fillStyle = "rgba(234, 247, 255, 0.72)";
    ctx.font = "500 26px Inter, sans-serif";
    ctx.fillText(meta, 46, 132);
    ctx.strokeStyle = "rgba(57, 245, 255, 0.24)";
    for (let i = 0; i < 7; i += 1) {
        const y = 174 + i * 13;
        ctx.beginPath();
        ctx.moveTo(46, y);
        ctx.lineTo(574 - Math.random() * 180, y);
        ctx.stroke();
    }
    const texture = new THREE.CanvasTexture(c);
    texture.colorSpace = THREE.SRGBColorSpace;
    return texture;
}

const chaosLabels = [
    ["Unread Email", "4,281 unresolved threads"],
    ["CRM Card", "Pipeline drift detected"],
    ["Slack Pulse", "17 priority escalations"],
    ["Spreadsheet", "Manual reconciliation"],
    ["API Failure", "Webhook latency spike"],
    ["Dashboard", "Metrics disagreeing"],
    ["Ticket Queue", "Support backlog rising"],
    ["Calendar", "Campaign blockers"]
];

chaosLabels.forEach((item, index) => {
    const material = new THREE.MeshBasicMaterial({
        map: makeTextTexture(item[0], item[1], index % 3 === 0 ? "#ff4164" : "#39f5ff"),
        transparent: true,
        opacity: 0.86,
        side: THREE.DoubleSide
    });
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(5.2, 2.25), material);
    const angle = index * 0.78;
    const radius = 10 + (index % 4) * 3;
    mesh.position.set(Math.cos(angle) * radius, Math.sin(index * 1.8) * 5.2, Math.sin(angle) * radius - 3);
    mesh.rotation.set(Math.random() * 0.8, angle + Math.PI, Math.random() * 0.35);
    mesh.userData = {
        speed: 0.16 + Math.random() * 0.26,
        drift: new THREE.Vector3(Math.random() - 0.5, Math.random() - 0.5, Math.random() - 0.5)
    };
    chaosGroup.add(mesh);
});

function createParticleField(count, radius, colorA, colorB) {
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    for (let i = 0; i < count; i += 1) {
        const r = radius * Math.pow(Math.random(), 0.58);
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);
        positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
        positions[i * 3 + 1] = r * Math.cos(phi) * 0.72;
        positions[i * 3 + 2] = r * Math.sin(phi) * Math.sin(theta);
        const mixed = colorA.clone().lerp(colorB, Math.random());
        colors[i * 3] = mixed.r;
        colors[i * 3 + 1] = mixed.g;
        colors[i * 3 + 2] = mixed.b;
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    const material = new THREE.PointsMaterial({
        size: 0.05,
        vertexColors: true,
        transparent: true,
        opacity: 0.88,
        blending: THREE.AdditiveBlending,
        depthWrite: false
    });
    return new THREE.Points(geometry, material);
}

const dustField = createParticleField(2600, 42, cyan, purple);
root.add(dustField);

const coreShell = new THREE.Mesh(
    new THREE.IcosahedronGeometry(4.2, 4),
    new THREE.MeshStandardMaterial({
        color: 0x071827,
        emissive: 0x123fff,
        emissiveIntensity: 0.45,
        roughness: 0.2,
        metalness: 0.72,
        transparent: true,
        opacity: 0.54,
        wireframe: true
    })
);
coreGroup.add(coreShell);

const innerCore = createParticleField(1100, 4.1, cyan, blue);
coreGroup.add(innerCore);

function createNodeNetwork(count, radius) {
    const group = new THREE.Group();
    const nodes = [];
    const nodeMaterial = new THREE.MeshBasicMaterial({ color: 0x39f5ff, transparent: true, opacity: 0.92 });
    for (let i = 0; i < count; i += 1) {
        const angle = (i / count) * Math.PI * 2;
        const y = Math.sin(i * 1.73) * radius * 0.45;
        const r = radius + Math.sin(i * 2.2) * 1.8;
        const node = new THREE.Mesh(new THREE.SphereGeometry(0.09 + (i % 4) * 0.025, 12, 12), nodeMaterial.clone());
        node.position.set(Math.cos(angle) * r, y, Math.sin(angle) * r);
        group.add(node);
        nodes.push(node.position.clone());
    }

    const linePositions = [];
    for (let i = 0; i < nodes.length; i += 1) {
        for (let j = i + 1; j < nodes.length; j += 1) {
            if (nodes[i].distanceTo(nodes[j]) < 4.7 || Math.random() > 0.965) {
                linePositions.push(nodes[i].x, nodes[i].y, nodes[i].z, nodes[j].x, nodes[j].y, nodes[j].z);
            }
        }
    }
    const lineGeometry = new THREE.BufferGeometry();
    lineGeometry.setAttribute("position", new THREE.Float32BufferAttribute(linePositions, 3));
    const lines = new THREE.LineSegments(
        lineGeometry,
        new THREE.LineBasicMaterial({
            color: 0x39f5ff,
            transparent: true,
            opacity: 0.22,
            blending: THREE.AdditiveBlending
        })
    );
    group.add(lines);
    return group;
}

const neuralNetwork = createNodeNetwork(72, 7.8);
coreGroup.add(neuralNetwork);
coreGroup.scale.setScalar(0.1);
coreGroup.position.set(0, 0, -3);

const agentSystems = [
    { name: "Planner", x: -14, y: 4, z: -20, color: cyan },
    { name: "Supervisor", x: 12, y: -1.5, z: -28, color: purple },
    { name: "Executor", x: -11, y: -5, z: -38, color: blue },
    { name: "Analyst", x: 14, y: 5, z: -48, color: cyan }
];

agentSystems.forEach((agent, index) => {
    const group = new THREE.Group();
    const ringMaterial = new THREE.MeshBasicMaterial({
        color: agent.color,
        transparent: true,
        opacity: 0.42,
        side: THREE.DoubleSide,
        blending: THREE.AdditiveBlending
    });
    for (let r = 0; r < 4; r += 1) {
        const ring = new THREE.Mesh(new THREE.TorusGeometry(1.5 + r * 0.58, 0.012, 10, 96), ringMaterial.clone());
        ring.rotation.set(Math.PI / 2 + r * 0.22, r * 0.35, index * 0.4);
        group.add(ring);
    }
    const spine = createNodeNetwork(24, 2.9);
    spine.scale.setScalar(0.72);
    group.add(spine);
    group.position.set(agent.x, agent.y, agent.z);
    agentsGroup.add(group);
});

const world = new THREE.Mesh(
    new THREE.SphereGeometry(6.2, 48, 48),
    new THREE.MeshBasicMaterial({
        color: 0x071a2e,
        transparent: true,
        opacity: 0.42,
        wireframe: true
    })
);
worldGroup.add(world);

const cityPoints = [
    [-74, 40.7],
    [-0.1, 51.5],
    [77.6, 12.9],
    [139.7, 35.6],
    [103.8, 1.35],
    [55.3, 25.2]
];

function latLonToVector3(lon, lat, radius) {
    const phi = (90 - lat) * Math.PI / 180;
    const theta = (lon + 180) * Math.PI / 180;
    return new THREE.Vector3(
        -radius * Math.sin(phi) * Math.cos(theta),
        radius * Math.cos(phi),
        radius * Math.sin(phi) * Math.sin(theta)
    );
}

cityPoints.forEach(([lon, lat], index) => {
    const point = latLonToVector3(lon, lat, 6.35);
    const pulse = new THREE.Mesh(
        new THREE.SphereGeometry(0.13, 16, 16),
        new THREE.MeshBasicMaterial({ color: index % 2 ? 0xb25cff : 0x39f5ff })
    );
    pulse.position.copy(point);
    worldGroup.add(pulse);
});

for (let i = 0; i < cityPoints.length; i += 1) {
    const a = latLonToVector3(cityPoints[i][0], cityPoints[i][1], 6.5);
    const b = latLonToVector3(cityPoints[(i + 2) % cityPoints.length][0], cityPoints[(i + 2) % cityPoints.length][1], 6.5);
    const mid = a.clone().add(b).multiplyScalar(0.5).normalize().multiplyScalar(10.4);
    const curve = new THREE.QuadraticBezierCurve3(a, mid, b);
    const arc = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(curve.getPoints(48)),
        new THREE.LineBasicMaterial({
            color: i % 2 ? 0xb25cff : 0x39f5ff,
            transparent: true,
            opacity: 0.42,
            blending: THREE.AdditiveBlending
        })
    );
    worldGroup.add(arc);
}
worldGroup.position.set(0, -2.2, -54);
worldGroup.scale.setScalar(0.22);

const civilization = createNodeNetwork(160, 16);
civilization.position.set(0, 0, -76);
civilization.scale.setScalar(0.04);
root.add(civilization);

const lenis = new Lenis({
    lerp: prefersReducedMotion ? 1 : 0.075,
    wheelMultiplier: 0.85,
    smoothWheel: !prefersReducedMotion
});

function raf(time) {
    lenis.raf(time);
    ScrollTrigger.update();
    requestAnimationFrame(raf);
}
requestAnimationFrame(raf);

ScrollTrigger.create({
    trigger: document.body,
    start: "top top",
    end: "bottom bottom",
    scrub: true,
    onUpdate: (self) => {
        scrollProgress = self.progress;
    }
});

gsap.utils.toArray(".story-section").forEach((section) => {
    gsap.fromTo(section.querySelectorAll(".chapter-kicker, h1, h2, p, .command-console, .task-stream span, .agent-card, .world-ops span, .cta-row a"),
        { y: 80, autoAlpha: 0, filter: "blur(12px)" },
        {
            y: 0,
            autoAlpha: 1,
            filter: "blur(0px)",
            duration: 1.1,
            ease: "power3.out",
            stagger: 0.055,
            scrollTrigger: {
                trigger: section,
                start: "top 65%",
                end: "center 38%",
                scrub: 1
            }
        }
    );
});

document.addEventListener("pointermove", (event) => {
    targetPointer.x = (event.clientX / window.innerWidth) * 2 - 1;
    targetPointer.y = -(event.clientY / window.innerHeight) * 2 + 1;
    cursorOrbit.style.left = `${event.clientX}px`;
    cursorOrbit.style.top = `${event.clientY}px`;
});

document.querySelectorAll(".magnetic").forEach((el) => {
    el.addEventListener("pointermove", (event) => {
        const rect = el.getBoundingClientRect();
        const x = event.clientX - rect.left - rect.width / 2;
        const y = event.clientY - rect.top - rect.height / 2;
        el.style.transform = `translate(${x * 0.12}px, ${y * 0.12}px)`;
    });
    el.addEventListener("pointerleave", () => {
        el.style.transform = "";
    });
});

function updateStage() {
    const chapter = chapters.find((item) => scrollProgress >= item.start && scrollProgress <= item.end) || chapters[chapters.length - 1];
    if (chapter.name !== activeStage) {
        activeStage = chapter.name;
        hudStage.textContent = chapter.name;
    }
}

function updateScene(delta, elapsed) {
    pointer.lerp(targetPointer, 0.06);
    updateStage();

    const chaosIntensity = 1 - smoothstep(0.12, 0.28, scrollProgress);
    const coreBirth = smoothstep(0.12, 0.34, scrollProgress);
    const agentTravel = smoothstep(0.32, 0.58, scrollProgress);
    const globalExec = smoothstep(0.54, 0.74, scrollProgress);
    const evolution = smoothstep(0.72, 0.9, scrollProgress);
    const finalReveal = smoothstep(0.86, 1, scrollProgress);

    const camX = Math.sin(scrollProgress * Math.PI * 2.1) * mapRange(scrollProgress, 0, 1, 2.5, 8) + pointer.x * 1.3;
    const camY = mapRange(scrollProgress, 0, 1, 4.2, 1.2) + pointer.y * 0.9;
    const camZ = mapRange(scrollProgress, 0, 1, 26, -66);
    camera.position.lerp(new THREE.Vector3(camX, camY, camZ), 0.045);
    camera.lookAt(pointer.x * 1.2, pointer.y * 0.8, camera.position.z - 18);

    scene.fog.density = 0.03 + scrollProgress * 0.018;
    keyLight.intensity = 70 + coreBirth * 110 + globalExec * 60;
    bloomLight.intensity = 42 + agentTravel * 90 + evolution * 100;
    keyLight.color.copy(cyan).lerp(blue, globalExec * 0.5);
    bloomLight.color.copy(purple).lerp(cyan, evolution * 0.6);

    chaosGroup.children.forEach((mesh, index) => {
        mesh.rotation.x += delta * mesh.userData.speed * (1.8 + chaosIntensity * 2.5);
        mesh.rotation.y += delta * mesh.userData.speed * (1.2 + chaosIntensity * 2.2);
        const collapse = smoothstep(0.13, 0.31, scrollProgress);
        mesh.position.lerp(new THREE.Vector3(0, 0, -5), collapse * 0.045);
        mesh.material.opacity = 0.86 * chaosIntensity;
        mesh.scale.setScalar(1 + Math.sin(elapsed * 2.4 + index) * 0.025 + collapse * -0.7);
    });

    dustField.rotation.y += delta * (0.015 + scrollProgress * 0.08);
    dustField.rotation.x = pointer.y * 0.06;
    dustField.material.opacity = 0.54 + (1 - chaosIntensity) * 0.22;

    coreGroup.scale.lerp(new THREE.Vector3(0.1 + coreBirth * 1.35, 0.1 + coreBirth * 1.35, 0.1 + coreBirth * 1.35), 0.06);
    coreGroup.rotation.y += delta * (0.15 + coreBirth * 0.7);
    coreGroup.rotation.x += delta * (0.08 + evolution * 0.22);
    coreShell.material.opacity = 0.08 + coreBirth * 0.54;
    innerCore.material.opacity = 0.15 + coreBirth * 0.75;
    neuralNetwork.children.forEach((child, index) => {
        if (child.material) {
            child.material.opacity = child.type === "LineSegments"
                ? 0.12 + coreBirth * 0.24 + evolution * 0.22
                : 0.45 + coreBirth * 0.5;
        }
        child.rotation.y += delta * 0.03 * (index + 1);
    });

    agentsGroup.children.forEach((group, index) => {
        const local = smoothstep(0.33 + index * 0.035, 0.46 + index * 0.04, scrollProgress);
        group.scale.lerp(new THREE.Vector3(local, local, local), 0.08);
        group.rotation.x += delta * (0.07 + local * 0.2);
        group.rotation.z += delta * (0.1 + local * 0.24);
    });

    worldGroup.scale.lerp(new THREE.Vector3(0.22 + globalExec * 1.05, 0.22 + globalExec * 1.05, 0.22 + globalExec * 1.05), 0.06);
    worldGroup.rotation.y += delta * (0.08 + globalExec * 0.42);
    worldGroup.children.forEach((child, index) => {
        if (child.material) {
            child.material.opacity = child.type === "Line" ? 0.1 + globalExec * 0.56 : 0.32 + globalExec * 0.68;
        }
        if (child.isMesh && child.geometry.type === "SphereGeometry") {
            const pulse = 1 + Math.sin(elapsed * (3 + globalExec * 7) + index) * 0.38 * globalExec;
            child.scale.setScalar(pulse);
        }
    });

    civilization.scale.lerp(new THREE.Vector3(0.04 + finalReveal * 0.82, 0.04 + finalReveal * 0.82, 0.04 + finalReveal * 0.82), 0.06);
    civilization.rotation.y += delta * (0.06 + finalReveal * 0.38);
    civilization.rotation.z = Math.sin(elapsed * 0.35) * 0.06 * finalReveal;
    civilization.children.forEach((child) => {
        if (child.material) {
            child.material.opacity = child.type === "LineSegments" ? finalReveal * 0.36 : finalReveal * 0.9;
        }
    });

    root.rotation.y = pointer.x * 0.025;
    root.rotation.x = pointer.y * -0.018;
}

function animate() {
    const delta = Math.min(clock.getDelta(), 0.05);
    const elapsed = clock.elapsedTime;
    updateScene(delta, elapsed);
    renderer.render(scene, camera);
    requestAnimationFrame(animate);
}
animate();

function resize() {
    const width = window.innerWidth;
    const height = window.innerHeight;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.8));
}

window.addEventListener("resize", resize);
