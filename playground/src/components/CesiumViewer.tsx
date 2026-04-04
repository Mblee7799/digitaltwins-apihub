import { useEffect, useRef } from 'react';
import {
  Viewer,
  GeoJsonDataSource,
  Color,
  Ion,
  Cartesian3,
  Math as CesiumMath,
  createWorldTerrainAsync,
  GoogleMaps,
} from 'cesium';
import 'cesium/Build/Cesium/Widgets/widgets.css';

interface Props {
  geojson: GeoJSON.FeatureCollection | null;
  suggestedDisplay?: string;
}

export function CesiumViewer({ geojson }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<Viewer | null>(null);

  useEffect(() => {
    if (!containerRef.current || viewerRef.current) return;

    const ionToken = import.meta.env.VITE_CESIUM_TOKEN ?? '';
    const googleToken = import.meta.env.VITE_GOOGLE_MAPS_KEY ?? '';

    if (ionToken) Ion.defaultAccessToken = ionToken;

    const viewer = new Viewer(containerRef.current, {
      animation: false,
      timeline: false,
      baseLayerPicker: !googleToken, // hide if using Google tiles
      geocoder: false,
      homeButton: true,
      sceneModePicker: true,
      navigationHelpButton: false,
      fullscreenButton: false,
    });

    // Google Earth imagery if token available
    if (googleToken) {
      GoogleMaps.defaultApiKey = googleToken;
      // Google Photorealistic 3D Tiles can be added via:
      // Cesium.createGooglePhotorealistic3DTileset() once key is set
    }

    // Enable terrain
    createWorldTerrainAsync().then((terrain) => {
      viewer.scene.terrainProvider = terrain;
    }).catch(() => {
      // Fallback to flat terrain if Ion token missing
    });

    // Start looking at CONUS
    viewer.camera.setView({
      destination: Cartesian3.fromDegrees(-98.0, 38.0, 8_000_000),
      orientation: {
        heading: CesiumMath.toRadians(0),
        pitch: CesiumMath.toRadians(-70),
        roll: 0,
      },
    });

    viewerRef.current = viewer;

    return () => {
      viewer.destroy();
      viewerRef.current = null;
    };
  }, []);

  // Update GeoJSON layer
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) return;

    viewer.dataSources.removeAll();

    if (!geojson || geojson.features.length === 0) return;

    GeoJsonDataSource.load(geojson, {
      stroke: Color.fromCssColorString('#00D4FF'),
      fill: Color.fromCssColorString('#00D4FF').withAlpha(0.25),
      strokeWidth: 2,
      markerColor: Color.fromCssColorString('#FF6B35'),
      clampToGround: true,
    }).then((dataSource) => {
      viewer.dataSources.add(dataSource);
      viewer.flyTo(dataSource, { duration: 1.5 });
    });
  }, [geojson]);

  return <div ref={containerRef} className="map-container" />;
}
