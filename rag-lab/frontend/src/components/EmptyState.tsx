interface EmptyStateProps {
  title: string;
  description: string;
  children?: React.ReactNode;
}

export default function EmptyState({
  title,
  description,
  children,
}: EmptyStateProps) {
  return (
    <div className="rounded-xl border border-dashed border-border bg-bg-panel px-6 py-12 text-center">
      <h2 className="text-base font-semibold text-text-primary">{title}</h2>
      <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-text-secondary">
        {description}
      </p>
      {children && <div className="mt-5">{children}</div>}
    </div>
  );
}
