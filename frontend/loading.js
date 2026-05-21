const ThinkingLoader = (() => {
    const SVG_NS = "http://www.w3.org/2000/svg";
    const config = {
        rotate: true,
        particleCount: 68,
        trailSpan: 0.39,
        durationMs: 4700,
        rotationDurationMs: 30000,
        pulseDurationMs: 4200,
        strokeWidth: 5.5,
        baseRadius: 7,
        detailAmplitude: 3,
        petalCount: 9,
        curveScale: 3.9
    };

    let initialized = false;
    let startedAt = 0;
    let animationFrame = null;
    let group = null;
    let path = null;
    let particles = [];

    function point(progress, detailScale) {
        const t = progress * Math.PI * 2;
        const petals = Math.round(config.petalCount);
        const x = config.baseRadius * Math.cos(t) -
            config.detailAmplitude * detailScale * Math.cos(petals * t);
        const y = config.baseRadius * Math.sin(t) -
            config.detailAmplitude * detailScale * Math.sin(petals * t);
        return {
            x: 50 + x * config.curveScale,
            y: 50 + y * config.curveScale
        };
    }

    function normalizeProgress(progress) {
        return ((progress % 1) + 1) % 1;
    }

    function getDetailScale(time) {
        const pulseProgress = (time % config.pulseDurationMs) / config.pulseDurationMs;
        const pulseAngle = pulseProgress * Math.PI * 2;
        return 0.52 + ((Math.sin(pulseAngle + 0.55) + 1) / 2) * 0.48;
    }

    function getRotation(time) {
        if (!config.rotate) {
            return 0;
        }
        return -((time % config.rotationDurationMs) / config.rotationDurationMs) * 360;
    }

    function buildPath(detailScale, steps = 480) {
        return Array.from({ length: steps + 1 }, (_, index) => {
            const curvePoint = point(index / steps, detailScale);
            return `${index === 0 ? "M" : "L"} ${curvePoint.x.toFixed(2)} ${curvePoint.y.toFixed(2)}`;
        }).join(" ");
    }

    function getParticle(index, progress, detailScale) {
        const tailOffset = index / (config.particleCount - 1);
        const curvePoint = point(normalizeProgress(progress - tailOffset * config.trailSpan), detailScale);
        const fade = Math.pow(1 - tailOffset, 0.56);
        return {
            x: curvePoint.x,
            y: curvePoint.y,
            radius: 0.9 + fade * 2.7,
            opacity: 0.04 + fade * 0.96
        };
    }

    function render(now) {
        if (!group || !path) {
            return;
        }
        const time = now - startedAt;
        const progress = (time % config.durationMs) / config.durationMs;
        const detailScale = getDetailScale(time);
        group.setAttribute("transform", `rotate(${getRotation(time)} 50 50)`);
        path.setAttribute("d", buildPath(detailScale));
        particles.forEach((node, index) => {
            const particle = getParticle(index, progress, detailScale);
            node.setAttribute("cx", particle.x.toFixed(2));
            node.setAttribute("cy", particle.y.toFixed(2));
            node.setAttribute("r", particle.radius.toFixed(2));
            node.setAttribute("opacity", particle.opacity.toFixed(3));
        });
        animationFrame = requestAnimationFrame(render);
    }

    function init() {
        if (initialized) {
            return;
        }
        group = document.getElementById("thinkingLoaderGroup");
        path = document.getElementById("thinkingLoaderPath");
        if (!group || !path) {
            return;
        }
        path.setAttribute("stroke-width", String(config.strokeWidth));
        particles = Array.from({ length: config.particleCount }, () => {
            const circle = document.createElementNS(SVG_NS, "circle");
            circle.setAttribute("fill", "currentColor");
            group.appendChild(circle);
            return circle;
        });
        initialized = true;
    }

    function start() {
        init();
        if (!initialized || animationFrame) {
            return;
        }
        if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
            path.setAttribute("d", buildPath(0.8));
            return;
        }
        startedAt = performance.now();
        animationFrame = requestAnimationFrame(render);
    }

    function stop() {
        if (animationFrame) {
            cancelAnimationFrame(animationFrame);
            animationFrame = null;
        }
    }

    return { start, stop };
})();

function showLoading(message = "Processing...") {

    const overlay =
        document.getElementById("loadingOverlay");

    const title =
        document.getElementById("loadingTitle");

    title.textContent = message;

    overlay.classList.add("loading-visible");

    document.body.style.overflow = "hidden";

    ThinkingLoader.start();
}

function hideLoading() {

    const overlay =
        document.getElementById("loadingOverlay");

    overlay.classList.remove("loading-visible");

    document.body.style.overflow = "auto";

    ThinkingLoader.stop();
}
