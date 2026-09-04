import React from "react";

export type TravelRoute = {
  id: string;
  label: string;
  price: number;
  durationHours: number;
  origin?: string;
  destination?: string;
};

type RouteComparisonMatrixProps = {
  routes: [TravelRoute | null, TravelRoute | null, TravelRoute | null] | null;
  currency?: string;
};

type RouteDiff = {
  vsLabel: string;
  priceDeltaText: string;
  timeDeltaText: string;
};

const formatSignedPercent = (value: number): string =>
  `${Math.abs(value).toFixed(0)}% ${value < 0 ? "cheaper" : "more expensive"}`;

const formatSignedHours = (value: number): string => {
  if (Math.abs(value) < 0.01) return "same travel time";
  return `${Math.abs(value).toFixed(1).replace(/\.0$/, "")} hours ${
    value < 0 ? "faster" : "longer"
  }`;
};

const buildRouteDiffs = (
  currentRoute: TravelRoute,
  allRoutes: TravelRoute[],
): RouteDiff[] => {
  return allRoutes
    .filter((route) => route.id !== currentRoute.id)
    .map((route) => {
      const safePrice = route.price === 0 ? 1 : route.price;
      const pricePercentDelta =
        ((currentRoute.price - route.price) / safePrice) * 100;
      const timeDelta = currentRoute.durationHours - route.durationHours;

      return {
        vsLabel: route.label,
        priceDeltaText: formatSignedPercent(pricePercentDelta),
        timeDeltaText: formatSignedHours(timeDelta),
      };
    });
};

export const RouteComparisonMatrix: React.FC<RouteComparisonMatrixProps> = ({
  routes,
  currency = "USD",
}) => {
  const validRoutes = (routes ?? []).filter(
    (route): route is TravelRoute => route !== null,
  );

  if (validRoutes.length === 0) {
    return (
      <section className="w-full rounded-2xl border border-slate-200 bg-white p-6 text-slate-600 shadow-sm">
        Route comparison is unavailable because route data is missing.
      </section>
    );
  }

  const formatter = new Intl.NumberFormat(undefined, {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  });

  return (
    <section className="w-full rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:p-6">
      <header className="mb-4">
        <h2 className="text-xl font-semibold text-slate-900">
          Route Comparison Matrix
        </h2>
        <p className="text-sm text-slate-600">
          Compare price and duration trade-offs across available routes.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {validRoutes.map((route) => {
          const diffs = buildRouteDiffs(route, validRoutes);

          return (
            <article
              key={route.id}
              className="flex h-full flex-col rounded-xl border border-slate-200 bg-slate-50 p-4"
            >
              <div className="mb-3">
                <h3 className="text-lg font-semibold text-slate-900">
                  {route.label}
                </h3>
                {route.origin && route.destination ? (
                  <p className="text-sm text-slate-500">
                    {route.origin} → {route.destination}
                  </p>
                ) : null}
              </div>

              <div className="mb-4 space-y-1">
                <p className="text-2xl font-bold text-slate-900">
                  {formatter.format(route.price)}
                </p>
                <p className="text-sm text-slate-600">
                  {route.durationHours.toFixed(1).replace(/\.0$/, "")} hours
                </p>
              </div>

              <ul className="mt-auto space-y-2 text-sm text-slate-700">
                {diffs.map((diff) => (
                  <li
                    key={`${route.id}-${diff.vsLabel}`}
                    className="rounded-lg bg-white p-2"
                  >
                    <span className="font-medium text-slate-900">
                      vs {diff.vsLabel}:
                    </span>{" "}
                    {diff.priceDeltaText} but {diff.timeDeltaText}
                  </li>
                ))}
              </ul>
            </article>
          );
        })}
      </div>
    </section>
  );
};

export default RouteComparisonMatrix;
