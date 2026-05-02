function showToast(message, type = "info") {

    const container =
        document.getElementById("toastContainer");

    const toast = document.createElement("div");

    toast.className = `toast toast-${type}`;

    let icon = "ℹ";

    if (type === "success") {
        icon = "✓";
    }

    if (type === "error") {
        icon = "✕";
    }

    if (type === "warning") {
        icon = "⚠";
    }

    toast.innerHTML = `
        <div class="toast-icon">
            ${icon}
        </div>

        <div class="toast-message">
            ${message}
        </div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add("toast-show");
    }, 10);

    setTimeout(() => {

        toast.classList.remove("toast-show");

        setTimeout(() => {
            toast.remove();
        }, 300);

    }, 3500);
}