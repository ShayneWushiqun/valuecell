import { toast } from "sonner";
import { getUserInfo } from "@/api/system";
import { VALUECELL_BACKEND_URL } from "@/constants/api";
import { useSystemStore } from "@/store/system-store";
import type { SystemInfo } from "@/types/system";

// API error type
export class ApiError extends Error {
  public status: number;
  public details?: unknown;
  public endpoint?: string;
  public method?: string;

  constructor(
    message: string,
    status: number,
    details?: unknown,
    meta?: { endpoint?: string; method?: string },
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
    this.endpoint = meta?.endpoint;
    this.method = meta?.method;
  }
}

export type ApiNetworkErrorKind =
  | "network_changed"
  | "temporary_network"
  | "offline"
  | "unreachable"
  | "timeout"
  | "aborted"
  | "unknown_network";

export class ApiNetworkError extends Error {
  public kind: ApiNetworkErrorKind;
  public endpoint: string;
  public method: string;
  public originalMessage: string;

  constructor(params: {
    kind: ApiNetworkErrorKind;
    endpoint: string;
    method: string;
    message: string;
    originalMessage: string;
  }) {
    super(params.message);
    this.name = "ApiNetworkError";
    this.kind = params.kind;
    this.endpoint = params.endpoint;
    this.method = params.method;
    this.originalMessage = params.originalMessage;
  }
}

export interface ApiResponse<T> {
  code: number;
  data: T;
  msg: string;
}

// request config interface
export interface RequestConfig {
  requiresAuth?: boolean;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  keepalive?: boolean;
  wrapError?: boolean;
  toastError?: boolean;
}

const TOAST_DEDUPE_WINDOW_MS = 5000;
const recentToastMap = new Map<string, number>();

const dedupedToastError = (message: string, key = message) => {
  const now = Date.now();
  const lastShownAt = recentToastMap.get(key);
  if (lastShownAt && now - lastShownAt < TOAST_DEDUPE_WINDOW_MS) {
    return;
  }
  recentToastMap.set(key, now);
  toast.error(message);
};

const formatNetworkErrorMessage = (kind: ApiNetworkErrorKind) => {
  switch (kind) {
    case "network_changed":
      return "网络环境发生变化，当前先使用缓存结果。";
    case "temporary_network":
      return "网络暂时波动，当前先使用缓存结果。";
    case "offline":
      return "当前似乎已离线，请检查网络后再试。";
    case "unreachable":
      return "当前无法连接到服务，请稍后再试。";
    case "timeout":
      return "请求超时，请稍后重试。";
    case "aborted":
      return "请求已取消。";
    default:
      return "网络请求失败，请稍后再试。";
  }
};

const classifyFetchError = (
  error: unknown,
  endpoint: string,
  method: string,
): ApiNetworkError => {
  const message =
    error instanceof Error ? error.message : typeof error === "string" ? error : "Unknown error";
  const normalizedMessage = message.toLowerCase();

  let kind: ApiNetworkErrorKind = "unknown_network";
  if (error instanceof DOMException && error.name === "AbortError") {
    kind = "aborted";
  } else if (normalizedMessage.includes("network changed")) {
    kind = "network_changed";
  } else if (
    !navigator.onLine ||
    normalizedMessage.includes("offline") ||
    normalizedMessage.includes("network request failed")
  ) {
    kind = "offline";
  } else if (normalizedMessage.includes("timeout")) {
    kind = "timeout";
  } else if (
    normalizedMessage.includes("failed to fetch") ||
    normalizedMessage.includes("networkerror") ||
    normalizedMessage.includes("load failed")
  ) {
    kind = "temporary_network";
  } else if (
    normalizedMessage.includes("fetch") ||
    normalizedMessage.includes("network")
  ) {
    kind = "unreachable";
  }

  return new ApiNetworkError({
    kind,
    endpoint,
    method,
    originalMessage: message,
    message: formatNetworkErrorMessage(kind),
  });
};

export const isApiNetworkError = (error: unknown): error is ApiNetworkError =>
  error instanceof ApiNetworkError;

export const isTemporaryApiNetworkError = (error: unknown) =>
  isApiNetworkError(error) &&
  ["network_changed", "temporary_network", "offline", "unreachable"].includes(
    error.kind,
  );

export const getServerUrl = (endpoint: string) => {
  if (endpoint.startsWith("http")) return endpoint;

  return `${import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1"}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
};

class ApiClient {
  // default config
  private config: RequestConfig = {
    requiresAuth: false,
    headers: {
      "Content-Type": "application/json",
    },
  };

  private async handleResponse<T>(
    response: Response,
    wrapError: boolean,
    endpoint: string,
    method: string,
    toastError: boolean,
  ): Promise<T> {
    if (wrapError && !response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const message = JSON.stringify(
        errorData.message ||
          errorData.detail ||
          response.statusText ||
          `HTTP ${response.status}`,
      );

      if (response.status === 401) {
        try {
          const {
            data: { access_token, refresh_token },
          } = await apiClient.post<
            ApiResponse<Pick<SystemInfo, "access_token" | "refresh_token">>
          >(`${VALUECELL_BACKEND_URL}/refresh`, {
            refreshToken: useSystemStore.getState().refresh_token,
          });

          if (access_token && refresh_token) {
            const userInfo = await getUserInfo(access_token);

            if (userInfo) {
              useSystemStore.getState().setSystemInfo({
                access_token,
                refresh_token,
                ...userInfo,
              });
            }
          }
        } catch (error) {
          dedupedToastError(JSON.stringify(error), "auth-refresh");
          useSystemStore.getState().clearSystemInfo();
        }
      } else if (toastError) {
        dedupedToastError(message, `${method}:${endpoint}:${response.status}`);
      }

      throw new ApiError(message, response.status, errorData, { endpoint, method });
    }

    const contentType = response.headers.get("content-type");
    if (contentType?.includes("application/json")) {
      return response.json();
    }

    return response.text() as unknown as T;
  }

  private async request<T>(
    method: string,
    endpoint: string,
    data?: unknown,
    config: RequestConfig = {},
  ): Promise<T> {
    const mergedConfig = { ...this.config, ...config };
    const url = getServerUrl(endpoint);

    // add authentication header
    if (mergedConfig.requiresAuth) {
      const token = useSystemStore.getState().access_token;
      if (token) {
        mergedConfig.headers!.Authorization = `Bearer ${token}`;
      }
    }

    // prepare request config
    const requestConfig: RequestInit = {
      method,
      headers: mergedConfig.headers,
      signal: mergedConfig.signal,
      keepalive: mergedConfig.keepalive,
    };

    // add request body
    if (data && ["POST", "PUT", "PATCH"].includes(method)) {
      if (data instanceof FormData) {
        delete mergedConfig.headers!["Content-Type"];
        requestConfig.body = data;
      } else {
        requestConfig.body = JSON.stringify(data);
      }
    }

    const toastError =
      mergedConfig.toastError ?? (method !== "GET" && method !== "HEAD");

    try {
      const response = await fetch(url, requestConfig);
      return this.handleResponse<T>(
        response,
        config.wrapError ?? true,
        endpoint,
        method,
        toastError,
      );
    } catch (error) {
      const networkError = classifyFetchError(error, endpoint, method);
      if (toastError && networkError.kind !== "aborted") {
        dedupedToastError(
          networkError.message,
          `${networkError.kind}:${networkError.endpoint}`,
        );
      }
      throw networkError;
    }
  }

  async get<T>(endpoint: string, config?: RequestConfig): Promise<T> {
    return this.request<T>("GET", endpoint, undefined, config);
  }

  async post<T>(
    endpoint: string,
    data?: unknown,
    config?: RequestConfig,
  ): Promise<T> {
    return this.request<T>("POST", endpoint, data, config);
  }

  async put<T>(
    endpoint: string,
    data?: unknown,
    config?: RequestConfig,
  ): Promise<T> {
    return this.request<T>("PUT", endpoint, data, config);
  }

  async patch<T>(
    endpoint: string,
    data?: unknown,
    config?: RequestConfig,
  ): Promise<T> {
    return this.request<T>("PATCH", endpoint, data, config);
  }

  async delete<T>(endpoint: string, config?: RequestConfig): Promise<T> {
    return this.request<T>("DELETE", endpoint, undefined, config);
  }

  // file upload
  async upload<T>(
    endpoint: string,
    formData: FormData,
    config?: RequestConfig,
  ): Promise<T> {
    return this.request<T>("POST", endpoint, formData, config);
  }
}

// default api client with authentication
export const apiClient = new ApiClient();
