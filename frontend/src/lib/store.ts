import { create } from "zustand";
import { persist } from "zustand/middleware";
import { DEFAULT_CONTEXT, type RetailerContext } from "./domain";

interface AppState {
  context: RetailerContext | null;
  setContext: (c: RetailerContext) => void;
  reset: () => void;
}

export const useApp = create<AppState>()(
  persist(
    (set) => ({
      context: null,
      setContext: (c) => set({ context: c }),
      reset: () => set({ context: null }),
    }),
    { name: "scout-app" },
  ),
);

export { DEFAULT_CONTEXT };
