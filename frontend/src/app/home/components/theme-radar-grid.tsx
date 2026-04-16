import ThemeRadarCard from "@/app/home/components/theme-radar-card";
import type { ThemeRadarItem } from "@/types/theme-radar";

export default function ThemeRadarGrid({ items }: { items: ThemeRadarItem[] }) {
  return (
    <section className="grid gap-4 xl:grid-cols-2">
      {items.map((item) => (
        <ThemeRadarCard key={item.theme_code} item={item} />
      ))}
    </section>
  );
}
