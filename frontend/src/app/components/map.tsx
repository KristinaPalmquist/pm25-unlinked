'use client';
import { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

export default function Map() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);

  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    try {
      map.current = new maplibregl.Map({
        container: mapContainer.current,
        style: {
          version: 8,
          sources: {
            'osm-tiles': {
              type: 'raster',
              tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
              tileSize: 256,
              attribution: '\u00A9 OpenStreetMap',
            },
          },
          layers: [
            {
              id: 'osm-tiles',
              type: 'raster',
              source: 'osm-tiles',
            },
          ],
        },
        center: [11.9746, 57.7089],
        zoom: 12,
        maxZoom: 15,
        minZoom: 8,
        maxBounds: [
          [11.4, 57.4],
          [12.5, 58.0],
        ],
      });
    } catch (error) {
      console.error('Map initialization error:', error);
    }

    return () => {
      map.current?.remove();
    };
  }, []);

  return (
    <div ref={mapContainer} style={{ width: '100%', height: '100vh', margin: 0, padding: 0 }} />
  );
}
