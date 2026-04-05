import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { authService } from "../../services/authService";
import { getUserFacingApiError } from "../../utils/apiErrors";

const pageStyles = {
  minHeight: "100vh",
  display: "grid",
  placeItems: "center",
  padding: "24px",
  background:
    "linear-gradient(160deg, #eff6ff 0%, #e0f2fe 40%, #f8fafc 100%)",
  fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
};

const cardStyles = {
  width: "100%",
  maxWidth: "480px",
  padding: "32px",
  borderRadius: "24px",
  backgroundColor: "rgba(255, 255, 255, 0.94)",
  boxShadow: "0 22px 54px rgba(15, 23, 42, 0.12)",
  border: "1px solid rgba(14, 116, 144, 0.12)",
};

const inputStyles = {
  width: "100%",
  padding: "14px 16px",
  borderRadius: "14px",
  border: "1px solid #cbd5e1",
  fontSize: "15px",
  outline: "none",
  boxSizing: "border-box",
  backgroundColor: "#ffffff",
};

function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((currentForm) => ({ ...currentForm, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");

    try {
      const response = await authService.login(form);
      setMessage(`Welcome back, ${response.user.name}.`);

      const { role } = response.user;
      const destination =
        role === "admin"
          ? "/admin/dashboard"
          : role === "faculty"
          ? "/faculty/dashboard"
          : "/dashboard";
      navigate(destination, { replace: true });
    } catch (requestError) {
      setError(
        getUserFacingApiError(
          requestError,
          "Unable to sign you in right now. Please try again shortly."
        )
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={pageStyles}>
      <div style={cardStyles}>
        <p
          style={{
            margin: 0,
            textTransform: "uppercase",
            letterSpacing: "0.14em",
            fontWeight: 700,
            fontSize: "12px",
            color: "#0e7490",
          }}
        >
          Secure Login
        </p>
        <h1 style={{ margin: "10px 0 8px", fontSize: "32px", color: "#0f172a" }}>
          Sign in to continue
        </h1>
        <p style={{ margin: "0 0 24px", color: "#475569", lineHeight: 1.6 }}>
          Use your verified email and password to access the complaint portal.
        </p>

        <form onSubmit={handleSubmit} style={{ display: "grid", gap: "18px" }}>
          <label style={{ display: "grid", gap: "8px", fontWeight: 600 }}>
            Email address
            <input
              style={inputStyles}
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              placeholder="you@example.com"
              required
            />
          </label>

          <label style={{ display: "grid", gap: "8px", fontWeight: 600 }}>
            Password
            <input
              style={inputStyles}
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              placeholder="Enter your password"
              required
            />
          </label>

          {error ? (
            <div
              style={{
                padding: "12px 14px",
                borderRadius: "14px",
                backgroundColor: "#fef2f2",
                color: "#b91c1c",
                border: "1px solid #fecaca",
              }}
            >
              {error}
            </div>
          ) : null}

          {message ? (
            <div
              style={{
                padding: "12px 14px",
                borderRadius: "14px",
                backgroundColor: "#eff6ff",
                color: "#1d4ed8",
                border: "1px solid #bfdbfe",
              }}
            >
              {message}
            </div>
          ) : null}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "14px 18px",
              border: "none",
              borderRadius: "14px",
              background: "linear-gradient(135deg, #0f172a 0%, #0e7490 100%)",
              color: "#ffffff",
              fontSize: "16px",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            {loading ? "Signing in..." : "Login"}
          </button>
        </form>

        <p style={{ margin: "22px 0 0", color: "#475569", textAlign: "center" }}>
          New here?{" "}
          <Link to="/register" style={{ color: "#0e7490", fontWeight: 700 }}>
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
}

export default Login;
