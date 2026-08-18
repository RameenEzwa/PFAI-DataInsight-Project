import { create } from "zustand";

const initialTheme = () => {
  if (typeof window === "undefined") return "light";
  return localStorage.getItem("datainsight-theme") || "light";
};

export const useAppStore = create((set) => ({
  selectedDatasetId: null,
  activeTab: "dashboard",
  theme: initialTheme(),
  setSelectedDatasetId: (selectedDatasetId) => set({ selectedDatasetId }),
  setActiveTab: (activeTab) => set({ activeTab }),
  toggleTheme: () =>
    set((state) => {
      const theme = state.theme === "dark" ? "light" : "dark";
      localStorage.setItem("datainsight-theme", theme);
      return { theme };
    }),
}));

