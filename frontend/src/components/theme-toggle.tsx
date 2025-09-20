"use client";

import * as React from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

export function ThemeToggle() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
    console.log("Theme Toggle Debug:", { theme, resolvedTheme });
  }, [theme, resolvedTheme]);

  if (!mounted) {
    return (
      <button className="w-10 h-10 rounded-full flex items-center justify-center bg-gray-200 dark:bg-gray-700">
        <Moon size={20} />
      </button>
    );
  }

  const handleToggle = () => {
    const newTheme = resolvedTheme === "dark" ? "light" : "dark";
    console.log("Toggling theme from", resolvedTheme, "to", newTheme);
    setTheme(newTheme);
  };

  return (
    <button
      onClick={handleToggle}
      className="w-10 h-10 rounded-full flex items-center justify-center bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 transition-colors"
    >
      {resolvedTheme === "dark" ? <Sun size={20} /> : <Moon size={20} />}
    </button>
  );
}