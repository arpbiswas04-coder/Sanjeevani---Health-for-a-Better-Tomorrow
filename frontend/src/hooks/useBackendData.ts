import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/store/authStore';
import { ApiError } from '@/services/httpClient';
import { getData, getDirectory, QueryParams } from '@/services/dataApi';

export function useCapability(permission?: string, global = false): boolean {
  const user = useAuthStore(state => state.user);
  return !!user && (!permission || !!user.backendPermissions?.includes(permission)) && (!global || user.scopeMode === 'global');
}
export function useBackendData<T>(path: string, params: QueryParams = {}, permission?: string, enabled = true, directory = false) {
  const user = useAuthStore(state => state.user);
  const allowed = useCapability(permission);
  const query = useQuery<T, Error>({
    queryKey: ['backend', user?.id, user?.scopeMode, user?.facilityIds, user?.districtIds, user?.backendPermissions, path, params, directory],
    queryFn: () => directory ? getDirectory(path, params) as Promise<T> : getData<T>(path, params),
    enabled: enabled && allowed, retry: false, staleTime: 0,
    refetchOnWindowFocus: true,
  });
  const denied = !user ? new ApiError('Please sign in to continue.', 401)
    : !allowed ? new ApiError(`Permission denied. Requires ${permission}.`, 403) : null;
  return { ...query, error: denied || query.error, data: denied || query.isError ? undefined : query.data,
    waiting: allowed && !enabled, isPending: allowed && enabled && query.isPending };
}
