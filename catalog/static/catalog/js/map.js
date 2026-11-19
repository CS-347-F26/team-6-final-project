// Public map viewer: draws the chosen historical map (rotated into place using its
// saved corners) over today's map, with a map picker, an opacity slider, and a
// "Show my location" button that puts a blue dot where the visitor is.
(function () {
    "use strict";

    // === DATA FROM THE PAGE ===
    const data = JSON.parse(document.getElementById("viewer-data").textContent);
    const msg = data.messages;
    const select = document.getElementById("map-select");
    const opacityInput = document.getElementById("map-opacity");
    const locateButton = document.getElementById("locate-me");
    const statusEl = document.getElementById("viewer-status");

    // === BASE MAP ===
    const map = L.map("viewer-map");
    window.addBasemap(map);

    // === HISTORICAL OVERLAY ===
    let overlay = null;

    // The three corners the rotated-image plugin needs, from a map's saved data
    function cornersOf(m) {
        return [m.corners.topleft, m.corners.topright, m.corners.bottomleft];
    }

    // Shows the historical map with this id and zooms to it
    function showMap(id) {
        const m = data.maps.find(function (item) { return item.id === id; });
        if (!m) return;
        if (overlay) {
            // Reuse the layer: swap the image and move it to the new corners
            overlay.setUrl(m.imageUrl);
            overlay.reposition(...cornersOf(m));
        } else {
            overlay = L.imageOverlay
                .rotated(m.imageUrl, ...cornersOf(m), { opacity: Number(opacityInput.value) })
                .addTo(map);
        }
        map.fitBounds(cornersOf(m), { padding: [20, 20] });
        // Keep ?map=<id> in the address bar so the view can be shared or bookmarked
        history.replaceState(null, "", "?map=" + id);
    }

    // Picker and opacity slider
    select.addEventListener("change", function () {
        showMap(Number(select.value));
    });
    opacityInput.addEventListener("input", function () {
        if (overlay) overlay.setOpacity(Number(opacityInput.value));
    });

    // === YOUR LOCATION ===
    // Browsers only allow this on https:// or localhost, and only after the visitor agrees
    let dot = null;
    let accuracyRing = null;
    let firstFix = true;

    locateButton.addEventListener("click", function () {
        statusEl.textContent = msg.locating;
        firstFix = true;
        // watch: keep updating as the visitor walks around
        map.locate({ watch: true, enableHighAccuracy: true });
    });

    // Each new position: move the dot (and center on it the first time only, so
    // the map doesn't keep jumping back while the visitor pans around)
    map.on("locationfound", function (e) {
        if (!dot) {
            accuracyRing = L.circle(e.latlng, { radius: e.accuracy, color: "#1a73e8", weight: 1, fillOpacity: 0.1 }).addTo(map);
            dot = L.circleMarker(e.latlng, { radius: 8, color: "#ffffff", weight: 3, fillColor: "#1a73e8", fillOpacity: 1 }).addTo(map);
        } else {
            dot.setLatLng(e.latlng);
            accuracyRing.setLatLng(e.latlng).setRadius(e.accuracy);
        }
        if (firstFix) {
            map.setView(e.latlng, Math.max(map.getZoom(), 16));
            firstFix = false;
        }
        statusEl.textContent = msg.located.replace("%s", Math.round(e.accuracy));
    });

    // Permission denied, no GPS, or not on https
    map.on("locationerror", function (e) {
        statusEl.textContent = msg.locateError + " " + e.message;
    });

    // === START ===
    showMap(data.selected);
})();
