import { useEffect, useState } from 'react';
import type { ToolManifest, ExecutionEnvelope } from './api/hub';
import { listTools, runTool } from './api/hub';
import { ToolList } from './components/ToolList';
import { ToolForm } from './components/ToolForm';
import { ResultPanel } from './components/ResultPanel';
import { CesiumViewer } from './components/CesiumViewer';
import { MapboxViewer } from './components/MapboxViewer';
import './App.css';

type ViewerMode = 'mapbox' | 'cesium';

export default function App() {
  const [tools, setTools] = useState<ToolManifest[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [result, setResult] = useState<ExecutionEnvelope | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [viewerMode, setViewerMode] = useState<ViewerMode>('mapbox');

  useEffect(() => {
    listTools().then(setTools).catch((e) => setError(e.message));
  }, []);

  const selected = tools.find((t) => t.id === selectedId) ?? null;
  const geojson = result?.result ?? null;
  const display = selected?.output_hints.suggested_display;

  const handleRun = async (params: Record<string, unknown>) => {
    if (!selectedId) return;
    setRunning(true);
    setError(null);
    try {
      const envelope = await runTool(selectedId, null, params);
      setResult(envelope);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error');
      setResult(null);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="app">
      <header>
        <h1>GeoHub Playground</h1>
        <span className="subtitle">Open Source Geospatial Tool Registry</span>
        <div className="viewer-toggle">
          <button
            className={viewerMode === 'mapbox' ? 'active' : ''}
            onClick={() => setViewerMode('mapbox')}
          >
            Mapbox 3D
          </button>
          <button
            className={viewerMode === 'cesium' ? 'active' : ''}
            onClick={() => setViewerMode('cesium')}
          >
            Cesium Globe
          </button>
        </div>
      </header>

      <div className="layout">
        <aside className="sidebar">
          <ToolList tools={tools} selected={selectedId} onSelect={setSelectedId} />
          {selected && (
            <ToolForm tool={selected} onRun={handleRun} running={running} />
          )}
          <ResultPanel result={result} error={error} />
        </aside>

        <main className="viewer">
          {viewerMode === 'mapbox' ? (
            <MapboxViewer geojson={geojson} suggestedDisplay={display} />
          ) : (
            <CesiumViewer geojson={geojson} suggestedDisplay={display} />
          )}
        </main>
      </div>
    </div>
  );
}
