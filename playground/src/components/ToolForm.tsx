import { useState } from 'react';
import type { ParameterSchema, ToolManifest } from '../api/hub';

interface Props {
  tool: ToolManifest;
  onRun: (params: Record<string, unknown>) => void;
  running: boolean;
}

function ParameterWidget({ param, value, onChange }: {
  param: ParameterSchema;
  value: unknown;
  onChange: (v: unknown) => void;
}) {
  const widget = param.widget === 'auto'
    ? (param.type === 'boolean' ? 'checkbox'
      : param.enum ? 'dropdown'
      : param.min != null && param.max != null ? 'slider'
      : 'textbox')
    : param.widget;

  switch (widget) {
    case 'slider':
      return (
        <div className="widget-slider">
          <input
            type="range"
            min={param.min ?? 0}
            max={param.max ?? 100}
            step={param.step ?? 1}
            value={value as number ?? param.default ?? param.min ?? 0}
            onChange={(e) => onChange(Number(e.target.value))}
          />
          <span className="slider-value">
            {value as number ?? param.default ?? param.min ?? 0}
            {param.unit ? ` ${param.unit}` : ''}
          </span>
        </div>
      );

    case 'checkbox':
      return (
        <input
          type="checkbox"
          checked={value as boolean ?? param.default ?? false}
          onChange={(e) => onChange(e.target.checked)}
        />
      );

    case 'dropdown':
      return (
        <select
          value={value as string ?? param.default ?? ''}
          onChange={(e) => onChange(e.target.value)}
        >
          {param.enum?.map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      );

    default:
      return (
        <input
          type={param.type === 'number' ? 'number' : 'text'}
          value={value as string ?? param.default ?? ''}
          placeholder={param.placeholder ?? ''}
          onChange={(e) => onChange(
            param.type === 'number' ? Number(e.target.value) : e.target.value
          )}
        />
      );
  }
}

export function ToolForm({ tool, onRun, running }: Props) {
  const [params, setParams] = useState<Record<string, unknown>>({});

  const groups = new Map<string, ParameterSchema[]>();
  for (const p of tool.parameters) {
    const g = p.group ?? 'Parameters';
    if (!groups.has(g)) groups.set(g, []);
    groups.get(g)!.push(p);
  }

  const handleRun = () => {
    const merged: Record<string, unknown> = {};
    for (const p of tool.parameters) {
      merged[p.name] = params[p.name] ?? p.default;
    }
    onRun(merged);
  };

  return (
    <div className="tool-form">
      <h3>{tool.name}</h3>
      <p className="tool-form-desc">{tool.description}</p>

      {tool.geometry_input.required && (
        <div className="geometry-hint">
          Draw: {tool.geometry_input.draw_modes.join(', ')}
          {tool.geometry_input.description && ` — ${tool.geometry_input.description}`}
        </div>
      )}

      {[...groups.entries()].map(([group, groupParams]) => (
        <fieldset key={group}>
          <legend>{group}</legend>
          {groupParams.map((p) => (
            <div key={p.name} className="param-row">
              <label>
                {p.name.replace(/_/g, ' ')}
                {p.required && <span className="required">*</span>}
              </label>
              <ParameterWidget
                param={p}
                value={params[p.name]}
                onChange={(v) => setParams({ ...params, [p.name]: v })}
              />
              <small>{p.description}</small>
            </div>
          ))}
        </fieldset>
      ))}

      <button className="run-btn" onClick={handleRun} disabled={running}>
        {running ? 'Running...' : 'Run Tool'}
      </button>

      <div className="tool-meta">
        <span>Mode: {tool.execution.mode}</span>
        <span>Speed: {tool.execution.estimated_duration}</span>
        {tool.output_hints.suggested_display !== 'auto' && (
          <span>Display: {tool.output_hints.suggested_display}</span>
        )}
      </div>
    </div>
  );
}
