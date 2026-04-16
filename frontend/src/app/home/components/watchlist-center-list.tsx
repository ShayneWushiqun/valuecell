import WatchlistCenterCard from "@/app/home/components/watchlist-center-card";
import type { WatchlistCenterItem } from "@/types/watchlist-center";

export default function WatchlistCenterList({
  items,
}: {
  items: WatchlistCenterItem[];
}) {
  return (
    <section className="grid gap-4 xl:grid-cols-2">
      {items.map((item) => (
        <WatchlistCenterCard key={item.ticker} item={item} />
      ))}
    </section>
  );
}
