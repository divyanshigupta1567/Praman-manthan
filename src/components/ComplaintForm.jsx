import React, { useState } from "react";
import { postComplaint, ApiError } from "../api";

const initialState = {
  complaint_text: "",
  latitude: "",
  longitude: "",
  locality: "",
  photoFile: null,
};

// On submit: posts { complaint_text, latitude, longitude, locality, image_url }
// to POST /api/complaints and displays the returned complaint_id (opaque —
// never parsed) and predicted_category.
export default function ComplaintForm({ onClose, onSubmitted, onToast }) {
  const [form, setForm] = useState(initialState);
  const [locating, setLocating] = useState(false);
  const [locationSource, setLocationSource] = useState(null); // "device" | "manual"
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null); // { complaint_id, predicted_category }

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  function useDeviceLocation() {
    if (!navigator.geolocation) {
      setError("Your browser doesn't support location — enter coordinates manually below.");
      return;
    }
    setLocating(true);
    setError(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setForm((f) => ({
          ...f,
          latitude: String(pos.coords.latitude),
          longitude: String(pos.coords.longitude),
        }));
        setLocationSource("device");
        setLocating(false);
      },
      () => {
        setLocating(false);
        setError("Couldn't get your location — enter coordinates manually below.");
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);

    if (!form.complaint_text.trim()) {
      setError("Describe the issue before submitting.");
      return;
    }
    if (form.latitude === "" || form.longitude === "") {
      setError("Add a location — use your device location or enter coordinates manually.");
      return;
    }

    setSubmitting(true);
    try {
      let image_url = null;
      if (form.photoFile) {
        // Swap for your real upload endpoint; this inlines a data URL as a
        // placeholder so the flow works end-to-end before that's wired up.
        image_url = await fileToDataUrl(form.photoFile);
      }

      const created = await postComplaint({
        complaint_text: form.complaint_text.trim(),
        latitude: Number(form.latitude),
        longitude: Number(form.longitude),
        locality: form.locality.trim() || undefined,
        image_url,
      });

      setResult(created);
      onSubmitted?.(created);
      onToast?.({
        type: "success",
        title: "Report Submitted",
        message: `Complaint ${created.complaint_id} logged under ${created.predicted_category || "Unassigned"}.`,
      });
    } catch (err) {
      const errMsg = err instanceof ApiError ? err.message : "Something went wrong submitting your report.";
      setError(errMsg);
      onToast?.({
        type: "error",
        title: "Submission Failed",
        message: errMsg,
      });
    } finally {
      setSubmitting(false);
    }
  }

  if (result) {
    return (
      <div className="complaint-modal" role="dialog" aria-label="Report submitted">
        <div className="complaint-modal-body">
          <h2>Report submitted</h2>
          <p>Your complaint ID is</p>
          <p className="complaint-id-display">{result.complaint_id}</p>
          <p>Predicted category: <strong>{result.predicted_category}</strong></p>
          <button type="button" className="btn-primary" onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="complaint-modal" role="dialog" aria-label="Report an issue">
      <form className="complaint-modal-body" onSubmit={handleSubmit}>
        <div className="complaint-modal-header">
          <h2>Report an issue</h2>
          <button type="button" className="btn-close" onClick={onClose} aria-label="Close form">
            ×
          </button>
        </div>

        <label className="field">
          <span>What's the issue?</span>
          <textarea
            value={form.complaint_text}
            onChange={(e) => update("complaint_text", e.target.value)}
            rows={4}
            placeholder="Describe what you're seeing, and where."
            required
          />
        </label>

        <label className="field">
          <span>Locality (optional)</span>
          <input
            type="text"
            value={form.locality}
            onChange={(e) => update("locality", e.target.value)}
            placeholder="e.g. Krishna Nagar"
          />
        </label>

        <div className="field">
          <span>Location</span>
          <button type="button" className="btn-secondary" onClick={useDeviceLocation} disabled={locating}>
            {locating ? "Getting your location…" : "Use my current location"}
          </button>
          {locationSource === "device" && form.latitude && (
            <p className="location-confirm">Using device location: {Number(form.latitude).toFixed(5)}, {Number(form.longitude).toFixed(5)}</p>
          )}
          <div className="latlng-fallback">
            <label>
              <span>Latitude</span>
              <input
                type="number"
                step="any"
                value={form.latitude}
                onChange={(e) => {
                  update("latitude", e.target.value);
                  setLocationSource("manual");
                }}
                placeholder="e.g. 27.4924"
              />
            </label>
            <label>
              <span>Longitude</span>
              <input
                type="number"
                step="any"
                value={form.longitude}
                onChange={(e) => {
                  update("longitude", e.target.value);
                  setLocationSource("manual");
                }}
                placeholder="e.g. 77.6737"
              />
            </label>
          </div>
        </div>

        <label className="field">
          <span>Photo (optional)</span>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => update("photoFile", e.target.files?.[0] || null)}
          />
        </label>

        {error && <p className="form-error" role="alert">{error}</p>}

        <button type="submit" className="btn-primary" disabled={submitting}>
          {submitting ? "Submitting…" : "Submit report"}
        </button>
      </form>
    </div>
  );
}

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error("Couldn't read the selected photo."));
    reader.readAsDataURL(file);
  });
}
