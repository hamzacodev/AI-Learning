import Link from "next/link";

interface AppHeaderProps {
  title: string;
  /** Right hand navigation link, usually pointing at the other page. */
  linkHref: string;
  linkLabel: string;
}

export default function AppHeader({
  title,
  linkHref,
  linkLabel,
}: AppHeaderProps) {
  return (
    <header className="sticky top-0 z-10 border-b border-border bg-bg/90 backdrop-blur">
      <div className="mx-auto flex h-14 w-full max-w-5xl items-center justify-between gap-4 px-5">
        <h1 className="text-base font-semibold text-text-primary">{title}</h1>
        <Link
          href={linkHref}
          className="rounded-md px-2 py-1 text-sm text-text-secondary transition-colors hover:text-accent"
        >
          {linkLabel}
        </Link>
      </div>
    </header>
  );
}
