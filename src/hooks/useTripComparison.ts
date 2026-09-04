import { useCallback, useEffect, useMemo, useRef, useState } from "react";

export type TripComparisonFilter = "all" | "lowest cost" | "shortest duration";

export interface ComparableRoute {
  cost: number;
  duration: number;
}

export interface TripItineraryState<TRoute> {
  routes: TRoute[];
  loading: boolean;
  error: string | null;
}

export interface UseTripComparisonResult<TRoute> {
  itineraries: [TripItineraryState<TRoute>, TripItineraryState<TRoute>, TripItineraryState<TRoute>];
  displayedRoutes: [TRoute[], TRoute[], TRoute[]];
  filter: TripComparisonFilter;
  setFilter: (filter: TripComparisonFilter) => void;
  showLowestCost: () => void;
  showShortestDuration: () => void;
  showAllRoutes: () => void;
  reloadAll: () => Promise<void>;
  reloadItinerary: (index: 0 | 1 | 2) => Promise<void>;
  isAnyLoading: boolean;
  hasAnyError: boolean;
}

type TripFetcher<TRoute> = () => Promise<TRoute[]>;

interface UseTripComparisonParams<TRoute extends ComparableRoute> {
  fetchItineraryA: TripFetcher<TRoute>;
  fetchItineraryB: TripFetcher<TRoute>;
  fetchItineraryC: TripFetcher<TRoute>;
  initialFilter?: TripComparisonFilter;
}

const defaultItineraryState = <TRoute,>(): TripItineraryState<TRoute> => ({
  routes: [],
  loading: false,
  error: null,
});

const normalizeError = (error: unknown): string => {
  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message;
  }

  if (typeof error === "string" && error.trim().length > 0) {
    return error;
  }

  return "Unable to load routes due to a network error. Please try again.";
};

const getFilteredRoutes = <TRoute extends ComparableRoute>(
  routes: TRoute[],
  filter: TripComparisonFilter,
): TRoute[] => {
  if (filter === "all" || routes.length <= 1) {
    return routes;
  }

  const metric = filter === "lowest cost" ? "cost" : "duration";
  const target = Math.min(...routes.map((route) => route[metric]));

  return routes.filter((route) => route[metric] === target);
};

export const useTripComparison = <TRoute extends ComparableRoute>({
  fetchItineraryA,
  fetchItineraryB,
  fetchItineraryC,
  initialFilter = "all",
}: UseTripComparisonParams<TRoute>): UseTripComparisonResult<TRoute> => {
  const [filter, setFilter] = useState<TripComparisonFilter>(initialFilter);
  const [itineraries, setItineraries] = useState<
    [TripItineraryState<TRoute>, TripItineraryState<TRoute>, TripItineraryState<TRoute>]
  >([defaultItineraryState(), defaultItineraryState(), defaultItineraryState()]);

  const isMountedRef = useRef(true);
  const requestVersionRef = useRef<[number, number, number]>([0, 0, 0]);
  const fetchersRef = useRef<[TripFetcher<TRoute>, TripFetcher<TRoute>, TripFetcher<TRoute>]>([
    fetchItineraryA,
    fetchItineraryB,
    fetchItineraryC,
  ]);

  useEffect(() => {
    fetchersRef.current = [fetchItineraryA, fetchItineraryB, fetchItineraryC];
  }, [fetchItineraryA, fetchItineraryB, fetchItineraryC]);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const reloadItinerary = useCallback(async (index: 0 | 1 | 2) => {
    const nextVersion = requestVersionRef.current[index] + 1;
    requestVersionRef.current[index] = nextVersion;

    setItineraries((current) => {
      const updated = [...current] as [
        TripItineraryState<TRoute>,
        TripItineraryState<TRoute>,
        TripItineraryState<TRoute>,
      ];
      updated[index] = { ...updated[index], loading: true, error: null };
      return updated;
    });

    try {
      const routes = await fetchersRef.current[index]();
      if (!isMountedRef.current || requestVersionRef.current[index] !== nextVersion) {
        return;
      }

      setItineraries((current) => {
        const updated = [...current] as [
          TripItineraryState<TRoute>,
          TripItineraryState<TRoute>,
          TripItineraryState<TRoute>,
        ];
        updated[index] = { routes, loading: false, error: null };
        return updated;
      });
    } catch (error: unknown) {
      if (!isMountedRef.current || requestVersionRef.current[index] !== nextVersion) {
        return;
      }

      setItineraries((current) => {
        const updated = [...current] as [
          TripItineraryState<TRoute>,
          TripItineraryState<TRoute>,
          TripItineraryState<TRoute>,
        ];
        updated[index] = { ...updated[index], loading: false, error: normalizeError(error) };
        return updated;
      });
    }
  }, []);

  const reloadAll = useCallback(async () => {
    await Promise.all([reloadItinerary(0), reloadItinerary(1), reloadItinerary(2)]);
  }, [reloadItinerary]);

  useEffect(() => {
    void reloadAll();
  }, [reloadAll]);

  const displayedRoutes = useMemo<[TRoute[], TRoute[], TRoute[]]>(
    () =>
      itineraries.map((itinerary) => getFilteredRoutes(itinerary.routes, filter)) as [
        TRoute[],
        TRoute[],
        TRoute[],
      ],
    [itineraries, filter],
  );

  const showLowestCost = useCallback(() => setFilter("lowest cost"), []);
  const showShortestDuration = useCallback(() => setFilter("shortest duration"), []);
  const showAllRoutes = useCallback(() => setFilter("all"), []);

  const isAnyLoading = itineraries.some((itinerary) => itinerary.loading);
  const hasAnyError = itineraries.some((itinerary) => itinerary.error !== null);

  return {
    itineraries,
    displayedRoutes,
    filter,
    setFilter,
    showLowestCost,
    showShortestDuration,
    showAllRoutes,
    reloadAll,
    reloadItinerary,
    isAnyLoading,
    hasAnyError,
  };
};
