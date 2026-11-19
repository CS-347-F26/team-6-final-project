// Staff georeferencing tool: click a spot on the scan, then the same spot on
// today's map, repeat 3+ times, then "Fit & save" sends the pairs to the server,
// which fits the alignment and returns where the image's corners land.
(function () {
    "use strict";

    // === DATA FROM THE PAGE ===
    const data = JSON.parse(document.getElementById("tool-data").textContent);
    const msg = data.messages;
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;
    const statusEl = document.getElementById("georef-status");
    const saveButton = document.getElementById("save-points");
    const opacityInput = document.getElementById("preview-opacity");
    const tableBody = document.getElementById("points-body");

    // === LEFT: THE SCAN ===
    // CRS.Simple treats the image as a flat grid. Leaflet's y axis points up, so
    // image pixel (x, y) is drawn at [lat = -y, lng = x], with the top edge at 0.
    const scanBounds = [[-data.height, 0], [0, data.width]];
    const scanMap = L.map("scan-map", { crs: L.CRS.Simple, minZoom: -3, maxZoom: 3 });
    L.imageOverlay(data.imageUrl, scanBounds).addTo(scanMap);
    scanMap.fitBounds(scanBounds);

    // === RIGHT: TODAY'S MAP ===
    // OpenStreetMap tiles (free, no key); starts at Harrisonburg's Court Square
    const worldMap = L.map("world-map").setView([38.4496, -78.8689], 15);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(worldMap);

    // === STATE ===
    // pairs: finished matches {x, y, lat, lng}; pending: a scan click waiting for its match
    let pairs = data.points.slice();
    let pending = null;
    let preview = null;
    const scanLayer = L.layerGroup().addTo(scanMap);
    const worldLayer = L.layerGroup().addTo(worldMap);

    // A small numbered pin (the number links the two halves of a pair)
    function numberedIcon(label, extraClass) {
        return L.divIcon({
            className: "gcp-marker " + (extraClass || ""),
            html: String(label),
            iconSize: [24, 24],
        });
    }

    // Shows a status line (also read aloud by screen readers)
    function setStatus(text) {
        statusEl.textContent = text;
    }

    // Draws (or updates) the fitted scan on today's map
    function showPreview(corners) {
        if (!corners) return;
        const args = [corners.topleft, corners.topright, corners.bottomleft];
        if (preview) {
            preview.reposition(...args);
        } else {
            preview = L.imageOverlay
                .rotated(data.imageUrl, ...args, { opacity: Number(opacityInput.value) })
                .addTo(worldMap);
        }
    }

    // Redraws pins and the table from the current state
    function render() {
        scanLayer.clearLayers();
        worldLayer.clearLayers();
        tableBody.replaceChildren();

        pairs.forEach(function (p, i) {
            const n = i + 1;
            // Pins on both maps
            L.marker([-p.y, p.x], { icon: numberedIcon(n), keyboard: false }).addTo(scanLayer);
            L.marker([p.lat, p.lng], { icon: numberedIcon(n), keyboard: false }).addTo(worldLayer);

            // Table row with a remove button
            const row = document.createElement("tr");
            row.innerHTML =
                "<td>" + n + "</td>" +
                "<td>" + p.x.toFixed(0) + ", " + p.y.toFixed(0) + "</td>" +
                "<td>" + p.lat.toFixed(5) + ", " + p.lng.toFixed(5) + "</td>";
            const cell = document.createElement("td");
            const remove = document.createElement("button");
            remove.type = "button";
            remove.className = "link-button";
            remove.textContent = msg.remove + " " + n;
            remove.addEventListener("click", function () {
                pairs.splice(i, 1);
                render();
            });
            cell.appendChild(remove);
            row.appendChild(cell);
            tableBody.appendChild(row);
        });

        // A scan click still waiting for its match gets a hollow pin
        if (pending) {
            L.marker([-pending.y, pending.x], {
                icon: numberedIcon(pairs.length + 1, "gcp-pending"),
                keyboard: false,
            }).addTo(scanLayer);
        }

        // Saving needs 3+ pairs and no half-finished pair
        saveButton.disabled = pairs.length < 3 || pending !== null;
        if (pending) setStatus(msg.pickWorld);
        else if (pairs.length < 3) setStatus(msg.needMore + " " + msg.pickScan);
        else setStatus(msg.ready);
    }

    // === CLICKS ===
    // Scan click: remember the pixel (ignore clicks outside the image)
    scanMap.on("click", function (e) {
        const x = e.latlng.lng;
        const y = -e.latlng.lat;
        if (x < 0 || y < 0 || x > data.width || y > data.height) return;
        pending = { x: x, y: y };
        render();
    });

    // Today's-map click: completes the pair started on the scan
    worldMap.on("click", function (e) {
        if (!pending) {
            setStatus(msg.pickScan);
            return;
        }
        pairs.push({ x: pending.x, y: pending.y, lat: e.latlng.lat, lng: e.latlng.lng });
        pending = null;
        render();
    });

    // === SAVE ===
    // Sends all pairs; the server fits them and returns the corners + error
    saveButton.addEventListener("click", async function () {
        saveButton.disabled = true;
        setStatus(msg.saving);
        try {
            const response = await fetch(data.saveUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
                body: JSON.stringify({ points: pairs }),
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error);
            showPreview(result.corners);
            setStatus(msg.saved.replace("%s", result.rms_error.toFixed(1)));
        } catch (error) {
            setStatus(msg.failed + " " + error.message);
        } finally {
            saveButton.disabled = pairs.length < 3;
        }
    });

    // Preview opacity slider
    opacityInput.addEventListener("input", function () {
        if (preview) preview.setOpacity(Number(opacityInput.value));
    });

    // === START ===
    // Show the saved alignment (if any) and zoom today's map to it
    if (data.corners) {
        showPreview(data.corners);
        worldMap.fitBounds([data.corners.topleft, data.corners.topright, data.corners.bottomleft]);
    }
    render();
})();
