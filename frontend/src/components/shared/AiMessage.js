import ReactMarkdown from 'react-markdown';

export function AiMessage({ text }) {
  if (!text) return null;

  return (
    <div className="ai-message prose prose-sm max-w-none" data-testid="ai-message">
      <ReactMarkdown
        components={{
          p: ({ children }) => <p className="mb-2 last:mb-0 text-sm leading-relaxed">{children}</p>,
          h1: ({ children }) => <h3 className="text-base font-bold mt-3 mb-1.5 text-foreground">{children}</h3>,
          h2: ({ children }) => <h4 className="text-sm font-bold mt-3 mb-1.5 text-foreground">{children}</h4>,
          h3: ({ children }) => <h5 className="text-sm font-semibold mt-2 mb-1 text-foreground">{children}</h5>,
          ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-0.5">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-0.5">{children}</ol>,
          li: ({ children }) => <li className="text-sm leading-relaxed">{children}</li>,
          strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
          em: ({ children }) => <em className="text-primary">{children}</em>,
          code: ({ children, inline }) =>
            inline !== false ? (
              <code className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono text-primary">{children}</code>
            ) : (
              <pre className="bg-muted p-3 rounded-md overflow-x-auto mb-2">
                <code className="text-xs font-mono">{children}</code>
              </pre>
            ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-primary/40 pl-3 my-2 text-muted-foreground italic text-sm">
              {children}
            </blockquote>
          ),
          hr: () => <hr className="my-3 border-border" />,
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer" className="text-primary underline hover:text-primary/80">
              {children}
            </a>
          ),
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}
