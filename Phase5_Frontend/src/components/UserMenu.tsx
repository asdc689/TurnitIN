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
    <div className="flex items-center gap-3">

      {/* Sun/Moon Pill Toggle */}
      <button
        onClick={toggleTheme}
        title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
        className={`relative w-14 h-7 rounded-full transition-colors duration-300 focus:outline-none ${
          theme === "dark" ? "bg-slate-700" : "bg-slate-200"
        }`}
      >
        <span className={`absolute top-1 w-5 h-5 rounded-full flex items-center justify-center shadow-sm transition-all duration-300 ${
          theme === "dark" ? "translate-x-8 bg-slate-900" : "translate-x-1 bg-white"
        }`}>
          {theme === "dark"
            ? <Moon className="w-3 h-3 text-indigo-400" />
            : <Sun className="w-3 h-3 text-yellow-500" />
          }
        </span>
      </button>

      {/* User Avatar Dropdown */}
      <div ref={ref} className="relative z-50">
        <button
          onClick={() => setOpen((o) => !o)}
          className="w-9 h-9 bg-indigo-600 hover:bg-indigo-500 rounded-full flex items-center justify-center transition-colors focus:outline-none"
          title={name}
        >
          <User className="w-4 h-4 text-white" />
        </button>

        {open && (
          <div className="absolute right-0 mt-3 w-52 bg-slate-900 border border-slate-700/60 rounded-2xl shadow-2xl py-2 z-50 overflow-hidden">

            {/* User name header */}
            <div className="px-4 py-2.5 mb-1">
              <p className="text-sm font-semibold text-slate-100">{name}</p>
            </div>

            {showDashboardLink && (
              <Link
                to="/dashboard"
                onClick={() => setOpen(false)}
                className="flex items-center gap-3 px-4 py-2.5 text-sm font-medium text-slate-300 hover:text-white hover:translate-x-1 transition-all duration-150"
              >
                <BarChart3 className="w-4 h-4 text-slate-500" />
                Dashboard
              </Link>
            )}

            <Link
              to="/profile"
              onClick={() => setOpen(false)}
              className="flex items-center gap-3 px-4 py-2.5 text-sm font-medium text-slate-300 hover:text-white hover:translate-x-1 transition-all duration-150"
            >
              <User className="w-4 h-4 text-slate-500" />
              Profile
            </Link>

            <button
              onClick={() => { setOpen(false); onLogout(); }}
              className="w-full flex items-center gap-3 px-4 py-2.5 text-sm font-medium text-red-400 hover:text-red-300 hover:translate-x-1 hover:bg-red-500/5 transition-all duration-150 text-left"
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