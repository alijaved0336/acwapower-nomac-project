"use client";

import { Provider } from "react-redux";
import { store, persistor } from "@/store/store";
import { PersistGate } from "redux-persist/integration/react";
import { SiteInitializer } from "./SiteInitializer";

export function ReduxProvider({ children }: { children: React.ReactNode }) {
  return (
    <Provider store={store}>
      <PersistGate loading={null} persistor={persistor}>
        <SiteInitializer>{children}</SiteInitializer>
      </PersistGate>
    </Provider>
  );
}
