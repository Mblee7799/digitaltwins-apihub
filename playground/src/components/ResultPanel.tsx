import type { ExecutionEnvelope } from '../api/hub';

interface Props {
  result: ExecutionEnvelope | null;
  error: string | null;
}

export function ResultPanel({ result, error }: Props) {
  if (error) {
    return (
      <div className="result-panel error">
        <h3>Error</h3>
        <p>{error}</p>
      </div>
    );
  }

  if (!result) return null;

  const { execution, warnings } = result;
  const featureCount = result.result.features.length;

  return (
    <div className="result-panel">
      <h3>Result</h3>
      <div className="exec-info">
        <span>{execution.tool_id} v{execution.tool_version}</span>
        <span>{execution.execution_time_ms}ms</span>
        <span>{featureCount} feature{featureCount !== 1 ? 's' : ''}</span>
        <span>{execution.crs}</span>
      </div>

      {warnings.length > 0 && (
        <div className="warnings">
          {warnings.map((w, i) => <p key={i}>{w}</p>)}
        </div>
      )}

      <div className="feature-table">
        <table>
          <thead>
            <tr>
              <th>Type</th>
              <th>Properties</th>
            </tr>
          </thead>
          <tbody>
            {result.result.features.map((f: GeoJSON.Feature, i: number) => (
              <tr key={i}>
                <td>{f.geometry?.type}</td>
                <td>
                  {Object.entries(f.properties ?? {}).map(([k, v]) => (
                    <span key={k} className="prop">
                      <strong>{k}:</strong> {String(v)}
                    </span>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
