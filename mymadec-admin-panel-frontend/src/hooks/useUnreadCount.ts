import { useQuery } from "@tanstack/react-query";
import api from "../lib/api";
import type { UnreadCount } from "../lib/types";

/** Shared unread-count query — subscribe once per layout tree. */
export function useUnreadCount() {
  return useQuery<UnreadCount>({
    queryKey: ["unread-count"],
    queryFn: () => api.get("/notifications/unread-count").then((r) => r.data),
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}
