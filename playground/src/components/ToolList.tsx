import type { ToolManifest } from '../api/hub';

interface Props {
  tools: ToolManifest[];
  selected: string | null;
  onSelect: (id: string) => void;
}

export function ToolList({ tools, selected, onSelect }: Props) {
  return (
    <div className="tool-list">
      <h3>Tools</h3>
      {tools.map((t) => (
        <button
          key={t.id}
          className={`tool-item ${selected === t.id ? 'active' : ''}`}
          onClick={() => onSelect(t.id)}
        >
          <span className="tool-name">{t.name}</span>
          <span className="tool-version">v{t.version}</span>
          <p className="tool-desc">{t.description}</p>
          <div className="tool-tags">
            {t.tags.map((tag) => (
              <span key={tag} className="tag">{tag}</span>
            ))}
          </div>
        </button>
      ))}
    </div>
  );
}
