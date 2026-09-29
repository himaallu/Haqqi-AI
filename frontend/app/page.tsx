import { HealthStatus } from "@/components/health-status";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-xl flex-1 flex-col justify-center gap-4 px-4 py-16">
      <h1 className="text-3xl font-semibold">
        Haqqi <span lang="ar">حقي</span>
      </h1>
      <p className="text-muted-foreground">Understand your work rights in the UAE, in your own language.</p>
      <HealthStatus />
    </main>
  );
}
