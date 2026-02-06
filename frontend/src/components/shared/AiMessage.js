import ReactMarkdown from 'react-markdown';

export function AiMessage({ text }) {
  if (!text) return null;

  return (
    <div className="ai-response" data-testid="ai-message">
      <ReactMarkdown
        components={{
          p: ({ children }) => (
            <p className="mb-3 last:mb-0 text-sm leading-[1.7] text-foreground/90">{children}</p>
          ),
          h1: ({ children }) => (
            <h3 className="text-base font-bold mt-4 mb-2 text-foreground border-b border-border pb-1">{children}</h3>
          ),
          h2: ({ children }) => (
            <h4 className="text-[15px] font-bold mt-4 mb-2 text-foreground flex items-center gap-2">
              <span className="w-1 h-4 bg-primary rounded-full inline-block" />
              {children}
            </h4>
          ),
          h3: ({ children }) => (
            <h5 className="text-sm font-semibold mt-3 mb-1.5 text-foreground">{children}</h5>
          ),
          ul: ({ children }) => (
            <ul className="mb-3 space-y-1.5 pl-1">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="mb-3 space-y-1.5 pl-1 list-none counter-reset-item">{children}</ol>
          ),
          li: ({ children, ordered, index }) => (
            <li className="text-sm leading-[1.6] flex items-start gap-2">
              <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-primary/60 flex-shrink-0" />
              <span className="text-foreground/85">{children}</span>
            </li>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-foreground">{children}</strong>
          ),
          em: ({ children }) => (
            <em className="text-primary/80 not-italic font-medium">{children}</em>
          ),
          code: ({ children, className }) => {
            const isBlock = className?.includes('language-');
            if (isBlock) {
              return (
                <pre className="bg-secondary/80 border border-border p-3 rounded-lg overflow-x-auto mb-3 mt-2">
                  <code className="text-xs font-mono text-foreground/80 leading-relaxed">{children}</code>
                </pre>
              );
            }
            return (
              <code className="bg-primary/8 text-primary border border-primary/15 px-1.5 py-0.5 rounded text-[13px] font-mono font-medium">
                {children}
              </code>
            );
          },
          pre: ({ children }) => <>{children}</>,
          blockquote: ({ children }) => (
            <blockquote className="border-l-3 border-primary/50 bg-primary/5 pl-4 pr-3 py-2.5 my-3 rounded-r-lg">
              <div className="text-sm text-foreground/80 [&>p]:mb-0">{children}</div>
            </blockquote>
          ),
          hr: () => <hr className="my-4 border-border" />,
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer" className="text-primary font-medium underline underline-offset-2 decoration-primary/40 hover:decoration-primary">
              {children}
            </a>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto mb-3 rounded-lg border border-border">
              <table className="w-full text-sm">{children}</table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-secondary/60">{children}</thead>
          ),
          th: ({ children }) => (
            <th className="px-3 py-2 text-left text-xs font-semibold text-foreground/70 uppercase tracking-wider">{children}</th>
          ),
          td: ({ children }) => (
            <td className="px-3 py-2 text-sm border-t border-border">{children}</td>
          ),
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}
