import { useEffect, useRef, useMemo } from "react";
import {
  useApiNotificationContext,
  type ApiConfig,
} from "../components/providers/ApiNotificationProvider";

interface UseApiNotificationsOptions {
  apis: ApiConfig[];
}

/**
 * Creates a stable hash of API configs for comparison
 */
const createApiHash = (apis: ApiConfig[]): string => {
  return apis
    .map(
      (a) =>
        `${a.key}:${a.site_id || "default"}:${a.data_availability_for_given_date}:${a.from_date}:${a.to_date}:${a.isLoading}:${a.isFetching}`
    )
    .join("|");
};

export const useApiNotifications = ({ apis }: UseApiNotificationsOptions) => {
  const { registerApiConfigs, unregisterApiConfigs } =
    useApiNotificationContext();

  const componentIdRef = useRef<string>(
    `component-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  );

  // Create stable hash for comparison
  const apiHash = useMemo(() => createApiHash(apis), [apis]);

  // Store previous hash to detect real changes
  const prevHashRef = useRef<string>("");
  const isRegisteredRef = useRef<boolean>(false);

  useEffect(() => {
    const componentId = componentIdRef.current;

    // Only register if the hash actually changed
    if (prevHashRef.current !== apiHash) {
      prevHashRef.current = apiHash;
      registerApiConfigs(componentId, apis);
      isRegisteredRef.current = true;
    } else if (!isRegisteredRef.current) {
      // Register on first mount even if hash is empty
      registerApiConfigs(componentId, apis);
      isRegisteredRef.current = true;
    }

    // Cleanup: unregister when component unmounts
    return () => {
      if (isRegisteredRef.current) {
        unregisterApiConfigs(componentId);
        isRegisteredRef.current = false;
      }
    };
  }, [apiHash, apis, registerApiConfigs, unregisterApiConfigs]);

  return {};
};
