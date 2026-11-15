import { useMemo } from "react";

import { useGetRolesQuery } from "@/store/api/roleApi";
import { BackendUser } from "../../../../types/api.types";
import { BackendRole } from "../../../../types";

/**
 * Lazily fetches global roles when the modal becomes visible,
 * and returns helpers to look up role details for a user's roles.
 */
export function useUserDetailsData(visible: boolean, user: BackendUser | null) {
  // Lazy load: only hit the endpoint when the modal is visible
  const {
    data: rolesRes,
    isLoading: rolesLoading,
    isFetching,
  } = useGetRolesQuery(undefined, {
    skip: !visible,
  });

  const roles: BackendRole[] = rolesRes?.items ?? [];
  // Mapping roles by their ids
  const roleMap = useMemo(() => roles, [roles]);

  // Function to get role details by role ID
  const getRoleDetails = (roleId: string): BackendRole | undefined =>
    roleMap.find((role) => role.id === roleId);

  return {
    roles,
    rolesLoading: rolesLoading || isFetching,
    getRoleDetails,
  };
}
