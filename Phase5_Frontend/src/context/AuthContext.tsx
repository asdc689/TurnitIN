import { createContext, useContext, useState, useEffect } from "react";
import type { ReactNode } from "react";
import type { User } from "../types"; 
import { authApi } from "../services/api";

// ── Types ─────────────────────────────────────────────────────────────────────

interface AuthContextType {
  user:          User | null;
  isLoading:     boolean;
  isAuthenticated: boolean;
  login:         (email: string, password: string) => Promise<void>;
  logout:        () => void;
  setUser:       (user: User | null) => void;
}

// ── Context ───────────────────────────────────────────────────────────────────

// We initialize with null, but the hook will ensure it's used safely
const AuthContext = createContext<AuthContextType | null>(null);

// ── Provider ──────────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: ReactNode }) {
  // State to hold the current user data
  const [user, setUser]         = useState<User | null>(null);
  // State to prevent rendering protected pages before we check local storage
  const [isLoading, setIsLoading] = useState(true);

  // On initial load, check if the user is already logged in via localStorage
  useEffect(() => {
    const stored = localStorage.getItem("user");
    const token  = localStorage.getItem("access_token");

    if (stored && token) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        // If the JSON is corrupted, clear it out safely
        localStorage.removeItem("user");
      }
    }
    // We are done checking, so the app can finish loading
    setIsLoading(false);
  }, []);

  // Centralized login function that hits the API and updates state
  const login = async (email: string, password: string) => {
    const data = await authApi.login(email, password);
    setUser(data.user);
  };

  // Centralized logout function that clears state and local storage
  const logout = () => {
    setUser(null);
    authApi.logout();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user, // Converts the user object to a true/false boolean
        login,
        logout,
        setUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// ── Hook ──────────────────────────────────────────────────────────────────────

// A custom hook so components can simply call `const { user } = useAuth()`
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}