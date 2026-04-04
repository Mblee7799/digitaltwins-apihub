const BASE = import.meta.env.VITE_HUB_URL ?? '';

export interface ParameterSchema {
  name: string;
  type: string;
  description: string;
  required: boolean;
  default: unknown;
  widget: string;
  min: number | null;
  max: number | null;
  step: number | null;
  enum: string[] | null;
  placeholder: string | null;
  unit: string | null;
  group: string | null;
}

export interface GeometryInput {
  required: boolean;
  accept: string[];
  draw_modes: string[];
  max_features: number | null;
  description: string;
}

export interface OutputHints {
  geometry_type: string[];
  suggested_display: string;
  label_property: string | null;
  color_property: string | null;
}

export interface ToolManifest {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  tags: string[];
  parameters: ParameterSchema[];
  geometry_input: GeometryInput;
  output_hints: OutputHints;
  execution: { mode: string; estimated_duration: string };
  input_tags: string[];
  output_tags: string[];
}

export interface ExecutionEnvelope {
  execution: {
    tool_id: string;
    tool_version: string;
    execution_id: string;
    execution_time_ms: number;
    feature_count: number;
    crs: string;
    timestamp: string;
    status: string;
  };
  result: GeoJSON.FeatureCollection;
  warnings: string[];
}

export async function listTools(): Promise<ToolManifest[]> {
  const r = await fetch(`${BASE}/api/v1/tools`);
  return r.json();
}

export async function getTool(id: string): Promise<ToolManifest> {
  const r = await fetch(`${BASE}/api/v1/tools/${id}`);
  return r.json();
}

export async function runTool(
  id: string,
  geojson: GeoJSON.FeatureCollection | null,
  parameters: Record<string, unknown>,
): Promise<ExecutionEnvelope> {
  const r = await fetch(`${BASE}/api/v1/tools/${id}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ geojson, parameters }),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: r.statusText }));
    throw new Error(err.detail || 'Tool execution failed');
  }
  return r.json();
}
