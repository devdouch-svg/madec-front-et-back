import { useQuery } from "@tanstack/react-query";
import { productsApi } from "../lib/api/services";
import { fetchPromptinosStats, promptinosListParams, type PromptinosView } from "../lib/promptinos";
import type { PaginatedResponse, Product } from "../lib/types";
import { useDebounce } from "./useDebounce";

export interface PromptinosFilters {
  page: number;
  search: string;
  view: PromptinosView;
}

export function usePromptinosCatalog(filters: PromptinosFilters) {
  const debouncedSearch = useDebounce(filters.search, 300);

  const listQuery = useQuery<PaginatedResponse<Product>>({
    queryKey: ["promptinos", filters.page, debouncedSearch, filters.view],
    queryFn: () =>
      productsApi
        .list(
          promptinosListParams({
            page: filters.page,
            search: debouncedSearch,
            view: filters.view,
          }),
        )
        .then((r) => r.data),
    placeholderData: (prev) => prev,
  });

  const statsQuery = useQuery({
    queryKey: ["promptinos", "stats"],
    queryFn: fetchPromptinosStats,
    staleTime: 60_000,
  });

  const isSearching = filters.search !== debouncedSearch;
  const isInitialLoading = listQuery.isLoading && !listQuery.data;

  return {
    debouncedSearch,
    isSearching,
    isInitialLoading,
    data: listQuery.data,
    isError: listQuery.isError,
    refetch: listQuery.refetch,
    isFetching: listQuery.isFetching,
    stats: statsQuery.data,
  };
}
