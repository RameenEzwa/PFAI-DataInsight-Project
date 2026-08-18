import { Moon, Sun } from "lucide-react";

import { useAppStore } from "../store/useAppStore";

export function ThemeToggle() {
  const theme = useAppStore((state) => state.theme);
  const toggleTheme = useAppStore((state) => state.toggleTheme);
  const Icon = theme === "dark" ? Sun : Moon;
  return (
    <button className="button-secondary h-10 w-10 px-0" onClick={toggleTheme} type="button" title="Toggle theme">
      <Icon className="h-4 w-4" />
    </button>
  );
}

