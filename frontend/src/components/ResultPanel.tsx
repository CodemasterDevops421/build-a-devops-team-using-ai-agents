import { ReactNode } from 'react';

type ResultPanelProps = {
  title: string;
  result?: ReactNode;
  onCopy?: () => void;
  copyDisabled?: boolean;
  footer?: ReactNode;
};

export function ResultPanel({ title, result, onCopy, copyDisabled, footer }: ResultPanelProps) {
  if (!result) {
    return null;
  }

  return (
    <div className="fade-in">
      <div className="result-toolbar">
        <span className="tag">{title}</span>
        {onCopy && (
          <button type="button" className="secondary-button" onClick={onCopy} disabled={copyDisabled}>
            Copy to clipboard
          </button>
        )}
      </div>
      <div className="output-panel" role="region" aria-live="polite">
        {result}
      </div>
      {footer}
    </div>
  );
}
