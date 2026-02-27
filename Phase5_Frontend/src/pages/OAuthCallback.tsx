import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Loader2 } from "lucide-react";

export default function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    // 1. Grab the tokens and user info from the URL parameters
    const accessToken = searchParams.get("access_token");
    const refreshToken = searchParams.get("refresh_token");
    const name = searchParams.get("name");

    if (accessToken && refreshToken) {
      // 2. Save them to localStorage so the app knows the user is logged in
      localStorage.setItem("access_token", accessToken);
      localStorage.setItem("refresh_token", refreshToken);
      
      if (name) {
        localStorage.setItem("user", JSON.stringify({ full_name: name }));
      }

      // 3. Force a hard reload to the dashboard. 
      // This ensures the AuthContext reads the new localStorage values immediately.
      window.location.replace("/dashboard");
    } else {
      // If something went wrong or the user denied access, send them back to login
      navigate("/login");
    }
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50">
      <Loader2 className="w-12 h-12 text-indigo-600 animate-spin mb-4" />
      <h2 className="text-2xl font-bold text-slate-800 mb-2">Authenticating...</h2>
      <p className="text-slate-500">Please wait while we securely log you in.</p>
    </div>
  );
}