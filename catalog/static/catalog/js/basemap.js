// Shared present-day base map for every Leaflet page (georeference tool, map viewer).
// USGS The National Map "Topo" tiles: US government, public domain, no API key,
// shows street names. US-only, which fits this app.
// Why not the alternatives (tested 2026-11):
// - tile.openstreetmap.org: its volunteer-run server blocked our browsers
//   ("not following the tile usage policy").
// - CARTO basemaps: now answer "API KEY REQUIRED" on every tile.
// To switch providers later, change only this file.
window.addBasemap = function (map) {
    return L.tileLayer(
        "https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}",
        {
            // The service only has tiles up to zoom 16; Leaflet enlarges them past that
            maxNativeZoom: 16,
            maxZoom: 18,
            attribution:
                'Map tiles: <a href="https://www.usgs.gov/programs/national-geospatial-program/national-map">USGS The National Map</a>',
        }
    ).addTo(map);
};
