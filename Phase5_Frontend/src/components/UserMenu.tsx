import { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import { User, LogOut, BarChart3, Sun, Moon } from "lucide-react";
import { useTheme } from "../context/ThemeContext";

export default function UserMenu({ 
  name, 
  onLogout,
  showDashboardLink = false 
}: { 
  name: string; 
  onLogout: () => void;
  showDashboardLink?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const { theme, toggleTheme } = useTheme();

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  return (
    <div className="flex items-center gap-2">

      {/* Sun/Moon Pill Toggle */}
      <button
        onClick={toggleTheme}
        title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
        className={`relative w-14 h-7 rounded-full transition-colors duration-300 focus:outline-none ${
          theme === "dark" ? "bg-slate-700" : "bg-slate-200"
        }`}
      >
        {/* Sliding circle */}
        <span className={`absolute top-1 w-5 h-5 rounded-full flex items-center justify-center shadow-sm transition-all duration-300 ${
          theme === "dark"
            ? "translate-x-8 bg-slate-900"
            : "translate-x-1 bg-white"
        }`}>
          {theme === "dark"
            ? <Moon className="w-3 h-3 text-indigo-400" />
            : <Sun className="w-3 h-3 text-yellow-500" />
          }
        </span>
      </button>

      {/* User Dropdown */}
      <div ref={ref} className="relative z-50">
        <button
          onClick={() => setOpen((o) => !o)}
          className="flex items-center gap-2 text-sm font-medium text-slate-700 hover:text-indigo-600 dark:text-slate-300 dark:hover:text-indigo-400 transition-colors"
        >
          <div className="w-7 h-7 bg-indigo-100 dark:bg-indigo-900 rounded-full flex items-center justify-center">
            <User className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
          </div>
          {name}
          <svg
            className={`w-3.5 h-3.5 text-slate-400 transition-transform ${open ? "rotate-180" : ""}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {open && (
          <div className="absolute right-0 mt-2 w-44 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-lg py-1 z-50">

            {showDashboardLink && (
              <Link
                to="/dashboard"
                onClick={() => setOpen(false)}
                className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
              >
                <BarChart3 className="w-4 h-4 text-slate-400 dark:text-slate-500" />
                Dashboard
              </Link>
            )}

            <Link
              to="/profile"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
            >
              <User className="w-4 h-4 text-slate-400 dark:text-slate-500" />
              Profile
            </Link>

            <div className="border-t border-slate-100 dark:border-slate-700 my-1" />

            <button
              onClick={() => { setOpen(false); onLogout(); }}
              className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors text-left"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        )}
      </div>
    </div>
  );
}