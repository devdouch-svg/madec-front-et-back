import { useAuth } from "../store/auth";
import type { User } from "./types";
export type AppRole = User["role"];

export const ROLE_LABELS: Record<AppRole, string> = {
  admin: "Administrateur",
  gestionnaire: "Gestionnaire",
  acheteur: "Acheteur",
  service: "Service ETL",
};

export function canAccess(roles: AppRole[] | undefined, userRole?: AppRole): boolean {
  if (!roles || roles.length === 0) return true;
  if (!userRole) return false;
  return roles.includes(userRole);
}

/**
 * Hook: clean role-check helpers derived from the current authenticated user.
 *
 * Usage:
 *   const { isAdmin, isAdminOrGest, isAcheteur, role } = useRole();
 */
export function useRole() {
  const { user } = useAuth();
  const role = user?.role;
  return {
    role,
    isAdmin:        role === "admin",
    isGest:         role === "gestionnaire",
    isAdminOrGest:  role === "admin" || role === "gestionnaire",
    isAcheteur:     role === "acheteur",
    isStaff:        role === "admin" || role === "gestionnaire",
    can: (...roles: AppRole[]) => !!role && (roles as string[]).includes(role),
  };
}
