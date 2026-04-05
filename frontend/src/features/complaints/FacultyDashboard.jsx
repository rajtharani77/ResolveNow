import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { authService } from "../../services/authService";
import { complaintService } from "../../services/complaintService";
import { getUserFacingApiError } from "../../utils/apiErrors";

// Using styles from StudentComplaintDashboard for consistency
const pageStyles = {
  minHeight: "100vh",
  padding: "24px",
  background: "linear-gradient(140deg, #f4f9f7 0%, #e0f2fe 50%, #fff7ed 100%)",
  fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
  color: "#0f172a",
};

const shellStyles = {
  maxWidth: "1180px",
  margin: "0 auto",
};

const heroCardStyles = {
  display: "grid",
  gridTemplateColumns: "minmax(0, 1.25fr) minmax(280px, 0.9fr)",
  gap: "24px",
  padding: "32px",
  borderRadius: "32px",
  backgroundColor: "rgba(255, 255, 255, 0.92)",
  boxShadow: "0 24px 64px rgba(15, 23, 42, 0.12)",
  border: "1px solid rgba(15, 118, 110, 0.12)",
};

const statCardStyles = {
  padding: "22px",
  borderRadius: "24px",
  backgroundColor: "rgba(255, 255, 255, 0.9)",
  boxShadow: "0 18px 44px rgba(15, 23, 42, 0.08)",
  border: "1px solid rgba(148, 163, 184, 0.16)",
};

const mainContentGrid = {
  display: "grid",
  gridTemplateColumns: "minmax(300px, 1fr) minmax(320px, 1.2fr)",
  gap: "20px",
  marginTop: "24px",
  alignItems: "start",
};

const panelStyles = {
  padding: "26px",
  borderRadius: "28px",
  backgroundColor: "rgba(255, 255, 255, 0.92)",
  boxShadow: "0 18px 44px rgba(15, 23, 42, 0.08)",
  border: "1px solid rgba(148, 163, 184, 0.16)",
};

function FacultyDashboard() {
  const navigate = useNavigate();
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedComplaintId, setSelectedComplaintId] = useState(null);
  const storedUser = useMemo(() => authService.getStoredUser(), []);

  // State for resolution form
  const [resolution, setResolution] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [resolutionError, setResolutionError] = useState("");

  const loadAssignedComplaints = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await complaintService.getAssignedToMe();
      setComplaints(response);
      if (!selectedComplaintId && response.length > 0) {
        const firstOpen = response.find((c) => c.status !== "RESOLVED");
        setSelectedComplaintId(firstOpen ? firstOpen._id : response[0]._id);
      }
    } catch (requestError) {
      setError(getUserFacingApiError(requestError));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!storedUser || storedUser.role !== "faculty") {
      navigate("/login", { replace: true });
      return;
    }
    loadAssignedComplaints();
  }, [storedUser, navigate]);

  const selectedComplaint = useMemo(
    () => complaints.find((c) => c._id === selectedComplaintId) || null,
    [complaints, selectedComplaintId]
  );

  useEffect(() => {
    setResolution("");
    setResolutionError("");
  }, [selectedComplaintId]);

  const handleResolutionSubmit = async (e) => {
    e.preventDefault();
    if (!resolution.trim() || !selectedComplaint) {
      setResolutionError("Resolution text cannot be empty.");
      return;
    }
    setSubmitting(true);
    setResolutionError("");
    try {
      await complaintService.resolveComplaint(selectedComplaint._id, { resolution });
      setResolution("");
      await loadAssignedComplaints();
    } catch (requestError) {
      setResolutionError(getUserFacingApiError(requestError));
    } finally {
      setSubmitting(false);
    }
  };

  const complaintStats = useMemo(() => {
    const total = complaints.length;
    const open = complaints.filter((c) => c.status !== "RESOLVED").length;
    const resolved = complaints.filter((c) => c.status === "RESOLVED").length;
    const highPriority = complaints.filter((c) => c.priority === "HIGH" && c.status !== "RESOLVED").length;
    return [
      { label: "Total Assigned", value: total },
      { label: "Open Right Now", value: open },
      { label: "Resolved by You", value: resolved },
      { label: "High Priority Open", value: highPriority },
    ];
  }, [complaints]);

  const handleLogout = async () => {
    await authService.logout();
    navigate("/login", { replace: true });
  };

  if (!storedUser) return null;

  return (
    <div style={pageStyles}>
      <div style={shellStyles}>
        <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "28px" }}>
          <h1 style={{ margin: 0 }}>Faculty Dashboard</h1>
          <button onClick={handleLogout} style={{ padding: "10px 20px", borderRadius: "10px", border: "1px solid #cbd5e1", background: "white", cursor: "pointer", fontWeight: "600" }}>Logout</button>
        </header>

        <section style={heroCardStyles}>
          <div>
            <h1 style={{ margin: "0 0 16px", fontSize: "clamp(2.5rem, 5vw, 4.2rem)", lineHeight: 1.02 }}>Welcome, {storedUser.name}</h1>
            <p style={{ margin: "0", fontSize: "18px", lineHeight: 1.75, color: "#475569", maxWidth: "640px" }}>This workspace is for reviewing and resolving assigned complaints. Select a complaint from the list to view its details and provide a resolution.</p>
          </div>
          <div style={{ padding: "24px", borderRadius: "24px", background: "linear-gradient(180deg, #0f172a 0%, #134e4a 100%)", color: "#ffffff" }}>
            <div style={{ fontSize: "13px", textTransform: "uppercase", letterSpacing: "0.14em", opacity: 0.76 }}>Faculty Flow</div>
            <div style={{ marginTop: "18px", fontSize: "28px", fontWeight: 800 }}>Review → Resolve → Close</div>
            <p style={{ marginTop: "12px", lineHeight: 1.7, color: "rgba(255,255,255,0.78)" }}>Review assigned complaints, provide a detailed resolution, and update the status to close the loop with the student.</p>
          </div>
        </section>

        <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "18px", marginTop: "24px" }}>
          {complaintStats.map((stat) => (<article key={stat.label} style={statCardStyles}><div style={{ color: "#64748b", fontSize: "13px", marginBottom: "8px" }}>{stat.label}</div><div style={{ fontSize: "36px", fontWeight: 800 }}>{stat.value}</div></article>))}
        </section>

        <section style={mainContentGrid}>
          <article style={panelStyles}>
            <h2 style={{ marginTop: 0 }}>Assigned Complaints</h2>
            {loading && <p>Loading complaints...</p>}
            {error && <p style={{ color: "red" }}>{error}</p>}
            {!loading && complaints.length === 0 && <p>You have no complaints assigned to you at the moment.</p>}
            <div style={{ display: "grid", gap: "14px" }}>
              {complaints.map((c) => {
                const isSelected = c._id === selectedComplaintId;
                return (<button key={c._id} onClick={() => setSelectedComplaintId(c._id)} style={{ textAlign: "left", padding: "20px", borderRadius: "22px", border: isSelected ? "2px solid #0f766e" : "1px solid #e2e8f0", background: isSelected ? "#f0f9f9" : "#fff", cursor: "pointer", width: "100%", boxShadow: "0 4px 12px rgba(0,0,0,0.04)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}><span style={{ fontWeight: 600, color: "#0f172a", fontSize: "16px" }}>{c.title}</span><span style={{ padding: "4px 8px", borderRadius: "12px", background: c.status === 'RESOLVED' ? '#dcfce7' : '#e0f2fe', color: c.status === 'RESOLVED' ? '#166534' : '#075985', fontSize: '12px', fontWeight: '600' }}>{c.status}</span></div>
                    <p style={{ margin: 0, color: "#64748b", fontSize: "14px" }}>ID: {c.complaint_id}</p>
                  </button>);
              })}
            </div>
          </article>
          <article style={panelStyles}>
            {!selectedComplaint ? (<div style={{ padding: "20px", textAlign: "center", color: "#475569" }}>Select a complaint from the list to view its details.</div>) : (
              <div style={{ display: "grid", gap: "16px" }}>
                <h3 style={{ marginTop: 0 }}>{selectedComplaint.title}</h3>
                <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>{selectedComplaint.description}</p>
                <div><strong>Status:</strong> {selectedComplaint.status}</div>
                <div><strong>Priority:</strong> {selectedComplaint.priority}</div>
                <div><strong>Submitted:</strong> {new Date(selectedComplaint.created_at).toLocaleDateString()}</div>
                {selectedComplaint.status === "RESOLVED" ? (<div style={{ marginTop: "16px", padding: "16px", borderRadius: "16px", backgroundColor: "#f0fdf4", border: "1px solid #bbf7d0" }}><h4 style={{ margin: "0 0 8px" }}>Your Resolution:</h4><p style={{ margin: 0, color: "#374151", lineHeight: 1.6 }}>{selectedComplaint.resolution}</p><em style={{ display: "block", marginTop: "12px", fontSize: "13px", color: "#6b7280" }}>Resolved on {new Date(selectedComplaint.resolved_at).toLocaleString()}</em></div>) : (
                  <form onSubmit={handleResolutionSubmit} style={{ display: "grid", gap: "16px", marginTop: "16px" }}>
                    <label style={{ fontWeight: 600 }}>Provide Resolution<textarea style={{ width: "100%", padding: "14px", borderRadius: "14px", border: "1px solid #cbd5e1", fontSize: "15px", minHeight: "120px", fontFamily: "inherit", lineHeight: 1.6, marginTop: "8px" }} value={resolution} onChange={(e) => setResolution(e.target.value)} placeholder="Explain the steps taken to resolve this complaint..." required minLength="20" /></label>
                    {resolutionError && <div style={{ padding: "12px", borderRadius: "12px", backgroundColor: "#fef2f2", color: "#b91c1c" }}>{resolutionError}</div>}
                    <button type="submit" disabled={submitting} style={{ width: "100%", padding: "14px", border: "none", borderRadius: "14px", background: "linear-gradient(135deg, #0f766e 0%, #14532d 100%)", color: "#ffffff", fontSize: "16px", fontWeight: 700, cursor: "pointer" }}>{submitting ? "Submitting..." : "Submit Resolution"}</button>
                  </form>
                )}
              </div>
            )}
          </article>
        </section>
      </div>
    </div>
  );
}

export default FacultyDashboard;