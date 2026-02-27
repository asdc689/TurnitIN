import { useState, useEffect } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Shield, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import axios from "axios";

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");

  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("No verification token found in the URL.");
      return;
    }

    const verify = async () => {
      try {
        const res = await axios.get(
          `http://localhost:8000/api/v1/auth/verify-email?token=${token}`
        );
        setMessage(res.data.message);
        setStatus("success");
      } catch (err) {
        if (axios.isAxiosError(err)) {
          setMessage(err.response?.data?.detail || "Verification failed.");
        } else {
          setMessage("An unexpected error occurred.");
        }
        setStatus("error");
      }
    };

    verify();
  }, [token]);

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">

        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-indigo-600 rounded-2xl mb-4">
            <Shield className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-slate-800">Plagiarism Detector</h1>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 text-center">

          {status === "loading" && (
            <>
              <Loader2 className="w-12 h-12 text-indigo-600 animate-spin mx-auto mb-4" />
              <h2 className="text-lg font-semibold text-slate-800 mb-2">
                Verifying your email...
              </h2>
              <p className="text-sm text-slate-500">Please wait a moment.</p>
            </>
          )}

          {status === "success" && (
            <>
              <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-4" />
              <h2 className="text-lg font-semibold text-slate-800 mb-2">
                Email Verified!
              </h2>
              <p className="text-sm text-slate-500 mb-6">{message}</p>
              <Link
                to="/login"
                className="inline-block bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-2.5 rounded-lg transition-colors text-sm"
              >
                Sign in to your account
              </Link>
            </>
          )}

          {status === "error" && (
            <>
              <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
              <h2 className="text-lg font-semibold text-slate-800 mb-2">
                Verification Failed
              </h2>
              <p className="text-sm text-slate-500 mb-6">{message}</p>
              <Link
                to="/login"
                className="inline-block text-indigo-600 hover:underline text-sm font-medium"
              >
                Back to login
              </Link>
            </>
          )}

        </div>
      </div>
    </div>
  );
}