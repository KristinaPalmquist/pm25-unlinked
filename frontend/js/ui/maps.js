export function initMap(config) {
  const map = new maplibregl.Map({
    container: "map",
    style: {
      version: 8,
      sources: {
        osm: {
          type: "raster",
          tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
          tileSize: 256,
          attribution: "© OpenStreetMap",
        },
      },
      layers: [{ id: "osm", type: "raster", source: "osm" }],
    },
    center: config.mapCenter,
    zoom: config.mapZoom,
    maxZoom: 14,
    maxBounds: [
      [config.mapBounds[0], config.mapBounds[1]],
      [config.mapBounds[2], config.mapBounds[3]],
    ],
  });

  map.addControl(new maplibregl.NavigationControl(), "top-right");

  return map;
}
