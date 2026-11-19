// Shared present-day base map for every Leaflet page (georeference tool, map viewer).
// OpenStreetMap's standard tiles: free, no API key. Their volunteer-run server
// has a usage policy (https://operations.osmfoundation.org/policies/tiles/):
// - Requests must carry a Referer. Django's default Referrer-Policy (same-origin)
//   strips it, so referrerPolicy below sends just our origin (never the page path).
// - Show the OSM attribution (below), and don't disable the browser cache.
// If tiles show "Access blocked", check DevTools "Disable cache" and privacy
// extensions first. A busy public deployment should switch to a tile provider
// with an API key; to change providers, edit only this file.
window.addBasemap = function (map) {
    return L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        referrerPolicy: "strict-origin-when-cross-origin",
        attribution:
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);
};
