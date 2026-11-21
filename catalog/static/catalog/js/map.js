// Main map page: shows today's map with a button for every historical map that
// covers the area on screen. Picking one draws it (rotated into place using its
// saved corners) over today's map. Also an opacity slider and a "Show my
// location" button that puts a blue dot where the visitor is.
(function () {
    "use strict";

    // === DATA FROM THE PAGE ===
    const data = JSON.parse(document.getElementById("viewer-data").textContent);
    const msg = data.messages;
    const buttonsEl = document.getElementById("map-buttons");
    const emptyEl = document.getElementById("map-buttons-empty");
    const opacityInput = document.getElementById("map-opacity");
    const locateButton = document.getElementById("locate-me");
    const statusEl = document.getElementById("viewer-status");

    // === BASE MAP ===
    const map = L.map("viewer-map");
    window.addBasemap(map);

    // Fallback view when there are no maps at all: downtown Harrisonburg
    const DEFAULT_VIEW = [38.4496, -78.8689];

    // === HISTORICAL OVERLAY ===
    let overlay = null;
    let activeId = null;  // id of the map currently drawn, or null

    // The three corners the rotated-image plugin needs, from a map's saved data
    function cornersOf(m) {
        return [m.corners.topleft, m.corners.topright, m.corners.bottomleft];
    }

    // The area a map covers: its 3 saved corners plus the 4th (bottom-right),
    // which sits opposite the top-left corner
    function boundsOf(m) {
        const c = m.corners;
        const bottomright = [
            c.topright[0] + c.bottomleft[0] - c.topleft[0],
            c.topright[1] + c.bottomleft[1] - c.topleft[1],
        ];
        return L.latLngBounds([c.topleft, c.topright, c.bottomleft, bottomright]);
    }

    // Zooms out far enough to see every map (or to the fallback spot if none)
    function showAllMaps() {
        if (data.maps.length) {
            const all = L.latLngBounds([]);
            data.maps.forEach(function (m) { all.extend(boundsOf(m)); });
            map.fitBounds(all, { padding: [20, 20] });
        } else {
            map.setView(DEFAULT_VIEW, 14);
        }
    }

    // Hides the historical map and drops ?map= from the address bar
    function hideMap() {
        if (overlay) map.removeLayer(overlay);
        overlay = null;
        activeId = null;
        history.replaceState(null, "", location.pathname);
        renderButtons();
    }

    // Shows the historical map with this id and zooms to it
    function showMap(id) {
        const m = data.maps.find(function (item) { return item.id === id; });
        if (!m) return;
        activeId = id;
        if (overlay) {
            // Reuse the layer: swap the image and move it to the new corners
            overlay.setUrl(m.imageUrl);
            overlay.reposition(...cornersOf(m));
        } else {
            overlay = L.imageOverlay
                .rotated(m.imageUrl, ...cornersOf(m), { opacity: Number(opacityInput.value) })
                .addTo(map);
        }
        map.fitBounds(boundsOf(m), { padding: [20, 20] });
        // Keep ?map=<id> in the address bar so the view can be shared or bookmarked
        history.replaceState(null, "", "?map=" + id);
        renderButtons();
    }

    // === MAP BUTTONS ===
    // Rebuilds the button row: one button per map that overlaps the view.
    // The shown map always keeps its button so it can be switched off.
    function renderButtons() {
        const view = map.getBounds();
        const here = data.maps.filter(function (m) {
            return m.id === activeId || boundsOf(m).intersects(view);
        });
        buttonsEl.replaceChildren();
        here.forEach(function (m) {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "map-choice";
            button.textContent = m.year + " · " + m.title;
            // aria-pressed tells screen readers which map is on
            button.setAttribute("aria-pressed", String(m.id === activeId));
            button.addEventListener("click", function () {
                // Clicking the map that's already on turns it off
                if (m.id === activeId) hideMap(); else showMap(m.id);
            });
            buttonsEl.appendChild(button);
        });

        // No maps at all: keep the page's own "none aligned yet" message
        if (!data.maps.length) return;

        // Nothing here: say so, and offer a way back to the maps
        emptyEl.replaceChildren();
        if (!here.length) {
            emptyEl.append(msg.noneHere + " ");
            const back = document.createElement("button");
            back.type = "button";
            back.className = "link-button";
            back.textContent = msg.showAll;
            back.addEventListener("click", showAllMaps);
            emptyEl.appendChild(back);
        }
    }

    // Panning, zooming, and the GPS re-center all end in "moveend"
    map.on("moveend", renderButtons);

    // Opacity slider
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
    // A ?map=<id> link opens that map; otherwise zoom out to show every map's button
    if (data.selected !== null) showMap(data.selected); else showAllMaps();
})();
