import { createContext, useContext, useEffect, useState } from "react";

type Theme = "light" | "dark";

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
  setPublicTheme: () => void;   // forces dark for public pages
  setAppTheme: () => void;      // restores user preference for app pages
}

const ThemeContext = createContext<ThemeContextType>({
  theme: "dark",
  toggleTheme: () => {},
  setPublicTheme: () => {},
  setAppTheme: () => {},
});

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  // User's saved preference — only used inside the app (dashboard, upload, report)
  const [appTheme, setAppThemeState] = useState<Theme>(() => {
    return (localStorage.getItem("appTheme") as Theme) || "light";
  });

  // Currently active theme applied to <html>
  const [theme, setTheme] = useState<Theme>("dark");

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
  }, [theme]);

  // Called by public pages (landing, login, register, etc.)
  // Forces dark mode without touching the user's saved preference
  const setPublicTheme = () => {
    setTheme("dark");
  };

  // Called by app pages (dashboard, upload, report) on mount
  // Restores the user's saved preference
  const setAppTheme = () => {
    setTheme(appTheme);
  };

  // User toggle — only affects app pages
  const toggleTheme = () => {
    const next = appTheme === "light" ? "dark" : "light";
    setAppThemeState(next);
    setTheme(next);
    localStorage.setItem("appTheme", next);
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setPublicTheme, setAppTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}