import { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

interface Props {
  geojson: GeoJSON.FeatureCollection | null;
  suggestedDisplay?: string;
}

const SOURCE_ID = 'tool-result';
const FILL_LAYER = 'tool-result-fill';
const LINE_LAYER = 'tool-result-line';
const POINT_LAYER = 'tool-result-points';

export function MapboxViewer({ geojson }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const token = import.meta.env.VITE_MAPBOX_TOKEN ?? '';
    if (!token) {
      console.warn('Set VITE_MAPBOX_TOKEN for Mapbox viewer');
      return;
    }

    mapboxgl.accessToken = token;

    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: 'mapbox://styles/mapbox/satellite-streets-v12',
      center: [-98.58, 39.83],
      zoom: 3.5,
      pitch: 45,
      bearing: 0,
      projection: 'globe',
      antialias: true,
    });

    map.addControl(new mapboxgl.NavigationControl(), 'bottom-right');

    map.on('style.load', () => {
      // 3D terrain
      map.setTerrain({ source: 'mapbox-dem', exaggeration: 1.5 });

      map.addSource('mapbox-dem', {
        type: 'raster-dem',
        url: 'mapbox://mapbox.mapbox-terrain-dem-v1',
        tileSize: 512,
        maxzoom: 14,
      });

      // Atmosphere / sky
      map.setFog({
        color: 'rgb(10, 10, 20)',
        'high-color': 'rgb(30, 30, 60)',
        'horizon-blend': 0.08,
        'space-color': 'rgb(5, 5, 15)',
        'star-intensity': 0.6,
      });
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update GeoJSON when results change
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    // Remove existing layers/source
    [POINT_LAYER, LINE_LAYER, FILL_LAYER].forEach((id) => {
      if (map.getLayer(id)) map.removeLayer(id);
    });
    if (map.getSource(SOURCE_ID)) map.removeSource(SOURCE_ID);

    if (!geojson || geojson.features.length === 0) return;

    map.addSource(SOURCE_ID, { type: 'geojson', data: geojson });

    // Polygon fills
    map.addLayer({
      id: FILL_LAYER,
      type: 'fill',
      source: SOURCE_ID,
      filter: ['==', ['geometry-type'], 'Polygon'],
      paint: {
        'fill-color': '#00D4FF',
        'fill-opacity': 0.2,
      },
    });

    // Lines + polygon outlines
    map.addLayer({
      id: LINE_LAYER,
      type: 'line',
      source: SOURCE_ID,
      filter: ['any',
        ['==', ['geometry-type'], 'Polygon'],
        ['==', ['geometry-type'], 'LineString'],
        ['==', ['geometry-type'], 'MultiLineString'],
      ],
      paint: {
        'line-color': '#00D4FF',
        'line-width': 2,
        'line-opacity': 0.85,
      },
    });

    // Points
    map.addLayer({
      id: POINT_LAYER,
      type: 'circle',
      source: SOURCE_ID,
      filter: ['==', ['geometry-type'], 'Point'],
      paint: {
        'circle-radius': 6,
        'circle-color': '#FF6B35',
        'circle-stroke-color': '#fff',
        'circle-stroke-width': 1,
        'circle-opacity': 0.9,
      },
    });

    // Popups on click
    [POINT_LAYER, FILL_LAYER, LINE_LAYER].forEach((layerId) => {
      map.on('click', layerId, (e) => {
        if (!e.features?.[0]) return;
        const props = e.features[0].properties ?? {};
        const html = Object.entries(props)
          .map(([k, v]) => `<b>${k}:</b> ${v}`)
          .join('<br/>');
        new mapboxgl.Popup({ maxWidth: '300px' })
          .setLngLat(e.lngLat)
          .setHTML(`<div style="font-size:12px">${html}</div>`)
          .addTo(map);
      });
      map.on('mouseenter', layerId, () => { map.getCanvas().style.cursor = 'pointer'; });
      map.on('mouseleave', layerId, () => { map.getCanvas().style.cursor = ''; });
    });

    // Fly to results
    const bounds = new mapboxgl.LngLatBounds();
    for (const f of geojson.features) {
      if (!f.geometry) continue;
      const coords = f.geometry.type === 'Point'
        ? [f.geometry.coordinates as [number, number]]
        : f.geometry.type === 'Polygon'
          ? (f.geometry.coordinates as [number, number][][])[0]
          : f.geometry.type === 'MultiLineString'
            ? (f.geometry.coordinates as [number, number][][]).flat()
            : f.geometry.type === 'LineString'
              ? f.geometry.coordinates as [number, number][]
              : [];
      for (const c of coords) bounds.extend(c as [number, number]);
    }
    if (!bounds.isEmpty()) {
      map.fitBounds(bounds, { padding: 60, maxZoom: 15, duration: 1500 });
    }
  }, [geojson]);

  return <div ref={containerRef} className="map-container" />;
}
