import type { Metadata } from "next";
import { HealthReport } from "@/components/health/health-report";

export const metadata: Metadata = {
  title: "Health report",
  description:
    "Baseline vs fixed evaluation metrics, citation accuracy, abstention behaviour, latency and a gallery of retrieval failures.",
};

const STATS = [
  { value: "80", label: "questions" },
  { value: "5", label: "categories" },
  { value: "7", label: "failure modes" },
];

export default function HealthPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 pb-4 pt-10 sm:px-6 sm:pt-14 lg:px-8">
      <section className="lg:flex lg:items-end lg:justify-between lg:gap-12">
        <div className="max-w-3xl">
          <div className="flex items-center gap-3">
            <span aria-hidden="true" className="h-px w-8 bg-moss" />
            <p className="eyebrow">Evaluation · Helios 80-question set</p>
          </div>
          <h1 className="mt-4 font-display text-[2.75rem] leading-[1.02] tracking-[-0.035em] text-ink sm:text-[3.9rem]">
            Health <span className="italic text-ember">report.</span>
          </h1>
          <p className="mt-4 max-w-2xl text-[0.96rem] leading-7 text-muted">
            The fixed pipeline is measured against the baseline on the same questions and the same
            deterministic metrics. The report keeps the main failures visible: stale versions,
            wrong pages, missed details, weak abstention and conflicting versions. Prompt-injection
            and tenant-isolation checks live in the security tests.
          </p>
        </div>

        <dl className="mt-8 grid grid-cols-3 divide-x divide-line overflow-hidden rounded-2xl border border-line bg-surface/60 sm:mt-8 sm:max-w-md lg:mt-0 lg:min-w-[21rem]">
          {STATS.map((stat) => (
            <div key={stat.label} className="px-4 py-3.5 sm:px-5">
              <dt className="font-mono text-[0.6rem] uppercase tracking-[0.13em] text-muted">
                {stat.label}
              </dt>
              <dd className="mt-1 font-display text-2xl leading-none text-ink">{stat.value}</dd>
            </div>
          ))}
        </dl>
      </section>

      <HealthReport />
    </div>
  );
}
