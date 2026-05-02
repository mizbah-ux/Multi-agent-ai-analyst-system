function showLoading(message = "Processing...") {

    const overlay =
        document.getElementById("loadingOverlay");

    const title =
        document.getElementById("loadingTitle");

    title.textContent = message;

    overlay.classList.add("loading-visible");

    document.body.style.overflow = "hidden";
}

function hideLoading() {

    const overlay =
        document.getElementById("loadingOverlay");

    overlay.classList.remove("loading-visible");

    document.body.style.overflow = "auto";
}