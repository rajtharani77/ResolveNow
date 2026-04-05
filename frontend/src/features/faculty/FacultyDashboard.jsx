import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { authService } from "../../services/authService";
import { complaintService } from "../../services/complaintService";
import { getUserFacingApiError } from "../../utils/apiErrors";

// Re-usable styles from other components for consistency
const pageStyles = {
  minHeight: "100vh",
  padding: "24px",
  background:
    "radial-gradient(circle at top left, rgba(15, 118, 110, 0.24), transparent 26%), radial-gradient(circle at bottom right, rgba(14, 116, 144, 0.18), transparent 28%), linear-gradient(140deg, #f4f9f7 0%, #e0f2fe 50%, #fff7ed 100%)",
  fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
  color: "#0f172a",
};

const shellStyles = {
  maxWidth: "1180px",
  margin: "0 auto",
};

const pillStyles = {
  display: "inline-block",
  padding: "8px 14px",
  borderRadius: "999px",
  backgroundColor: "rgba(15, 118, 110, 0.1)",
  color: "#0f766e",
  fontSize: "12px",
  fontWeight: 800,
  textTransform: "uppercase",
  letterSpacing: "0.14em",
};

const navButtonBase = {
  padding: "12px 18px",
  borderRadius: "14px",
  border: "1px solid #cbd5e1",
  backgroundColor: "#ffffff",
  color: "#0f172a",
  fontWeight: 700,
  cursor: "pointer",
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
  minHeight: "120px",
  fontFamily: "inherit",
};

const primaryButtonStyles = {
  ...navButtonBase,
  border: "none",
  background: "linear-gradient(135deg, #0f766e 0%, #14532d 100%)",
  color: "#ffffff",
};

function formatDate(value) {
  if (!value) return "N/A";
  return new Date(value).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function FacultyDashboard() {
  const navigate = useNavigate();
  const [complaints, setComplaints] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedComplaintId, setSelectedComplaintId] = useState(null);
  const [resolutionExplanation, setResolutionExplanation] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [resolutionError, setResolutionError] = useState("");
  const [resolutionSuccess, setResolutionSuccess] = useState("");

  const storedUser = useMemo(() => authService.getStoredUser(), []);

  const loadAssignedComplaints = async () => {
    setLoading(true);
    setError("");
    try {
      // Assumes a new method in complaintService
      const assigned = await complaintService.getAssignedToMe();
      setComplaints(assigned);
      if (!selectedComplaintId && assigned.length > 0) {
        setSelectedComplaintId(assigned[0]._id);
      }
    } catch (requestError) {
      setError(
        getUserFacingApiError(
          requestError,
          "Could not load assigned complaints."
        )
      );
    } finally {
      setLoading(false);
    }
  };

  const loadDepartments = async () => {
    try {
      const response = await complaintService.getDepartments();
      setDepartments(response);
    } catch (requestError) {
      // Non-critical error, so we don't block the UI
      console.error("Failed to load departments:", requestError);
    }
  };

  useEffect(() => {
    if (!storedUser) {
      navigate("/login", { replace: true });
      return;
    }
    if (storedUser.role !== "faculty") {
      navigate("/dashboard", { replace: true });
      return;
    }

    loadAssignedComplaints();
    loadDepartments();
  }, [navigate, storedUser]);

  const selectedComplaint = useMemo(
    () => complaints.find((c) => c._id === selectedComplaintId) || null,
    [complaints, selectedComplaintId]
  );

  useEffect(() => {
    // Reset resolution form when a new complaint is selected
    setResolutionExplanation("");
    setResolutionError("");
    setResolutionSuccess("");
  }, [selectedComplaintId]);

  const handleLogout = async () => {
    await authService.logout();
    navigate("/login", { replace: true });
  };

  const handleResolveSubmit = async (event) => {
    event.preventDefault();
    if (!selectedComplaintId || !resolutionExplanation.trim()) {
      setResolutionError("Resolution explanation cannot be empty.");
      return;
    }

    setIsSubmitting(true);
    setResolutionError("");
    setResolutionSuccess("");

    try {
      // Assumes a new method in complaintService
      const response = await complaintService.resolveComplaint(
        selectedComplaintId,
        resolutionExplanation
      );
      setResolutionSuccess(response.message || "Complaint resolved successfully.");
      setResolutionExplanation("");
      // Refresh the list to show the updated status
      await loadAssignedComplaints();
    } catch (requestError) {
      setResolutionError(
        getUserFacingApiError(requestError, "Failed to resolve complaint.")
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const getDepartmentName = (departmentId) => {
    return (
      departments.find((d) => d.id === departmentId)?.name || departmentId || "N/A"
    );
  };

  if (!storedUser || storedUser.role !== "faculty") {
    return null; // Or a loading spinner
  }

  return (
    <div style={pageStyles}>
      <div style={shellStyles}>
        <header
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "16px",
            marginBottom: "28px",
            flexWrap: "wrap",
          }}
        >
          <div>
            <div style={pillStyles}>Faculty Dashboard</div>
            <h1 style={{ margin: "10px 0 0", fontSize: "34px" }}>
              Welcome, {storedUser.name}
            </h1>
          </div>
          <button type="button" onClick={handleLogout} style={navButtonBase}>
            Logout
          </button>
        </header>

        <section
          style={{
            display: "grid",
            gridTemplateColumns: "minmax(320px, 0.8fr) minmax(0, 1fr)",
            gap: "20px",
            alignItems: "start",
          }}
        >
          {/* Complaint List */}
          <article
            style={{
              padding: "26px",
              borderRadius: "28px",
              backgroundColor: "rgba(255, 255, 255, 0.92)",
              boxShadow: "0 18px 44px rgba(15, 23, 42, 0.08)",
              border: "1px solid rgba(148, 163, 184, 0.16)",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "22px",
              }}
            >
              <h2 style={{ margin: 0, fontSize: "28px" }}>Assigned Complaints</h2>
              <button
                type="button"
                onClick={loadAssignedComplaints}
                style={navButtonBase}
                disabled={loading}
              >
                {loading ? "Refreshing..." : "Refresh"}
              </button>
            </div>

            {error && <div style={{ color: "#b91c1c" }}>{error}</div>}

            {loading && !complaints.length ? (
              <div>Loading complaints...</div>
            ) : null}

            {!loading && !complaints.length ? (
              <div style={{ padding: "20px", background: "#f8fafc" }}>
                You have no complaints assigned to you at the moment.
              </div>
            ) : null}

            <div style={{ display: "grid", gap: "14px" }}>
              {complaints.map((complaint) => {
                const isSelected = complaint._id === selectedComplaintId;
                return (
                  <button
                    key={complaint._id}
                    type="button"
                    onClick={() => setSelectedComplaintId(complaint._id)}
                    style={{
                      textAlign: "left",
                      padding: "20px",
                      borderRadius: "22px",
                      border: isSelected
                        ? "2px solid #0f766e"
                        : "1px solid #e2e8f0",
                      background: isSelected ? "#f0fdfa" : "#fff",
                      cursor: "pointer",
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                      {complaint.image_url && (
                        <img
                          src={complaint.image_url}
                          alt="Attachment"
                          style={{
                            width: "60px",
                            height: "60px",
                            borderRadius: "12px",
                            objectFit: "cover",
                            flexShrink: 0,
                          }}
                        />
                      )}
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            marginBottom: "8px",
                          }}
                        >
                          <span style={{ fontWeight: 700, color: "#0f766e" }}>
                            {complaint.status}
                          </span>
                          <span style={{ color: "#64748b", fontSize: "13px" }}>
                            {complaint.priority}
                          </span>
                        </div>
                        <h3 style={{ margin: "0 0 6px", fontSize: "20px", whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {complaint.title}
                        </h3>
                        <p style={{ margin: 0, color: "#64748b", fontSize: "13px" }}>
                          {complaint.complaint_id}
                        </p>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </article>

          <aside
            style={{
              position: "sticky",
              top: "24px",
              padding: "26px",
              borderRadius: "28px",
              backgroundColor: "rgba(255, 255, 255, 0.92)",
              boxShadow: "0 18px 44px rgba(15, 23, 42, 0.08)",
              border: "1px solid rgba(148, 163, 184, 0.16)",
            }}
          >
            {!selectedComplaint ? (
              <div>Select a complaint to view details and resolve it.</div>
            ) : (
              <div>
                <div style={{ marginBottom: "24px" }}>
                  <p
                    style={{
                      margin: 0,
                      color: "#64748b",
                      fontSize: "13px",
                    }}
                  >
                    {selectedComplaint.complaint_id}
                  </p>
                  <h2 style={{ margin: "8px 0", fontSize: "28px" }}>
                    {selectedComplaint.title}
                  </h2>
                  <p style={{ margin: 0, color: "#475569", lineHeight: 1.7 }}>
                    {selectedComplaint.description}
                  </p>
                  <div
                    style={{
                      marginTop: "16px",
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr",
                      gap: "12px",
                      fontSize: "14px",
                    }}
                  >
                    <span>
                      <strong>Status:</strong> {selectedComplaint.status}
                    </span>
                    <span>
                      <strong>Priority:</strong> {selectedComplaint.priority}
                    </span>
                    <span>
                      <strong>Department:</strong>{" "}
                      {getDepartmentName(selectedComplaint.department_id)}
                    </span>
                    <span>
                      <strong>Deadline:</strong>{" "}
                      {formatDate(selectedComplaint.deadline)}
                    </span>
                  </div>
                </div>

                {selectedComplaint.status !== "RESOLVED" ? (
                  <form onSubmit={handleResolveSubmit}>
                    <h3 style={{ fontSize: "22px", marginBottom: "12px" }}>
                      Resolve Complaint
                    </h3>
                    <textarea
                      name="resolution"
                      style={inputStyles}
                      placeholder="Explain the resolution provided..."
                      value={resolutionExplanation}
                      onChange={(e) => setResolutionExplanation(e.target.value)}
                      required
                    />
                    {resolutionError && (
                      <div
                        style={{
                          color: "#b91c1c",
                          marginTop: "10px",
                          fontSize: "14px",
                        }}
                      >
                        {resolutionError}
                      </div>
                    )}
                    {resolutionSuccess && (
                      <div
                        style={{
                          color: "#166534",
                          marginTop: "10px",
                          fontSize: "14px",
                        }}
                      >
                        {resolutionSuccess}
                      </div>
                    )}
                    <button
                      type="submit"
                      disabled={isSubmitting}
                      style={{ ...primaryButtonStyles, width: "100%", marginTop: "16px" }}
                    >
                      {isSubmitting ? "Submitting..." : "Submit Resolution"}
                    </button>
                  </form>
                ) : (
                  <div
                    style={{
                      padding: "16px",
                      borderRadius: "16px",
                      backgroundColor: "#ecfdf5",
                      color: "#166534",
                      border: "1px solid #bbf7d0",
                    }}
                  >
                    <strong>This complaint has been resolved.</strong>
                    <p style={{ margin: "8px 0 0", lineHeight: 1.6 }}>
                      {selectedComplaint.resolution_explanation}
                    </p>
                  </div>
                )}
              </div>
            )}
          </aside>
        </section>
      </div>
    </div>
  );
}

export default FacultyDashboard;