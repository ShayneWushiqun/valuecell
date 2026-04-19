import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
import { Links, Meta, Outlet, Scripts, ScrollRestoration } from "react-router";
import "@/i18n";
import AppSidebar from "@/components/valuecell/app/app-sidebar";
import { useLanguage } from "@/store/settings-store";
import { Toaster } from "./components/ui/sonner";

import "./global.css";
import { SidebarProvider } from "./components/ui/sidebar";
import { ApiError, isApiNetworkError } from "./lib/api-client";

export function Layout({ children }: { children: React.ReactNode }) {
  const language = useLanguage();
  const htmlLang =
    {
      en: "en",
      zh_CN: "zh-CN",
      zh_TW: "zh-TW",
      ja: "ja",
    }[language] ?? "en";

  return (
    <html lang={htmlLang} suppressHydrationWarning>
      <head>
        <meta charSet="UTF-8" />
        <link rel="icon" type="image/svg+xml" href="/logo.svg" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Value Cell</title>
        <Meta />
        <Links />
      </head>
      <body>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,
      gcTime: 30 * 60 * 1000,
      refetchOnWindowFocus: false,
      refetchOnReconnect: false,
      refetchOnMount: false,
      retry: (failureCount, error) => {
        if (isApiNetworkError(error)) {
          return false;
        }
        if (error instanceof ApiError) {
          if (error.status >= 500) {
            return failureCount < 1;
          }
          return false;
        }
        return failureCount < 1;
      },
    },
    mutations: {
      retry: false,
    },
  },
});

import { AutoUpdateCheck } from "@/components/valuecell/app/auto-update-check";
import { BackendHealthCheck } from "@/components/valuecell/app/backend-health-check";
import { TrackerProvider } from "./provider/tracker-provider";

export default function Root() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider
        attribute="class"
        defaultTheme="system"
        enableSystem
        enableColorScheme
        storageKey="valuecell-theme"
      >
        <BackendHealthCheck>
          <TrackerProvider>
            <SidebarProvider>
              <div className="fixed flex size-full overflow-hidden">
                <AppSidebar />

                <main
                  className="relative flex flex-1 overflow-hidden"
                  id="main-content"
                >
                  <Outlet />
                </main>
                <Toaster />
              </div>
            </SidebarProvider>
          </TrackerProvider>
          <AutoUpdateCheck />
        </BackendHealthCheck>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
