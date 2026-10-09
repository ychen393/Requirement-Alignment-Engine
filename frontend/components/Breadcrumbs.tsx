import Link from "next/link";

export function Breadcrumbs({ items }: { items: string[] }) {
  return (
    <div className="breadcrumbs">
      <Link href="/">⌂ 工作台</Link>
      {items.map((item) => <span key={item}>/　{item}</span>)}
    </div>
  );
}
